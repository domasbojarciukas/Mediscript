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
    "LWS": "Allgemein: Patient wach, orientiert. Haltung und Gang normal. Einbeinstand unauffälig.\nInspektion: Keine Druckdolenz.\nBewegung: Flexion/Extension normal, Seitneigung normal.\nLasègue-Test negativ. Keine neurologischen Ausfälle.",
    "HWS": "Allgemein: Patient wach, orientiert. Haltung normal.\nInspektion: Keine Fehlstellung oder Schwellung.\nBewegung: Flexion, Extension, Lateralflexion und Rotation unauffällig. Spurling Test negativ.",
    "Schulter": "Allgemein: Patient wach, orientiert. Schulterbeweglichkeit symmetrisch.\nInspektion: Keine Schwellung, Rötung oder Atrophie.\nBewegung: Abduktion, Anteversion, Retroversion, Innen- und Aussenrotation physiologisch.",
    "Knie": "Allgemein: Patient wach, orientiert. Kniebeweglichkeit symmetrisch.\nInspektion: Keine Schwellung, Rötung oder Deformität.\nBewegung: Flexion und Extension physiologisch. Stabilitätstest unauffällig.",
    "Hand": "Allgemein: Patient wach, orientiert. Hände normal gelagert.\nInspektion: Keine Deformitäten, Rötungen oder Schwellungen.\nBewegung: Daumen, Fingerbeweglichkeit und Greiffunktion unauffällig.",
    "Internistisch": "Allgemeinzustand: Wach, orientiert, kein akuter Leidensdruck.\nHerz, Kreislauf, Abdomen physiologisch.",
    "Neuro": "Bewusstsein und Orientierung: wach, klar, orientiert.\nMotorik, Sensibilität, Reflexe physiologisch.\nKoordination unauffällig."
}

# -----------------------------
# Sidebar for tabs
# -----------------------------
tab = st.sidebar.radio("Abschnitt auswählen", [
    "Dokumenttyp auswählen",
    "Patientenangaben",
    "Befunde & Einschätzung",
    "Kostengutsprache / Rehabilitation / Stationär",
    "Feedback"
])

# -----------------------------
# Initialize session state
# -----------------------------
if "generated_text" not in st.session_state:
    st.session_state.generated_text = ""
if "elapsed_time" not in st.session_state:
    st.session_state.elapsed_time = 0

# -----------------------------
# Document type selection
# -----------------------------
if tab == "Dokumenttyp auswählen":
    doc_type = st.selectbox(
        "Dokumenttyp auswählen",
        ("Ambulanter Erstbericht", "Ambulanter Verlaufsbericht",
         "Kostengutsprache Medikament", "Kostengutsprache Rehabilitation",
         "Stationärer Bericht")
    )
    st.session_state.doc_type = doc_type

doc_type = st.session_state.get("doc_type", "Ambulanter Erstbericht")

# -----------------------------
# Patientenangaben tab
# -----------------------------
if tab == "Patientenangaben":
    if doc_type == "Ambulanter Erstbericht":
        z = st.text_area("Zuweisung (Wer, Datum, Anlass)", placeholder="z.B. Hausarzt / Notfall / Selbstzuweisung; Datum; Anlass der Vorstellung", height=80)
        jetzige_leiden = st.text_area("Jetzige Leiden (Stichworte, Symptome)", placeholder="- Schulterschmerzen bds\n- Beckengürtelschmerzen\n- Morgensteifigkeit ca. 60 Minuten\n- Keine Fieber", height=120)
        anamnesis = st.text_area("Anamnese (chronologisch, fragmentiert)", placeholder="09/2024: Erstmaliges Auftreten der Beschwerden\n09/2024: Rasche Besserung unter Prednison 25 mg\nNach Tapern Rezidiv der Schmerzen\n07/2025: Beginn MTX, gut verträglich", height=140)
        selected_status = st.selectbox("Status wählen (optional für automatisches Ausfüllen)", [""] + list(STATUS_TEMPLATES.keys()))
        status_text = st.text_area("Status", value=STATUS_TEMPLATES.get(selected_status, ""), placeholder="Hier wird der Status angezeigt oder kann manuell eingegeben werden", height=200)

    elif doc_type == "Ambulanter Verlaufsbericht":
        patient = st.text_input("Patientinfo", placeholder="z.B. 55-jährige Patientin mit lumbalen Schmerzen, Erstvorstellung am 06.11.2025")
        verlauf = st.text_area("Verlauf seit letzter Konsultation", placeholder="Subjektiver Verlauf, neue Symptome, Besserung / Verschlechterung", height=120)
        neue_befunde = st.text_area("Neue Befunde", placeholder="Neue Laborwerte, Bildgebung, klinische Untersuchungen seit letzter Konsultation", height=120)
        therapie = st.text_area("Therapie / Weiteres Vorgeen", placeholder="Therapieanpassungen, geplante Massnahmen, Verlaufskontrollen", height=100)

# -----------------------------
# Befunde & Einschätzung tab
# -----------------------------
if tab == "Befunde & Einschätzung":
    if doc_type in ["Ambulanter Erstbericht", "Ambulanter Verlaufsbericht"]:
        vd = st.text_area("Klinische Verdachtsdiagnose (unter Einschätzung)", placeholder="Falls unklar: Leitsymptom(e), Arbeitsdiagnose, DD", height=80)
        befunde = st.text_area("Befunde (Labor, Bilder, Untersuchung)", placeholder="Klinischer Status; relevante Laborwerte; Bildgebung (inkl. Datum)", height=120)
        einschätzung = st.text_area("Klinische Einschätzung", placeholder="Zusammenfassende Beurteilung, Risikoeinschätzung, Verlauf", height=120)
        therapeutisch = st.text_area("Therapeutisches Vorgehen", placeholder="Medikamentös / nicht-medikamentös; begonnen / geplant", height=100)

# -----------------------------
# Kostengutsprache / Rehab / Stationär tab
# -----------------------------
if tab == "Kostengutsprache / Rehabilitation / Stationär":
    if doc_type == "Kostengutsprache Medikament":
        context = st.text_area("Klinischer Kontext *", placeholder="z.B. 72-jährige Patientin mit multiplen Frakturen", height=90)
        prior = st.text_area("Bisherige Therapien und Limitationen *", placeholder="z.B. MTX und Salazopyrin abgesetzt", height=100)
        med = st.text_input("Beantragtes Medikament *", placeholder="z.B. Actemra® (Tocilizumab)")
        indication = st.text_area("Indikation für beantragte Therapie *", placeholder="Warum ist dieses Medikament medizinisch indiziert?")
        dosage = st.text_input("Dosierung / Therapiedauer", placeholder="z.B. 8 mg/kg i.v. alle 4 Wochen")
        justification = st.text_area("Medizinische Begründung und Risiko bei Nichtbewilligung *", placeholder="z.B. hohes Frakturrisiko, Progression, irreversible Schäden", height=110)
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

        Medizinische Begründung:
        {justification}

        Off-label / Art. 71 KVV:
        {off_label}

        Evidenz / Leitlinien:
        {evidence}
        """).strip()
    elif doc_type == "Kostengutsprache Rehabilitation":
        rehab = st.text_input("Rehabilitationsmaßnahme", placeholder="z.B. Physikalische Therapie 3x pro Woche")
        patient = st.text_input("Patient", placeholder="z.B. 55-jährige Patientin")
        user_input = f"Rehabilitation: {rehab}\nPatient: {patient}"
    elif doc_type == "Stationärer Bericht":
        patient = st.text_input("Patient", placeholder="z.B. 72-jährige Patientin")
        anlass = st.text_area("Anlass / Aufnahmegrund", placeholder="z.B. akute Exazerbation einer COPD", height=120)
        befunde = st.text_area("Befunde (Labor, Bilder, Untersuchung)", placeholder="z.B. Blutwerte, Röntgen Thorax, EKG", height=120)
        therapie = st.text_area("Therapie / Weiteres Vorgeen", placeholder="z.B. O2-Therapie, Medikationen, Monitoring", height=100)
        user_input = f"Patient: {patient}\nAnlass: {anlass}\nBefunde: {befunde}\nTherapie: {therapie}"

# -----------------------------
# Feedback tab
# -----------------------------
if tab == "Feedback":
    st.markdown("<div style='font-size:15px; font-weight:600;'>💬 Feedback / Rückmeldung</div>", unsafe_allow_html=True)
    feedback = st.text_area("Schreibe dein Feedback", placeholder="z.B. 'Status könnte detaillierter sein…'", height=80, key="feedback_box")
    if st.button("Feedback senden"):
        if feedback.strip():
            send_feedback_email(feedback)
            st.success("Danke für dein Feedback! 🙏")
        else:
            st.warning("Bitte zuerst Feedback eingeben.")

# -----------------------------
# Generate Bericht button (bottom)
# -----------------------------
if st.button("Bericht generieren") and 'user_input' in locals() and user_input.strip() != "":
    with st.spinner("Bericht wird generiert… Bitte warten."):
        start_time = time.time()
        prompt_key_map = {
            "Ambulanter Erstbericht": "ERSTBERICHT_PROMPT",
            "Ambulanter Verlaufsbericht": "VERLAUF_PROMPT",
            "Kostengutsprache Medikament": "KOSTENGUT_MED_PROMPT",
            "Kostengutsprache Rehabilitation": "KOSTENGUT_REHA_PROMPT",
            "Stationärer Bericht": "STATIONAER_PROMPT"
        }
        prompt_text = st.secrets[prompt_key_map[doc_type]]
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "system", "content": prompt_text},{"role":"user","content": user_input}],
            temperature=0.3
        )
        st.session_state.generated_text = response.choices[0].message.content
        st.session_state.elapsed_time = time.time() - start_time

# -----------------------------
# Show generated report
# -----------------------------
if st.session_state.generated_text:
    st.markdown("### Generierter Bericht")
    st.text_area(label="", value=st.session_state.generated_text, height=350)
    primary_color = st.get_option("theme.primaryColor")
    safe_text = st.session_state.generated_text.replace("`","\\`").replace("\\","\\\\").replace("\n","\\n").replace('"','\\"')
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
# Disclaimer
# -----------------------------
st.caption(
    "Dieses Tool dient der Unterstützung beim Verfassen medizinischer Texte. "
    "Die inhaltliche Verantwortung verbleibt bei der behandelnden Ärztin / beim behandelnden Arzt. "
    "Es werden keine Daten gespeichert."
)
