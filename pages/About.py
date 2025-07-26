import streamlit as st
import os
import base64
from chatbot.config import PROJECT_ROOT
# Import de la page Accueil pour navigation

# La navigation est gérée automatiquement par Streamlit via le dossier `pages/`
# Pas besoin d'importer `acceuil.py` manuellement ni de créer un selectbox.
# Cette page About sera accessible depuis le menu latéral généré par Streamlit.
st.set_page_config(
    page_title="À propos - Fonctionnalités",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Meta tag mobile
st.markdown(
    """
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    """,
    unsafe_allow_html=True
)

# Charger CSS
def load_css(path: str):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.error(f"Fichier CSS introuvable : {path}")

css_path = os.path.join(PROJECT_ROOT, 'css', 'styles.css')
load_css(css_path)

# Fonction utilitaire pour encoder les images
def encode_image_to_base64(image_path: str) -> str:
    if os.path.exists(image_path):
        with open(image_path, "rb") as img:
            return base64.b64encode(img.read()).decode()
    return ""

# Chemin vers le dossier assets
assets_path = os.path.join(os.path.dirname(__file__), '..', 'assets')

# Définition des fonctionnalités
features = [
    {
        "title": "Réglementation",
        "description": "Accès instantané aux textes officiels et aux normes.",
        "image": encode_image_to_base64(os.path.join(assets_path, "telecom.png"))
    },
    {
        "title": "Assistant Intelligent",
        "description": "Réponses précises et contextualisées basées sur l'IA.",
        "image": encode_image_to_base64(os.path.join(assets_path, "ai-assistant.png"))
    },
    {
        "title": "Multilingue",
        "description": "Disponible en français et en anglais pour plus d'accessibilité.",
        "image": encode_image_to_base64(os.path.join(assets_path, "translation.png"))
    }
]

# Titre de la page
st.title("✨ Fonctionnalités de l'application")

# Conteneur HTML pour les cartes (affichage flex responsive)
st.markdown("""
<div class="cards-container">
""", unsafe_allow_html=True)

# Boucle HTML des feature cards
for feat in features:
    st.markdown(f"""
    <div class="feature-card">
      <img src="data:image/png;base64,{feat['image']}" alt="{feat['title']}" />
      <h3>{feat['title']}</h3>
      <p>{feat['description']}</p>
    </div>
    """, unsafe_allow_html=True)

# Fin du conteneur
st.markdown("""
</div>
""", unsafe_allow_html=True)
