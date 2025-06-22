import os
import tempfile
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

def log_message(message, level='info'):
    """
    Log a message with timestamp
    
    Args:
        message (str): Message to log
        level (str): Log level (info, warning, error, debug)
    """
    logger = logging.getLogger(__name__)
    
    if level.lower() == 'info':
        logger.info(message)
    elif level.lower() == 'warning':
        logger.warning(message)
    elif level.lower() == 'error':
        logger.error(message)
    elif level.lower() == 'debug':
        logger.debug(message)
    else:
        logger.info(message)

def save_audio_file(audio_data, file_extension='.wav'):
    """
    Save audio data to a temporary file
    
    Args:
        audio_data (bytes): Audio data as bytes
        file_extension (str): File extension for the audio file
        
    Returns:
        str: Path to the saved temporary file
    """
    try:
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(
            suffix=file_extension, 
            delete=False
        )
        
        # Write audio data
        temp_file.write(audio_data)
        temp_file.close()
        
        log_message(f"Audio saved to temporary file: {temp_file.name}")
        return temp_file.name
        
    except Exception as e:
        log_message(f"Error saving audio file: {str(e)}", 'error')
        raise

def display_error(error_message, error_type="Error"):
    """
    Format error message for display
    
    Args:
        error_message (str): Error message to display
        error_type (str): Type of error (Error, Warning, etc.)
        
    Returns:
        str: Formatted error message
    """
    timestamp = datetime.now().strftime("%H:%M:%S")
    return f"[{timestamp}] {error_type}: {error_message}"

def validate_api_key():
    """
    Validate that required API keys are available
    
    Returns:
        dict: Validation result with status and missing keys
    """
    required_keys = {
        'OPENAI_API_KEY': 'OpenAI API key for image generation and speech processing'
    }
    
    missing_keys = []
    available_keys = []
    
    for key, description in required_keys.items():
        if os.getenv(key):
            available_keys.append(key)
        else:
            missing_keys.append({'key': key, 'description': description})
    
    return {
        'is_valid': len(missing_keys) == 0,
        'missing_keys': missing_keys,
        'available_keys': available_keys
    }

def format_file_size(size_bytes):
    """
    Format file size in human readable format
    
    Args:
        size_bytes (int): Size in bytes
        
    Returns:
        str: Formatted size string
    """
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"

def get_supported_audio_formats():
    """
    Get list of supported audio formats
    
    Returns:
        list: List of supported audio file extensions
    """
    return ['.wav', '.mp3', '.m4a', '.ogg', '.flac', '.aac']

def cleanup_temp_files(file_paths):
    """
    Clean up temporary files
    
    Args:
        file_paths (list): List of file paths to delete
    """
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                log_message(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            log_message(f"Error cleaning up file {file_path}: {str(e)}", 'warning')

def format_duration(seconds):
    """
    Format duration in seconds to human readable format
    
    Args:
        seconds (float): Duration in seconds
        
    Returns:
        str: Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{int(minutes)}m {int(remaining_seconds)}s"
    else:
        hours = seconds // 3600
        remaining_minutes = (seconds % 3600) // 60
        return f"{int(hours)}h {int(remaining_minutes)}m"

def safe_filename(filename):
    """
    Create a safe filename by removing/replacing unsafe characters
    
    Args:
        filename (str): Original filename
        
    Returns:
        str: Safe filename
    """
    import re
    
    # Remove or replace unsafe characters
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing spaces and dots
    safe_name = safe_name.strip(' .')
    
    # Ensure filename is not empty
    if not safe_name:
        safe_name = f"file_{int(time.time())}"
    
    return safe_name

def check_microphone_permissions():
    """
    Check if microphone permissions are available
    
    Returns:
        bool: True if microphone is accessible, False otherwise
    """
    try:
        import pyaudio
        
        # Try to initialize PyAudio
        audio = pyaudio.PyAudio()
        
        # Check if any input devices are available
        device_count = audio.get_device_count()
        has_input_device = False
        
        for i in range(device_count):
            device_info = audio.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:
                has_input_device = True
                break
        
        audio.terminate()
        
        if not has_input_device:
            log_message("No input audio devices found", 'warning')
            return False
        
        log_message("Microphone permissions check passed")
        return True
        
    except Exception as e:
        log_message(f"Microphone permission check failed: {str(e)}", 'error')
        return False

def estimate_processing_time(audio_duration):
    """
    Estimate processing time based on audio duration
    
    Args:
        audio_duration (float): Audio duration in seconds
        
    Returns:
        float: Estimated processing time in seconds
    """
    # Rough estimates based on typical processing times
    speech_to_text_time = audio_duration * 0.3  # Usually faster than real-time
    image_generation_time = 15  # DALL-E typically takes 10-20 seconds
    moderation_time = 3  # Quick analysis
    
    total_time = speech_to_text_time + image_generation_time + moderation_time
    
    return max(5, total_time)  # Minimum 5 seconds

def get_system_info():
    """
    Get basic system information for debugging
    
    Returns:
        dict: System information
    """
    import platform
    import sys
    
    return {
        'platform': platform.platform(),
        'python_version': sys.version,
        'timestamp': datetime.now().isoformat(),
        'available_apis': {
            'openai': bool(os.getenv('OPENAI_API_KEY'))
        }
    }
