# acceuil.py

import os
import sys
import time
import base64
import tempfile
import streamlit as st
import pandas as pd
import plotly.express as px
from gtts import gTTS

# Modules internes
from chatbot.rag_pipeline import get_answer, search_faiss
from chatbot.utils import load_text_data, init_session
from chatbot.memory import ChatMemory
from chatbot.config import ASSETS_DIRECTORY, PROJECT_ROOT

# Initialisation
init_session()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'chatbot')))

# Configuration Streamlit
st.set_page_config(
    page_title="Assistance IA Télécom",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Charger CSS
def load_css(path: str):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            css = f.read()
            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    else:
        st.error(f"Fichier CSS introuvable : {path}")

css_path = os.path.join(PROJECT_ROOT, 'css', 'Styles_modified.css')
load_css(css_path)

# Session state init
texts = load_text_data()
st.session_state.setdefault("chat_memory", ChatMemory())
st.session_state.setdefault("lang", "fr")

# Synthèse vocale
def lire_texte_audio(text: str):
    lang_code = 'fr' if st.session_state.lang == "fr" else 'en'
    tts = gTTS(text=text, lang=lang_code)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        tts.save(tmp.name)
        st.audio(open(tmp.name, "rb").read(), format="audio/mpeg")

# Sidebar : langue et fichier
st.sidebar.title("Paramètres")
st.session_state.lang = st.sidebar.radio("Langue", ["fr", "en"])
uploaded_file = st.sidebar.file_uploader("📎 Envoyer un fichier texte", type=["txt"])

# Texte selon langue
def load_texts_and_features():
    if st.session_state.lang == "fr":
        return (
            "Assistance IA Télécom 📱",
            "Votre assistant intelligent pour la réglementation des télécommunications au Burkina Faso",
            "Tapez votre message ici...",
            "Envoyer",
            "🪩 Effacer la conversation"
        )
    else:
        return (
            "Telecom AI Assistance 📱",
            "Your smart assistant for telecommunications regulation in Burkina Faso",
            "Type your message here...",
            "Send",
            "🪩 Clear conversation"
        )

title, subtitle, placeholder, submit_txt, clear_txt = load_texts_and_features()

# En-tête
st.markdown(f"""
<div class="header">
  <h1>{title}</h1>
  <p>{subtitle}</p>
</div>
""", unsafe_allow_html=True)

# Historique de chat
chat_container = st.container()
with chat_container:
    st.markdown('<div class="chat-history">', unsafe_allow_html=True)
    for idx, msg in enumerate(st.session_state.chat_memory.history):
        st.markdown(f"""
          <div class='chat-container'>
            <div class='bubble user'>{msg['user']}</div>
          </div>
          <div class='chat-container'>
            <div class='bubble bot'>{msg['bot']}</div>
          </div>
        """, unsafe_allow_html=True)
        if st.button(f"🎧 Écouter réponse {idx+1}", key=f"tts_{idx}"):
            lire_texte_audio(msg['bot'])
    st.markdown('</div>', unsafe_allow_html=True)

# Zone de saisie en bas
with st.container():
    st.markdown("<div class='input-area'>", unsafe_allow_html=True)
    col1, col2 = st.columns([8, 1])
    with col1:
        query = st.text_input("", placeholder=placeholder, label_visibility="collapsed")
    with col2:
        submitted = st.button(submit_txt)
    st.markdown("</div>", unsafe_allow_html=True)

# Traitement de la requête
if submitted and query:
    if len(query.split()) >= 3:
        with st.spinner("💡 L'assistant réfléchit..."):
            results = search_faiss(query, top_n=5)
            context = "\n".join([d for d, _ in results] + st.session_state.chat_memory.get_context())
            answer = get_answer(query, context)
            st.session_state.chat_memory.add_to_memory(query, answer)
            lire_texte_audio(answer)
        st.rerun()
    else:
        warn = "Veuillez entrer une question à 3 mots minimum." if st.session_state.lang == "fr" else "Enter at least 3 words."
        st.warning(warn)

# Analyse de fichier texte
if uploaded_file:
    content = uploaded_file.read().decode("utf-8")
    word_count = len(content.split())
    st.success(f"📄 Le fichier contient {word_count} mots.")

# Graphique interactif
st.markdown("### 📊 Statistiques des sujets")
data = pd.DataFrame({
    "Sujet": ["5G", "Fibre", "Roaming", "Facturation", "Support"],
    "Questions": [12, 9, 7, 5, 3]
})
fig = px.bar(data, x="Sujet", y="Questions", title="Sujets les plus demandés")
st.plotly_chart(fig)

