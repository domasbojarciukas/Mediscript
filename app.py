import streamlit as st
import openai

# -------------------------------
# OpenAI API key from Streamlit Secrets
# -------------------------------
openai.api_key = st.secrets["OPENAI_API_KEY"]

# -------------------------------
# Function to load system prompt
# -------------------------------
def load_prompt(report_type):
    if report_type == "Ambulanter Erstbericht":
        path = "prompts/erstbericht.txt"
    else:
        path = "prompts/verlaufsbericht.txt"
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

# -------------------------------
# Streamlit UI
# -------------------------------
st.title("Mediscript – Schweizer Medizinische Dokumentation")

report_type = st.selectbox("Berichtstyp", ["Ambulanter Erstbericht", "Ambulanter Verlaufsbericht"])

# Dynamically display fields depending on report type
if report_type == "Ambulanter Erstbericht":
    zuweisung = st.text_input("Zuweisung (Wer, Datum, Anlass)")
    verdachtsdiagnose = st.text_area("Verdachtsdiagnose")
    befunde = st.text_area("Befunde (Labor, Bilder, Untersuchung)")
    klinische_einschaetzung = st.text_area("Klinische Einschätzung")
    therapeutisches_vorgehen = st.text_area("Therapeutisches Vorgehen")

elif report_type == "Ambulanter Verlaufsbericht":
    patient = st.text_input("Patient / Verlaufskontrolle am (Datum)")
    verlauf = st.text_area("Verlauf seit letzter Konsultation")
    neue_befunde = st.text_area("Neue Befunde")
    beurteilung = st.text_area("Beurteilung")
    therapie_weiteres = st.text_area("Therapie / Weiteres Vorgehen")

# -------------------------------
# Generate report button
# -------------------------------
if st.button("Bericht generieren"):

    system_prompt = load_prompt(report_type)

    # Build user input depending on report type
    if report_type == "Ambulanter Erstbericht":
        user_input = f"""
Zuweisung: {zuweisung}
Verdachtsdiagnose: {verdachtsdiagnose}
Befunde: {befunde}
Klinische Einschätzung: {klinische_einschaetzung}
Therapeutisches Vorgehen: {therapeutisches_vorgehen}
"""
    else:
        user_input = f"""
Patient: {patient}
Verlauf seit letzter Konsultation: {verlauf}
Neue Befunde: {neue_befunde}
Beurteilung: {beurteilung}
Therapie / Weiteres Vorgehen: {therapie_weiteres}
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4.1",
            temperature=0.3,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
        )

        report_text = response.choices[0].message.content

    except Exception as e:
        report_text = f"Fehler bei der Berichtserstellung: {e}"

    st.text_area("Generierter Bericht", report_text, height=500)
