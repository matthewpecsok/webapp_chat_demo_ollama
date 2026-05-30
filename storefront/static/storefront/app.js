const chatForm = document.querySelector("#chatForm");
const chatInput = document.querySelector("#chatInput");
const chatLog = document.querySelector("#chatLog");
const chatError = document.querySelector("#chatError");
const clearChat = document.querySelector("#clearChat");
const askButtons = document.querySelectorAll(".ask-button");

let history = [];

function csrfToken() {
  const match = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : "";
}

function appendMessage(role, text) {
  const node = document.createElement("div");
  node.className = `message ${role}`;
  node.textContent = text;
  chatLog.appendChild(node);
  chatLog.scrollTop = chatLog.scrollHeight;
  return node;
}

function setError(message) {
  chatError.textContent = message;
  chatError.hidden = !message;
}

function setBusy(isBusy) {
  chatForm.querySelector("button").disabled = isBusy;
  chatInput.disabled = isBusy;
}

async function sendMessage(message) {
  setBusy(true);
  setError("");
  appendMessage("user", message);
  const pending = appendMessage("assistant pending", "Choosing a good match...");

  try {
    const response = await fetch("/chat/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken(),
      },
      body: JSON.stringify({ message, history }),
    });
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || data.error || "The advisor is unavailable.");
    }

    pending.textContent = data.reply;
    pending.classList.remove("pending");
    history = [
      ...history,
      { role: "user", content: message },
      { role: "assistant", content: data.reply },
    ].slice(-8);
  } catch (error) {
    pending.remove();
    setError(error.message);
  } finally {
    setBusy(false);
    chatInput.focus();
  }
}

chatForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const message = chatInput.value.trim();
  if (!message) return;
  chatInput.value = "";
  sendMessage(message);
});

askButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const title = button.dataset.title;
    chatInput.value = `Would ${title} work for my wardrobe?`;
    chatInput.focus();
  });
});

clearChat.addEventListener("click", () => {
  history = [];
  chatLog.innerHTML = "";
  appendMessage(
    "assistant",
    "Tell me where you are wearing it, your budget, and the fit you like."
  );
  setError("");
  chatInput.focus();
});
