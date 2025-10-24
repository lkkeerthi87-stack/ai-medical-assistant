from deep_translator import GoogleTranslator
import edge_tts
import asyncio
from playsound import playsound
import tempfile

# ------------------ Supported languages ------------------
# Map display name → ISO code for translation
language_code_map = {
    "English": "en",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Hindi": "hi",
    "Chinese": "zh",
    "Japanese": "ja",
    "Arabic": "ar",
    # Add more languages if needed
}

# ------------------ Translate text ------------------
def translate_text(text, target_lang="en"):
    """
    Translate text to the target language.
    """
    try:
        translated = GoogleTranslator(source='auto', target=target_lang).translate(text)
        return translated
    except Exception as e:
        print(f"[Translate] Error: {e}")
        return text  # fallback: return original text

# ------------------ Constant male voice ------------------
CONSTANT_MALE_VOICE = "en-US-GuyNeural"  # constant male voice for all languages

async def _speak_edge(text):
    """
    Internal function to convert text to speech with edge-tts and play it.
    """
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            mp3_file = f.name
        communicate = edge_tts.Communicate(text, CONSTANT_MALE_VOICE)
        await communicate.save(mp3_file)
        playsound(mp3_file)
    except Exception as e:
        print(f"[Voice] Error: {e}")

def speak_text(text):
    """
    Convert text to speech (male voice) and play it.
    """
    asyncio.run(_speak_edge(text))
