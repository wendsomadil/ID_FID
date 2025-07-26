import os
import streamlit.components.v1 as components

_HERE = os.path.dirname(os.path.abspath(__file__))
_FRONTEND_DIR = os.path.join(_HERE, "..", "frontend")

print("✅ Composant chat_input chargé depuis :", _FRONTEND_DIR)

chat_input = components.declare_component(
    name="chat_input",
    path=os.path.abspath(_FRONTEND_DIR)
)
