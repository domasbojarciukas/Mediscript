import streamlit as st
from openai import OpenAI

# -----------------------------
# Streamlit page config + hide header/footer
# -----------------------------
st.set_page_config(page_title="Mediscript", layout="centered")

st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True
)

# -----------------------------
# OpenAI client using Streamlit secrets
# -----------------------------
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# -----------------------------
# App title
# -----------------------------
st.title("Mediscript - Testphase")

# -----------------------------
# Select document type
# -----------------------------
doc_type = st.selectbox(
    "Dokumenttyp auswählen",
    ("Ambulanter Erstbericht", "Ambulanter Verlaufsbericht", "Kostengutsprache Medikament", "Kostengutsprache Rehabilitation", "Stationärer Bericht")
)

# -----------------------------
# Define input fields per doc type
# -----------------------------
user_input = ""

if doc_type == "Ambulanter Erstbericht":
    z = st.text_input("Zuweisung (Wer, Datum, Anlass)")
    vd = st.text_input("Klinische Verdachtsdiagnose")
    befunde = st.text_area("Befunde (Labor, Bilder, Untersuchung)", height=120)
    einschätzung = st.text_area("Klinische Einschätzung", height=120)
    therapeutisch = st.text_area("Therapeutisches Vorgehen", height=100)
    user_input = f"Zuweisung: {z}\nVerdachtsdiagnose: {vd}\nBefunde: {befunde}\nEinschätzung: {einschätzung}\nTherapeutisches Vorgehen: {therapeutisch}"

elif doc_type == "Ambulanter Verlaufsbericht":
    patient = st.text_input("Patient")
    verlauf = st.text_area("Verlauf seit letzter Konsultation", height=120)
    neue_befunde = st.text_area("Neue Befunde", height=120)
    beurteilung = st.text_area("Beurteilung", height=120)
    therapie = st.text_area("Therapie / Weiteres Vorgehen", height=100)
    user_input = f"Patient: {patient}\nVerlauf: {verlauf}\nNeue Befunde: {neue_befunde}\nBeurteilung: {beurteilung}\nTherapie: {therapie}"

elif doc_type == "Kostengutsprache Medikament":
    med = st.text_input("Medikament / Indikation")
    patient = st.text_input("Patient")
    user_input = f"Medikament: {med}\nPatient: {patient}"

elif doc_type == "Kostengutsprache Rehabilitation":
    rehab = st.text_input("Rehabilitationsmaßnahme")
    patient = st.text_input("Patient")
    user_input = f"Rehabilitation: {rehab}\nPatient: {patient}"

elif doc_type == "Stationärer Bericht":
    patient = st.text_input("Patient")
    anlass = st.text_area("Anlass / Aufnahmegrund", height=120)
    befunde = st.text_area("Befunde (Labor, Bilder, Untersuchung)", height=120)
    therapie = st.text_area("Therapie / Weiteres Vorgehen", height=100)
    user_input = f"Patient: {patient}\nAnlass: {anlass}\nBefunde: {befunde}\nTherapie: {therapie}"

# -----------------------------
# Generate Bericht button
# -----------------------------
if st.button("Bericht generieren") and user_input.strip() != "":
    # Select correct prompt from secrets
    prompt_key = {
        "Ambulanter Erstbericht": "ERSTBERICHT_PROMPT",
        "Ambulanter Verlaufsbericht": "VERLAUF_PROMPT",
        "Kostengutsprache Medikament": "KOSTENGUT_MED_PROMPT",
        "Kostengutsprache Rehabilitation": "KOSTENGUT_REHA_PROMPT",
        "Stationärer Bericht": "STATIONAER_PROMPT"
    }[doc_type]

    prompt_text = st.secrets[prompt_key]

    # Call OpenAI API
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": prompt_text},
            {"role": "user", "content": user_input}
        ],
        temperature=0.3
    )

    generated_text = response.choices[0].message.content

    # Display output
    st.markdown("### Generierter Bericht")
    st.text_area(
        label="",
        value=generated_text,
        height=350
    )
    
    # Copy button using JS
    st.markdown(
        f"""
        <button onclick="navigator.clipboard.writeText(`{generated_text.replace('`','\\`')}`)">
            Bericht kopieren
        </button>
        """,
        unsafe_allow_html=True
    )
    
# -------------------------
# Optional disclaimer
# -------------------------
st.caption(
    "Dieses Tool dient der Unterstützung beim Verfassen medizinischer Texte. "
    "Die inhaltliche Verantwortung verbleibt bei der behandelnden Ärztin / beim behandelnden Arzt."
)
