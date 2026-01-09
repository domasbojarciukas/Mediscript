import time
import streamlit as st
import streamlit.components.v1 as components
import textwrap
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

st.title("Mediscript - Testphase")

# -----------------------------
# OpenAI client
# -----------------------------
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# -----------------------------
# Select document type
# -----------------------------
doc_type = st.selectbox(
    "Dokumenttyp auswählen",
    ("Ambulanter Erstbericht", "Ambulanter Verlaufsbericht",
     "Kostengutsprache Medikament", "Kostengutsprache Rehabilitation",
     "Stationärer Bericht")
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
Inspektion: Keine Fehlstellung oder Schwellung. Palpation: Paravertebrale Muskelspannung normal, Druckdolenz nur minimal.  
Bewegung: Flexion, Extension, Lateralflexion und Rotation unauffällig. Keine neurologischen Auffälligkeiten.""",
    "Schulter": """Allgemein: Patient wach, orientiert. Schulterbeweglichkeit symmetrisch.  
Inspektion: Keine Schwellung, Rötung oder Atrophie. Palpation: keine Druckdolenz.  
Bewegung: Abduktion, Anteversion, Retroversion, Innen- und Außenrotation physiologisch. Kraftprüfung normal. Keine neurologischen Auffälligkeiten.""",
    "Knie": """Allgemein: Patient wach, orientiert. Kniebeweglichkeit symmetrisch.  
Inspektion: Keine Schwellung, Rötung oder Deformität. Palpation: keine Druckdolenz, keine Gelenkergüsse.  
Bewegung: Flexion und Extension physiologisch. Stabilitätstest unauffällig. Keine neurologischen Auffälligkeiten.""",
    "Hand": """Allgemein: Patient wach, orientiert. Hände normal gelagert.  
Inspektion: Keine Deformitäten, Rötungen oder Schwellungen. Palpation: keine Druckdolenz an Gelenken oder Sehnen.  
Bewegung: Daumen, Fingerbeweglichkeit und Greiffunktion unauffällig. Sensibilität und Kraft normal.""",
    "Internistisch": """Allgemeinzustand: Wach, orientiert, kein akuter Leidensdruck. Hautfarbe normal, keine Zyanose oder Ikterus. Atemwege frei, Atmung ruhig und regelmässig.  
Herz: rhythmisch, keine Extrasystolen, keine Herzgeräusche. Kreislauf: Blutdruck und Puls physiologisch, keine peripheren Ödeme.  
Abdomen: weich, nicht druckschmerzhaft, keine Resistenzen oder Organvergrößerungen palpabel. Leber- und Milzrand nicht tastbar. Keine Lymphadenopathie. Keine Zeichen für akute Infektion.""",
    "Neuro": """Bewusstsein und Orientierung: wach, klar, orientiert zu Person, Ort und Zeit. Sprache und Sprachexpression unauffällig.  
Motorik: Kraft symmetrisch in allen Extremitäten, kein Paresen. Sensibilität: Berührung, Schmerz, Vibration, Temperatur physiologisch.  
Reflexe: physiologisch, keine pathologischen Babinski- oder Hoffmann-Zeichen. Koordination: Finger-Nase-Test, Knie-Hacke-Test unauffällig. Gang: stabil, ohne Ataxie. Keine Auffälligkeiten im Hirnnervenstatus."""
}

# -----------------------------
# Streamlit UI Inputs
# -----------------------------

if doc_type == "Ambulanter Erstbericht":
    z = st.text_area(
        "Zuweisung (Wer, Datum, Anlass)",
        placeholder="z.B. Hausarzt / Notfall / Selbstzuweisung; Datum; Anlass der Vorstellung",
        height=80
    )

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

    selected_status = st.selectbox(
        "Status wählen (optional für automatisches Ausfüllen)",
        [""] + list(STATUS_TEMPLATES.keys())
    )

    status_text = st.text_area(
        "Status",
        value=STATUS_TEMPLATES.get(selected_status, ""),
        height=200
    )

    vd = st.text_area(
        "Klinische Verdachtsdiagnose",
        placeholder="Falls unklar: Leitsymptom(e), Arbeitsdiagnose, DD",
        height=80
    )

    befunde = st.text_area(
        "Befunde (Labor, Bilder, Untersuchung)",
        placeholder="Klinischer Status; relevante Laborwerte; Bildgebung (inkl. Datum)",
        height=120
    )

    einschätzung = st.text_area(
        "Klinische Einschätzung",
        placeholder="Zusammenfassende Beurteilung, Risikoeinschätzung, Verlauf",
        height=120
    )

    therapeutisch = st.text_area(
        "Therapeutisches Vorgehen",
        placeholder="Medikamentös / nicht-medikamentös; begonnen / geplant",
        height=100
    )

    # Assemble structured input for AI
    user_input = (
        f"Jetzige Leiden:\n{jetzige_leiden}\n\n"
        f"Anamnese:\n{anamnesis}\n\n"
        f"Status:\n{status_text}\n\n"
        f"Zuweisung:\n{z}\n\n"
        f"Verdachtsdiagnose:\n{vd}\n\n"
        f"Befunde:\n{befunde}\n\n"
        f"Einschätzung:\n{einschätzung}\n\n"
        f"Therapeutisches Vorgehen:\n{therapeutisch}"
    )

    st.write("---")

    with st.expander("Strukturierte Input-Vorschau (für Überprüfung)"):
        st.markdown(
            f"**Jetzige Leiden:**\n{jetzige_leiden}\n\n"
            f"**Anamnese:**\n{anamnesis}\n\n"
            f"**Status:**\n{status_text}\n"
    )
    
    st.subheader("Strukturierte Input-Vorschau")
    st.markdown(
        f"**Jetzige Leiden:**\n{jetzige_leiden}\n\n"
        f"**Anamnese:**\n{anamnesis}\n\n"
        f"**Status:**\n{status_text}\n"
    )

    # -----------------------------
    # AI generation trigger (example)
    # -----------------------------
    if st.button("Bericht generieren", key="erstbericht_button"):
    bericht_text = "Hier würde der generierte Beurteilungstext erscheinen..."
    procedere_text = "Hier würden die Bullet-Points für Procedere erscheinen."

    st.write("---")
    st.subheader("Generierter Bericht (Beurteilung)")
    st.write(bericht_text)

    st.subheader("Procedere")
    st.write(procedere_text)

elif doc_type == "Ambulanter Verlaufsbericht":
    patient = st.text_input(
        "Patientinfo",
        placeholder="z.B. 55-jährige Patientin mit lumbalen Schmerzen, Erstvorstellung am 06.11.2025"
    )

    verlauf = st.text_area(
        "Verlauf seit letzter Konsultation",
        placeholder="Subjektiver Verlauf, neue Symptome, Besserung / Verschlechterung",
        height=120
    )

    neue_befunde = st.text_area(
        "Neue Befunde",
        placeholder="Neue Laborwerte, Bildgebung, klinische Untersuchungen seit letzter Konsultation",
        height=120
    )

    beurteilung = st.text_area(
        "Beurteilung",
        placeholder="Zusammenfassende Einschätzung des aktuellen Zustands und Verlaufs",
        height=120
    )

    therapie = st.text_area(
        "Therapie / Weiteres Vorgehen",
        placeholder="Therapieanpassungen, geplante Massnahmen, Verlaufskontrollen",
        height=100
    )

    user_input = (
        f"Patient: {patient}\n"
        f"Verlauf: {verlauf}\n"
        f"Neue Befunde: {neue_befunde}\n"
        f"Beurteilung: {beurteilung}\n"
        f"Therapie: {therapie}"
    )

elif doc_type == "Kostengutsprache Medikament":

    st.markdown("### Angaben zur Kostengutsprache")

    context = st.text_area(
    "Klinischer Kontext *",
    placeholder="z.B. 72-jährige Patientin mit manifester Osteoporose und multiplen Fragilitätsfrakturen ohne adäquates Ansprechen auf antiresorptive Therapie",
    height=90
    )

    prior = st.text_area(
    "Bisherige Therapien und Limitationen *",
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

    # Optional but very useful
    with st.expander("➕ Optionale Angaben"):
        off_label = st.selectbox(
            "Off-label / Art. 71 KVV relevant?",
            ["Unklar", "Nein", "Ja"]
        )

        evidence = st.text_area(
            "Leitlinien / Evidenz (optional)",
            placeholder="Studien, Fachgesellschaften"
        )

    # Build structured prompt input
    
    user_input = textwrap.dedent(f"""
Klinischer Kontext:
{context}

Bisherige Therapien / Limitationen:
{prior}

Beantragtes Medikament:
{med}

Indikation:
{indication}

Dosierung / Dauer:
{dosage}

Begründung und Risiken:
{justification}

Off-label / Art. 71 KVV:
{off_label}

Evidenz / Leitlinien:
{evidence}
""").strip()

elif doc_type == "Kostengutsprache Rehabilitation":
    rehab = st.text_input("Rehabilitationsmaßnahme")
    patient = st.text_input("Patient")
    user_input = f"Rehabilitation: {rehab}\nPatient: {patient}"

elif doc_type == "Stationärer Bericht":
    patient = st.text_input("Patient")
    anlass = st.text_area("Anlass / Aufnahmegrund", height=120)
    befunde = st.text_area("Befunde (Labor, Bilder, Untersuchung)", height=120)
    therapie = st.text_area("Therapie / Weiteres Vorgehen", height=100)
    user_input = f"Patient: {patient}\nAnlass: {anlass}\nBefunde: {befunde}\nTherapie: {therapie}"

# -----------------------------
# Generate Bericht
# -----------------------------

if st.button("Bericht generieren") and user_input.strip() != "":
    with st.spinner("Bericht wird generiert… Bitte warten."):
        start_time = time.time()  # START TIMER
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

         # Save report to session state
        st.session_state.generated_text = response.choices[0].message.content
        elapsed = time.time() - start_time  # END TIMER
        st.session_state.elapsed_time = elapsed

# Show report if generated
if "generated_text" in st.session_state:
    generated_text = st.session_state.generated_text
    st.markdown("### Generierter Bericht")
    st.text_area(label="", value=generated_text, height=350)

    # Copy-to-clipboard as HTML button
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
            }});
        ">
            Bericht kopieren
        </button>
    """, height=40)

# Show elapsed time
    st.info(f"⏱️ Bericht generiert in {st.session_state.elapsed_time:.2f} Sekunden")

# -------------------------
# Optional disclaimer
# -------------------------
st.caption(
    "Dieses Tool dient der Unterstützung beim Verfassen medizinischer Texte. "
    "Die inhaltliche Verantwortung verbleibt bei der behandelnden Ärztin / beim behandelnden Arzt."
)
