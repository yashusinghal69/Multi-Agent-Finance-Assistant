import os
import tempfile
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

def transcribe_audio_with_groq(audio_file_path, model="whisper-large-v3"):


    groq_api_key = os.getenv('GROQ_API_KEY')
    if not groq_api_key:
        return "Error: GROQ_API_KEY not found in environment variables"
    
    # Initialize Groq client
    client = Groq(api_key=groq_api_key)
    
    # Check if file exists
    if not os.path.exists(audio_file_path):
        return "Error: Audio file not found"
    
    # Transcribe audio
    with open(audio_file_path, 'rb') as audio_file:
        transcription = client.audio.transcriptions.create(
            model=model,
            file=audio_file,
            language="en"
        )
    
    return transcription.text
        

def transcribe_uploaded_audio(audio_file_path):
    return transcribe_audio_with_groq(audio_file_path)
