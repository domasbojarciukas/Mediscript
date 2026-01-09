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

st.title("Mediscript - Testphase")

# -----------------------------
# OpenAI client
# -----------------------------
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# -----------------------------
# Status templates
# -----------------------------
STATUS_TEMPLATES = {
    "LWS": "Allgemein: Patient wach, orientiert. Haltung und Gang normal.\nInspektion: ...",
    "HWS": "Allgemein: Patient wach, orientiert. Haltung normal.\nInspektion: ...",
    "Schulter": "Allgemein: Patient wach, orientiert. Schulterbeweglichkeit symmetrisch.\nInspektion: ...",
    "Knie": "Allgemein: Patient wach, orientiert. Kniebeweglichkeit symmetrisch.\nInspektion: ...",
    "Hand": "Allgemein: Patient wach, orientiert. Hände normal gelagert.\nInspektion: ...",
    "Internistisch": "Allgemeinzustand: Wach, orientiert, kein akuter Leidensdruck.\nHerz: ...",
    "Neuro": "Bewusstsein und Orientierung: wach, klar, orientiert.\nMotorik: ...",
}

# -----------------------------
# Sidebar sections as tabs
# -----------------------------
section = st.sidebar.radio(
    "Abschnitt wählen",
    ["Dokumenttyp", "Patientenangaben", "Leiden & Anamnese", "Status & Befunde", "Einschätzung & Therapie", "Generierung & Feedback"]
)

# -----------------------------
# Store all inputs in session state
# -----------------------------
if "doc_type" not in st.session_state:
    st.session_state.doc_type = "Ambulanter Erstbericht"

if "feedback" not in st.session_state:
    st.session_state.feedback = ""

# -----------------------------
# Section: Dokumenttyp auswählen
# -----------------------------
if section == "Dokumenttyp":
    st.session_state.doc_type = st.selectbox(
        "Dokumenttyp auswählen",
        ("Ambulanter Erstbericht", "Ambulanter Verlaufsbericht",
         "Kostengutsprache Medikament", "Kostengutsprache Rehabilitation",
         "Stationärer Bericht"),
        index=["Ambulanter Erstbericht", "Ambulanter Verlaufsbericht",
               "Kostengutsprache Medikament", "Kostengutsprache Rehabilitation",
               "Stationärer Bericht"].index(st.session_state.doc_type)
    )
    st.caption("ℹ️ Unklare oder ausstehende Angaben können leer gelassen werden.")

# -----------------------------
# Section: Patientenangaben
# -----------------------------
if section == "Patientenangaben":
    doc_type = st.session_state.doc_type
    if doc_type in ["Ambulanter Erstbericht", "Ambulanter Verlaufsbericht"]:
        st.session_state.patient = st.text_input("Patient", placeholder="z.B. 55-jährige Patientin")
        st.session_state.zuweisung = st.text_area("Zuweisung (Wer, Datum, Anlass)", placeholder="z.B. Hausarzt / Notfall / Selbstzuweisung; Datum; Anlass der Vorstellung", height=80)
    elif doc_type == "Kostengutsprache Medikament":
        st.session_state.patient = st.text_input("Patient", placeholder="z.B. 72-jährige Patientin")
    elif doc_type == "Kostengutsprache Rehabilitation":
        st.session_state.patient = st.text_input("Patient", placeholder="z.B. 55-jährige Patientin")
    elif doc_type == "Stationärer Bericht":
        st.session_state.patient = st.text_input("Patient", placeholder="z.B. 72-jährige Patientin")

# -----------------------------
# Section: Leiden & Anamnese
# -----------------------------
if section == "Leiden & Anamnese":
    doc_type = st.session_state.doc_type
    if doc_type == "Ambulanter Erstbericht":
        st.session_state.jetzige_leiden = st.text_area(
            "Jetzige Leiden", placeholder="- Schulterschmerzen bds\n- Beckengürtelschmerzen", height=120
        )
        st.session_state.anamnese = st.text_area(
            "Anamnese", placeholder="09/2024: Erstmaliges Auftreten der Beschwerden", height=140
        )
    elif doc_type == "Ambulanter Verlaufsbericht":
        st.session_state.verlauf = st.text_area(
            "Verlauf seit letzter Konsultation", placeholder="Neue Symptome, Besserung / Verschlechterung", height=120
        )

# -----------------------------
# Section: Status & Befunde
# -----------------------------
if section == "Status & Befunde":
    doc_type = st.session_state.doc_type
    if doc_type == "Ambulanter Erstbericht":
        selected_status = st.selectbox("Status wählen", [""] + list(STATUS_TEMPLATES.keys()))
        st.session_state.status = st.text_area("Status", value=STATUS_TEMPLATES.get(selected_status, ""), placeholder="Hier wird Status angezeigt", height=200)
        st.session_state.vd = st.text_area("Klinische Verdachtsdiagnose", placeholder="Leitsymptom(e), Arbeitsdiagnose, DD", height=80)
        st.session_state.befunde = st.text_area("Befunde (Labor, Bilder, Untersuchung)", placeholder="Relevante Laborwerte, Bildgebung", height=120)

# -----------------------------
# Section: Einschätzung & Therapie
# -----------------------------
if section == "Einschätzung & Therapie":
    doc_type = st.session_state.doc_type
    if doc_type == "Ambulanter Erstbericht":
        st.session_state.einschaetzung = st.text_area("Einschätzung", placeholder="Zusammenfassende Beurteilung", height=120)
        st.session_state.therapie = st.text_area("Therapeutisches Vorgehen", placeholder="Medikamentös / nicht-medikamentös", height=100)

# -----------------------------
# Section: Generierung & Feedback
# -----------------------------
if section == "Generierung & Feedback":
    # Build user_input depending on doc type
    doc_type = st.session_state.doc_type
    user_input = ""
    if doc_type == "Ambulanter Erstbericht":
        user_input = f"""Jetzige Leiden:\n{st.session_state.get('jetzige_leiden','')}\n\nAnamnese:\n{st.session_state.get('anamnese','')}\n\nStatus:\n{st.session_state.get('status','')}\n\nZuweisung:\n{st.session_state.get('zuweisung','')}\n\nVerdachtsdiagnose:\n{st.session_state.get('vd','')}\n\nBefunde:\n{st.session_state.get('befunde','')}\n\nEinschätzung:\n{st.session_state.get('einschaetzung','')}\n\nTherapeutisches Vorgehen:\n{st.session_state.get('therapie','')}"""

    if st.button("Bericht generieren") and user_input.strip() != "":
        with st.spinner("Bericht wird generiert…"):
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
                messages=[{"role": "system", "content": prompt_text},
                          {"role": "user", "content": user_input}],
                temperature=0.3
            )
            st.session_state.generated_text = response.choices[0].message.content
            st.session_state.elapsed_time = time.time() - time.time()

    if "generated_text" in st.session_state:
        st.subheader("Generierter Bericht")
        st.text_area("", st.session_state.generated_text, height=350)

    st.markdown("---")
    st.markdown("<div style='font-size:15px; font-weight:600;'>💬 Feedback / Rückmeldung</div>", unsafe_allow_html=True)
    st.session_state.feedback = st.text_area("Schreibe dein Feedback", placeholder="z.B. 'Status könnte detaillierter sein…'", height=80, key="feedback_box")
    if st.button("Feedback senden"):
        if st.session_state.feedback.strip():
            send_feedback_email(st.session_state.feedback)
            st.success("Danke für dein Feedback! 🙏")
        else:
            st.warning("Bitte zuerst Feedback eingeben.")
