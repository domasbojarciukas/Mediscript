import time
import streamlit as st
import textwrap
import smtplib
from email.mime.text import MIMEText
from openai import OpenAI

# -----------------------------
# Page config
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

# -----------------------------
# OpenAI client
# -----------------------------
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# -----------------------------
# Sidebar: Folium-style clickable doc types
# -----------------------------
st.sidebar.markdown("## 📄 Dokumenttyp auswählen")
doc_types = [
    "Ambulanter Erstbericht",
    "Ambulanter Verlaufsbericht",
    "Kostengutsprache Medikament",
    "Kostengutsprache Rehabilitation",
    "Stationärer Bericht"
]

for dt in doc_types:
    if st.sidebar.button(dt):
        st.session_state.doc_type = dt

if "doc_type" not in st.session_state:
    st.session_state.doc_type = "Ambulanter Erstbericht"

doc_type = st.session_state.doc_type

# -----------------------------
# Status templates
# -----------------------------
STATUS_TEMPLATES = {
    "LWS": "Allgemein: Patient wach, orientiert. Haltung und Gang normal.\nInspektion: Keine Fehlstellung. Palpation unauffällig.\nBewegung: Flexion/Extension normal. Keine neurologischen Auffälligkeiten.",
    "HWS": "Allgemein: Patient wach, orientiert. Haltung normal.\nInspektion: Keine Fehlstellung. Palpation unauffällig.\nBewegung: Flexion/Extension/Lateralflexion/Rotation unauffällig.",
    "Schulter": "Allgemein: Patient wach, orientiert. Schulterbeweglichkeit symmetrisch.\nInspektion/Palpation unauffällig.\nBewegung physiologisch.",
    "Knie": "Allgemein: Patient wach, orientiert. Kniebeweglichkeit symmetrisch.\nInspektion/Palpation unauffällig.\nFlexion/Extension physiologisch. Stabilitätstest unauffällig.",
    "Hand": "Allgemein: Patient wach, orientiert. Hände normal.\nInspektion/Palpation unauffällig.\nDaumen/Fingerbeweglichkeit physiologisch.",
    "Internistisch": "Allgemeinzustand: Wach, orientiert. Hautfarbe normal.\nHerz rhythmisch, keine Extrasystolen.\nAbdomen weich, nicht druckschmerzhaft.",
    "Neuro": "Bewusstsein wach, orientiert. Sprache unauffällig.\nMotorik und Sensibilität physiologisch. Reflexe normal. Koordination unauffällig."
}

# -----------------------------
# Main Area
# -----------------------------
st.title(f"Mediscript – {doc_type}")
st.caption("ℹ️ Unklare oder noch ausstehende Angaben können leer gelassen oder kurz beschrieben werden.")

user_input = ""

# -----------------------------
# Ambulanter Erstbericht
# -----------------------------
if doc_type == "Ambulanter Erstbericht":
    z = st.text_area("Zuweisung (Wer, Datum, Anlass)", placeholder="Hausarzt / Notfall / Selbstzuweisung; Datum; Anlass", height=80)
    jetzige_leiden = st.text_area("Jetzige Leiden", placeholder="- Schulterschmerzen bds\n- Beckengürtelschmerzen", height=120)
    anamnesis = st.text_area("Anamnese", placeholder="09/2024: Erstmaliges Auftreten der Beschwerden...", height=140)
    selected_status = st.selectbox("Status wählen (optional)", [""] + list(STATUS_TEMPLATES.keys()))
    status_text = st.text_area("Status & Befunde", value=STATUS_TEMPLATES.get(selected_status, ""), placeholder="Hier wird Status & Befunde angezeigt", height=200)
    einschätzung = st.text_area("Klinische Einschätzung (inkl. Verdachtsdiagnose)", placeholder="Verdachtsdiagnose & Beurteilung", height=120)
    therapeutisch = st.text_area("Therapeutisches Vorgehen", placeholder="Medikamentös / nicht-medikamentös; begonnen / geplant", height=100)

    user_input = textwrap.dedent(f"""
Jetzige Leiden:
{jetzige_leiden}

Anamnese:
{anamnesis}

Status & Befunde:
{status_text}

Zuweisung:
{z}

Einschätzung:
{einschätzung}

Therapeutisches Vorgehen:
{therapeutisch}
""").strip()

# -----------------------------
# Ambulanter Verlaufsbericht
# -----------------------------
elif doc_type == "Ambulanter Verlaufsbericht":
    jetzige_leiden = st.text_area("Jetzige Leiden", placeholder="- Schulterschmerzen bds\n- Beckengürtelschmerzen", height=120)
    anamnesis = st.text_area("Anamnese", placeholder="Subjektiver Verlauf seit letzter Konsultation", height=140)
    selected_status = st.selectbox("Status wählen (optional)", [""] + list(STATUS_TEMPLATES.keys()))
    status_text = st.text_area("Status & Befunde", value=STATUS_TEMPLATES.get(selected_status, ""), placeholder="Hier wird Status & Befunde angezeigt", height=200)
    beurteilung = st.text_area("Klinische Einschätzung (inkl. Verdachtsdiagnose)", placeholder="Verdachtsdiagnose & Beurteilung", height=120)
    therapie = st.text_area("Therapeutisches Vorgehen", placeholder="Therapie / Weiteres Vorgehen", height=100)

    user_input = textwrap.dedent(f"""
Jetzige Leiden:
{jetzige_leiden}

Anamnese:
{anamnesis}

Status & Befunde:
{status_text}

Einschätzung:
{beurteilung}

Therapeutisches Vorgehen:
{therapie}
""").strip()

# -----------------------------
# Kostengutsprache Medikament
# -----------------------------
elif doc_type == "Kostengutsprache Medikament":
    context = st.text_area("Klinischer Kontext *", placeholder="72-jährige Patientin mit Osteoporose...", height=90)
    prior = st.text_area("Bisherige Therapien *", placeholder="MTX, Salazopyrin...", height=100)
    med = st.text_input("Beantragtes Medikament *", placeholder="Actemra®")
    indication = st.text_area("Indikation *", placeholder="Warum ist das Medikament medizinisch indiziert…")
    dosage = st.text_input("Dosierung / Therapiedauer", placeholder="8 mg/kg i.v. alle 4 Wochen")
    justification = st.text_area("Begründung / Risiko bei Nichtbewilligung *", placeholder="z.B. hohes Frakturrisiko…", height=110)
    with st.expander("➕ Optionale Angaben"):
        off_label = st.selectbox("Off-label / Art. 71 KVV relevant?", ["Unklar", "Nein", "Ja"])
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

# -----------------------------
# Kostengutsprache Rehabilitation
# -----------------------------
elif doc_type == "Kostengutsprache Rehabilitation":
    rehab = st.text_input("Rehabilitationsmaßnahme", placeholder="Physikalische Therapie 3x/Woche")
    patient = st.text_input("Patient", placeholder="55-jährige Patientin")
    user_input = f"Rehabilitation: {rehab}\nPatient: {patient}"

# -----------------------------
# Stationärer Bericht
# -----------------------------
elif doc_type == "Stationärer Bericht":
    patient = st.text_input("Patient", placeholder="72-jährige Patientin")
    anlass = st.text_area("Anlass / Aufnahmegrund", placeholder="Akute Exazerbation einer COPD", height=120)
    status_text = st.text_area("Status & Befunde", placeholder="Allgemein, Befunde, Labor, Bildgebung...", height=200)
    einschätzung = st.text_area("Klinische Einschätzung (inkl. Verdachtsdiagnose)", placeholder="Verdachtsdiagnose & Beurteilung", height=120)
    therapie = st.text_area("Therapeutisches Vorgehen", placeholder="Therapie / Weiteres Vorgehen", height=100)

    user_input = textwrap.dedent(f"""
Patient: {patient}

Anlass:
{anlass}

Status & Befunde:
{status_text}

Einschätzung:
{einschätzung}

Therapeutisches Vorgehen:
{therapie}
""").strip()

# -----------------------------
# AI Generation
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
# Show report if generated
# -----------------------------
if "generated_text" in st.session_state:
    st.markdown("### Generierter Bericht")
    st.text_area(label="", value=st.session_state.generated_text, height=350)
    st.info(f"⏱️ Bericht generiert in {st.session_state.elapsed_time:.2f} Sekunden")

# -----------------------------
# Feedback section
# -----------------------------
st.markdown("---")
st.markdown("<div style='font-size:15px; font-weight:600;'>💬 Feedback / Rückmeldung</div>", unsafe_allow_html=True)
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
st.caption(
    "Dieses Tool dient der Unterstützung beim Verfassen medizinischer Texte. "
    "Die inhaltliche Verantwortung verbleibt bei der behandelnden Ärztin / beim behandelnden Arzt."
)
