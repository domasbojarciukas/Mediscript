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
# OpenAI client
# -----------------------------
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

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
# Status templates
# -----------------------------
STATUS_TEMPLATES = {
    "LWS": """Allgemein: Patient wach, orientiert. Haltung und Gang normal. Einbeinstand unauffälig.  
Inspektion: Keine sichtbare Fehlstellung. Palpation: Paravertebrale Druckdolenz nicht vorhanden, keine Druckdolenz an Processi spinosi.  
Bewegung: Flexion/Extension normal, Seitneigung normal. Lasègue-Test negativ, Quadrantentest unauffällig, 3-Phasentest unauffällig, Viererzeichen physiologisch. Keine neurologischen Ausfälle.""",
    "HWS": """Allgemein: Patient wach, orientiert. Haltung normal.  
Inspektion: Keine Fehlstellung oder Schwellung. Palpation: Paravertebrale Muskelspannung normal, keine Druckdolenz.  
Bewegung: Flexion, Extension, Lateralflexion und Rotation unauffällig. Spurling Test negativ. Keine neurologischen Auffälligkeiten.""",
    "Schulter": """Allgemein: Patient wach, orientiert. Schulterbeweglichkeit symmetrisch.  
Inspektion: Keine Schwellung, Rötung oder Atrophie. Palpation: keine Druckdolenz.  
Bewegung: Abduktion, Anteversion, Retroversion, Innen- und Aussenrotation physiologisch. Orientierend Schürzen- und Nackengriff problemlos, AC-Gelenk Palpation und Body-Cross-Provokation unauffälig. Kraftprüfung normal. Keine neurologischen Auffälligkeiten.""",
    "Knie": """Allgemein: Patient wach, orientiert. Kniebeweglichkeit symmetrisch. Inspektion: Keine Schwellung, Rötung oder Deformität. Palpation: keine Druckdolenz, keine Gelenkergüsse.  
Bewegung: Flexion und Extension physiologisch. Stabilitätstest unauffällig. Keine neurologischen Auffälligkeiten.""",
    "Hüfte": """Rotationsprüfung: AR/IR schmerzfrei und nicht eingeschränkt, Drehmanzeichen negativ, kein axialer Stauchungsschmerz, kein Leistendruckschmerz.""",
    "Hand": """Allgemein: Patient wach, orientiert. Hände normal gelagert.  
Inspektion: Keine Deformitäten, Rötungen oder Schwellungen. Palpation: keine Druckdolenz an Gelenken oder Sehnen.  
Bewegung: Daumen, Fingerbeweglichkeit und Greiffunktion unauffällig. Sensibilität und Kraft normal.""",
    "Internistisch": """Allgemeinzustand: Wach, orientiert, kein akuter Leidensdruck. Hautfarbe normal, keine Zyanose oder Ikterus. Atemwege frei, Atmung ruhig und regelmässig.  
Herz: rhythmisch, keine Extrasystolen, keine Herzgeräusche. Kreislauf: Blutdruck und Puls physiologisch, keine peripheren Ödeme.  
Abdomen: weich, nicht druckschmerzhaft, keine Resistenzen oder Organvergrösserungen palpabel. Leber- und Milzrand nicht tastbar. Keine Lymphadenopathie. Keine Zeichen für akute Infektion.""",
    "Neuro": """Bewusstsein und Orientierung: wach, klar, orientiert zu Person, Ort und Zeit. Sprache und Sprachexpression unauffällig.  
Motorik: Kraft symmetrisch in allen Extremitäten, kein Paresen. Sensibilität: Berührung, Schmerz, Vibration, Temperatur physiologisch.  
Reflexe: physiologisch, keine pathologischen Babinski- oder Hoffmann-Zeichen. Koordination: Finger-Nase-Test, Knie-Hacke-Test unauffällig. Gang: stabil, ohne Ataxie. Keine Auffälligkeiten im Hirnnervenstatus."""
}

# -----------------------------
# Sidebar document selection
# -----------------------------
st.sidebar.title("Mediscript – Dokumenttyp")
doc_type = st.sidebar.radio(
    "Wähle ein Dokument:",
    ("Ambulanter Erstbericht", "Ambulanter Verlaufsbericht", "Kostengutsprache", "Stationärer Bericht")
)

st.caption("ℹ️ Unklare oder ausstehende Angaben können leer gelassen werden.")

# -----------------------------
# Main content
# -----------------------------
user_input = ""

if doc_type in ["Ambulanter Erstbericht", "Ambulanter Verlaufsbericht", "Stationärer Bericht"]:
    tabs = st.tabs(["Patient / Zuweisung", "Jetzige Leiden & Anamnese", "Status", "Einschätzung", "Therapie / Procedere"])

    # -------- Patient / Zuweisung --------
    with tabs[0]:
        patient = st.text_input("Patient", placeholder="z.B. 72-jährige Patientin")
        zuweisung = st.text_area(
            "Zuweisung (Wer, Datum, Anlass)",
            placeholder="z.B. Hausarzt / Notfall / Selbstzuweisung; Datum; Anlass der Vorstellung",
            height=80
        )
        if doc_type == "Ambulanter Verlaufsbericht":
            last_visit = st.text_area(
                "Verlauf seit letzter Konsultation",
                placeholder="Subjektiver Verlauf, neue Symptome, Besserung / Verschlechterung",
                height=120
            )

    # -------- Jetzige Leiden & Anamnese --------
    with tabs[1]:
        jetzige_leiden = st.text_area(
            "Jetzige Leiden",
            placeholder="- Schulterschmerzen bds\n- Beckengürtelschmerzen\n- Morgensteifigkeit",
            height=120
        )
        anamnesis = st.text_area(
            "Anamnese",
            placeholder="Chronologisch, fragmentiert",
            height=140
        )

    # -------- Status --------
    with tabs[2]:
        selected_status = st.selectbox(
            "Status auswählen (optional für automatisches Ausfüllen)",
            [""] + list(STATUS_TEMPLATES.keys())
        )
        status_text = st.text_area(
            "Status",
            value=STATUS_TEMPLATES.get(selected_status, ""),
            placeholder="Hier wird Status angezeigt oder kann manuell eingegeben werden",
            height=200
        )

    # -------- Einschätzung --------
    with tabs[3]:
        vd = st.text_area(
            "Verdachtsdiagnose (Teil der Einschätzung)",
            placeholder="Falls unklar: Leitsymptom(e), Arbeitsdiagnose, DD",
            height=80
        )
        einschätzung = st.text_area(
            "Einschätzung",
            placeholder="Zusammenfassende Beurteilung, Risikoeinschätzung, Verlauf",
            height=120
        )

    # -------- Therapie / Procedere --------
    with tabs[4]:
        befunde = st.text_area(
            "Befunde (Labor, Bilder, Untersuchung)",
            placeholder="z.B. Blutwerte, Röntgen Thorax, EKG",
            height=120
        )
        therapeutisch = st.text_area(
            "Therapeutisches Vorgehen",
            placeholder="Medikamentös / nicht-medikamentös; begonnen / geplant",
            height=100
        )

    # Assemble user input
    user_input = (
        f"Patient: {patient}\n"
        f"Zuweisung: {zuweisung}\n"
        f"Jetzige Leiden:\n{jetzige_leiden}\n"
        f"Anamnese:\n{anamnesis}\n"
        f"Status:\n{status_text}\n"
        f"Verdachtsdiagnose:\n{vd}\n"
        f"Einschätzung:\n{einschätzung}\n"
        f"Befunde:\n{befunde}\n"
        f"Therapeutisches Vorgehen:\n{therapeutisch}"
    )

elif doc_type == "Kostengutsprache":
    st.sidebar.title("Kostengutsprache")
    tabs = st.tabs(["Angaben", "Optionale Angaben"])

    # -------- Angaben --------
    with tabs[0]:
        context = st.text_area(
            "Klinischer Kontext *",
            placeholder="z.B. 72-jährige Patientin mit manifester Osteoporose und multiplen Fragilitätsfrakturen",
            height=90
        )
        prior = st.text_area(
            "Bisherige Therapien / Limitationen *",
            placeholder="z.B. MTX und Salazopyrin wegen Nebenwirkungen abgesetzt; Steroide nicht langfristig vertretbar",
            height=100
        )
        med = st.text_input(
            "Beantragtes Medikament *",
            placeholder="z.B. Actemra® (Tocilizumab)"
        )
        indication = st.text_area(
            "Indikation für beantragte Therapie *",
            placeholder="Warum ist dieses Medikament medizinisch indiziert?"
        )
        dosage = st.text_input(
            "Dosierung / Therapiedauer",
            placeholder="z.B. 8 mg/kg i.v. alle 4 Wochen"
        )
        justification = st.text_area(
            "Medizinische Begründung und Risiko bei Nichtbewilligung *",
            placeholder="z.B. hohes Frakturrisiko, Progression, irreversible Schäden, fehlende Therapiealternativen",
            height=110
        )

    # -------- Optionale Angaben --------
    with tabs[1]:
        off_label = st.selectbox(
            "Off-label / Art. 71 KVV relevant?",
            ["Unklar", "Nein", "Ja"]
        )
        evidence = st.text_area(
            "Leitlinien / Evidenz (optional)",
            placeholder="Studien, Fachgesellschaften"
        )

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

# -----------------------------
# Generate Bericht
# -----------------------------
if st.button("Bericht generieren") and user_input.strip() != "":
    with st.spinner("Bericht wird generiert… Bitte warten."):
        start_time = time.time()
        prompt_key = {
            "Ambulanter Erstbericht": "ERSTBERICHT_PROMPT",
            "Ambulanter Verlaufsbericht": "VERLAUF_PROMPT",
            "Kostengutsprache": "KOSTENGUT_MED_PROMPT",
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

# -------------------------
# Feedback section
# -------------------------
st.markdown("---")
st.markdown(
    "<div style='font-size:15px; font-weight:600;'>💬 Feedback / Rückmeldung</div>",
    unsafe_allow_html=True
)

feedback = st.text_area(
    "Schreibe dein Feedback",
    placeholder="z.B. 'Status könnte detaillierter sein…'",
    height=80,
    key="feedback_box"
)

if st.button("Feedback senden"):
    if feedback.strip():
        send_feedback_email(feedback)
        st.success("Danke für dein Feedback! 🙏")
    else:
        st.warning("Bitte zuerst Feedback eingeben.")
