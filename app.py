import streamlit as st
import openai 

# MUST be the first Streamlit command
st.set_page_config(
    page_title="Mediscript",
    page_icon="🩺",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": None
    }
)

# Hide Streamlit UI elements
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

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
st.title("Mediscript - Schweizer Medizinische Dokumentation")

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

# -------------------------
# Placeholder for generated text
# -------------------------
generated_text = ""

# -------------------------
# Generate Report Button
# -------------------------
if st.button("Bericht generieren") and user_input.strip() != "":
    # choose prompt key depending on doc_type
    prompt_key = {
        "Ambulanter Erstbericht": "ERSTBERICHT_PROMPT",
        "Ambulanter Verlaufsbericht": "VERLAUF_PROMPT",
        "Kostengutsprache – Medikament": "KOSTENGUT_MED_PROMPT",
        "Kostengutsprache – Rehabilitation": "KOSTENGUT_REHA_PROMPT",
        "Stationärer Bericht": "STATIONAER_PROMPT"
    }[doc_type]

    prompt = st.secrets[prompt_key]

    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_input}
        ],
        temperature=0.3
    )

    generated_text = response.choices[0].message.content

# -------------------------
# Display Generated Report
# -------------------------
st.markdown("### Generierter Bericht")
st.text_area(
    label="",
    value=generated_text,
    height=350
)

# -------------------------
# Copy Button (Streamlit 1.26+)
# -------------------------
if st.button("Text kopieren") and generated_text:
    st.experimental_set_clipboard(generated_text)

# -------------------------
# Optional disclaimer
# -------------------------
st.caption(
    "Dieses Tool dient der Unterstützung beim Verfassen medizinischer Texte. "
    "Die inhaltliche Verantwortung verbleibt bei der behandelnden Ärztin / beim behandelnden Arzt."
)
