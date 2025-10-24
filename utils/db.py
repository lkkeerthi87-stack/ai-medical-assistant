# utils/db.py
import pandas as pd
from rapidfuzz import process, fuzz

DATA_PATH = "medical_data.csv"
df = None
all_symptoms = []  # <-- list of all symptoms for intent detection

def init_db():
    """
    Initialize the medical database.
    Normalizes column names and strips extra spaces.
    """
    global df, all_symptoms
    try:
        df = pd.read_csv(DATA_PATH)
    except FileNotFoundError:
        raise FileNotFoundError(f"CSV file not found at path: {DATA_PATH}")

    # Normalize headers: strip spaces + lowercase
    df.columns = df.columns.str.strip().str.lower()

    # Required columns in lowercase
    expected_cols = ["symptom", "possible diseases", "treatment"]
    missing_cols = [col for col in expected_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"CSV missing required columns: {missing_cols}")

    # Clean string columns
    for col in expected_cols:
        df[col] = df[col].astype(str).str.strip()

    # Prepare lowercase symptom list for intent detection
    all_symptoms = [s.lower() for s in df['symptom'].tolist()]

    print(f"✅ Database loaded successfully with {len(df)} records and {len(all_symptoms)} symptoms.")

def get_diagnosis(user_input, top_n=5):
    """
    Returns the top_n matching diseases and treatments for the given symptom.
    Uses fuzzy string matching.
    """
    global df
    if df is None:
        raise ValueError("Database not initialized. Call init_db() first.")

    user_input_clean = user_input.strip().lower()
    symptoms_list = df['symptom'].tolist()

    # Fuzzy match
    matches = process.extract(
        user_input_clean,
        symptoms_list,
        scorer=fuzz.WRatio,
        limit=top_n
    )

    diagnosis_list = []
    treatment_list = []

    for match_symptom, score, idx in matches:
        if score < 60:  # ignore poor matches
            continue
        row = df.iloc[idx]
        diagnosis_list.append(row['possible diseases'])
        treatment_list.append(row['treatment'])

    if not diagnosis_list:
        return ["No matching disease found"], ["Please consult a doctor for proper treatment."]

    return diagnosis_list, treatment_list
