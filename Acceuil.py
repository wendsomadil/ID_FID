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
import hashlib
import re
import json
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

# Modules internes
from chatbot.rag_pipeline import get_answer, search_faiss
from chatbot.utils import load_text_data, init_session
from chatbot.memory import ChatMemory
from chatbot.config import PROJECT_ROOT
from db import insert_message, get_all_messages

# Initialisation de la session
init_session()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'chatbot')))

# Configuration Streamlit
st.set_page_config(
    page_title="Assistance IA Télécom",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Classe de cache pour les réponses
class ResponseCache:
    def __init__(self, cache_file="response_cache.json", ttl_hours=24):
        self.cache_file = cache_file
        self.ttl = timedelta(hours=ttl_hours)
        self.cache = self._load_cache()
    
    def _load_cache(self):
        try:
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_cache(self):
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f)
    
    def _get_hash(self, query, context):
        """Crée un hash unique pour la requête et le contexte"""
        content = f"{query}{context}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, query, context):
        cache_key = self._get_hash(query, context)
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            # Vérifier si le cache est encore valide
            cache_time = datetime.fromisoformat(cached_data['timestamp'])
            if datetime.now() - cache_time < self.ttl:
                return cached_data['response']
        return None
    
    def set(self, query, context, response):
        cache_key = self._get_hash(query, context)
        self.cache[cache_key] = {
            'response': response,
            'timestamp': datetime.now().isoformat(),
            'query': query  # Pour le débogage
        }
        self._save_cache()

# Initialisation du cache
response_cache = ResponseCache()

# Fonction pour vérifier si une exception est une erreur de quota
def is_quota_error(exception):
    exception_str = str(exception).lower()
    return any(keyword in exception_str for keyword in ["429", "quota", "rate limit", "rate_limit"])

# Fonction avec retry pour les appels à l'API Gemini
@retry(
    stop=stop_after_attempt(3),  # Maximum 3 tentatives
    wait=wait_exponential(multiplier=1, min=4, max=60),  # Backoff exponentiel
    retry=retry_if_exception(is_quota_error),  # Ne réessayer que pour les erreurs de quota
)
def get_answer_with_retry(query, context):
    return get_answer(query, context)

# Mode dégradé pour maintenir l'expérience utilisateur
def get_fallback_response(query):
    """
    Fournit une réponse de secours quand l'API n'est pas disponible
    """
    # Détecter le type de question pour fournir une réponse générique
    query_lower = query.lower()
    
    # Base de connaissances des questions fréquentes
    faq_responses = {
        "arcep": "L'ARCEP (Autorité de Régulation des Communications Électroniques et des Postes) est l'organisme de régulation des télécommunications au Burkina Faso. Elle est responsable de la régulation du secteur des communications électroniques et des postes, veillant à la concurrence loyale, à la protection des utilisateurs et au développement du secteur.",
        "réglementation": "Les réglementations des télécommunications au Burkina Faso sont principalement définies par le Code des Communications Électroniques et les textes d'application de l'ARCEP. Pour des informations spécifiques, je vous recommande de consulter le site officiel de l'ARCEP.",
        "licence": "Pour obtenir une licence de télécommunication, vous devez soumettre une demande à l'ARCEP avec les documents requis. Les procédures détaillées sont disponibles sur le site web de l'ARCEP.",
        "plainte": "Pour déposer une plainte concernant les services de télécommunication, vous pouvez contacter le service client de votre opérateur ou saisir l'ARCEP via leur plateforme de traitement des réclamations.",
        "artp": "L'ARTP (Autorité de Régulation des Télécommunications/TIC et des Postes) est l'organisme de régulation des télécommunications au Burkina Faso. Elle est responsable de la régulation du secteur des communications électroniques et des postes, veillant à la concurrence loyale, à la protection des utilisateurs et au développement du secteur.",
        "télécom": "Le secteur des télécommunications au Burkina Faso est régulé par l'ARCEP. Pour des informations spécifiques, veuillez consulter leur site web officiel.",
        "internet": "Pour toute question relative à l'accès à Internet, veuillez contacter votre fournisseur d'accès à Internet ou consulter le site de l'ARCEP pour les aspects réglementaires.",
        "opérateur": "Les opérateurs de télécommunications au Burkina Faso doivent être agréés par l'ARCEP. Pour la liste des opérateurs autorisés, veuillez consulter le site web de l'ARCEP.",
    }
    
    # Recherche de correspondances dans la question
    for keyword, response in faq_responses.items():
        if keyword in query_lower:
            return response
    
    # Réponse par défaut si aucune correspondance n'est trouvée
    return "Je ne peux pas fournir de réponse détaillée pour le moment en raison de limitations techniques. Veuillez réessayer plus tard ou consulter le site de l'ARCEP (www.arcep.bf) pour plus d'informations sur la réglementation des télécommunications au Burkina Faso."

def get_answer_with_fallback(query, context):
    """
    Fonction principale qui gère le cache, les retry et le fallback
    """
    # Vérifier d'abord le cache
    cached_response = response_cache.get(query, context)
    if cached_response:
        return cached_response, False  # False = réponse from cache, pas fallback
    
    try:
        # Essayer d'obtenir une réponse de l'API
        response = get_answer_with_retry(query, context)
        # Mettre en cache la réponse
        response_cache.set(query, context, response)
        return response, False
        
    except Exception as e:
        if is_quota_error(e):
            # Mode dégradé
            fallback_response = get_fallback_response(query)
            return fallback_response, True  # True = réponse fallback
        else:
            # Autre type d'erreur
            error_msg = f"Erreur technique: {str(e)}"
            return error_msg, True

# Meta tag mobile
st.markdown("""
<meta name="viewport" content="width=device-width, initial-scale=1.0">
""", unsafe_allow_html=True)

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

# Helper : microphone
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

# Session state init
st.session_state.setdefault("chat_memory", ChatMemory())
st.session_state.setdefault("lang", "fr")
st.session_state.setdefault("service_status", "opérationnel")
st.session_state.setdefault("fallback_messages", {})  # Pour stocker quels messages sont en mode dégradé

# Synthèse vocale
def lire_texte_audio(text: str):
    lang_code = 'fr' if st.session_state.lang == "fr" else 'en'
    tts = gTTS(text=text, lang=lang_code)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        tts.save(tmp.name)
        st.audio(open(tmp.name, "rb").read(), format="audio/mpeg")

# Fonction pour afficher le statut du service
def display_service_status():
    """
    Affiche un indicateur de statut du service
    """
    status = st.session_state.service_status
    color = "green" if status == "opérationnel" else "orange"
    
    st.sidebar.markdown(f"""
    <div style="background-color: {color}; color: white; padding: 0.5rem; border-radius: 0.5rem; text-align: center; margin-bottom: 1rem;">
        Statut du service: <strong>{status}</strong>
    </div>
    """, unsafe_allow_html=True)

# Sidebar : langue et fichier
with st.sidebar:
    display_service_status()
    st.markdown("""
    <div style="text-align:center; margin-bottom:2rem;">
        <h2 style="color:white;">⚙️ Paramètres</h2>
    </div>
    """, unsafe_allow_html=True)
    
    st.session_state.lang = st.radio("Langue", ["fr", "en"])
    uploaded_file = st.file_uploader("📎 Envoyer un fichier texte", type=["txt"])
    
    if st.toggle("🌙 Mode sombre"):
        st.markdown("<body class='dark-mode'>", unsafe_allow_html=True)
    
    # Ajouter des statistiques dans la sidebar
    st.markdown("---")
    st.markdown("""
    <div style="color:white;">
        <h4>📊 Statistiques</h4>
        <p>📝 Documents traités: 12</p>
        <p>💬 Conversations: 24</p>
        <p>⏱️ Temps moyen: 2.4s</p>
    </div>
    """, unsafe_allow_html=True)

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

# Encodage des images
def encode_image_to_base64(image_path: str) -> str:
    if os.path.exists(image_path):
        with open(image_path, "rb") as img:
            return base64.b64encode(img.read()).decode()
    return ""

# Chemin vers les assets
assets_path = os.path.join(os.path.dirname(__file__), '..', 'assets')

# Après avoir encodé feature4_img via :
feature4_img = encode_image_to_base64(os.path.join(assets_path, "citadel.png"))

# Header amélioré
st.markdown(f"""
<div class="custom-header">
    <h1>{title}</h1>
    <p>{subtitle}</p>
</div>
""", unsafe_allow_html=True)

# Ajouter des indicateurs de performance
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
    <div style="background:white; padding:1rem; border-radius:1rem; text-align:center; box-shadow:0 5px 15px rgba(0,0,0,0.08)">
        <h3>📄 Documents</h3>
        <p style="font-size:2rem; font-weight:bold; margin:0">12</p>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown("""
    <div style="background:white; padding:1rem; border-radius:1rem; text-align:center; box-shadow:0 5px 15px rgba(0,0,0,0.08)">
        <h3>💬 Conversations</h3>
        <p style="font-size:2rem; font-weight:bold; margin:0">24</p>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown("""
    <div style="background:white; padding:1rem; border-radius:1rem; text-align:center; box-shadow:0 5px 15px rgba(0,0,0,0.08)">
        <h3>⏱️ Temps moyen</h3>
        <p style="font-size:2rem; font-weight:bold; margin:0">2.4s</p>
    </div>
    """, unsafe_allow_html=True)

# Chat display
st.markdown("""
<div style="margin:2rem 0 1rem 0;">
    <h2>💬 Conversation</h2>
</div>
""", unsafe_allow_html=True)

chat_container = st.container()
with chat_container:
    st.markdown('<div class="chat-history">', unsafe_allow_html=True)
    for idx, msg in enumerate(st.session_state.chat_memory.history):
        # Vérifier si ce message est en mode dégradé
        is_fallback = st.session_state.fallback_messages.get(idx, False)
        
        # Message utilisateur
        st.markdown(f"""
            <div class='chat-container'>
                <div class='bubble user'>{msg['user']}</div>
            </div>
        """, unsafe_allow_html=True)
        
        # Message bot avec boutons
        badge = " ⚠️ (Réponse générique)" if is_fallback else ""
        
        st.markdown(f"""
            <div class='chat-container'>
                <div class='bubble bot'>
                    {msg['bot']}{badge}
                    <div style="display: flex; margin-top: 10px;">
                        <button onclick="navigator.clipboard.writeText('{msg['bot'].replace("'", "\\'")}')" style="background: rgba(255,255,255,0.3); border: none; border-radius: 50%; width: 30px; height: 30px; cursor: pointer; margin-right: 10px;">📋</button>
                        <button onclick="window.parent.document.getElementById('tts_{idx}').click()" style="background: rgba(255,255,255,0.3); border: none; border-radius: 50%; width: 30px; height: 30px; cursor: pointer;">🎧</button>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Bouton caché pour la synthèse vocale
        st.markdown(f'<div style="display: none;">', unsafe_allow_html=True)
        if st.button(f"Écouter réponse {idx+1}", key=f"tts_{idx}"):
            lire_texte_audio(msg['bot'])
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Input & RAG pipeline avec gestion d'erreur élégante
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
                
                # Utiliser le nouveau système avec cache et fallback
                answer, is_fallback = get_answer_with_fallback(query, context)
                
                # Mettre à jour le statut du service
                st.session_state.service_status = "opérationnel" if not is_fallback else "mode dégradé"
                
                # Ajouter à l'historique
                st.session_state.chat_memory.add_to_memory(query, answer)
                
                # Stocker l'information sur le mode dégradé séparément
                current_idx = len(st.session_state.chat_memory.history) - 1
                st.session_state.fallback_messages[current_idx] = is_fallback
                
            st.rerun()
        except Exception as e:
            st.error(f"""
            ❌ **Erreur technique**
            
            Une erreur s'est produite lors du traitement de votre demande:
            ```{str(e)}```
            
            Veuillez réessayer ou contacter le support technique si le problème persiste.
            """)

process_query()

# Suggestions de questions
st.markdown("""
<div style="margin:1rem 0;">
    <h4>💡 Questions suggérées</h4>
</div>
""", unsafe_allow_html=True)

suggestions_fr = [
    "Quelles sont les réglementations pour les opérateurs télécoms?",
    "Comment obtenir une licence de télécommunication?",
    "Quelles sont les obligations des FAI?",
    "Qui contacter pour une plainte concernant les services telecom?"
]

suggestions_en = [
    "What are the regulations for telecom operators?",
    "How to obtain a telecommunications license?",
    "What are the obligations of ISPs?",
    "Who to contact for a complaint about telecom services?"
]

suggestions = suggestions_fr if st.session_state.lang == "fr" else suggestions_en

cols = st.columns(2)
for i, suggestion in enumerate(suggestions):
    with cols[i % 2]:
        if st.button(suggestion, use_container_width=True):
            st.session_state.suggested_query = suggestion
            st.rerun()

# Wordcloud
if uploaded_file:
    st.markdown("""
    <div style="margin:2rem 0 1rem 0;">
        <h2>📊 Analyse du document</h2>
    </div>
    """, unsafe_allow_html=True)
    
    content = uploaded_file.read().decode("utf-8")
    word_count = len(content.split())
    st.success(f"📄 Le fichier contient {word_count} mots.")
    
    st.markdown("### ☁️ Nuage de mots")
    wordcloud = WordCloud(width=800, height=300, background_color='white').generate(content)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis("off")
    st.pyplot(fig)

# Bouton pour effacer la conversation
if st.sidebar.button(clear_txt):
    st.session_state.chat_memory.clear()
    st.session_state.fallback_messages = {}
    st.session_state.service_status = "opérationnel"
    st.rerun()

# Ajouter un pied de page
st.markdown("""
<div style="text-align:center; margin-top:3rem; padding:1.5rem; color:gray;">
    <hr style="margin-bottom:1rem;">
    <p>Assistance IA Télécom © 2023 - Propulsé par Streamlit et l'IA</p>
</div>
""", unsafe_allow_html=True)

# JavaScript pour le défilement automatique
components.html("""
<script>
function scrollToBottom() {
    const chatHistory = window.parent.document.querySelector('.chat-history');
    if (chatHistory) {
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }
}
setTimeout(scrollToBottom, 100);
</script>
""", height=0)
