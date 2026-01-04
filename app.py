import streamlit as st
import openai

# -------------------------------
# Set OpenAI API key from Streamlit Secrets
# -------------------------------
openai.api_key = st.secrets["OPENAI_API_KEY"]

# -------------------------------
# Function to load prompts
# -------------------------------
def load_prompt(report_type):
    if report_type == "Erstbericht":
        path = "prompts/erstbericht.txt"
    else:
        path = "prompts/verlaufsbericht.txt"
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

# -------------------------------
# Streamlit UI
# -------------------------------
st.title("mediscript – Swiss Ambulatory Reports")

report_type = st.selectbox("Berichtstyp", ["Erstbericht", "Verlaufsbericht"])
datum = st.text_input("Datum (dd.mm.yyyy)")
klinisch = st.text_area("Klinische Angaben / Verlauf")
befunde = st.text_area("Labor / Bildgebung")
therapie = st.text_area("Therapie / Medikation")

# -------------------------------
# Generate report button
# -------------------------------
if st.button("Bericht generieren"):

    system_prompt = load_prompt(report_type)

    user_input = f"""
Datum: {datum}
Klinische Angaben: {klinisch}
Befunde: {befunde}
Therapie: {therapie}
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
        )

        report_text = response.choices[0].message.content

    except Exception as e:
        report_text = f"Fehler bei der Berichtserstellung: {e}"

    st.text_area("Generierter Bericht", report_text, height=400)
