function sendMessage() {
  const input = document.getElementById("chatInput").value;
  Streamlit.setComponentValue(input);
}

Streamlit.setComponentReady();
Streamlit.setFrameHeight(100);
