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
st.set_page_config(page_title="Mediscript", layout="wide")
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
    "LWS": "Allgemein: Patient wach, orientiert. Haltung und Gang normal.\nInspektion: Keine Fehlstellung. Palpation: unauffällig.\nBewegung: Flexion/Extension normal.",
    "HWS": "Allgemein: Patient wach, orientiert. Haltung normal.\nInspektion: keine Schwellung. Palpation normal.\nBewegung: Flexion/Extension unauffällig.",
    "Schulter": "Allgemein: Patient wach, orientiert. Schulterbeweglichkeit symmetrisch.\nInspektion: keine Schwellung.\nBewegung physiologisch.",
    "Knie": "Allgemein: Patient wach, orientiert. Kniebeweglichkeit symmetrisch.\nInspektion: unauffällig.\nBewegung physiologisch.",
    "Hand": "Allgemein: Patient wach, orientiert. Hände normal gelagert.\nInspektion: keine Deformitäten.\nBewegung physiologisch.",
    "Internistisch": "Allgemeinzustand: Wach, orientiert, kein akuter Leidensdruck.\nHerz: rhythmisch.\nAbdomen: weich.",
    "Neuro": "Bewusstsein: wach, klar, orientiert.\nMotorik und Reflexe physiologisch.\nKoordination unauffällig."
}

# -----------------------------
# Layout: Folium-style vertical "tabs"
# -----------------------------
doc_options = [
    "Ambulanter Erstbericht",
    "Ambulanter Verlaufsbericht",
    "Kostengutsprache Medikament",
    "Kostengutsprache Rehabilitation",
    "Stationärer Bericht"
]

col1, col2 = st.columns([2, 10])
with col1:
    doc_type = st.radio("Dokumenttyp auswählen", doc_options, index=0)

# -----------------------------
# User input fields per document type
# -----------------------------
user_input = ""

with col2:
    if doc_type == "Ambulanter Erstbericht":
        st.subheader("Patientendaten")
        z = st.text_area("Zuweisung (Wer, Datum, Anlass)", placeholder="z.B. Hausarzt / Notfall / Selbstzuweisung; Datum; Anlass", height=80)
        jetzige_leiden = st.text_area("Jetzige Leiden", placeholder="- Schulterschmerzen\n- Beckengürtelschmerzen", height=120)
        anamnesis = st.text_area("Anamnese", placeholder="09/2024: Beschwerden begannen...", height=140)

        st.subheader("Status & Befunde")
        selected_status = st.selectbox("Status wählen (optional)", [""] + list(STATUS_TEMPLATES.keys()))
        status_text = st.text_area("Status", value=STATUS_TEMPLATES.get(selected_status, ""), placeholder="Hier Status eintragen", height=200)
        befunde = st.text_area("Befunde", placeholder="Klinische Werte, Labor, Bildgebung", height=120)

        st.subheader("Einschätzung & Therapie")
        einschätzung = st.text_area("Klinische Einschätzung (inkl. Verdachtsdiagnose)", placeholder="Beurteilung, Risikoeinschätzung", height=120)
        therapeutisch = st.text_area("Therapeutisches Vorgehen", placeholder="Medikamentös / nicht-medikamentös", height=100)

        user_input = f"Jetzige Leiden:\n{jetzige_leiden}\n\nAnamnese:\n{anamnesis}\n\nStatus:\n{status_text}\n\nBefunde:\n{befunde}\n\nZuweisung:\n{z}\n\nEinschätzung:\n{einschätzung}\n\nTherapeutisches Vorgehen:\n{therapeutisch}"

    elif doc_type == "Ambulanter Verlaufsbericht":
        st.subheader("Patientendaten")
        patient = st.text_input("Patientinfo", placeholder="z.B. 55-jährige Patientin")
        jetzige_leiden = st.text_area("Jetzige Leiden", placeholder="- Beschwerden aktuell", height=120)
        anamnesis = st.text_area("Anamnese", placeholder="Verlauf seit letzter Konsultation", height=140)

        st.subheader("Status & Befunde")
        selected_status = st.selectbox("Status wählen (optional)", [""] + list(STATUS_TEMPLATES.keys()))
        status_text = st.text_area("Status", value=STATUS_TEMPLATES.get(selected_status, ""), placeholder="Hier Status eintragen", height=200)
        befunde = st.text_area("Neue Befunde", placeholder="Labor, Bildgebung, klinische Untersuchung", height=120)

        st.subheader("Einschätzung & Therapie")
        beurteilung = st.text_area("Beurteilung", placeholder="Zusammenfassende Einschätzung", height=120)
        therapie = st.text_area("Therapie / Weiteres Vorgehen", placeholder="Therapieanpassungen, Verlaufskontrollen", height=100)

        user_input = f"Patient: {patient}\nJetzige Leiden:\n{jetzige_leiden}\n\nAnamnese:\n{anamnesis}\n\nStatus:\n{status_text}\n\nBefunde:\n{befunde}\n\nBeurteilung:\n{beurteilung}\n\nTherapie:\n{therapie}"

    elif doc_type == "Kostengutsprache Medikament":
        st.subheader("Kostengutsprache – Medikament")
        context = st.text_area("Klinischer Kontext *", placeholder="z.B. Osteoporose...", height=90)
        prior = st.text_area("Bisherige Therapien / Limitationen *", placeholder="z.B. MTX, Salazopyrin", height=100)
        med = st.text_input("Beantragtes Medikament *", placeholder="z.B. Actemra® (Tocilizumab)")
        indication = st.text_area("Indikation *", placeholder="Warum indiziert?")
        dosage = st.text_input("Dosierung / Therapiedauer", placeholder="z.B. 8 mg/kg i.v. alle 4 Wochen")
        justification = st.text_area("Begründung / Risiko bei Nichtbewilligung *", placeholder="Risiko, Progression...", height=110)

        with st.expander("Optionale Angaben"):
            off_label = st.selectbox("Off-label / Art. 71 KVV?", ["Unklar", "Nein", "Ja"])
            evidence = st.text_area("Leitlinien / Evidenz (optional)", placeholder="Studien, Fachgesellschaften")

        user_input = textwrap.dedent(f"""
        Klinischer Kontext:
        {context}

        Vorbehandlungen:
        {prior}

        Beantragtes Medikament:
        {med}

        Indikation:
        {indication}

        Dosierung:
        {dosage}

        Begründung:
        {justification}

        Off-label / Art. 71 KVV:
        {off_label}

        Evidenz:
        {evidence}
        """).strip()

    elif doc_type == "Kostengutsprache Rehabilitation":
        st.subheader("Kostengutsprache – Rehabilitation")
        rehab = st.text_input("Rehabilitationsmaßnahme", placeholder="z.B. Physikalische Therapie 3x pro Woche")
        patient = st.text_input("Patient", placeholder="z.B. 55-jährige Patientin")
        user_input = f"Rehabilitation: {rehab}\nPatient: {patient}"

    elif doc_type == "Stationärer Bericht":
        st.subheader("Patientendaten")
        patient = st.text_input("Patient", placeholder="z.B. 72-jährige Patientin")
        anlass = st.text_area("Anlass / Aufnahmegrund", placeholder="z.B. Exazerbation COPD", height=120)
        jetzige_leiden = st.text_area("Jetzige Leiden", placeholder="- Beschwerden aktuell", height=120)
        anamnesis = st.text_area("Anamnese", placeholder="Chronologie", height=140)

        st.subheader("Status & Befunde")
        selected_status = st.selectbox("Status wählen (optional)", [""] + list(STATUS_TEMPLATES.keys()))
        status_text = st.text_area("Status", value=STATUS_TEMPLATES.get(selected_status, ""), placeholder="Hier Status eintragen", height=200)
        befunde = st.text_area("Befunde", placeholder="Labor, Bildgebung, klinische Untersuchung", height=120)

        st.subheader("Einschätzung & Therapie")
        einschätzung = st.text_area("Klinische Einschätzung (inkl. Verdachtsdiagnose)", placeholder="Beurteilung, Risikoeinschätzung", height=120)
        therapeutisch = st.text_area("Therapeutisches Vorgehen", placeholder="Medikamentös / nicht-medikamentös", height=100)

        user_input = f"Patient: {patient}\nJetzige Leiden:\n{jetzige_leiden}\n\nAnamnese:\n{anamnesis}\n\nStatus:\n{status_text}\n\nBefunde:\n{befunde}\n\nEinschätzung:\n{einschätzung}\n\nTherapie:\n{therapeutisch}"

# -----------------------------
# Generate Bericht
# -----------------------------
if st.button("Bericht generieren") and user_input.strip():
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
# Show report if generated
# -----------------------------
if "generated_text" in st.session_state:
    generated_text = st.session_state.generated_text
    st.markdown("### Generierter Bericht")
    st.text_area(label="", value=generated_text, height=350)
    st.info(f"⏱️ Bericht generiert in {st.session_state.elapsed_time:.2f} Sekunden")

# -------------------------
# Feedback
# -------------------------
st.markdown("---")
st.markdown("<div style='font-size:15px; font-weight:600;'>💬 Feedback / Rückmeldung</div>", unsafe_allow_html=True)
feedback = st.text_area("Schreibe dein Feedback", placeholder="z.B. 'Status könnte detaillierter sein…'", height=80, key="feedback_box")

if st.button("Feedback senden"):
    if feedback.strip():
        send_feedback_email(feedback)
        st.success("Danke für dein Feedback! 🙏")
    else:
        st.warning("Bitte zuerst Feedback eingeben.")
