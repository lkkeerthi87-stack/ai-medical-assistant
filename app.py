import streamlit as st
import re
import asyncio
import threading
import random
import time
from utils.db import init_db, get_diagnosis, all_symptoms
from utils.reminder import schedule_reminder_at
from utils.translator import translate_text, language_code_map
import edge_tts
import nest_asyncio
import base64
import pandas as pd

# ------------------ Fix asyncio for Streamlit ------------------
nest_asyncio.apply()

# ------------------ Initialize session flags ------------------
if "voice_enabled" not in st.session_state:
    st.session_state.voice_enabled = True

# ------------------ NLP LOGIC ------------------
responses = {
    "greeting": ["Hello! How can I help you today?"],
    "symptom": ["Let me check possible causes and treatments for your symptom..."],
    "goodbye": ["Goodbye! Take care."],
    "unknown": ["I'm not sure I understand. Could you please rephrase?"]
}

# ------------------ Intent Prediction ------------------
def predict_intent(text):
    text = text.lower().strip()
    if any(word in text for word in ["hello", "hi", "hey", "good morning", "good evening"]):
        return "greeting"
    if any(word in text for word in ["bye", "goodbye", "see you", "take care"]):
        return "goodbye"
    if any(symptom.lower() in text for symptom in all_symptoms):
        return "symptom"
    return "unknown"

def process_text(text):
    return predict_intent(text)

# ------------------ Initialization ------------------
if "db_initialized" not in st.session_state:
    init_db()
    st.session_state.db_initialized = True

if "user_input" not in st.session_state:
    st.session_state.user_input = ""

if "conversation" not in st.session_state:
    st.session_state.conversation = []

if "selected_language" not in st.session_state:
    st.session_state.selected_language = "English"

# ------------------ UI Setup ------------------
st.set_page_config(page_title="AI Medical Assistant", page_icon="🩺", layout="centered")
st.title("🩺 Medi Assistant CHATBOT")
st.markdown("### Your smart companion for quick symptom checks and medical assistance.")
chat_container = st.container()

# ------------------ Bot Language Selector ------------------
st.selectbox(
    "🌐 Select bot response language",
    list(language_code_map.keys()),
    index=list(language_code_map.keys()).index(st.session_state.selected_language),
    key="selected_language"
)

# ------------------ Voice Toggle ------------------
st.checkbox("🔊 Enable Voice", value=st.session_state.voice_enabled, key="voice_enabled")

# ------------------ Voice Map for Edge TTS ------------------
voice_map = {
    "en": "en-US-GuyNeural",
    "es": "es-ES-AlvaroNeural",
    "fr": "fr-FR-HenriNeural",
    "de": "de-DE-KarlNeural",
    "hi": "hi-IN-SwaraNeural",
    "ta": "ta-IN-ValluvarNeural",
    "zh": "zh-CN-YunxiNeural",
    "ja": "ja-JP-KeitaNeural",
    "ar": "ar-SA-HamedNeural"
}

# ------------------ Speak Bot ------------------
async def speak_bot(text_lines, lang_code):
    if not st.session_state.voice_enabled:
        return  # Skip voice playback

    text_lines = [line.strip() for line in text_lines if line.strip()]
    if not text_lines:
        return
    lang_key = lang_code[:2]
    voice_name = voice_map.get(lang_key, "en-US-GuyNeural")
    full_text = " ".join(text_lines)
    try:
        communicate = edge_tts.Communicate(full_text, voice_name)
        await communicate.save("bot_speech.mp3")
        with open("bot_speech.mp3", "rb") as f:
            audio_bytes = f.read()
        b64_audio = base64.b64encode(audio_bytes).decode()
        audio_html = f"""
        <audio autoplay hidden>
            <source src="data:audio/mp3;base64,{b64_audio}" type="audio/mp3">
        </audio>
        """
        st.components.v1.html(audio_html, height=0)
    except edge_tts.exceptions.NoAudioReceived as e:
        st.error("❌ No audio received. Check text content and voice settings.")
        print("NoAudioReceived:", e)

def speak_bot_async(text_lines, lang_code):
    asyncio.run(speak_bot(text_lines, lang_code))

# ------------------ Process Input ------------------
def process_input(user_input):
    user_input = user_input.strip()
    if not user_input:
        return

    st.session_state.conversation.append({"role": "user", "message": user_input})
    intent = process_text(user_input)
    bot_lines = []

    if intent == "symptom":
        diagnosis_list, treatment_list = get_diagnosis(user_input, top_n=10)
        if diagnosis_list:
            st.session_state.conversation.append({"role": "bot", "message": "🧾 Possible Diagnoses:"})

            results_df = pd.DataFrame({
                "Disease": diagnosis_list,
                "Treatment": treatment_list
            })
            st.session_state.conversation.append({"role": "bot_table", "table": results_df})

            table_text = ""
            for d, t in zip(diagnosis_list, treatment_list):
                table_text += f"Disease: {d}. Treatment: {t}. "

            bot_lines.append("🧾 Possible Diagnoses:")
            bot_lines.append(table_text)
        else:
            bot_lines.append("❌ No related condition found. Please consult a doctor.")
    else:
        bot_lines.append(responses.get(intent, ["Sorry, I didn’t understand that."])[0])

    target_lang_code = language_code_map.get(st.session_state.selected_language, "en")
    translated_lines = []
    for line in bot_lines:
        translated_line = translate_text(line, target_lang_code)
        translated_lines.append(translated_line)
        st.session_state.conversation.append({"role": "bot", "message": translated_line})

    speak_bot_async(translated_lines, target_lang_code)
    st.session_state.user_input = ""
    update_chat_display()

# ------------------ Update Chat Display ------------------
def update_chat_display():
    with chat_container:
        for msg in st.session_state.conversation:
            if msg["role"] == "user":
                st.markdown(f"**You:** {msg['message']}")
            elif msg["role"] == "bot":
                st.markdown(f"**Bot:** {msg['message']}")
            elif msg["role"] == "bot_table":
                st.dataframe(msg["table"], use_container_width=True, height=250)

# ------------------ Input Section ------------------
text_input = st.text_input(
    "Type your message:",
    value=st.session_state.user_input,
    placeholder="e.g., I have joint pain or headache..."
)
if text_input:
    st.session_state.user_input = text_input
    process_input(text_input)

# ------------------ Medicine Reminder Section ------------------
st.markdown("### ⏰ Set a Medicine Reminder")
col1, col2 = st.columns([2, 3])
with col1:
    reminder_time = st.text_input("Enter time (HH:MM)", placeholder="e.g., 14:30")
with col2:
    reminder_message = st.text_input("Reminder message", value="Time to take your medicine!")

if st.button("Set Reminder"):
    if reminder_time.strip():
        try:
            schedule_reminder_at(reminder_time, reminder_message, sound_file="alarm.mp3")
            st.success(f"✅ Reminder set at {reminder_time}")
        except Exception as e:
            st.error(f"❌ Failed to set reminder: {e}")
    else:
        st.warning("⚠️ Please enter a valid time")

# ------------------ Dynamic Footer with Rotating Health Quotes ------------------
health_quotes = [
    "Health is wealth. – Proverb",
    "To keep the body in good health is a duty… otherwise we shall not be able to keep our mind strong and clear. – Buddha",
    "It is health that is real wealth and not pieces of gold and silver. – Mahatma Gandhi",
    "Take care of your body. It’s the only place you have to live. – Jim Rohn",
    "The greatest wealth is health. – Virgil",
    "Those who think they have no time for exercise will sooner or later have to find time for illness. – Edward Stanley",
    "Let food be thy medicine and medicine be thy food. – Hippocrates",
    "Calm mind brings inner strength and self-confidence, so that’s very important for good health. – Dalai Lama",
    "Your diet is a bank account. Good food choices are good investments. – Bethenny Frankel",
    "The mind and body are not separate. What affects one, affects the other. – Unknown"
]

footer_container = st.empty()

def show_dynamic_footer():
    while True:
        quote = random.choice(health_quotes)
        footer_container.markdown("---")
        footer_container.caption(f"💡 Health Tip: {quote}")
        time.sleep(10)

threading.Thread(target=show_dynamic_footer, daemon=True).start()
