# tools/transcribe.py
from langchain_core.tools import tool
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

@tool
def transcribe_audio(filename: str) -> str:
    """
    Transcribe speech from an audio file into text.
    Use this immediately after downloading an .mp3 or .wav file to know what is said inside it.

    Args:
        filename (str): The filename of the audio (e.g., 'audio.mp3') located in LLMFiles/.

    Returns:
        str: The transcribed text.
    """
    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return "Error: GROQ_API_KEY not found."

        # Initialize Groq Client
        client = Groq(api_key=api_key)
        
        # Construct full path (assuming download_file saves to LLMFiles)
        file_path = os.path.join("LLMFiles", filename)
        
        if not os.path.exists(file_path):
            return f"Error: File {file_path} does not exist. Did you download it first?"

        # Open file and send to Groq Whisper
        with open(file_path, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(filename, file.read()),
                model="distil-whisper-large-v3-en", # Fast and accurate English model
                response_format="json",
                temperature=0.0
            )
            
        return transcription.text

    except Exception as e:
        return f"Error transcribing audio: {str(e)}"
