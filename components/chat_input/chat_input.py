import streamlit.components.v1 as components
import os

_component_func = components.declare_component(
    "chat_input",
    path=os.path.join(os.path.dirname(__file__), "frontend")
)

def chat_input(placeholder="Votre message ici...", key=None, lang="fr"):
    return _component_func(placeholder=placeholder, lang=lang, default="", key=key)
