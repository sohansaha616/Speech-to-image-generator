import os
import requests
from openai import OpenAI
from utils import log_message

class ImageGenerator:
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def generate_image(self, prompt, size="1024x1024", quality="standard"):
        """
        Generate an image using OpenAI DALL-E based on text prompt
        
        Args:
            prompt (str): Text description for image generation
            size (str): Image size (256x256, 512x512, 1024x1024)
            quality (str): Image quality (standard, hd)
            
        Returns:
            dict: Result containing success status, URL, and error message if any
        """
        try:
            log_message(f"Generating image for prompt: {prompt[:100]}...")
            
            # Validate prompt
            if not prompt or len(prompt.strip()) == 0:
                return {
                    'success': False,
                    'error': 'Prompt cannot be empty',
                    'url': None
                }
            
            # Check prompt length (DALL-E 3 has a limit)
            if len(prompt) > 4000:
                prompt = prompt[:4000]
                log_message("Prompt truncated to 4000 characters")
            
            # Generate image using DALL-E 3
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            response = self.openai_client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size,
                quality=quality,
                n=1,
            )
            
            image_url = response.data[0].url
            log_message("Image generated successfully")
            
            return {
                'success': True,
                'url': image_url,
                'error': None,
                'revised_prompt': getattr(response.data[0], 'revised_prompt', None)
            }
            
        except Exception as e:
            error_message = str(e)
            log_message(f"Error generating image: {error_message}")
            
            # Check for specific error types
            if "content_policy_violation" in error_message.lower():
                return {
                    'success': False,
                    'error': 'Content violates OpenAI policy. Please try a different prompt.',
                    'url': None
                }
            elif "billing" in error_message.lower() or "quota" in error_message.lower():
                return {
                    'success': False,
                    'error': 'API quota exceeded or billing issue. Please check your OpenAI account.',
                    'url': None
                }
            elif "rate_limit" in error_message.lower():
                return {
                    'success': False,
                    'error': 'Rate limit exceeded. Please wait a moment and try again.',
                    'url': None
                }
            else:
                return {
                    'success': False,
                    'error': f'Image generation failed: {error_message}',
                    'url': None
                }
    
    def enhance_prompt(self, basic_prompt):
        """
        Enhance a basic prompt to get better image generation results
        
        Args:
            basic_prompt (str): Basic text prompt
            
        Returns:
            str: Enhanced prompt with artistic details
        """
        try:
            log_message("Enhancing prompt for better results...")
            
            enhancement_request = f"""
            Enhance this image prompt to be more detailed and artistic while keeping the core meaning:
            "{basic_prompt}"
            
            Add artistic style, lighting, composition details but keep it under 200 words.
            Make it suitable for DALL-E image generation.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert at writing prompts for AI image generation. Create detailed, artistic prompts that will produce high-quality images."},
                    {"role": "user", "content": enhancement_request}
                ],
                max_tokens=200
            )
            
            enhanced_prompt = response.choices[0].message.content.strip()
            log_message("Prompt enhanced successfully")
            
            return enhanced_prompt
            
        except Exception as e:
            log_message(f"Error enhancing prompt: {str(e)}")
            # Return original prompt if enhancement fails
            return basic_prompt
    
    def generate_variations(self, image_url, n=1):
        """
        Generate variations of an existing image
        
        Args:
            image_url (str): URL of the source image
            n (int): Number of variations to generate (1-4)
            
        Returns:
            dict: Result containing success status and variation URLs
        """
        try:
            log_message(f"Generating {n} variations of image...")
            
            # Download the source image
            response = requests.get(image_url)
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': 'Could not download source image',
                    'urls': []
                }
            
            # Note: DALL-E 3 doesn't support variations directly
            # This would require DALL-E 2 or a different approach
            log_message("Image variations not supported with DALL-E 3")
            
            return {
                'success': False,
                'error': 'Image variations not supported with current model',
                'urls': []
            }
            
        except Exception as e:
            log_message(f"Error generating variations: {str(e)}")
            return {
                'success': False,
                'error': f'Variation generation failed: {str(e)}',
                'urls': []
            }
    
    def validate_prompt(self, prompt):
        """
        Validate if a prompt is suitable for image generation
        
        Args:
            prompt (str): Text prompt to validate
            
        Returns:
            dict: Validation result with recommendations
        """
        try:
            validation_issues = []
            recommendations = []
            
            # Check prompt length
            if len(prompt) < 10:
                validation_issues.append("Prompt is too short")
                recommendations.append("Add more descriptive details")
            
            if len(prompt) > 4000:
                validation_issues.append("Prompt is too long")
                recommendations.append("Reduce prompt length to under 4000 characters")
            
            # Check for potentially problematic content
            problematic_words = [
                'violence', 'weapon', 'blood', 'death', 'kill', 
                'nude', 'naked', 'sexual', 'explicit'
            ]
            
            prompt_lower = prompt.lower()
            found_issues = [word for word in problematic_words if word in prompt_lower]
            
            if found_issues:
                validation_issues.append(f"Potentially problematic content: {', '.join(found_issues)}")
                recommendations.append("Consider rephrasing to avoid content policy violations")
            
            is_valid = len(validation_issues) == 0
            
            return {
                'is_valid': is_valid,
                'issues': validation_issues,
                'recommendations': recommendations
            }
            
        except Exception as e:
            log_message(f"Error validating prompt: {str(e)}")
            return {
                'is_valid': False,
                'issues': ['Validation error occurred'],
                'recommendations': ['Please try again']
            }
