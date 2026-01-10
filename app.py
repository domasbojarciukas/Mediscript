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
st.markdown(
    """
    <style>
    footer {visibility: hidden;}
    header {visibility: hidden;}

    section[data-testid="stSidebar"] {
        min-width: 300px;
        max-width: 300px;
        transform: none !important;
        padding-top: 0.5rem;
    }

    /* Hide radio circles */
    div[role="radiogroup"] > label > div:first-child {
        display: none;
    }

    /* Base styling for labels */
    div[role="radiogroup"] label {
        display: block;
        width: 100%;
        padding: 0.4rem 0.6rem;
        margin: 0.1rem 0;
        border-radius: 6px;
        background-color: transparent;
        cursor: pointer;
        font-size: 0.9rem;
        font-weight: 400;
        color: rgb(49, 51, 63);
        transition: background-color 0.1s ease;
    }

    /* Hover */
    div[role="radiogroup"] label:hover {
        background-color: rgba(151, 166, 195, 0.12);
    }

    /* ✅ Selected (persistent) */
    div[role="radiogroup"] input[type="radio"]:checked + div {
        background-color: rgba(151, 166, 195, 0.26);
        font-weight: 300;
    }

    /* Selected hover */
    div[role="radiogroup"] input[type="radio"]:checked + div:hover {
        background-color: rgba(151, 166, 195, 0.12);
    }
    </style>
    """,
    unsafe_allow_html=True
)
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
# Sidebar: Document type
# -----------------------------
doc_type = st.sidebar.radio(
    "Dokumenttyp auswählen",
    ("Ambulanter Erstbericht", "Ambulanter Verlaufsbericht",
     "Kostengutsprache Medikament", "Kostengutsprache Rehabilitation",
     "Stationärer Bericht")
)

st.caption("ℹ️ Unklare oder noch ausstehende Angaben können leer gelassen oder kurz beschrieben werden.")

# -----------------------------
# Status templates
# -----------------------------
STATUS_TEMPLATES = {
    "LWS": """Allgemein: Patient wach, orientiert. Haltung und Gang normal. Einbeinstand unauffälig.  
Inspektion: Keine sichtbare Fehlstellung. Palpation: Paravertebrale Druckdolenz nicht vorhanden.  
Bewegung: Flexion/Extension normal, Seitneigung normal. Lasègue-Test negativ, Quadrantentest unauffällig. Keine neurologischen Ausfälle.""",
    "HWS": """Allgemein: Patient wach, orientiert. Haltung normal.  
Inspektion: Keine Fehlstellung oder Schwellung. Palpation: normal. Bewegung: Flexion, Extension, Lateralflexion und Rotation unauffällig. Spurling Test negativ.""",
    "Schulter": """Allgemein: Patient wach, orientiert. Schulterbeweglichkeit symmetrisch.  
Inspektion: Keine Schwellung, Rötung oder Atrophie. Palpation: keine Druckdolenz. Bewegung: Abduktion, Anteversion, Retroversion, Innen- und Aussenrotation physiologisch. Kraftprüfung normal.""",
    "Knie": """Allgemein: Patient wach, orientiert. Kniebeweglichkeit symmetrisch. Inspektion: Keine Schwellung, Rötung oder Deformität. Palpation: keine Druckdolenz, keine Gelenkergüsse. Bewegung: Flexion und Extension physiologisch. Stabilitätstest unauffällig.""",
    "Hüfte": """Rotationsprüfung: AR/IR schmerzfrei und nicht eingeschränkt, Drehmanzeichen negativ, kein axialer Stauchungsschmerz, kein Leistendruckschmerz.""",
    "Hand": """Allgemein: Patient wach, orientiert. Hände normal gelagert.  
Inspektion: Keine Deformitäten, Rötungen oder Schwellungen. Palpation: keine Druckdolenz. Bewegung: Daumen, Fingerbeweglichkeit und Greiffunktion unauffällig.""",
    "Internistisch": """Allgemeinzustand: Wach, orientiert, kein akuter Leidensdruck. Hautfarbe normal, keine Zyanose oder Ikterus. Lunge: ubiquitär vesikuläre Atemgeräusche. Herz: rhythmisch, keine Extrasystolen. Abdomen: weich, nicht druckschmerzhaft. Keine Resistenzen tastbar.""",
    "Neuro": """Bewusstsein und Orientierung: wach, klar, orientiert zu Person, Ort und Zeit. Sprache und Sprachexpression unauffällig. Motorik: Kraft symmetrisch, Sensibilität physiologisch. Reflexe physiologisch. Koordination unauffällig."""
}

# -----------------------------
# Initialize user input
# -----------------------------
user_input = ""

# -----------------------------
# Ambulanter Erstbericht / Stationärer Bericht / Ambulanter Verlaufsbericht tabs
# -----------------------------
if doc_type in ["Ambulanter Erstbericht", "Ambulanter Verlaufsbericht", "Stationärer Bericht"]:
    tabs = st.tabs(["Patient / Zuweisung", "Jetzige Leiden & Anamnese", "Status & Befunde", "Einschätzung", "Therapie / Procedere"])

    # -------- Patient / Zuweisung --------
    with tabs[0]:
        patient = st.text_input("Patient", placeholder="z.B. 72-jährige Patientin")
        if doc_type == "Ambulanter Erstbericht":
            z = st.text_area(
                "Zuweisung (Wer, Datum, Anlass)",
                placeholder="z.B. Hausarzt / Notfall / Selbstzuweisung; Datum; Anlass der Vorstellung",
                height=80
            )
        else:
            z = ""

    # -------- Jetzige Leiden & Anamnese --------
    with tabs[1]:
        jetzige_leiden = st.text_area(
            "Jetzige Leiden (Stichworte, Symptome)",
            placeholder="- Schulterschmerzen bds\n- Beckengürtelschmerzen\n- Morgensteifigkeit ca. 60 Minuten\n- Keine Fieber",
            height=120
        )
        anamnesis = st.text_area(
            "Anamnese (chronologisch, fragmentiert)",
            placeholder="09/2024: Erstmaliges Auftreten der Beschwerden\n09/2024: Rasche Besserung unter Prednison 25 mg\nNach Tapern Rezidiv der Schmerzen\n07/2025: Beginn MTX, gut verträglich",
            height=140
        )

    # -------- Status & Befunde --------
    with tabs[2]:
        selected_status = st.selectbox(
            "Status wählen (optional für automatisches Ausfüllen)",
            [""] + list(STATUS_TEMPLATES.keys())
        )
        status_text = st.text_area(
            "Status",
            value=STATUS_TEMPLATES.get(selected_status, ""),
            placeholder="Hier wird der Status angezeigt oder kann manuell eingegeben werden",
            height=200
        )
        befunde = st.text_area(
            "Befunde (Labor, Bilder, Untersuchung)",
            placeholder="Klinischer Status; relevante Laborwerte; Bildgebung (inkl. Datum)",
            height=120
        )

    # -------- Einschätzung --------
    with tabs[3]:
        einschätzung = st.text_area(
            "Klinische Einschätzung (inkl. Verdachtsdiagnose)",
            placeholder="Zusammenfassende Beurteilung, Risikoeinschätzung, Verlauf, Verdachtsdiagnose",
            height=140
        )

    # -------- Therapie / Procedere --------
    with tabs[4]:
        therapeutisch = st.text_area(
            "Therapeutisches Vorgehen",
            placeholder="Medikamentös / nicht-medikamentös; begonnen / geplant",
            height=100
        )

    # -------- Assemble input --------
    user_input = (
        f"Patient: {patient}\n"
        f"Zuweisung: {z}\n"
        f"Jetzige Leiden:\n{jetzige_leiden}\n"
        f"Anamnese:\n{anamnesis}\n"
        f"Status:\n{status_text}\n"
        f"Befunde:\n{befunde}\n"
        f"Einschätzung:\n{einschätzung}\n"
        f"Therapeutisches Vorgehen:\n{therapeutisch}"
    )

# -----------------------------
# Kostengutsprache tabs
# -----------------------------
elif doc_type == "Kostengutsprache Medikament":
    
        context = st.text_area(
            "Klinischer Kontext *",
            placeholder="z.B. 72-jährige Patientin mit manifester Osteoporose und multiplen Fragilitätsfrakturen",
            height=90
        )
        prior = st.text_area(
            "Bisherige Therapien und Limitationen *",
            placeholder="z.B. MTX und Salazopyrin wegen Nebenwirkungen abgesetzt; Steroide nicht langfristig vertretbar",
            height=100
        )
        med = st.text_input("Beantragtes Medikament *", placeholder="z.B. Actemra® (Tocilizumab)")
        indication = st.text_area("Indikation für beantragte Therapie *", placeholder="Warum ist dieses Medikament medizinisch indiziert?")
        dosage = st.text_input("Dosierung / Therapiedauer", placeholder="z.B. 8 mg/kg i.v. alle 4 Wochen")
        justification = st.text_area("Medizinische Begründung und Risiko bei Nichtbewilligung *", height=110,
                                     placeholder="z.B. hohes Frakturrisiko, Progression, irreversible Schäden")

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
    rehab = st.text_input("Rehabilitationsmassnahme", placeholder="z.B. Physikalische Therapie 3x pro Woche")
    patient_reha = st.text_input("Patient", placeholder="z.B. 55-jährige Patientin")
    user_input = f"Rehabilitation: {rehab}\nPatient: {patient_reha}"

# -----------------------------
# Generate Bericht
# -----------------------------
if st.button("Bericht generieren") and user_input.strip() != "":
    with st.spinner("Bericht wird generiert… Bitte warten."):
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

    safe_text = generated_text.replace("`","\\`").replace("\\","\\\\").replace("\n","\\n").replace('"','\\"')
    primary_color = st.get_option("theme.primaryColor")

    components.html(f"""
    <button style='
        padding: 0.45em 1em;
        font-size: 1em;
        font-weight: 600;
        border-radius: 0.25em;
        border: none;
        background-color: {primary_color};
        color: white;
        cursor: pointer;
    '
    onclick='
        const text = `{safe_text}`;
        navigator.clipboard.writeText(text).then(() => {{
            alert("Bericht in die Zwischenablage kopiert!");
        }});
    '>
        Bericht kopieren
    </button>
""", height=40)

    st.info(f"⏱️ Bericht generiert in {st.session_state.elapsed_time:.2f} Sekunden")

# -----------------------------
# Feedback
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
    "Die inhaltliche Verantwortung verbleibt bei der behandelnden Ärztin / beim behandelnden Arzt. "
    "Es werden keine Daten gespeichert."
)
