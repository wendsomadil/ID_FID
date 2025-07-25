function renderMessages(messages) {
  const container = document.getElementById("chatDisplay");
  container.innerHTML = "";

  messages.forEach(msg => {
    const div = document.createElement("div");
    div.className = "message " + msg.role;
    div.innerHTML = `<div>${msg.text}</div><div class="timestamp">${msg.timestamp}</div>`;
    container.appendChild(div);
  });
}

Streamlit.events.addEventListener("message", (event) => {
  renderMessages(event.detail.args.messages);
});

Streamlit.setComponentReady();
Streamlit.setFrameHeight(400);
