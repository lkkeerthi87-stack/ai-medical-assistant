import os
from gtts import gTTS
from playsound import playsound

def speak_bot(text_lines, language="en"):
    """
    Speak a list of bot messages in the selected language.

    Parameters:
        text_lines (list): List of strings to speak.
        language (str): Language code for TTS (e.g., "en", "hi", "ta").
    """
    full_text = " ".join(text_lines)
    try:
        tts = gTTS(text=full_text, lang=language)
        audio_file = "bot_speech.mp3"
        tts.save(audio_file)
        playsound(audio_file)
        os.remove(audio_file)
    except Exception as e:
        print(f"[Voice] Error: {e}")
