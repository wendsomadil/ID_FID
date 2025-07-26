function sendMessage() {
  const input = document.getElementById("chatInput").value;
  Streamlit.setComponentValue(input);
}

document.addEventListener("DOMContentLoaded", function () {
  const inputField = document.getElementById("chatInput");
  inputField.addEventListener("keydown", function (event) {
    if (event.key === "Enter") {
      event.preventDefault();
      sendMessage();
    }
  });
});

Streamlit.setComponentReady();
Streamlit.setFrameHeight(100);
