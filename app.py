import time
import textwrap
import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI

# -----------------------------
# Page config + hide header/footer
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

st.title("Mediscript – Testphase")

# -----------------------------
# OpenAI client
# -----------------------------
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# -----------------------------
# Select document type
# -----------------------------
doc_type = st.selectbox(
    "Dokumenttyp auswählen",
    (
        "Ambulanter Erstbericht",
        "Ambulanter Verlaufsbericht",
        "Kostengutsprache Medikament",
        "Kostengutsprache Rehabilitation",
        "Stationärer Bericht",
    )
)

st.caption(
    "ℹ️ Unklare oder noch ausstehende Angaben können leer gelassen oder kurz beschrieben werden."
)

# -----------------------------
# Status templates
# -----------------------------
STATUS_TEMPLATES = {
    "LWS": """Allgemein: Patient wach, orientiert. Haltung und Gang normal.
Inspektion: Keine sichtbare Fehlstellung. Palpation: Paravertebrale Druckdolenz vorhanden, Druckdolenz an Processi spinosi.
Bewegung: Flexion/Extension normal, Seitneigung normal. Lasègue-Test negativ, Quadrantentest unauffällig, 3-Phasentest unauffällig, Viererzeichen physiologisch. Keine neurologischen Ausfälle.""",

    "HWS": """Allgemein: Patient wach, orientiert. Haltung normal.
Inspektion: Keine Fehlstellung oder Schwellung. Palpation: Paravertebrale Muskelspannung leicht erhöht.
Bewegung: Flexion, Extension, Lateralflexion und Rotation altersentsprechend. Keine neurologischen Auffälligkeiten.""",

    "Schulter": """Allgemein: Patient wach, orientiert.
Inspektion: Keine Schwellung, Rötung oder Atrophie.
Palpation: Keine relevante Druckdolenz.
Bewegung: Abduktion, Anteversion, Innen- und Außenrotation frei. Kraft altersentsprechend.""",

    "Knie": """Allgemein: Patient wach, orientiert.
Inspektion: Keine Schwellung oder Deformität.
Palpation: Kein Erguss, keine relevante Druckdolenz.
Bewegung: Flexion und Extension frei, Bandstabilität klinisch unauffällig.""",

    "Hand": """Allgemein: Patient wach, orientiert.
Inspektion: Keine Deformitäten oder Schwellungen.
Palpation: Keine Druckdolenz an Gelenken oder Sehnen.
Bewegung: Faustschluss und Fingerstreckung vollständig, Kraft und Sensibilität erhalten.""",

    "Internistisch": """Allgemeinzustand gut, wach und orientiert.
Herz-Kreislauf: Rhythmisch, keine pathologischen Herzgeräusche, normfrequenter Puls, keine peripheren Ödeme.
Lunge: Vesikuläres Atemgeräusch beidseits, keine Nebengeräusche.
Abdomen: Weich, nicht druckdolent, keine Resistenzen palpabel.""",

    "Neuro": """Bewusstsein klar, voll orientiert.
Motorik: Kraft symmetrisch, keine Paresen.
Sensibilität: Oberflächlich und tief unauffällig.
Reflexe: Seitengleich, physiologisch, keine Pyramidenbahnzeichen.
Koordination und Gangbild unauffällig."""
}

# -----------------------------
# Document-specific inputs
# -----------------------------
user_input = ""

if doc_type == "Ambulanter Erstbericht":

    z = st.text_area(
        "Zuweisung (Wer, Datum, Anlass)",
        height=80
    )

    jetzige_leiden = st.text_area(
        "Jetzige Leiden",
        height=120
    )

    anamnesis = st.text_area(
        "Anamnese",
        height=140
    )

    selected_status = st.selectbox(
        "Statusvorlage (optional)",
        [""] + list(STATUS_TEMPLATES.keys())
    )

    status_text = st.text_area(
        "Status",
        value=STATUS_TEMPLATES.get(selected_status, ""),
        height=200
    )

    vd = st.text_area("Klinische Verdachtsdiagnose", height=80)
    befunde = st.text_area("Befunde", height=120)
    einschätzung = st.text_area("Klinische Einschätzung", height=120)
    therapeutisch = st.text_area("Therapeutisches Vorgehen", height=100)

    user_input = textwrap.dedent(f"""
    Zuweisung:
    {z}

    Jetzige Leiden:
    {jetzige_leiden}

    Anamnese:
    {anamnesis}

    Status:
    {status_text}

    Klinische Verdachtsdiagnose:
    {vd}

    Befunde:
    {befunde}

    Klinische Einschätzung:
    {einschätzung}

    Therapeutisches Vorgehen:
    {therapeutisch}
    """).strip()

elif doc_type == "Ambulanter Verlaufsbericht":

    patient = st.text_input("Patient / Kontext")
    verlauf = st.text_area("Verlauf seit letzter Konsultation", height=120)
    neue_befunde = st.text_area("Neue Befunde", height=120)
    beurteilung = st.text_area("Beurteilung", height=120)
    therapie = st.text_area("Therapie / Weiteres Vorgehen", height=100)

    user_input = textwrap.dedent(f"""
    Patient:
    {patient}

    Verlauf:
    {verlauf}

    Neue Befunde:
    {neue_befunde}

    Beurteilung:
    {beurteilung}

    Therapie:
    {therapie}
    """).strip()

elif doc_type == "Kostengutsprache Medikament":

    context = st.text_area("Klinischer Kontext", height=90)
    prior = st.text_area("Bisherige Therapien / Limitationen", height=100)
    med = st.text_input("Beantragtes Medikament")
    indication = st.text_area("Indikation")
    dosage = st.text_input("Dosierung / Dauer")
    justification = st.text_area("Begründung und Risiken", height=110)

    # Optional details
    with st.expander("Optionale Angaben (empfohlen bei Rückfragen der Versicherung)"):
        off_label = st.selectbox(
            "Off-label / Art. 71 KVV relevant?",
            ["Unklar", "Nein", "Ja"]
        )
        evidence = st.text_area(
            "Leitlinien / Evidenz",
            placeholder="z.B. EULAR, ACR, relevante Studien"
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

elif doc_type == "Kostengutsprache Rehabilitation":

    rehab = st.text_input("Rehabilitationsmassnahme")
    patient = st.text_input("Patient")

    user_input = f"Patient: {patient}\nRehabilitation: {rehab}"

elif doc_type == "Stationärer Bericht":

    patient = st.text_input("Patient")
    anlass = st.text_area("Aufnahmegrund", height=120)
    befunde = st.text_area("Befunde", height=120)
    therapie = st.text_area("Therapie / Weiteres Vorgehen", height=100)

    user_input = textwrap.dedent(f"""
    Patient:
    {patient}

    Aufnahmegrund:
    {anlass}

    Befunde:
    {befunde}

    Therapie:
    {therapie}
    """).strip()

# -----------------------------
# Generate Bericht (SINGLE button)
# -----------------------------
if st.button("Bericht generieren") and user_input.strip():

    with st.spinner("Bericht wird generiert …"):
        start_time = time.time()

        prompt_key = {
            "Ambulanter Erstbericht": "ERSTBERICHT_PROMPT",
            "Ambulanter Verlaufsbericht": "VERLAUF_PROMPT",
            "Kostengutsprache Medikament": "KOSTENGUT_MED_PROMPT",
            "Kostengutsprache Rehabilitation": "KOSTENGUT_REHA_PROMPT",
            "Stationärer Bericht": "STATIONAER_PROMPT",
        }[doc_type]

        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": st.secrets[prompt_key]},
                {"role": "user", "content": user_input},
            ],
            temperature=0.3,
        )

        st.session_state.generated_text = response.choices[0].message.content
        st.session_state.elapsed_time = time.time() - start_time

# -----------------------------
# Output
# -----------------------------
if "generated_text" in st.session_state:

    st.markdown("### Generierter Bericht")
    st.text_area("", st.session_state.generated_text, height=350)

    safe_text = (
        st.session_state.generated_text
        .replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("\n", "\\n")
        .replace('"', '\\"')
    )

    components.html(
        f"""
        <button onclick="navigator.clipboard.writeText(`{safe_text}`)">
            Bericht kopieren
        </button>
        """,
        height=40,
    )

    st.info(f"⏱️ Generiert in {st.session_state.elapsed_time:.2f} Sekunden")

# -----------------------------
# Disclaimer
# -----------------------------
st.caption(
    "Dieses Tool dient der Unterstützung beim Verfassen medizinischer Texte. "
    "Die inhaltliche Verantwortung verbleibt bei der behandelnden Ärztin / beim behandelnden Arzt."
)
