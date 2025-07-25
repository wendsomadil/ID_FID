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
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import streamlit.components.v1 as components

# Modules internes
from chatbot.rag_pipeline import get_answer, search_faiss
from chatbot.utils import load_text_data, init_session
from chatbot.memory import ChatMemory
from chatbot.config import PROJECT_ROOT
from db import insert_message, get_all_messages

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

css_path = os.path.join(PROJECT_ROOT, 'css', 'styles.css')
load_css(css_path)

# Encodage des images
def encode_image_to_base64(image_path: str) -> str:
    if os.path.exists(image_path):
        with open(image_path, "rb") as img:
            return base64.b64encode(img.read()).decode()
    return ""

assets_path = os.path.join(os.path.dirname(__file__), "assets")
feature1_img = encode_image_to_base64(os.path.join(assets_path, "telecom.png"))
feature2_img = encode_image_to_base64(os.path.join(assets_path, "ai-assistant.png"))
feature3_img = encode_image_to_base64(os.path.join(assets_path, "translation.png"))

features = [
    {"title": "Réglementation", "description": "Un accès instantané", "image": feature1_img},
    {"title": "Assistant Intelligent", "description": "Réponses précises basées sur l'IA", "image": feature2_img},
    {"title": "Multilingue", "description": "Disponible en français et en anglais", "image": feature3_img},
]

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
def load_texts():
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

title, subtitle, placeholder, submit_txt, clear_txt = load_texts()

# Après chaque réponse :
insert_message(query, answer)

# Pour afficher l’historique depuis la base :
for user, bot, ts in get_all_messages():
    st.markdown(f"**👤 {user}**  \n**🤖 {bot}**  \n*🕒 {ts}*")

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
            <div class='bubble bot'>{msg['bot']}
              <button onclick="navigator.clipboard.writeText('{msg['bot']}')" style="margin-left:10px;">📋</button>
            </div>
          </div>
        """, unsafe_allow_html=True)
        if st.button(f"🎧 Écouter réponse {idx+1}", key=f"tts_{idx}"):
            lire_texte_audio(msg['bot'])
    st.markdown('</div>', unsafe_allow_html=True)

# Zone de saisie en bas
components.html(f"""
<style>
  .chat-input-container {{
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 1rem;
    background-color: var(--card-bg);
    border-radius: 16px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    max-width: 100%;
    margin-top: 1rem;
    font-family: 'Segoe UI', sans-serif;
  }}

  .chat-input-container img {{
    width: 40px;
    height: 40px;
    border-radius: 50%;
    object-fit: cover;
    box-shadow: 0 0 5px rgba(0,0,0,0.1);
  }}

  .chat-input-container input {{
    flex-grow: 1;
    padding: 0.8rem 1rem;
    border-radius: 12px;
    border: 1px solid #ccc;
    font-size: 1rem;
    transition: box-shadow 0.3s ease;
  }}

  .chat-input-container input:focus {{
    outline: none;
    box-shadow: 0 0 8px var(--accent);
    border-color: var(--accent);
  }}

  .chat-input-container button {{
    background-color: var(--button-bg);
    color: white;
    border: none;
    padding: 0.8rem 1.2rem;
    border-radius: 12px;
    font-weight: bold;
    cursor: pointer;
    transition: background-color 0.3s ease, transform 0.2s ease;
  }}

  .chat-input-container button:hover {{
    background-color: var(--button-hover);
    transform: scale(1.05);
  }}

  @media (max-width: 600px) {{
    .chat-input-container {{
      flex-direction: column;
      align-items: stretch;
    }}

    .chat-input-container button {{
      width: 100%;
    }}
  }}
</style>

<div class="chat-input-container">
  <img src="https://avatars.githubusercontent.com/u0&v=4
  <input type="text" placeholder="{placeholder}" />
  <button>{submit_txt}</button>
</div>
""", height=150)

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

    # Wordcloud
    st.markdown("### ☁️ Nuage de mots")
    wordcloud = WordCloud(width=800, height=300, background_color='white').generate(content)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis("off")
    st.pyplot(fig)

# Graphique interactif
st.markdown("### 📊 Statistiques des sujets")
data = pd.DataFrame({
    "Sujet": ["5G", "Fibre", "Roaming", "Facturation", "Support"],
    "Questions": [12, 9, 7, 5, 3]
})
fig = px.bar(data, x="Sujet", y="Questions", title="Sujets les plus demandés")
st.plotly_chart(fig)

# Fonctionnalités visuelles
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

# Export historique
if st.sidebar.button("💾 Exporter l'historique"):
    export_text = ""
    for msg in st.session_state.chat_memory.history:
        export_text += f"👤 {msg['user']}\n🤖 {msg['bot']}\n\n"
    st.sidebar.download_button("📥 Télécharger .txt", export_text, file_name="historique_chat.txt")
