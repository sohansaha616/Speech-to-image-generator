# Speech-to-Image Generator

A Python Streamlit application that converts real-time speech to text and generates AI images with content moderation and age restrictions.

## Features

- **Real-time Audio Recording**: Record audio directly from your microphone
- **Audio File Upload**: Upload audio files in various formats (WAV, MP3, M4A, OGG)
- **Speech-to-Text**: Convert audio to text using OpenAI Whisper
- **AI Image Generation**: Generate images from text using DALL-E 3
- **Content Moderation**: Automatic filtering of inappropriate content
- **Age Restrictions**: 18+ content detection and filtering
- **Image Gallery**: View and manage generated images with content ratings

## Requirements

- Python 3.11+
- OpenAI API Key

## Installation

1. **Clone or download this project**

2. **Install dependencies:**
   ```bash
   pip install streamlit openai pillow pyaudio requests speechrecognition
   ```

3. **Set up your OpenAI API Key:**
   - Get an API key from https://platform.openai.com
   - Set it as an environment variable:
     ```bash
     export OPENAI_API_KEY="your-api-key-here"
     ```
   - Or create a `.env` file with:
     ```
     OPENAI_API_KEY=your-api-key-here
     ```

## Running the Application

```bash
streamlit run app.py
```

The app will be available at `http://localhost:8501`

## How to Use

1. **Record Audio**: Click "Start Recording" to capture 5 seconds of audio (if microphone is available)
2. **Upload Audio**: Alternatively, upload an audio file using the file uploader
3. **Convert Speech**: Click "Convert Speech to Text" to transcribe the audio
4. **Generate Image**: Edit the transcribed text if needed, then click "Generate Image"
5. **View Gallery**: Check the Image Gallery tab to see all generated images with content ratings

## File Structure

- `app.py` - Main Streamlit application
- `audio_processor.py` - Handles audio recording and speech-to-text conversion
- `image_generator.py` - Manages AI image generation using DALL-E 3
- `content_moderator.py` - Content moderation and age rating system
- `utils.py` - Utility functions for file handling and logging
- `.streamlit/config.toml` - Streamlit configuration

## Content Moderation

The app includes comprehensive content moderation:

- **Text Moderation**: Prompts are checked before image generation
- **Image Analysis**: Generated images are analyzed for content appropriateness
- **Age Ratings**: Content is rated as General, Teen, Mature, or Adult (18+)
- **Content Filtering**: 18+ content can be hidden in the gallery
- **Safety Warnings**: Clear warnings are displayed for mature content

## Microphone Compatibility

The app gracefully handles environments without microphones:
- Detects microphone availability on startup
- Disables recording features if no microphone is found
- Provides clear feedback about microphone status
- Always allows audio file uploads as an alternative

## Troubleshooting

**Microphone Issues:**
- Ensure your microphone is connected and working
- Grant microphone permissions to your browser/application
- Try uploading an audio file instead

**API Issues:**
- Verify your OpenAI API key is correct and has sufficient credits
- Check your internet connection
- Review error messages in the app for specific guidance

**Audio Format Issues:**
- Supported formats: WAV, MP3, M4A, OGG
- Keep audio files under 25MB for best performance

## Privacy and Safety

- Audio files are processed temporarily and not permanently stored
- Generated images are stored only in your current session
- Content moderation helps ensure appropriate image generation
- All API communications use secure HTTPS connections

## Credits

Built using:
- Streamlit for the web interface
- OpenAI Whisper for speech recognition
- OpenAI DALL-E 3 for image generation
- OpenAI GPT-4o for content moderation