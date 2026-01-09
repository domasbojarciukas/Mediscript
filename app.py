import time
import streamlit as st
import streamlit.components.v1 as components
import textwrap
from openai import OpenAI
import smtplib
from email.mime.text import MIMEText

# -----------------------------
# Page config + hide header/footer
# -----------------------------
st.set_page_config(page_title="Mediscript", layout="centered")
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Feedback email function
# -----------------------------
def send_feedback_email(message: str):
    msg = MIMEText(message, "plain", "utf-8")
    msg["Subject"] = "💬 Mediscript – Neues Feedback"
    msg["From"] = st.secrets["FEEDBACK_EMAIL_FROM"]
    msg["To"] = st.secrets["FEEDBACK_EMAIL_TO"]

    with smtplib.SMTP(st.secrets["SMTP_SERVER"], st.secrets["SMTP_PORT"]) as server:
        server.starttls()
        server.login(
            st.secrets["FEEDBACK_EMAIL_FROM"],
            st.secrets["SMTP_PASSWORD"]
        )
        server.send_message(msg)

# -----------------------------
# OpenAI client
# -----------------------------
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# -----------------------------
# Status templates
# -----------------------------
STATUS_TEMPLATES = {
    "LWS": "Allgemein: Patient wach, orientiert. Haltung und Gang normal. Einbeinstand unauffälig.\nInspektion: Keine sichtbare Fehlstellung. Palpation: keine Druckdolenz.\nBewegung: Flexion/Extension normal. Lasègue-Test negativ.",
    "HWS": "Allgemein: Patient wach, orientiert. Haltung normal.\nInspektion: Keine Fehlstellung. Palpation normal.\nBewegung: Flexion, Extension, Lateralflexion und Rotation unauffällig.",
    "Schulter": "Allgemein: Patient wach, orientiert. Schulterbeweglichkeit symmetrisch.\nInspektion: Keine Schwellung oder Rötung.\nPalpation: keine Druckdolenz.\nBewegung: physiologisch. Kraftprüfung normal.",
    "Knie": "Allgemein: Patient wach, orientiert. Kniebeweglichkeit symmetrisch.\nInspektion: Keine Schwellung.\nBewegung: Flexion und Extension physiologisch. Stabilitätstest unauffällig.",
    "Hüfte": "Rotationsprüfung: AR/IR schmerzfrei, Drehmanzeichen negativ, kein axialer Stauchungsschmerz.",
    "Hand": "Allgemein: Patient wach, orientiert. Hände normal gelagert.\nInspektion: Keine Deformitäten. Palpation: keine Druckdolenz.\nBewegung: physiologisch.",
    "Internistisch": "Allgemeinzustand: Wach, orientiert, kein akuter Leidensdruck.\nHerz: rhythmisch, keine Extrasystolen.\nAbdomen: weich, nicht druckschmerzhaft.",
    "Neuro": "Bewusstsein und Orientierung: wach, klar, orientiert.\nMotorik: Kraft symmetrisch, kein Paresen.\nReflexe: physiologisch."
}

# -----------------------------
# Page title
# -----------------------------
st.title("Mediscript - Testphase")
st.caption("ℹ️ Unklare oder ausstehende Angaben können leer gelassen werden.")

# -----------------------------
# Select document type
# -----------------------------
doc_type = st.selectbox(
    "Dokumenttyp auswählen",
    ("Ambulanter Erstbericht", "Ambulanter Verlaufsbericht",
     "Kostengutsprache Medikament", "Kostengutsprache Rehabilitation",
     "Stationärer Bericht")
)

user_input = ""

# -----------------------------
# UI for Ambulanter Erstbericht
# -----------------------------
if doc_type == "Ambulanter Erstbericht":
    st.markdown("### Patientendaten")
    z = st.text_area("Zuweisung (Wer, Datum, Anlass)", placeholder="z.B. Hausarzt / Notfall / Selbstzuweisung; Datum; Anlass der Vorstellung", height=80)

    col1, col2 = st.columns(2)
    with col1:
        jetzige_leiden = st.text_area("Jetzige Leiden", placeholder="- Schulterschmerzen bds\n- Beckengürtelschmerzen", height=120)
        anamnesis = st.text_area("Anamnese", placeholder="Chronologische Beschwerden…", height=140)
    with col2:
        selected_status = st.selectbox("Status wählen (optional)", [""] + list(STATUS_TEMPLATES.keys()))
        status_text = st.text_area("Status", value=STATUS_TEMPLATES.get(selected_status, ""), placeholder="Hier Status eintragen oder auswählen", height=200)

    vd = st.text_area("Klinische Verdachtsdiagnose", placeholder="Leitsymptom(e), Arbeitsdiagnose, DD", height=80)
    befunde = st.text_area("Befunde", placeholder="Laborwerte, Bildgebung, klinische Untersuchung", height=120)
    einschätzung = st.text_area("Klinische Einschätzung", placeholder="Zusammenfassende Beurteilung, Risikoeinschätzung", height=120)
    therapeutisch = st.text_area("Therapeutisches Vorgehen", placeholder="Medikamentös / nicht-medikamentös", height=100)

    user_input = f"""Jetzige Leiden:\n{jetzige_leiden}\n\nAnamnese:\n{anamnesis}\n\nStatus:\n{status_text}\n\nZuweisung:\n{z}\n\nVerdachtsdiagnose:\n{vd}\n\nBefunde:\n{befunde}\n\nEinschätzung:\n{einschätzung}\n\nTherapeutisches Vorgehen:\n{therapeutisch}"""

# -----------------------------
# AI generation button
# -----------------------------
if st.button("Bericht generieren") and user_input.strip() != "":
    with st.spinner("Bericht wird generiert…"):
        start_time = time.time()
        prompt_key = {
            "Ambulanter Erstbericht": "ERSTBERICHT_PROMPT",
            "Ambulanter Verlaufsbericht": "VERLAUF_PROMPT",
            "Kostengutsprache Medikament": "KOSTENGUT_MED_PROMPT",
            "Kostengutsprache Rehabilitation": "KOSTENGUT_REHA_PROMPT",
            "Stationärer Bericht": "STATIONAER_PROMPT"
        }[doc_type]

        prompt_text = st.secrets[prompt_key]

        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": prompt_text},
                {"role": "user", "content": user_input}
            ],
            temperature=0.3
        )

        st.session_state.generated_text = response.choices[0].message.content
        st.session_state.elapsed_time = time.time() - start_time

# -----------------------------
# Show generated report
# -----------------------------
if "generated_text" in st.session_state:
    st.markdown("### Generierter Bericht")
    st.text_area(label="", value=st.session_state.generated_text, height=350)

    safe_text = st.session_state.generated_text.replace("`","\\`").replace("\\","\\\\").replace("\n","\\n").replace('"','\\"')
    primary_color = st.get_option("theme.primaryColor")

    components.html(f"""
        <button style="
            padding: 0.45em 1em;
            font-size: 1em;
            font-weight: 600;
            border-radius: 0.25em;
            border: none;
            background-color: {primary_color};
            color: white;
            cursor: pointer;
        "
        onclick="
            const text = `{safe_text}`;
            navigator.clipboard.writeText(text).then(() => {{
                alert('Bericht in die Zwischenablage kopiert!');
            }});">
            Bericht kopieren
        </button>
    """, height=40)

    st.info(f"⏱️ Bericht generiert in {st.session_state.elapsed_time:.2f} Sekunden")

# -----------------------------
# Feedback section
# -----------------------------
st.markdown("---")
st.markdown("<div style='font-size:14px; font-weight:500;'>💬 Feedback / Rückmeldung</div>", unsafe_allow_html=True)
feedback = st.text_area("Schreibe dein Feedback", placeholder="z.B. 'Status könnte detaillierter sein…'", height=80, key="feedback_box")

if st.button("Feedback senden"):
    if feedback.strip():
        send_feedback_email(feedback)
        st.success("Danke für dein Feedback! 🙏")
    else:
        st.warning("Bitte zuerst Feedback eingeben.")

# -----------------------------
# Disclaimer
# -----------------------------
st.caption("Dieses Tool dient der Unterstützung beim Verfassen medizinischer Texte. Die Verantwortung bleibt bei der behandelnden Ärztin / beim behandelnden Arzt.")
