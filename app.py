import streamlit as st
import openai

# Title
st.title("mediscript – Swiss Ambulatory Reports")

# Load OpenAI client
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Function to load prompt text
def load_prompt(report_type):
    if report_type == "Erstbericht":
        path = "prompts/erstbericht.txt"
    else:
        path = "prompts/verlaufsbericht.txt"

    with open(path, "r", encoding="utf-8") as f:
        return f.read()

# UI elements
report_type = st.selectbox("Berichtstyp", ["Erstbericht", "Verlaufsbericht"])

datum = st.text_input("Datum (dd.mm.yyyy)")
klinisch = st.text_area("Klinische Angaben / Verlauf")
befunde = st.text_area("Labor / Bildgebung")
therapie = st.text_area("Therapie / Medikation")

# Generate report
if st.button("Bericht generieren"):
    system_prompt = load_prompt(report_type)

    user_input = f"""
    Datum: {datum}
    Klinische Angaben: {klinisch}
    Befunde: {befunde}
    Therapie: {therapie}
    """

response = openai.ChatCompletion.create(
    model="gpt-4o-mini",
    temperature=0.2,
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]
)

    st.text_area(
        "Generierter Bericht",
        response.choices[0].message.content,
        height=400
    )
