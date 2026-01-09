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

/* Folium-like sidebar buttons */
[data-testid="stSidebar"] button {
    width: 100%;
    text-align: left;
    padding: 0.45em 0.75em;
    margin-bottom: 0.35em;
    border-radius: 6px;
    border: none;
    background-color: #f1f3f6;
    font-size: 0.95rem;
}
[data-testid="stSidebar"] button:hover {
    background-color: #e2e6ec;
}
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

st.title("Mediscript – Testphase")

# -----------------------------
# OpenAI client
# -----------------------------
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# -----------------------------
# Sidebar: Document type (Folium-style)
# -----------------------------
DOCUMENTS = [
    "Ambulanter Erstbericht",
    "Ambulanter Verlaufsbericht",
    "Kostengutsprache Medikament",
    "Kostengutsprache Rehabilitation",
    "Stationärer Bericht"
]

if "doc_type" not in st.session_state:
    st.session_state.doc_type = DOCUMENTS[0]

st.sidebar.markdown("## 📄 Dokumenttyp")

for d in DOCUMENTS:
    if st.sidebar.button(d, key=f"doc_{d}"):
        st.session_state.doc_type = d

doc_type = st.session_state.doc_type

st.caption("ℹ️ Unklare oder noch ausstehende Angaben können leer gelassen oder kurz beschrieben werden.")

# -----------------------------
# Status templates
# -----------------------------
STATUS_TEMPLATES = {
    "LWS": """Allgemein: Patient wach, orientiert. Haltung und Gang normal.  
Inspektion: Keine sichtbare Fehlstellung. Palpation: keine relevante Druckdolenz.  
Bewegung: Flexion/Extension normal. Lasègue negativ.""",
    "HWS": """Allgemein: wach, orientiert.  
Beweglichkeit frei, Spurling negativ.""",
    "Schulter": """Beweglichkeit symmetrisch, keine Druckdolenz.""",
    "Knie": """Keine Ergüsse, Beweglichkeit frei.""",
    "Hüfte": """Rotation frei, kein Leistenschmerz.""",
    "Hand": """Beweglichkeit und Kraft unauffällig.""",
    "Internistisch": """Kardiopulmonal stabil, Abdomen weich.""",
    "Neuro": """Keine fokal-neurologischen Defizite."""
}

# -----------------------------
# Initialize user input
# -----------------------------
user_input = ""

# -----------------------------
# Ambulanter / Stationär / Verlauf
# -----------------------------
if doc_type in ["Ambulanter Erstbericht", "Ambulanter Verlaufsbericht", "Stationärer Bericht"]:

    tabs = st.tabs([
        "Patient / Zuweisung",
        "Jetzige Leiden & Anamnese",
        "Status & Befunde",
        "Einschätzung",
        "Therapie / Procedere"
    ])

    with tabs[0]:
        patient = st.text_input("Patient", placeholder="z.B. 72-jährige Patientin")
        if doc_type == "Ambulanter Erstbericht":
            z = st.text_area(
                "Zuweisung (Wer, Datum, Anlass)",
                placeholder="Hausarzt / Notfall; Datum; Anlass",
                height=80
            )
        else:
            z = ""

    with tabs[1]:
        jetzige_leiden = st.text_area(
            "Jetzige Leiden",
            placeholder="- Rückenschmerzen\n- Morgensteifigkeit",
            height=120
        )
        anamnesis = st.text_area(
            "Anamnese",
            placeholder="Chronologischer Verlauf",
            height=140
        )

    with tabs[2]:
        selected_status = st.selectbox(
            "Status-Vorlage (optional)",
            [""] + list(STATUS_TEMPLATES.keys())
        )
        status_text = st.text_area(
            "Status",
            value=STATUS_TEMPLATES.get(selected_status, ""),
            height=200
        )
        befunde = st.text_area(
            "Befunde",
            placeholder="Labor, Bildgebung",
            height=120
        )

    with tabs[3]:
        einschätzung = st.text_area(
            "Einschätzung (inkl. Verdachtsdiagnose)",
            height=140
        )

    with tabs[4]:
        therapeutisch = st.text_area(
            "Therapie / Procedere",
            height=100
        )

    user_input = f"""
Patient: {patient}
Zuweisung: {z}
Jetzige Leiden: {jetzige_leiden}
Anamnese: {anamnesis}
Status: {status_text}
Befunde: {befunde}
Einschätzung: {einschätzung}
Therapie: {therapeutisch}
""".strip()

# -----------------------------
# Kostengutsprache Medikament
# -----------------------------
elif doc_type == "Kostengutsprache Medikament":

    context = st.text_area("Klinischer Kontext *", height=90)
    prior = st.text_area("Vorbehandlungen *", height=100)
    med = st.text_input("Beantragtes Medikament *")
    indication = st.text_area("Indikation *")
    dosage = st.text_input("Dosierung")
    justification = st.text_area("Medizinische Begründung *", height=110)

    user_input = textwrap.dedent(f"""
    Klinischer Kontext: {context}
    Vorbehandlungen: {prior}
    Medikament: {med}
    Indikation: {indication}
    Dosierung: {dosage}
    Begründung: {justification}
    """).strip()

# -----------------------------
# Kostengutsprache Reha
# -----------------------------
elif doc_type == "Kostengutsprache Rehabilitation":
    rehab = st.text_input("Rehabilitationsmassnahme")
    patient_reha = st.text_input("Patient")
    user_input = f"Reha: {rehab}\nPatient: {patient_reha}"

# -----------------------------
# Generate Bericht
# -----------------------------
if st.button("Bericht generieren") and user_input:
    with st.spinner("Bericht wird generiert…"):
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": st.secrets["ERSTBERICHT_PROMPT"]},
                {"role": "user", "content": user_input}
            ],
            temperature=0.3
        )
        st.session_state.generated_text = response.choices[0].message.content

# -----------------------------
# Show report
# -----------------------------
if "generated_text" in st.session_state:
    st.markdown("### Generierter Bericht")
    st.text_area("", st.session_state.generated_text, height=350)

# -----------------------------
# Feedback
# -----------------------------
st.markdown("---")
st.markdown("**💬 Feedback / Rückmeldung**")

feedback = st.text_area("Feedback", height=80)
if st.button("Feedback senden"):
    if feedback.strip():
        send_feedback_email(feedback)
        st.success("Danke für dein Feedback! 🙏")

# -----------------------------
# Disclaimer
# -----------------------------
st.caption(
    "Dieses Tool dient der Unterstützung beim Verfassen medizinischer Texte. "
    "Die Verantwortung verbleibt bei der behandelnden Ärztin / beim behandelnden Arzt."
)
