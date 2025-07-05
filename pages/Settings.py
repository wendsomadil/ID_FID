# pages/Settings.py
import streamlit as st
from chatbot.utils import init_session
init_session()

st.set_page_config(page_title="Paramètres", page_icon="⚙️")

# Appliquer le thème actuel (pour le background HTML/CSS)
st.markdown(f"<body data-theme='{st.session_state.theme}'>", unsafe_allow_html=True)

# Titre
st.header("⚙️ Paramètres" if st.session_state.lang == "fr" else "⚙️ Settings")

# --------- Sauvegarde des valeurs précédentes ---------
if "prev_theme" not in st.session_state:
    st.session_state.prev_theme = st.session_state.theme
if "prev_lang" not in st.session_state:
    st.session_state.prev_lang = st.session_state.lang

# --------- Choix du thème ---------
theme_label = "Thème de l'application" if st.session_state.lang == "fr" else "Application Theme"
theme_options = ["Clair", "Sombre"] if st.session_state.lang == "fr" else ["Light", "Dark"]
theme_index = 0 if st.session_state.theme == "light" else 1

selected_theme = st.radio(theme_label, theme_options, index=theme_index)
st.session_state.theme = "light" if selected_theme in ["Clair", "Light"] else "dark"

# --------- Choix de la langue ---------
lang_label = "Langue" if st.session_state.lang == "fr" else "Language"
lang_options = ["Français", "English"]
lang_index = 0 if st.session_state.lang == "fr" else 1

selected_lang = st.selectbox(lang_label, lang_options, index=lang_index)
st.session_state.lang = "fr" if selected_lang == "Français" else "en"

# --------- Détection de changement ---------
if (
    st.session_state.theme != st.session_state.prev_theme
    or st.session_state.lang != st.session_state.prev_lang
):
    st.session_state.prev_theme = st.session_state.theme
    st.session_state.prev_lang = st.session_state.lang
    st.rerun()
