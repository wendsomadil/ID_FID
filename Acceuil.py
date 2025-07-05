# acceuil.py

import os
import sys
import time
import base64
import tempfile
import streamlit as st
from gtts import gTTS
from chatbot.rag_pipeline import get_answer, search_faiss
from chatbot.utils import load_text_data, init_session
from chatbot.memory import ChatMemory
from streamlit_option_menu import option_menu
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
            st.markdown(f"<style data-theme='light'>{css}</style>", unsafe_allow_html=True)
    else:
        st.error(f"Fichier CSS introuvable : {path}")

css_path = os.path.join(PROJECT_ROOT, 'css', 'styles.css')
load_css(css_path)

# Session state init
texts = load_text_data()
st.session_state.setdefault("chat_memory", ChatMemory())
st.session_state.setdefault("theme", "light")
st.session_state.setdefault("lang", "fr")

# Utilitaires
def encode_image_to_base64(image_path: str) -> str:
    if os.path.exists(image_path):
        with open(image_path, "rb") as img:
            return base64.b64encode(img.read()).decode()
    return None

def lire_texte_audio(text: str):
    lang_code = 'fr' if st.session_state.lang == "fr" else 'en'
    tts = gTTS(text=text, lang=lang_code)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        tts.save(tmp.name)
        st.audio(open(tmp.name, "rb").read(), format="audio/mpeg")

# Images
assets_path = os.path.join(os.path.dirname(__file__), "assets")
ia_logo      = encode_image_to_base64(os.path.join(assets_path, "ia_telecom.png"))
citadel_logo = encode_image_to_base64(os.path.join(assets_path, "citadel.png"))
hero_img     = encode_image_to_base64(os.path.join(assets_path, "telecom_hero.jpg"))
feature1_img = encode_image_to_base64(os.path.join(assets_path, "telecommunication.png"))
feature2_img = encode_image_to_base64(os.path.join(assets_path, "ai-assistant.png"))
feature3_img = encode_image_to_base64(os.path.join(assets_path, "translation.png"))

# Texte selon langue
def load_texts_and_features():
    if st.session_state.lang == "fr":
        return (
            "Assistance IA Télécom 📱",
            "Votre assistant intelligent pour la réglementation des télécommunications au Burkina Faso",
            "Tapez votre message ici...",
            "Envoyer",
            "🪩 Effacer la conversation",
            [
                {"title": "Réglementation Complète", "description": "Accès instantané à toute la réglementation des télécommunications", "image": feature1_img},
                {"title": "Assistant Intelligent",   "description": "Réponses précises basées sur l'IA",                             "image": feature2_img},
                {"title": "Multilingue",            "description": "Disponible en français et en anglais",                     "image": feature3_img},
            ]
        )
    else:
        return (
            "Telecom AI Assistance 📱",
            "Your smart assistant for telecommunications regulation in Burkina Faso",
            "Type your message here...",
            "Send",
            "🪩 Clear conversation",
            [
                {"title": "Comprehensive Regulation", "description": "Instant access to all telecom regulations", "image": feature1_img},
                {"title": "Smart Assistant",           "description": "Accurate AI-based answers",                "image": feature2_img},
                {"title": "Multilingual",              "description": "French & English support",                "image": feature3_img},
            ]
        )

# Chargement
title, subtitle, placeholder, submit_txt, clear_txt, features = load_texts_and_features()

# En-tête
st.markdown(f"""
<div class="header">
  <h1>{title}</h1>
  <p>{subtitle}</p>
</div>
""", unsafe_allow_html=True)

# Formulaire de chat
st.markdown("### 💬 Chat")
with st.form("chat_form", clear_on_submit=True):
    col1, col2 = st.columns([5, 1])
    with col1:
        query = st.text_input("", placeholder=placeholder, label_visibility="collapsed")
    with col2:
        submitted = st.form_submit_button(submit_txt)
        if st.form_submit_button(clear_txt):
            st.session_state.chat_memory.clear_memory()
            st.rerun()

# Historique de chat
chat_container = st.container()
with chat_container:
    st.markdown('<div class="chat-history">', unsafe_allow_html=True)
    for idx, msg in enumerate(st.session_state.chat_memory.history):
        st.markdown(f"""
          <div class='chat-container'>
            <div class='bubble user'>{msg['user']}</div>
            <img class='avatar' src='https://i.imgur.com/IX8FzVb.png' />
          </div>
          <div class='chat-container'>
            <img class='avatar' src='https://i.imgur.com/tfMZ5cD.png' />
            <div class='bubble bot'>{msg['bot']}</div>
          </div>
        """, unsafe_allow_html=True)
        if st.button(f"🎧 Écouter réponse {idx+1}", key=f"tts_{idx}"):
            lire_texte_audio(msg['bot'])
    st.markdown('</div>', unsafe_allow_html=True)

# Traitement de la requête
if submitted and query:
    if len(query.split()) >= 3:
        spinner = "💡 L'assistant réfléchit..." if st.session_state.lang == "fr" else "💡 Assistant thinking..."
        with st.spinner(spinner):
            results = search_faiss(query, top_n=5)
            context = "\n".join([d for d, _ in results] + st.session_state.chat_memory.get_context())
            answer = get_answer(query, context)
            st.session_state.chat_memory.add_to_memory(query, answer)

            placeholder = chat_container.empty()
            txt = ""
            for c in answer:
                txt += c
                placeholder.markdown(f"""
                  <div class='chat-container'>
                    <img class='avatar' src='https://i.imgur.com/tfMZ5cD.png' />
                    <div class='bubble bot'>{txt}</div>
                  </div>
                """, unsafe_allow_html=True)
                time.sleep(0.01)
        st.rerun()
    else:
        warn = "Veuillez entrer une question à 3 mots minimum." if st.session_state.lang == "fr" else "Enter at least 3 words."
        st.warning(warn)

# Fonctionnalités
st.markdown("### ✨ Fonctionnalités")
cols = st.columns(3)
for i, feat in enumerate(features):
    with cols[i]:
        st.markdown(f"""
        <div class="feature-card">
          <img src="data:image/png;base64,{feat['image']}" />
          <h3>{feat['title']}</h3>
          <p>{feat['description']}</p>
        </div>
        """, unsafe_allow_html=True)

# Appliquer thème light explicitement
st.markdown("<body data-theme='light'>", unsafe_allow_html=True)
