import streamlit as st
import os
import tempfile
import time
from PIL import Image
import requests
from io import BytesIO

from audio_processor import AudioProcessor
from image_generator import ImageGenerator
from content_moderator import ContentModerator
from utils import save_audio_file, display_error, log_message

# Initialize session state
if 'generated_images' not in st.session_state:
    st.session_state.generated_images = []
if 'audio_processor' not in st.session_state:
    st.session_state.audio_processor = AudioProcessor()
if 'image_generator' not in st.session_state:
    st.session_state.image_generator = ImageGenerator()
if 'content_moderator' not in st.session_state:
    st.session_state.content_moderator = ContentModerator()

def main():
    st.title("🎤 Speech-to-Image Generator")
    st.markdown("Record your voice, convert to text, and generate AI images with content moderation")
    
    # Check API key availability
    if not os.getenv("OPENAI_API_KEY"):
        st.error("⚠️ OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
        st.stop()
    
    # Main interface tabs
    tab1, tab2, tab3 = st.tabs(["🎙️ Record & Generate", "🖼️ Image Gallery", "⚙️ Settings"])
    
    with tab1:
        st.header("Record Audio")
        
        # Check microphone availability
        microphone_available = st.session_state.audio_processor.microphone_available
        
        if not microphone_available:
            st.warning("⚠️ Microphone not available in this environment. Please upload an audio file instead.")
        
        # Audio recording section
        col1, col2 = st.columns([1, 1])
        
        with col1:
            record_button_disabled = not microphone_available
            if st.button("🎤 Start Recording", type="primary", disabled=record_button_disabled):
                with st.spinner("Recording... Speak now!"):
                    # Record audio for 5 seconds (can be adjusted)
                    audio_data = st.session_state.audio_processor.record_audio(duration=5)
                    if audio_data:
                        st.success("✅ Recording completed!")
                        st.session_state.recorded_audio = audio_data
                    else:
                        st.error("❌ Failed to record audio. Please check your microphone.")
        
        with col2:
            # Upload audio file option
            uploaded_file = st.file_uploader("Or upload an audio file", type=['wav', 'mp3', 'm4a', 'ogg'])
            if uploaded_file is not None:
                st.session_state.recorded_audio = uploaded_file.read()
                st.success("✅ Audio file uploaded!")
        
        # Process recorded audio
        if hasattr(st.session_state, 'recorded_audio'):
            st.header("Speech-to-Text Conversion")
            
            if st.button("🔄 Convert Speech to Text"):
                with st.spinner("Converting speech to text..."):
                    try:
                        # Save audio to temporary file
                        temp_audio_path = save_audio_file(st.session_state.recorded_audio)
                        
                        # Convert speech to text
                        transcribed_text = st.session_state.audio_processor.speech_to_text(temp_audio_path)
                        
                        if transcribed_text:
                            st.session_state.transcribed_text = transcribed_text
                            st.success("✅ Speech converted to text successfully!")
                            st.text_area("Transcribed Text:", value=transcribed_text, height=100)
                        else:
                            st.error("❌ Could not transcribe audio. Please try again with clearer speech.")
                        
                        # Clean up temporary file
                        os.unlink(temp_audio_path)
                        
                    except Exception as e:
                        st.error(f"❌ Error during speech-to-text conversion: {str(e)}")
                        log_message(f"Speech-to-text error: {str(e)}")
        
        # Generate image from text
        if hasattr(st.session_state, 'transcribed_text'):
            st.header("Text-to-Image Generation")
            
            # Show the text that will be used for image generation
            text_to_generate = st.text_area(
                "Edit prompt if needed:", 
                value=st.session_state.transcribed_text, 
                height=100,
                key="image_prompt"
            )
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                if st.button("🎨 Generate Image", type="primary"):
                    if text_to_generate.strip():
                        with st.spinner("Generating image... This may take a moment."):
                            try:
                                # Check content moderation first
                                moderation_result = st.session_state.content_moderator.moderate_text(text_to_generate)
                                
                                if not moderation_result['is_safe']:
                                    st.error(f"❌ Content blocked: {moderation_result['reason']}")
                                    st.warning("🔞 This content is not appropriate for image generation.")
                                else:
                                    # Generate image
                                    image_result = st.session_state.image_generator.generate_image(text_to_generate)
                                    
                                    if image_result['success']:
                                        # Download and display image
                                        response = requests.get(image_result['url'])
                                        image = Image.open(BytesIO(response.content))
                                        
                                        # Moderate the generated image
                                        image_moderation = st.session_state.content_moderator.moderate_image(image)
                                        
                                        # Store in session state
                                        image_data = {
                                            'image': image,
                                            'prompt': text_to_generate,
                                            'timestamp': time.time(),
                                            'moderation': image_moderation
                                        }
                                        st.session_state.generated_images.append(image_data)
                                        
                                        # Display image with appropriate warnings
                                        st.success("✅ Image generated successfully!")
                                        
                                        if image_moderation['is_adult_content']:
                                            st.warning("🔞 **18+ Content Warning**: This image may contain mature content.")
                                        
                                        st.image(image, caption=f"Generated from: '{text_to_generate}'", use_column_width=True)
                                        
                                    else:
                                        st.error(f"❌ Failed to generate image: {image_result['error']}")
                                        
                            except Exception as e:
                                st.error(f"❌ Error during image generation: {str(e)}")
                                log_message(f"Image generation error: {str(e)}")
                    else:
                        st.warning("⚠️ Please enter some text to generate an image.")
            
            with col2:
                if st.button("🗑️ Clear All Data"):
                    # Clear session state
                    for key in ['recorded_audio', 'transcribed_text', 'generated_images']:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.session_state.generated_images = []
                    st.success("✅ All data cleared!")
                    st.rerun()
    
    with tab2:
        st.header("Generated Image Gallery")
        
        if st.session_state.generated_images:
            st.write(f"Total images: {len(st.session_state.generated_images)}")
            
            # Filter options
            show_adult_content = st.checkbox("🔞 Show 18+ content", value=False)
            
            # Display images in reverse chronological order
            for idx, image_data in enumerate(reversed(st.session_state.generated_images)):
                # Skip adult content if filter is enabled
                if image_data['moderation']['is_adult_content'] and not show_adult_content:
                    continue
                
                with st.expander(f"Image {len(st.session_state.generated_images) - idx}: {image_data['prompt'][:50]}..."):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        if image_data['moderation']['is_adult_content']:
                            st.warning("🔞 **18+ Content Warning**")
                        
                        st.image(image_data['image'], use_column_width=True)
                    
                    with col2:
                        st.write("**Prompt:**")
                        st.write(image_data['prompt'])
                        st.write("**Generated:**")
                        st.write(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(image_data['timestamp'])))
                        
                        if image_data['moderation']['is_adult_content']:
                            st.write("**Content Rating:** 18+")
                        else:
                            st.write("**Content Rating:** General")
        else:
            st.info("📭 No images generated yet. Use the 'Record & Generate' tab to create your first image!")
    
    with tab3:
        st.header("Settings & Information")
        
        st.subheader("🔧 Configuration")
        st.write("**OpenAI API Status:**", "✅ Connected" if os.getenv("OPENAI_API_KEY") else "❌ Not configured")
        
        st.subheader("ℹ️ How it works")
        st.write("""
        1. **Record Audio**: Click 'Start Recording' to capture 5 seconds of audio from your microphone
        2. **Speech-to-Text**: The audio is processed using OpenAI's Whisper model
        3. **Content Moderation**: Text is checked for inappropriate content
        4. **Image Generation**: Safe prompts are sent to DALL-E 3 for image creation
        5. **Image Moderation**: Generated images are analyzed for age-appropriate content
        6. **Display**: Images are shown with appropriate content warnings
        """)
        
        st.subheader("🛡️ Content Moderation")
        st.write("""
        - Text prompts are automatically screened for inappropriate content
        - Generated images are analyzed for mature content
        - 18+ content is clearly labeled and can be filtered in the gallery
        - Inappropriate prompts are blocked before image generation
        """)
        
        st.subheader("🎤 Audio Tips")
        st.write("""
        - Speak clearly and at a normal pace
        - Ensure your microphone is working and permissions are granted
        - Record in a quiet environment for best results
        - You can also upload audio files (WAV, MP3, M4A, OGG)
        """)

if __name__ == "__main__":
    main()
