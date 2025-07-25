import streamlit.components.v1 as components
import os

_component_func = components.declare_component(
    "chat_display",
    path=os.path.join(os.path.dirname(__file__), "frontend")
)

def chat_display(messages, key=None):
    return _component_func(messages=messages, key=key)
