// Sidebar toggle functionality
document.addEventListener('DOMContentLoaded', function () {
  const sidebar = document.getElementById('leftsidebar');
  const mainContent = document.getElementById('mainContent');
  const toggleBtn = document.getElementById('toggleSidebar');

  toggleBtn.addEventListener('click', function () {
    sidebar.classList.toggle('collapsed');
    mainContent.classList.toggle('expanded');

    if (sidebar.classList.contains('collapsed')) {
      toggleBtn.innerHTML = '☰';
    } else {
      toggleBtn.innerHTML = '←';
    }
  });
});

// Chat functionality
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const messageArea = document.getElementById('messageArea');

// Example event: Sending the user's message
sendBtn.addEventListener('click', () => {
  const text = userInput.value.trim();
  if (!text) return;

  // Display user message in the message area (if you want a chat-like effect)
  const userMsgDiv = document.createElement('div');
  userMsgDiv.style.margin = '10px 0';
  userMsgDiv.textContent = `User: ${text}`;
  messageArea.appendChild(userMsgDiv);

  // Clear the input
  userInput.value = '';

  // You could call your backend / AI API here...
  // Then append an AI response to the message area, for example:
  const aiMsgDiv = document.createElement('div');
  aiMsgDiv.style.margin = '10px 0';
  aiMsgDiv.textContent = `AI: This is a mock response for "${text}".`;
  messageArea.appendChild(aiMsgDiv);

  // Scroll to bottom if needed
  messageArea.scrollTop = messageArea.scrollHeight;
});

// Optional: Press Enter to send
userInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') {
    e.preventDefault();
    sendBtn.click();
  }
});

// If you want to handle suggestion tags:
document.querySelectorAll('.tag-btn').forEach((btn) => {
  btn.addEventListener('click', () => {
    userInput.value = btn.textContent; // put the tag text into input
    userInput.focus();
  });
});