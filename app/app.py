import streamlit as st
import pandas as pd
import pickle
import plotly.graph_objects as go
import pdfplumber
from groq import Groq
import json
import re
import os
import base64
from datetime import datetime

# ============================================
# CONFIGURATION DE LA PAGE
# ============================================
st.set_page_config(
    page_title="RecrutIA — Analyse de CV",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================
# CSS — Dark luxury editorial
# ============================================
st.markdown('<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap" rel="stylesheet">', unsafe_allow_html=True)

st.markdown("""<style>
/* Base */
*, *::before, *::after { box-sizing: border-box; }
html, body, [data-testid="stAppViewContainer"] {
    background: #07070d !important;
    color: #e2e0da !important;
    font-family: 'DM Sans', sans-serif !important;
}
[data-testid="stAppViewContainer"] > .main { background: #07070d !important; }
[data-testid="stHeader"] { background: transparent !important; }
section[data-testid="stMain"] > div { padding-top: 1rem !important; }

/* Hide chrome */
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: #0e0e18 !important;
    border-right: 1px solid #1a1a2e !important;
}
[data-testid="stSidebar"] * { color: #8888aa !important; font-family: 'DM Sans', sans-serif !important; }
[data-testid="stSidebar"] input {
    background: #16162a !important; border: 1px solid #25253a !important;
    color: #e2e0da !important; border-radius: 8px !important;
}
[data-testid="stSidebar"] .stButton > button {
    background: #16162a !important; border: 1px solid #25253a !important;
    color: #8888aa !important; border-radius: 8px !important;
    box-shadow: none !important; font-size: 0.85rem !important;
}

/* Buttons */
[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #6d28d9, #4338ca) !important;
    color: #fff !important; border: none !important; border-radius: 10px !important;
    font-family: 'Syne', sans-serif !important; font-weight: 700 !important;
    font-size: 0.95rem !important; letter-spacing: 0.04em !important;
    padding: 0.7rem 2rem !important; transition: all 0.2s !important;
    box-shadow: 0 4px 18px rgba(109,40,217,.3) !important;
}
[data-testid="stButton"] > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 28px rgba(109,40,217,.5) !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
    background: #0e0e18 !important; border: 2px dashed #25253a !important;
    border-radius: 14px !important; transition: border-color 0.2s !important;
}
[data-testid="stFileUploader"]:hover { border-color: #6d28d9 !important; }
[data-testid="stFileUploader"] * { color: #8888aa !important; }
[data-testid="stFileUploader"] small { color: #444460 !important; }

/* Expander */
[data-testid="stExpander"] {
    background: #0e0e18 !important; border: 1px solid #1a1a2e !important;
    border-radius: 12px !important;
}
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary p { color: #8888aa !important; }

/* Inputs inside expander */
[data-testid="stNumberInput"] input, [data-testid="stTextInput"] input {
    background: #16162a !important; border: 1px solid #25253a !important;
    color: #e2e0da !important; border-radius: 8px !important;
}
[data-testid="stSelectbox"] > div > div {
    background: #16162a !important; border: 1px solid #25253a !important;
    color: #e2e0da !important; border-radius: 8px !important;
}
[data-testid="stRadio"] label, [data-testid="stSelectbox"] label,
[data-testid="stNumberInput"] label, [data-testid="stSlider"] label {
    color: #8888aa !important; font-size: 0.85rem !important;
}
[data-testid="stSlider"] [role="slider"] { background: #6d28d9 !important; }

/* Status */
[data-testid="stStatus"] {
    background: #0e0e18 !important; border: 1px solid #1a1a2e !important;
    border-radius: 12px !important; color: #8888aa !important;
}

/* Alerts */
[data-testid="stAlert"] { background: #0e0e18 !important; border-radius: 10px !important; }

/* HR */
hr { border-color: #1a1a2e !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: #07070d; }
::-webkit-scrollbar-thumb { background: #25253a; border-radius: 3px; }

/* Plotly */
.js-plotly-plot, .plot-container { background: transparent !important; }
</style>
""", unsafe_allow_html=True)

# ============================================
# RÉSOLUTION DE LA CLÉ API GROQ  (logique inchangée)
# ============================================
def get_api_key():
    # 1️⃣ Streamlit Cloud secrets
    try:
        if "GROK_API_KEY" in st.secrets:
            return st.secrets["GROK_API_KEY"]
    except Exception:
        pass

    # 2️⃣ Variable d’environnement (local)
    env_key = os.environ.get("GROK_API_KEY")
    if env_key:
        return env_key

    # 3️⃣ Saisie manuelle dans la sidebar
    return st.session_state.get("api_key_input")

# ── Sidebar : minimaliste, statut discret ──
with st.sidebar:
    st.markdown("<p style='font-size:0.75rem;font-weight:700;letter-spacing:0.12em;color:#444460;text-transform:uppercase;margin-bottom:0.8rem;'>Configuration</p>", unsafe_allow_html=True)

    api_key_input = st.text_input(
        "Cle API Groq",
        type="password",
        placeholder="gsk_...",
        key="api_key_input",
        help="Gratuit sur console.groq.com"
    )
    if get_api_key():
        st.markdown("<span style='color:#4ade80;font-size:0.8rem;'>&#9679; Connecte</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span style='color:#f87171;font-size:0.8rem;'>&#9679; Cle manquante &mdash; console.groq.com</span>", unsafe_allow_html=True)

    st.markdown("---")
    if st.session_state.get("cv_parsed"):
        if st.button("Nouveau CV", use_container_width=True):
            st.session_state.cv_parsed = False
            st.session_state.extracted_data = None
            st.session_state.cv_text = None
            st.rerun()

# ============================================
# EXTRACTION (logique 100% inchangée)
# ============================================
def extract_text_from_pdf(pdf_file) -> str:
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        if row:
                            text += " | ".join([cell or "" for cell in row]) + "\n"
        return text.strip()
    except Exception as e:
        st.error(f"Erreur lecture PDF: {str(e)}")
        return None


def extract_cv_with_groq(cv_text: str) -> dict:
    api_key = get_api_key()
    if not api_key:
        st.error("Cle API Groq manquante. Renseignez-la dans la sidebar.")
        return None

    client = Groq(api_key=api_key)

    system_prompt = """Tu es un expert RH et analyste de CV. 
Tu dois extraire avec précision les informations d'un CV et retourner UNIQUEMENT un objet JSON valide.
Aucun texte avant ou après le JSON. Aucun markdown, aucun commentaire. Pas de ```json```.

Les règles d'extraction :
- Age : déduis-le depuis la date de naissance si disponible (année actuelle = 2025), sinon estime depuis le parcours. Range: 18-65.
- Gender : 1 = Homme, 0 = Femme. Déduis depuis prénom, civilité (M./Mme), accords grammaticaux (né/née). Si vraiment inconnu: 1.
- MaritalStatus : 0=Célibataire, 1=Marié(e), 2=Divorcé(e)/Séparé(e). Si non mentionné: 0.
- Education : 1=Sans diplôme/Brevet, 2=Bac, 3=Bac+2 (BTS/DUT/DEUG), 4=Bac+3/4 (Licence/Bachelor/Master1), 5=Bac+5+ (Master2/Ingénieur/MBA/Doctorat).
- TotalWorkingYears : total des années d'expérience professionnelle (calcule depuis les dates des postes). Range: 0-40.
- DistanceFromHome : en km, si non mentionné estime selon ville de résidence vs ville de travail majoritaire (15 par défaut si inconnu).
- BusinessTravel : 0=Pas de déplacements, 1=Déplacements rares (quelques fois/an), 2=Déplacements fréquents (plusieurs fois/mois).
- TrainingTimesLastYear : nombre de formations/certifications obtenues. Compte les certifs, diplômes pro récents. Range: 0-6.

Champs additionnels :
- full_name : nom complet
- current_job_title : poste actuel ou dernier poste
- email : adresse email si présente, sinon ""
- phone : téléphone si présent, sinon ""
- location : ville/pays de résidence
- top_skills : liste de 3-5 compétences clés (array de strings)
- languages : langues parlées (array de strings)
- education_detail : dernier diplôme en clair
- last_company : dernière entreprise
- confidence_score : entre 0 et 100, ta confiance dans l'extraction

Réponds avec UNIQUEMENT ce JSON, strictement rien d'autre :
{"Age":30,"Gender":1,"MaritalStatus":0,"Education":4,"TotalWorkingYears":5,"DistanceFromHome":10,"BusinessTravel":1,"TrainingTimesLastYear":2,"full_name":"Jean Dupont","current_job_title":"Développeur","email":"","phone":"","location":"Paris","top_skills":["Python"],"languages":["Français"],"education_detail":"Master Info","last_company":"TechCorp","confidence_score":85}"""

    user_prompt = f"""Voici le texte extrait d'un CV. Analyse-le et extrais toutes les informations demandées.

=== TEXTE DU CV ===
{cv_text[:6000]}
===================

Retourne UNIQUEMENT le JSON, rien d'autre."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=1000,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        raw = response.choices[0].message.content.strip()
        raw = re.sub(r'^```json\s*', '', raw)
        raw = re.sub(r'^```\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
        raw = raw.strip()
        extracted = json.loads(raw)

        extracted['Age'] = max(18, min(65, int(extracted.get('Age', 30))))
        extracted['Gender'] = int(extracted.get('Gender', 1)) if extracted.get('Gender') in [0, 1] else 1
        extracted['MaritalStatus'] = int(extracted.get('MaritalStatus', 0)) if extracted.get('MaritalStatus') in [0, 1, 2] else 0
        extracted['Education'] = max(1, min(5, int(extracted.get('Education', 3))))
        extracted['TotalWorkingYears'] = max(0, min(40, int(extracted.get('TotalWorkingYears', 5))))
        extracted['DistanceFromHome'] = max(1, min(50, int(extracted.get('DistanceFromHome', 10))))
        extracted['BusinessTravel'] = int(extracted.get('BusinessTravel', 1)) if extracted.get('BusinessTravel') in [0, 1, 2] else 1
        extracted['TrainingTimesLastYear'] = max(0, min(6, int(extracted.get('TrainingTimesLastYear', 2))))
        return extracted

    except json.JSONDecodeError as e:
        st.error(f"Erreur parsing JSON: {str(e)}")
        st.code(raw, language="text")
        return None
    except Exception as e:
        st.error(f"Erreur API Groq: {str(e)}")
        return None


def parse_cv(pdf_file):
    with st.status("Analyse IA du CV en cours...", expanded=True) as status:
        st.write("Extraction du texte PDF...")
        cv_text = extract_text_from_pdf(pdf_file)
        if not cv_text or len(cv_text) < 50:
            status.update(label="PDF illisible ou vide", state="error")
            st.error("Le PDF semble vide ou illisible. Verifiez qu'il n'est pas scanne/image.")
            return None, None
        st.write(f"{len(cv_text)} caracteres extraits")
        st.write("Analyse par Llama 3.3 70B (Groq)...")
        extracted = extract_cv_with_groq(cv_text)
        if extracted:
            confidence = extracted.get('confidence_score', 0)
            status.update(label=f"Extraction reussie — confiance {confidence}%", state="complete")
        else:
            status.update(label="Echec de l'extraction IA", state="error")
            return None, None
    return extracted, cv_text


# ============================================
# ML (logique 100% inchangée)
# ============================================
@st.cache_resource
def load_model():
    try:
        with open('models/random_forest.pkl', 'rb') as f:
            return pickle.load(f)
    except:
        return None


def prepare_input_data(input_dict):
    full_input = {
        'Age': input_dict.get('Age', 30),
        'BusinessTravel': input_dict.get('BusinessTravel', 1),
        'DistanceFromHome': input_dict.get('DistanceFromHome', 10),
        'Education': input_dict.get('Education', 3),
        'Gender': input_dict.get('Gender', 1),
        'JobInvolvement': 3,
        'MaritalStatus': input_dict.get('MaritalStatus', 1),
        'PerformanceRating': 3,
        'TotalWorkingYears': input_dict.get('TotalWorkingYears', 5),
        'TrainingTimesLastYear': input_dict.get('TrainingTimesLastYear', 3)
    }
    expected_features = [
        'Age', 'BusinessTravel', 'DistanceFromHome', 'Education', 'Gender',
        'JobInvolvement', 'MaritalStatus', 'PerformanceRating',
        'TotalWorkingYears', 'TrainingTimesLastYear'
    ]
    return pd.DataFrame([full_input])[expected_features]


def calculate_recruitment_score(attrition_prob):
    return max(0, min(100, 100 - (attrition_prob * 100)))


def get_recruitment_advice(score):
    if score >= 80:
        return {"decision": "FORTEMENT RECOMMANDE", "color": "#16a34a", "bg": "#052e16",
                "accent": "#4ade80", "advice": "Candidat excellent avec un fort potentiel de stabilite", "grade": "A"}
    elif score >= 60:
        return {"decision": "RECOMMANDE", "color": "#ca8a04", "bg": "#1c1405",
                "accent": "#facc15", "advice": "Bon candidat, presenterait un risque modere", "grade": "B"}
    elif score >= 40:
        return {"decision": "A EVALUER", "color": "#ea580c", "bg": "#1c0f05",
                "accent": "#fb923c", "advice": "Candidat avec quelques reserves, entretien approfondi recommande", "grade": "C"}
    else:
        return {"decision": "DECONSEILLE", "color": "#dc2626", "bg": "#1c0505",
                "accent": "#f87171", "advice": "Risque eleve d'instabilite, recherche d'autres candidats recommandee", "grade": "D"}
def generate_ai_justification(data: dict, score: float, decision: str) -> str:
    """Genere une justification detaillee du score via Groq."""
    api_key = get_api_key()
    if not api_key:
        return None

    client = Groq(api_key=api_key)

    edu_map = {1: "Sans diplome", 2: "Baccalaureat", 3: "Bac+2 (BTS/DUT)",
               4: "Bac+3/4 (Licence/Master 1)", 5: "Bac+5 et plus (Master/Ingenieur)"}
    travel_map = {0: "aucun deplacement professionnel", 1: "deplacements rares",
                  2: "deplacements frequents"}
    marital_map = {0: "celibataire", 1: "marie(e)", 2: "divorce(e)"}

    prompt = f"""Tu es un expert RH senior. Tu dois rediger une analyse professionnelle concise (5-7 phrases)
pour justifier pourquoi ce candidat a obtenu la decision "{decision}" avec un score de {score:.0f}%.

Profil du candidat :
- Nom : {data.get("full_name", "N/A")}
- Poste : {data.get("current_job_title", "N/A")}
- Age : {data["Age"]} ans
- Situation familiale : {marital_map[data["MaritalStatus"]]}
- Formation : {edu_map[data["Education"]]} — {data.get("education_detail", "")}
- Experience totale : {data["TotalWorkingYears"]} ans
- Formations suivies l'an dernier : {data["TrainingTimesLastYear"]}
- Distance domicile-travail : {data["DistanceFromHome"]} km
- Disponibilite aux deplacements : {travel_map[data["BusinessTravel"]]}
- Competences : {", ".join(data.get("top_skills", []))}
- Langues : {", ".join(data.get("languages", []))}

Redige une analyse RH professionnelle en francais qui :
1. Explique les facteurs positifs qui ont contribue au score
2. Mentionne les facteurs de risque eventuels (attrition, stabilite)
3. Conclut avec une recommandation concrete pour le recruteur
Sois direct, factuel et professionnel. Pas de titre, pas de liste, juste un paragraphe fluide."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return None






def get_pdf_download_button(filepath: str, label: str, filename: str, accent: str = "#6d28d9") -> str:
    """Retourne un bouton de telechargement HTML pour un PDF."""
    try:
        with open(filepath, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        return f'''
        <a href="data:application/pdf;base64,{b64}" download="{filename}"
           style="display:inline-flex;align-items:center;gap:0.5rem;
                  background:transparent;border:1px solid {accent}50;
                  color:{accent};border-radius:8px;padding:0.45rem 1rem;
                  font-family:'Syne',sans-serif;font-weight:600;font-size:0.82rem;
                  letter-spacing:0.04em;text-decoration:none;
                  transition:all 0.2s;cursor:pointer;"
           onmouseover="this.style.background=\'{accent}15\';this.style.borderColor=\'{accent}80\'"
           onmouseout="this.style.background='transparent';this.style.borderColor=\'{accent}50\'">
            &#x2B07; {label}
        </a>'''
    except FileNotFoundError:
        return ""

# ============================================
# SESSION STATE
# ============================================
if 'cv_parsed' not in st.session_state:
    st.session_state.cv_parsed = False
    st.session_state.extracted_data = None
    st.session_state.cv_text = None
if 'mode' not in st.session_state:
    st.session_state.mode = 'cv'  # 'cv' ou 'form'

model = load_model()

# ============================================
# EN-TETE
# ============================================
st.markdown("""
<div style="padding:3rem 0 0.5rem; text-align:center;">
<div style="display:inline-block; background:#6d28d914; border:1px solid #6d28d930;
                border-radius:50px; padding:0.35rem 1.1rem; font-size:1.5rem;
                letter-spacing:0.16em; color:#a78bfa; font-family:'Syne',sans-serif;
                font-weight:700; text-transform:uppercase; margin-bottom:1.2rem;">
        Analyse de CV par Intelligence Artificielle
    </div>
<p style="color:#444460;font-size:0.95rem;font-weight:400;
               max-width:520px;margin:0 auto 0.4rem;line-height:1.6;">
        Analysez un CV en PDF ou saisissez manuellement les donnees &mdash;
        obtenez un score de stabilite genere par Random Forest
        et une analyse narrative par Llama 3.3.
    </p>
<div style="display:inline-flex;align-items:center;gap:0.5rem;
                background:#6d28d910;border:1px solid #6d28d930;
                border-radius:50px;padding:0.3rem 1.1rem;margin-bottom:1.4rem;">
        <div style="width:6px;height:6px;border-radius:50%;background:#a78bfa;"></div>
        <span style="font-family:'Syne',sans-serif;font-size:0.68rem;font-weight:700;
                      letter-spacing:0.18em;color:#a78bfa;text-transform:uppercase;">
            Deux modes d'analyse
        </span>
    </div>



</div>
""", unsafe_allow_html=True)

st.markdown("<div style='height:1.8rem'></div>", unsafe_allow_html=True)

# Separateur visuel
st.markdown("""
<div style="display:flex;align-items:center;gap:1rem;max-width:520px;margin:0 auto 1.6rem;">
    <div style="flex:1;height:1px;background:linear-gradient(90deg,transparent,#1a1a2e);"></div>
    <span style="font-family:'Syne',sans-serif;font-size:0.65rem;font-weight:700;
                  letter-spacing:0.2em;color:#25253a;text-transform:uppercase;">Choisissez un mode</span>
    <div style="flex:1;height:1px;background:linear-gradient(90deg,#1a1a2e,transparent);"></div>
</div>
""", unsafe_allow_html=True)

# ── Mode switcher ──
st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
col_tab_l, col_tab_c, col_tab_r = st.columns([1, 2, 1])
with col_tab_c:
    tab_col1, tab_col2 = st.columns(2)
    with tab_col1:
        cv_active = st.session_state.mode == 'cv'
        cv_style = f"background:{'#6d28d9' if cv_active else '#0e0e18'};border:1px solid {'#6d28d9' if cv_active else '#1a1a2e'};color:{'#fff' if cv_active else '#555570'};border-radius:10px;padding:0.6rem 1rem;text-align:center;font-family:'Syne',sans-serif;font-weight:700;font-size:0.85rem;cursor:pointer;"
        if st.button("Analyse CV (PDF)", use_container_width=True,
                     type="primary" if cv_active else "secondary"):
            st.session_state.mode = 'cv'
            st.session_state.cv_parsed = False
            st.session_state.extracted_data = None
            st.rerun()
    with tab_col2:
        form_active = st.session_state.mode == 'form'
        if st.button("Saisie Manuelle", use_container_width=True,
                     type="primary" if form_active else "secondary"):
            st.session_state.mode = 'form'
            st.rerun()

st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

if model is None:
    st.markdown("""
    <div style="background:#1c0505;border:1px solid #7f1d1d;border-radius:12px;
                padding:1.2rem;text-align:center;color:#fca5a5;margin:2rem 0;">
        Modele ML introuvable &mdash; verifiez <code>models/random_forest.pkl</code>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ============================================
# MODE CV — IMPORT ET ANALYSE
# ============================================
if st.session_state.mode == 'cv':
 if not st.session_state.cv_parsed:
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        uploaded_file = st.file_uploader(
            "Deposez votre CV (PDF)",
            type=['pdf'],
            label_visibility="collapsed",
            help="CV au format PDF — texte selectionnable de preference"
        )
        st.markdown("""
        <p style="text-align:center;color:#333350;font-size:0.78rem;margin-top:0.4rem;">
            Format PDF &nbsp;&middot;&nbsp; Texte selectionnable recommande
        </p>
        """, unsafe_allow_html=True)

        # Boutons CV exemples
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        st.markdown("""
        <p style="text-align:center;font-family:'Syne',sans-serif;font-size:0.68rem;
                   font-weight:700;letter-spacing:0.14em;color:#333350;text-transform:uppercase;
                   margin-bottom:0.6rem;">CV exemples pour tester</p>
        """, unsafe_allow_html=True)

        btn1 = get_pdf_download_button(
            "cv_exemple.pdf",
            "Karim — BTS / Marie",
            "cv_karim_mansouri.pdf",
            accent="#6d28d9"
        )
        btn2 = get_pdf_download_button(
            "cv_exemple_senior.pdf",
            "Ibrahim — Ingenieur Senior",
            "cv_ibrahim_benchekroun.pdf",
            accent="#4338ca"
        )

        st.markdown(f"""
        <div style="display:flex;justify-content:center;gap:0.8rem;flex-wrap:wrap;">
            {btn1}
            {btn2}
        </div>
        """, unsafe_allow_html=True)

    if uploaded_file is not None:
        extracted_data, cv_text = parse_cv(uploaded_file)
        if extracted_data:
            st.session_state.extracted_data = extracted_data
            st.session_state.cv_text = cv_text
            st.session_state.cv_parsed = True
            st.rerun()
        else:
            st.markdown("""
            <div style="background:#1c0505;border:1px solid #7f1d1d;border-radius:10px;
                        padding:1rem;text-align:center;color:#fca5a5;">
                Echec de l'analyse du CV
            </div>""", unsafe_allow_html=True)

    # Cards landing
    st.markdown("<div style='height:2.5rem'></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    for col, (num, title, desc) in zip(
        [c1, c2, c3],
        [("01", "Import PDF", "Depose le fichier PDF — texte ou scanne"),
         ("02", "Extraction IA", "Llama 3.3 70B extrait toutes les donnees cles"),
         ("03", "Score ML", "Random Forest predit le risque d'attrition")]
    ):
        with col:
            st.markdown(f"""
            <div style="background:#0e0e18;border:1px solid #1a1a2e;border-radius:14px;
                        padding:1.8rem 1.5rem;text-align:center;">
                <div style="font-family:'Syne',sans-serif;font-size:2rem;font-weight:800;
                             color:#6d28d9;margin-bottom:0.7rem;">{num}</div>
                <div style="font-family:'Syne',sans-serif;font-weight:700;font-size:0.9rem;
                             color:#e2e0da;margin-bottom:0.4rem;">{title}</div>
                <div style="color:#555570;font-size:0.8rem;line-height:1.5;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

# ============================================
# AFFICHAGE DES RÉSULTATS
# ============================================
 elif st.session_state.cv_parsed and st.session_state.extracted_data:
    data = st.session_state.extracted_data
    confidence = data.get('confidence_score', 0)
    conf_color = "#4ade80" if confidence >= 75 else "#facc15" if confidence >= 50 else "#f87171"

    # ── Carte candidat ──
    skills_badges = "".join([
        f"<span style='background:#1a1428;border:1px solid #6d28d940;color:#a78bfa;"
        f"padding:0.2rem 0.7rem;border-radius:20px;font-size:0.78rem;margin:0.15rem;"
        f"display:inline-block;'>{s}</span>"
        for s in data.get('top_skills', [])
    ])
    lang_badges = "".join([
        f"<span style='background:#0e1e14;border:1px solid #16a34a40;color:#4ade80;"
        f"padding:0.2rem 0.7rem;border-radius:20px;font-size:0.78rem;margin:0.15rem;"
        f"display:inline-block;'>{l}</span>"
        for l in data.get('languages', [])
    ])
    email_part = f"<span style='color:#555570;'>&#x2709;&nbsp;{data.get('email','')}</span>&nbsp;&nbsp;" if data.get('email') else ""
    phone_part = f"<span style='color:#555570;'>&#x260E;&nbsp;{data.get('phone','')}</span>" if data.get('phone') else ""

    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#0e0e18 0%,#130e1e 100%);
                border:1px solid #25153e;border-radius:18px;padding:2rem 2.5rem;
                margin-bottom:1.5rem;position:relative;overflow:hidden;">
        <div style="position:absolute;top:-40px;right:-40px;width:280px;height:280px;
                    background:radial-gradient(circle,#6d28d915,transparent 70%);pointer-events:none;"></div>
        <div style="display:flex;justify-content:space-between;align-items:flex-start;
                    flex-wrap:wrap;gap:1.5rem;position:relative;">
            <div style="flex:1;min-width:260px;">
                <h2 style="font-family:'Syne',sans-serif;font-size:1.9rem;font-weight:800;
                            color:#fff;margin:0 0 0.3rem;">{data.get('full_name','Candidat inconnu')}</h2>
                <p style="color:#a78bfa;font-size:1rem;font-weight:500;margin:0 0 0.4rem;">
                    {data.get('current_job_title','N/A')}
                    &nbsp;<span style='color:#333350;'>&#x7C;</span>&nbsp;
                    <span style='color:#555570;'>{data.get('last_company','N/A')}</span>
                </p>
                <p style="color:#555570;font-size:0.88rem;margin:0 0 1rem;">
                    &#x1F4CD;&nbsp;{data.get('location','N/A')}&nbsp;&nbsp;{email_part}{phone_part}
                </p>
                <div style="margin-bottom:0.6rem;">
                    <span style="font-size:0.7rem;font-weight:700;letter-spacing:0.1em;
                                  color:#444460;text-transform:uppercase;">Competences</span>
                    <div style="margin-top:0.3rem;">{skills_badges}</div>
                </div>
                <div>
                    <span style="font-size:0.7rem;font-weight:700;letter-spacing:0.1em;
                                  color:#444460;text-transform:uppercase;">Langues</span>
                    <div style="margin-top:0.3rem;">{lang_badges}</div>
                </div>
            </div>
            <div style="text-align:right;min-width:180px;">
                <div style="background:#07070d;border:1px solid #1a1a2e;border-radius:12px;
                             padding:1rem 1.5rem;display:inline-block;margin-bottom:0.6rem;">
                    <div style="font-family:'Syne',sans-serif;font-size:2.2rem;font-weight:800;
                                 color:{conf_color};line-height:1;">{confidence}%</div>
                    <div style="color:#444460;font-size:0.68rem;text-transform:uppercase;
                                 letter-spacing:0.1em;margin-top:0.2rem;">Confiance</div>
                </div>
                <p style="color:#333350;font-size:0.75rem;margin:0.3rem 0;">Llama 3.3 70B via Groq</p>
                <p style="color:#444460;font-size:0.8rem;margin:0;">{data.get('education_detail','N/A')}</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Label section ──
    st.markdown("""
    <p style="font-family:'Syne',sans-serif;font-size:0.68rem;font-weight:700;
               letter-spacing:0.15em;color:#333350;text-transform:uppercase;margin-bottom:0.8rem;">
        Donnees extraites pour le modele ML
    </p>
    """, unsafe_allow_html=True)

    # ── 8 metric tiles ──
    edu_map = {1: "Sans diplome", 2: "Bac", 3: "Bac+2", 4: "Bac+3/4", 5: "Bac+5+"}
    marital_map = {0: "Celibataire", 1: "Marie(e)", 2: "Divorce(e)"}
    travel_map = {0: "Aucun", 1: "Rare", 2: "Frequent"}

    tiles = [
        ("Age", f"{data['Age']} ans"),
        ("Genre", "Homme" if data['Gender'] == 1 else "Femme"),
        ("Situation", marital_map[data['MaritalStatus']]),
        ("Formation", edu_map[data['Education']]),
        ("Experience", f"{data['TotalWorkingYears']} ans"),
        ("Formations/an", str(data['TrainingTimesLastYear'])),
        ("Distance", f"{data['DistanceFromHome']} km"),
        ("Deplacements", travel_map[data['BusinessTravel']]),
    ]
    cols8 = st.columns(8)
    for col, (label, value) in zip(cols8, tiles):
        with col:
            st.markdown(f"""
            <div style="background:#0e0e18;border:1px solid #1a1a2e;border-radius:10px;
                         padding:0.9rem 0.5rem;text-align:center;margin-bottom:1rem;">
                <div style="font-family:'Syne',sans-serif;font-size:0.95rem;font-weight:700;
                             color:#e2e0da;margin-bottom:0.25rem;">{value}</div>
                <div style="color:#444460;font-size:0.65rem;text-transform:uppercase;
                             letter-spacing:0.07em;">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    # ── Correction manuelle (logique identique) ──
    with st.expander("Modifier les donnees extraites si necessaire"):
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            data['Age'] = st.number_input("Age", min_value=18, max_value=65, value=data['Age'])
            gender_e = st.radio("Genre", ["Homme", "Femme"], index=0 if data['Gender'] == 1 else 1, horizontal=True)
            data['Gender'] = 1 if gender_e == "Homme" else 0
            marital_e = st.selectbox("Situation Familiale", ["Celibataire", "Marie(e)", "Divorce(e)"], index=data['MaritalStatus'])
            data['MaritalStatus'] = {"Celibataire": 0, "Marie(e)": 1, "Divorce(e)": 2}[marital_e]
        with col_e2:
            edu_e = st.selectbox("Niveau d'Etudes", ["Sans diplome/Brevet", "Baccalaureat", "Bac+2 (BTS/DUT)", "Bac+3/4 (Licence/M1)", "Bac+5+ (Master/Ingenieur)"], index=data['Education'] - 1)
            data['Education'] = {"Sans diplome/Brevet": 1, "Baccalaureat": 2, "Bac+2 (BTS/DUT)": 3, "Bac+3/4 (Licence/M1)": 4, "Bac+5+ (Master/Ingenieur)": 5}[edu_e]
            data['TotalWorkingYears'] = st.number_input("Annees d'experience", min_value=0, max_value=50, value=data['TotalWorkingYears'])
            data['TrainingTimesLastYear'] = st.slider("Formations (an dernier)", min_value=0, max_value=6, value=data['TrainingTimesLastYear'])
        col_e3, col_e4 = st.columns(2)
        with col_e3:
            data['DistanceFromHome'] = st.slider("Distance domicile-travail (km)", min_value=1, max_value=50, value=data['DistanceFromHome'])
        with col_e4:
            travel_e = st.selectbox("Deplacements pro", ["Pas de deplacements", "Deplacements rares", "Deplacements frequents"], index=data['BusinessTravel'])
            data['BusinessTravel'] = {"Pas de deplacements": 0, "Deplacements rares": 1, "Deplacements frequents": 2}[travel_e]

    # ── Bouton prediction (logique identique) ──
    st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        predict_button = st.button("Analyser le candidat", type="primary", use_container_width=True)

    # ============================================
    # RÉSULTATS ML (logique identique)
    # ============================================
    if predict_button:
        input_data = prepare_input_data(data)
        prediction = model.predict(input_data)[0]
        probability = model.predict_proba(input_data)[0]
        attrition_prob = probability[1]
        recruitment_score = calculate_recruitment_score(attrition_prob)
        advice = get_recruitment_advice(recruitment_score)

        st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

        # ── Score banner ──
        st.markdown(f"""
        <div style="background:{advice['bg']};border:1px solid {advice['accent']}30;
                     border-radius:18px;padding:2.5rem;text-align:center;
                     position:relative;overflow:hidden;margin-bottom:1.5rem;">
            <div style="position:absolute;inset:0;background:radial-gradient(circle at 50% 0%,
                         {advice['accent']}10,transparent 70%);pointer-events:none;"></div>
            <div style="position:relative;">
                <p style="font-family:'Syne',sans-serif;font-size:0.68rem;font-weight:700;
                            letter-spacing:0.2em;color:{advice['accent']}80;
                            text-transform:uppercase;margin-bottom:0.8rem;">Decision de recrutement</p>
                <div style="font-family:'Syne',sans-serif;font-size:5rem;font-weight:800;
                             color:{advice['accent']};line-height:1;margin-bottom:0.4rem;">
                    {recruitment_score:.0f}<span style="font-size:2.2rem;">%</span>
                </div>
                <div style="font-family:'Syne',sans-serif;font-size:1.2rem;font-weight:700;
                             color:{advice['accent']};letter-spacing:0.08em;margin-bottom:0.5rem;">
                    {advice['decision']}
                </div>
                <p style="color:#666680;font-size:0.88rem;">{advice['advice']}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Jauge + analyse ──
        col_g, col_a = st.columns([1, 1])

        with col_g:
            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=recruitment_score,
                number={'suffix': '%', 'font': {'size': 32, 'color': advice['accent'], 'family': 'Syne'}},
                delta={'reference': 50, 'increasing': {'color': advice['accent']}},
                gauge={
                    'axis': {'range': [None, 100], 'tickcolor': '#333350',
                              'tickwidth': 1, 'tickfont': {'color': '#444460', 'size': 10}},
                    'bar': {'color': advice['color'], 'thickness': 0.25},
                    'bgcolor': '#0e0e18',
                    'borderwidth': 0,
                    'steps': [
                        {'range': [0, 40], 'color': '#1c0505'},
                        {'range': [40, 60], 'color': '#1c1405'},
                        {'range': [60, 80], 'color': '#052e16'},
                        {'range': [80, 100], 'color': '#042318'},
                    ],
                    'threshold': {
                        'line': {'color': advice['accent'], 'width': 2},
                        'thickness': 0.75, 'value': recruitment_score
                    }
                }
            ))
            fig.update_layout(
                height=280,
                margin=dict(l=20, r=20, t=30, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font={'color': '#8888aa', 'family': 'DM Sans'}
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        with col_a:
            strengths = []
            if data['Age'] <= 35: strengths.append("Profil junior avec fort potentiel d'evolution")
            if data['TotalWorkingYears'] >= 5: strengths.append("Experience professionnelle solide")
            if data['Education'] >= 4: strengths.append("Niveau d'etudes superieur")
            if data['DistanceFromHome'] <= 15: strengths.append("Proximite geographique favorable")
            if data['TrainingTimesLastYear'] >= 3: strengths.append("Investissement fort en formation continue")

            concerns = []
            if data['Age'] > 50: concerns.append("Profil senior — verifier alignement salarial")
            if data['DistanceFromHome'] > 30: concerns.append("Distance importante — risque de turn-over")
            if data['TrainingTimesLastYear'] == 0: concerns.append("Pas de formation recente")
            if data['TotalWorkingYears'] < 2: concerns.append("Experience limitee")

            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

            if strengths:
                st.markdown("""<p style="font-size:0.68rem;font-weight:700;letter-spacing:0.12em;
                    color:#4ade8080;text-transform:uppercase;margin-bottom:0.5rem;
                    font-family:'Syne',sans-serif;">Points forts</p>""", unsafe_allow_html=True)
                for s in strengths:
                    st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.4rem;">
                        <div style="width:5px;height:5px;border-radius:50%;background:#4ade80;flex-shrink:0;"></div>
                        <span style="color:#8888aa;font-size:0.85rem;">{s}</span>
                    </div>""", unsafe_allow_html=True)

            if concerns:
                st.markdown("""<p style="font-size:0.68rem;font-weight:700;letter-spacing:0.12em;
                    color:#fb923c80;text-transform:uppercase;margin-bottom:0.5rem;margin-top:1rem;
                    font-family:'Syne',sans-serif;">Points d'attention</p>""", unsafe_allow_html=True)
                for c in concerns:
                    st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.4rem;">
                        <div style="width:5px;height:5px;border-radius:50%;background:#fb923c;flex-shrink:0;"></div>
                        <span style="color:#8888aa;font-size:0.85rem;">{c}</span>
                    </div>""", unsafe_allow_html=True)

            if not strengths and not concerns:
                st.markdown("<p style='color:#444460;font-size:0.85rem;'>Profil equilibre</p>", unsafe_allow_html=True)

        # ── Recommandation finale ──
        st.markdown(f"""
        <div style="background:{advice['bg']};border:1px solid {advice['accent']}25;
                     border-radius:12px;padding:1.2rem 2rem;margin-top:0.5rem;
                     display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:1rem;">
            <div>
                <p style="font-size:0.68rem;font-weight:700;letter-spacing:0.12em;
                            color:{advice['accent']}70;text-transform:uppercase;
                            font-family:'Syne',sans-serif;margin:0 0 0.2rem;">Recommandation finale</p>
                <p style="font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:700;
                            color:{advice['accent']};margin:0;">{advice['decision']}</p>
            </div>
            <div style="background:{advice['accent']}18;border-radius:50%;width:46px;height:46px;
                         display:flex;align-items:center;justify-content:center;
                         font-family:'Syne',sans-serif;font-size:1.3rem;font-weight:800;
                         color:{advice['accent']};">{advice['grade']}</div>
        </div>
        """, unsafe_allow_html=True)

        # ── Justification IA ──
        st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
        st.markdown("""
        <p style="font-family:'Syne',sans-serif;font-size:0.68rem;font-weight:700;
                   letter-spacing:0.15em;color:#333350;text-transform:uppercase;margin-bottom:0.8rem;">
            Analyse detaillee par l'IA
        </p>
        """, unsafe_allow_html=True)

        with st.spinner("Redaction de l'analyse RH..."):
            justification = generate_ai_justification(data, recruitment_score, advice["decision"])

        if justification:
            st.markdown(f"""
            <div style="background:#0e0e18;border:1px solid #1a1a2e;border-radius:14px;
                         padding:1.8rem 2rem;position:relative;overflow:hidden;">
                <div style="position:absolute;top:0;left:0;width:4px;height:100%;
                             background:linear-gradient(180deg,{advice['accent']},{advice['accent']}40);
                             border-radius:4px 0 0 4px;"></div>
                <div style="padding-left:0.5rem;">
                    <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:1rem;">
                        <div style="background:{advice['accent']}18;border:1px solid {advice['accent']}30;
                                     border-radius:8px;padding:0.3rem 0.8rem;">
                            <span style="font-family:'Syne',sans-serif;font-size:0.72rem;font-weight:700;
                                          color:{advice['accent']};letter-spacing:0.08em;">
                                Llama 3.3 70B — Analyse RH
                            </span>
                        </div>
                        <span style="color:#333350;font-size:0.75rem;">
                            Score {recruitment_score:.0f}% &middot; {advice['decision']}
                        </span>
                    </div>
                    <p style="color:#a0a0c0;font-size:0.92rem;line-height:1.75;margin:0;">
                        {justification}
                    </p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background:#0e0e18;border:1px solid #1a1a2e;border-radius:14px;
                         padding:1.5rem 2rem;color:#444460;font-size:0.85rem;text-align:center;">
                Analyse IA indisponible — verifiez la cle API dans la sidebar
            </div>
            """, unsafe_allow_html=True)

# ============================================
# MODE FORMULAIRE — SAISIE MANUELLE
# ============================================
elif st.session_state.mode == 'form':

    st.markdown("""
    <p style="font-family:'Syne',sans-serif;font-size:0.68rem;font-weight:700;
               letter-spacing:0.15em;color:#333350;text-transform:uppercase;margin-bottom:1rem;">
        Informations du candidat
    </p>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""<p style="font-size:0.75rem;font-weight:700;letter-spacing:0.1em;
            color:#6d28d9;text-transform:uppercase;margin-bottom:0.5rem;font-family:'Syne',sans-serif;">
            Profil personnel</p>""", unsafe_allow_html=True)
        f_age = st.number_input("Age", min_value=18, max_value=65, value=25, step=1)
        f_gender = st.radio("Genre", ["Homme", "Femme"], horizontal=True)
        f_gender_code = 1 if f_gender == "Homme" else 0
        f_marital = st.selectbox("Situation familiale",
            ["Marie(e)","Celibataire",  "Divorce(e)"])
        f_marital_code = {"Celibataire": 0, "Marie(e)": 1, "Divorce(e)": 2}[f_marital]

    with col2:
        st.markdown("""<p style="font-size:0.75rem;font-weight:700;letter-spacing:0.1em;
            color:#6d28d9;text-transform:uppercase;margin-bottom:0.5rem;font-family:'Syne',sans-serif;">
            Formation & experience</p>""", unsafe_allow_html=True)
        f_edu = st.selectbox("Niveau d'etudes", [
            "Bac+2 (BTS/DUT)", "Sans diplome/Brevet", "Baccalaureat",
             "Bac+3/4 (Licence/M1)", "Bac+5+ (Master/Ingenieur)"])
        f_edu_code = {
            "Sans diplome/Brevet": 1, "Baccalaureat": 2,
            "Bac+2 (BTS/DUT)": 3, "Bac+3/4 (Licence/M1)": 4,
            "Bac+5+ (Master/Ingenieur)": 5
        }[f_edu]
        f_exp = st.number_input("Annees d'experience", min_value=0, max_value=50, value=5)
        f_training = st.slider("Formations (annee derniere)", min_value=0, max_value=6, value=2)

    col3, col4 = st.columns(2)
    with col3:
        st.markdown("""<p style="font-size:0.75rem;font-weight:700;letter-spacing:0.1em;
            color:#6d28d9;text-transform:uppercase;margin-bottom:0.5rem;font-family:'Syne',sans-serif;">
            Situation geographique</p>""", unsafe_allow_html=True)
        f_distance = st.slider("Distance domicile-travail (km)", min_value=1, max_value=50, value=6)
    with col4:
        st.markdown("""<p style="font-size:0.75rem;font-weight:700;letter-spacing:0.1em;
            color:#6d28d9;text-transform:uppercase;margin-bottom:0.5rem;font-family:'Syne',sans-serif;">
            Disponibilite</p>""", unsafe_allow_html=True)
        f_travel = st.selectbox("Deplacements professionnels",
            ["Deplacements rares","Pas de deplacements",  "Deplacements frequents"])
        f_travel_code = {"Pas de deplacements": 0, "Deplacements rares": 1, "Deplacements frequents": 2}[f_travel]

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    col_b1, col_b2, col_b3 = st.columns([1, 2, 1])
    with col_b2:
        form_predict = st.button("Analyser le candidat", type="primary", use_container_width=True)

    if form_predict:
        f_input = prepare_input_data({
            'Age': f_age, 'BusinessTravel': f_travel_code,
            'DistanceFromHome': f_distance, 'Education': f_edu_code,
            'Gender': f_gender_code, 'MaritalStatus': f_marital_code,
            'TotalWorkingYears': f_exp, 'TrainingTimesLastYear': f_training
        })
        f_prob = model.predict_proba(f_input)[0]
        f_score = calculate_recruitment_score(f_prob[1])
        f_advice = get_recruitment_advice(f_score)

        st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

        # Score banner
        st.markdown(f"""
        <div style="background:{f_advice['bg']};border:1px solid {f_advice['accent']}30;
                     border-radius:18px;padding:2.5rem;text-align:center;
                     position:relative;overflow:hidden;margin-bottom:1.5rem;">
            <div style="position:absolute;inset:0;background:radial-gradient(circle at 50% 0%,
                         {f_advice['accent']}10,transparent 70%);pointer-events:none;"></div>
            <div style="position:relative;">
                <p style="font-family:'Syne',sans-serif;font-size:0.68rem;font-weight:700;
                            letter-spacing:0.2em;color:{f_advice['accent']}80;
                            text-transform:uppercase;margin-bottom:0.8rem;">Decision de recrutement</p>
                <div style="font-family:'Syne',sans-serif;font-size:5rem;font-weight:800;
                             color:{f_advice['accent']};line-height:1;margin-bottom:0.4rem;">
                    {f_score:.0f}<span style="font-size:2.2rem;">%</span>
                </div>
                <div style="font-family:'Syne',sans-serif;font-size:1.2rem;font-weight:700;
                             color:{f_advice['accent']};letter-spacing:0.08em;margin-bottom:0.5rem;">
                    {f_advice['decision']}
                </div>
                <p style="color:#666680;font-size:0.88rem;">{f_advice['advice']}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Jauge + insights
        col_g, col_a = st.columns([1, 1])
        with col_g:
            fig2 = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=f_score,
                number={'suffix': '%', 'font': {'size': 32, 'color': f_advice['accent'], 'family': 'Syne'}},
                delta={'reference': 50, 'increasing': {'color': f_advice['accent']}},
                gauge={
                    'axis': {'range': [None, 100], 'tickcolor': '#333350',
                              'tickwidth': 1, 'tickfont': {'color': '#444460', 'size': 10}},
                    'bar': {'color': f_advice['color'], 'thickness': 0.25},
                    'bgcolor': '#0e0e18', 'borderwidth': 0,
                    'steps': [
                        {'range': [0, 40], 'color': '#1c0505'},
                        {'range': [40, 60], 'color': '#1c1405'},
                        {'range': [60, 80], 'color': '#052e16'},
                        {'range': [80, 100], 'color': '#042318'},
                    ],
                    'threshold': {'line': {'color': f_advice['accent'], 'width': 2},
                                  'thickness': 0.75, 'value': f_score}
                }
            ))
            fig2.update_layout(height=280, margin=dict(l=20, r=20, t=30, b=10),
                               paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                               font={'color': '#8888aa', 'family': 'DM Sans'})
            st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})

        with col_a:
            f_strengths, f_concerns = [], []
            if f_age <= 35: f_strengths.append("Profil junior avec fort potentiel d'evolution")
            if f_exp >= 5:  f_strengths.append("Experience professionnelle solide")
            if f_edu_code >= 4: f_strengths.append("Niveau d'etudes superieur")
            if f_distance <= 15: f_strengths.append("Proximite geographique favorable")
            if f_training >= 3: f_strengths.append("Investissement fort en formation continue")
            if f_age > 50:  f_concerns.append("Profil senior — verifier alignement salarial")
            if f_distance > 30: f_concerns.append("Distance importante — risque de turn-over")
            if f_training == 0: f_concerns.append("Pas de formation recente")
            if f_exp < 2:   f_concerns.append("Experience limitee")

            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
            if f_strengths:
                st.markdown("""<p style="font-size:0.68rem;font-weight:700;letter-spacing:0.12em;
                    color:#4ade8080;text-transform:uppercase;margin-bottom:0.5rem;
                    font-family:'Syne',sans-serif;">Points forts</p>""", unsafe_allow_html=True)
                for s in f_strengths:
                    st.markdown(f"""<div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.4rem;">
                        <div style="width:5px;height:5px;border-radius:50%;background:#4ade80;flex-shrink:0;"></div>
                        <span style="color:#8888aa;font-size:0.85rem;">{s}</span></div>""", unsafe_allow_html=True)
            if f_concerns:
                st.markdown("""<p style="font-size:0.68rem;font-weight:700;letter-spacing:0.12em;
                    color:#fb923c80;text-transform:uppercase;margin-bottom:0.5rem;margin-top:1rem;
                    font-family:'Syne',sans-serif;">Points d'attention</p>""", unsafe_allow_html=True)
                for c in f_concerns:
                    st.markdown(f"""<div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.4rem;">
                        <div style="width:5px;height:5px;border-radius:50%;background:#fb923c;flex-shrink:0;"></div>
                        <span style="color:#8888aa;font-size:0.85rem;">{c}</span></div>""", unsafe_allow_html=True)

        # Recommandation finale
        st.markdown(f"""
        <div style="background:{f_advice['bg']};border:1px solid {f_advice['accent']}25;
                     border-radius:12px;padding:1.2rem 2rem;margin-top:0.5rem;
                     display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:1rem;">
            <div>
                <p style="font-size:0.68rem;font-weight:700;letter-spacing:0.12em;
                            color:{f_advice['accent']}70;text-transform:uppercase;
                            font-family:'Syne',sans-serif;margin:0 0 0.2rem;">Recommandation finale</p>
                <p style="font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:700;
                            color:{f_advice['accent']};margin:0;">{f_advice['decision']}</p>
            </div>
            <div style="background:{f_advice['accent']}18;border-radius:50%;width:46px;height:46px;
                         display:flex;align-items:center;justify-content:center;
                         font-family:'Syne',sans-serif;font-size:1.3rem;font-weight:800;
                         color:{f_advice['accent']};">{f_advice['grade']}</div>
        </div>
        """, unsafe_allow_html=True)

        # Analyse IA
        st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
        st.markdown("""
        <p style="font-family:'Syne',sans-serif;font-size:0.68rem;font-weight:700;
                   letter-spacing:0.15em;color:#333350;text-transform:uppercase;margin-bottom:0.8rem;">
            Analyse detaillee par l'IA
        </p>
        """, unsafe_allow_html=True)

        form_data_for_ai = {
            'Age': f_age, 'Gender': f_gender_code, 'MaritalStatus': f_marital_code,
            'Education': f_edu_code, 'TotalWorkingYears': f_exp,
            'DistanceFromHome': f_distance, 'BusinessTravel': f_travel_code,
            'TrainingTimesLastYear': f_training,
            'full_name': 'Candidat', 'current_job_title': '',
            'education_detail': f_edu, 'top_skills': [], 'languages': []
        }
        with st.spinner("Redaction de l'analyse RH..."):
            f_justification = generate_ai_justification(form_data_for_ai, f_score, f_advice["decision"])

        if f_justification:
            st.markdown(f"""
            <div style="background:#0e0e18;border:1px solid #1a1a2e;border-radius:14px;
                         padding:1.8rem 2rem;position:relative;overflow:hidden;">
                <div style="position:absolute;top:0;left:0;width:4px;height:100%;
                             background:linear-gradient(180deg,{f_advice['accent']},{f_advice['accent']}40);
                             border-radius:4px 0 0 4px;"></div>
                <div style="padding-left:0.5rem;">
                    <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:1rem;">
                        <div style="background:{f_advice['accent']}18;border:1px solid {f_advice['accent']}30;
                                     border-radius:8px;padding:0.3rem 0.8rem;">
                            <span style="font-family:'Syne',sans-serif;font-size:0.72rem;font-weight:700;
                                          color:{f_advice['accent']};letter-spacing:0.08em;">
                                Llama 3.3 70B — Analyse RH
                            </span>
                        </div>
                        <span style="color:#333350;font-size:0.75rem;">
                            Score {f_score:.0f}% &middot; {f_advice['decision']}
                        </span>
                    </div>
                    <p style="color:#a0a0c0;font-size:0.92rem;line-height:1.75;margin:0;">
                        {f_justification}
                    </p>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ── Footer ──
st.markdown("<div style='height:3rem'></div>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center;color:#2a2a40;padding:1rem;font-size:0.78rem;border-top:1px solid #1a1a2e;">
    Extraction par Llama 3.3 70B (Groq) &nbsp;&middot;&nbsp; Prediction par Random Forest
</div>
""", unsafe_allow_html=True)