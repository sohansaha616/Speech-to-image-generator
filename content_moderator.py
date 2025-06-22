import os
import json
from openai import OpenAI
from PIL import Image
import base64
import io
from utils import log_message

class ContentModerator:
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Define content categories and thresholds
        self.adult_keywords = [
            'nude', 'naked', 'sexual', 'explicit', 'adult', 'pornographic',
            'erotic', 'intimate', 'seductive', 'provocative', 'sensual'
        ]
        
        self.violence_keywords = [
            'violence', 'violent', 'weapon', 'gun', 'blood', 'death', 'kill',
            'murder', 'fight', 'battle', 'war', 'destruction', 'harm'
        ]
        
        self.inappropriate_keywords = [
            'hate', 'racist', 'discriminatory', 'offensive', 'inappropriate',
            'illegal', 'drugs', 'gambling', 'extremist'
        ]
    
    def moderate_text(self, text):
        """
        Moderate text content for appropriateness
        
        Args:
            text (str): Text to moderate
            
        Returns:
            dict: Moderation result with safety status and reason
        """
        try:
            log_message(f"Moderating text content: {text[:50]}...")
            
            # Use OpenAI's moderation endpoint
            response = self.openai_client.moderations.create(input=text)
            
            moderation_result = response.results[0]
            
            # Check if content is flagged
            if moderation_result.flagged:
                flagged_categories = []
                categories = moderation_result.categories
                
                # Check specific categories
                if categories.sexual:
                    flagged_categories.append("sexual content")
                if categories.violence:
                    flagged_categories.append("violent content")
                if categories.hate:
                    flagged_categories.append("hate speech")
                if categories.harassment:
                    flagged_categories.append("harassment")
                if categories.self_harm:
                    flagged_categories.append("self-harm content")
                
                reason = f"Content flagged for: {', '.join(flagged_categories)}"
                
                return {
                    'is_safe': False,
                    'reason': reason,
                    'flagged_categories': flagged_categories,
                    'confidence': max(moderation_result.category_scores.__dict__.values())
                }
            
            # Additional keyword-based checking
            text_lower = text.lower()
            found_issues = []
            
            # Check for adult content keywords
            adult_matches = [word for word in self.adult_keywords if word in text_lower]
            if adult_matches:
                found_issues.append("adult content indicators")
            
            # Check for violence keywords
            violence_matches = [word for word in self.violence_keywords if word in text_lower]
            if violence_matches:
                found_issues.append("violent content indicators")
            
            # Check for inappropriate keywords
            inappropriate_matches = [word for word in self.inappropriate_keywords if word in text_lower]
            if inappropriate_matches:
                found_issues.append("inappropriate content indicators")
            
            if found_issues:
                return {
                    'is_safe': False,
                    'reason': f"Detected: {', '.join(found_issues)}",
                    'flagged_categories': found_issues,
                    'confidence': 0.7
                }
            
            log_message("Text content approved")
            return {
                'is_safe': True,
                'reason': 'Content approved',
                'flagged_categories': [],
                'confidence': 0.1
            }
            
        except Exception as e:
            log_message(f"Error moderating text: {str(e)}")
            # Err on the side of caution
            return {
                'is_safe': False,
                'reason': f'Moderation error: {str(e)}',
                'flagged_categories': ['error'],
                'confidence': 1.0
            }
    
    def moderate_image(self, image):
        """
        Moderate image content for age-appropriateness
        
        Args:
            image (PIL.Image): Image to moderate
            
        Returns:
            dict: Moderation result with content rating
        """
        try:
            log_message("Moderating image content...")
            
            # Convert image to base64 for analysis
            image_base64 = self._image_to_base64(image)
            
            # Use OpenAI Vision API to analyze image content
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a content moderator. Analyze this image and determine if it contains:
                        1. Adult/sexual content (nudity, sexual situations, etc.)
                        2. Violent content (weapons, blood, violence, etc.)
                        3. Inappropriate content for general audiences
                        
                        Respond with JSON in this format:
                        {
                            "is_adult_content": boolean,
                            "is_violent": boolean,
                            "is_inappropriate": boolean,
                            "content_rating": "general" | "teen" | "mature" | "adult",
                            "description": "brief description of concerning elements if any",
                            "confidence": number between 0 and 1
                        }"""
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Please analyze this image for content moderation."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=300
            )
            
            try:
                analysis = json.loads(response.choices[0].message.content)
            except json.JSONDecodeError:
                # Fallback parsing
                analysis = {
                    "is_adult_content": False,
                    "is_violent": False,
                    "is_inappropriate": False,
                    "content_rating": "general",
                    "description": "Analysis failed",
                    "confidence": 0.5
                }
            
            log_message(f"Image moderation completed: {analysis['content_rating']}")
            
            return {
                'is_adult_content': analysis.get('is_adult_content', False),
                'is_violent': analysis.get('is_violent', False),
                'is_inappropriate': analysis.get('is_inappropriate', False),
                'content_rating': analysis.get('content_rating', 'general'),
                'description': analysis.get('description', ''),
                'confidence': analysis.get('confidence', 0.5),
                'requires_warning': analysis.get('is_adult_content', False) or 
                                  analysis.get('is_violent', False) or 
                                  analysis.get('is_inappropriate', False)
            }
            
        except Exception as e:
            log_message(f"Error moderating image: {str(e)}")
            
            # Return conservative moderation result on error
            return {
                'is_adult_content': True,
                'is_violent': False,
                'is_inappropriate': True,
                'content_rating': 'adult',
                'description': f'Moderation error: {str(e)}',
                'confidence': 1.0,
                'requires_warning': True
            }
    
    def _image_to_base64(self, image):
        """
        Convert PIL Image to base64 string
        
        Args:
            image (PIL.Image): Image to convert
            
        Returns:
            str: Base64 encoded image
        """
        try:
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize image if too large (to save on API costs)
            max_size = (1024, 1024)
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Convert to base64
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=85)
            image_bytes = buffer.getvalue()
            
            return base64.b64encode(image_bytes).decode('utf-8')
            
        except Exception as e:
            log_message(f"Error converting image to base64: {str(e)}")
            raise
    
    def get_content_rating_description(self, rating):
        """
        Get description for content rating
        
        Args:
            rating (str): Content rating
            
        Returns:
            str: Description of the rating
        """
        descriptions = {
            'general': 'Suitable for all ages',
            'teen': 'Suitable for ages 13 and up',
            'mature': 'Suitable for ages 17 and up',
            'adult': 'Suitable for ages 18 and up only'
        }
        
        return descriptions.get(rating, 'Unknown rating')
    
    def should_show_warning(self, moderation_result):
        """
        Determine if content warning should be shown
        
        Args:
            moderation_result (dict): Result from moderate_image
            
        Returns:
            bool: True if warning should be shown
        """
        return (
            moderation_result.get('is_adult_content', False) or
            moderation_result.get('is_violent', False) or
            moderation_result.get('is_inappropriate', False) or
            moderation_result.get('content_rating', 'general') in ['mature', 'adult']
        )
