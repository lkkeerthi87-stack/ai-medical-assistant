import re
from rapidfuzz import process, fuzz
import pandas as pd

# Load symptoms from CSV
df = pd.read_csv("medical_data.csv")  # columns: symptom,disease,treatment
all_symptoms = [s.lower().strip() for s in df["symptom"].tolist()]

responses = {
    "greeting": "Hello! How can I help you today?",
    "symptom": "Let me check possible causes and treatments for your symptom...",
    "goodbye": "Goodbye! Take care.",
    "unknown": "I'm not sure I understand. Could you please rephrase?",
}

# ------------------ Predict Intent ------------------
def predict_intent(text):
    text_clean = re.sub(r"\b(i have|i am having|feeling|suffering from|got|my|in|the|of)\b", "", text.lower()).strip()

    # Greeting
    if any(word in text_clean for word in ["hello", "hi", "hey", "good morning", "good evening"]):
        return "greeting"

    # Goodbye
    if any(word in text_clean for word in ["bye", "goodbye", "see you", "take care"]):
        return "goodbye"

    # Symptom fuzzy match
    matches = process.extract(text_clean, all_symptoms, scorer=fuzz.partial_ratio, limit=5)
    matched_symptoms = [m[0] for m in matches if m[1] >= 50]
    if matched_symptoms:
        return "Symptom"

    return "unknown"

def process_text(text):
    intent = predict_intent(text)
    response = responses.get(intent, responses["unknown"])
    return intent, response
