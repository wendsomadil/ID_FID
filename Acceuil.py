# Acceuil.py
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

def microphone_input():
    components.html("""
    <script>
    const waitForInput = setInterval(() => {
        const inputBox = window.parent.document.querySelector('textarea');
        if (inputBox) {
            clearInterval(waitForInput);
            const micButton = document.createElement('button');
            micButton.innerText = '🎙️';
            micButton.style.marginLeft = '8px';
            micButton.style.padding = '4px 8px';
            micButton.style.borderRadius = '6px';
            micButton.style.border = 'none';
            micButton.style.background = '#6366f1';
            micButton.style.color = 'white';
            micButton.style.cursor = 'pointer';
            micButton.title = 'Dicter votre question';

            micButton.onclick = () => {
                if (window.hasOwnProperty('webkitSpeechRecognition')) {
                    const recognition = new webkitSpeechRecognition();
                    recognition.continuous = false;
                    recognition.interimResults = false;
                    recognition.lang = 'fr-FR';
                    recognition.start();

                    recognition.onresult = function(e) {
                        inputBox.value = e.results[0][0].transcript;
                        inputBox.dispatchEvent(new Event('input', { bubbles: true }));
                        recognition.stop();
                    };

                    recognition.onerror = function(e) {
                        recognition.stop();
                    };
                } else {
                    alert("La reconnaissance vocale n'est pas supportée par ce navigateur.");
                }
            };

            inputBox.parentNode.appendChild(micButton);
        }
    }, 500);
    </script>
    """, height=0)

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
feature4_img = encode_image_to_base64(os.path.join(assets_path, "citadel.png"))

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
if st.sidebar.toggle("🌙 Mode sombre"):
    st.markdown("<body class='dark-mode'>", unsafe_allow_html=True)

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

# En-tête stylisé avec image de fond
st.markdown(f"""
<div style="background-image: url('data:image/png;base64,{feature4_img}');
             background-size: cover;
             background-position: center;
             padding: 2rem;
             border-radius: 12px;
             text-align: center;
             color: white;
             box-shadow: 0 4px 12px rgba(0,0,0,0.3);">
  <h1 style="font-size: 2.5rem; font-weight: bold; text-shadow: 1px 1px 2px black;">{title}</h1>
  <p style="font-size: 1.2rem; text-shadow: 1px 1px 2px black;">{subtitle}</p>
</div>
""", unsafe_allow_html=True)

# Afficher l’historique depuis la base
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

suggestions = {
    "fr": [
        "Quels sont les frais de roaming ?",
        "Comment fonctionne la 5G ?",
        "Quelles sont les règles de facturation ?"
    ]
}

st.markdown("#### 💡 Suggestions")
for i, q in enumerate(suggestions[st.session_state.lang]):
    if st.button(q, key=f"suggest_{i}"):
        st.session_state["suggested_query"] = q
        st.rerun()
    st.markdown(f"<div class='suggestion-button'>{q}</div>", unsafe_allow_html=True)

# Zone de saisie en bas et traitement
def process_query():
    microphone_input()

    query = st.chat_input(placeholder=placeholder, key="native_chat_input")

    if "suggested_query" in st.session_state:
        query = st.session_state.pop("suggested_query")

    if query and len(query.split()) >= 3:
        try:
            with st.spinner("💡 L'assistant réfléchit..."):
                results = search_faiss(query, top_n=5)
                context = "\n".join([d for d, _ in results] + st.session_state.chat_memory.get_context())
                answer = get_answer(query, context)
                st.session_state.chat_memory.add_to_memory(query, answer)
                lire_texte_audio(answer)
            st.rerun()
        except Exception as e:
            st.error(f"❌ Erreur : {e}")
process_query()

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
