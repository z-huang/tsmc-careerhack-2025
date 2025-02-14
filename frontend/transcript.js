document.addEventListener('DOMContentLoaded', function () {
  const sidebar = document.getElementById('leftsidebar');
  const mainContent = document.getElementById('mainContent');
  const toggleBtn = document.getElementById('toggleSidebar');
  const chatBtn = document.querySelector('.chat-btn');
  const chatPopup = document.getElementById('chatPopup');
  const closeChatBtn = document.getElementById('closeChatBtn');

  // 側邊欄切換功能
  toggleBtn.addEventListener('click', function () {
    sidebar.classList.toggle('collapsed');
    mainContent.classList.toggle('expanded');

    if (sidebar.classList.contains('collapsed')) {
      toggleBtn.innerHTML = '☰';
    } else {
      toggleBtn.innerHTML = '←';
    }
  });

  // Chat popup 切換功能
  function toggleChatPopup() {
    chatPopup.classList.toggle('show');
  }

  // 點擊 Chat 按鈕時切換顯示狀態
  chatBtn.addEventListener('click', toggleChatPopup);

  // 點擊關閉按鈕時隱藏 chat popup，並阻止事件冒泡
  closeChatBtn.addEventListener('click', (e) => {
    e.stopPropagation(); // 防止事件冒泡到外層
    chatPopup.classList.remove('show');
  });

  // Chat functionality
  const chatInput = document.getElementById('chatInput');
  const sendChatBtn = document.getElementById('sendChatBtn');
  const chatMessages = document.getElementById('chatMessages');

  // Example event: Sending a chat message
  sendChatBtn.addEventListener('click', () => {
    const text = chatInput.value.trim();
    if (!text) return;

    // Display user message
    const userMsgDiv = document.createElement('div');
    userMsgDiv.style.margin = '10px 0';
    userMsgDiv.textContent = `User: ${text}`;
    chatMessages.appendChild(userMsgDiv);

    // Clear the input
    chatInput.value = '';

    // Mock AI response
    const aiMsgDiv = document.createElement('div');
    aiMsgDiv.style.margin = '10px 0';
    aiMsgDiv.textContent = `AI: This is a mock response for "${text}".`;
    chatMessages.appendChild(aiMsgDiv);

    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
  });

  // Press Enter to send chat message
  chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      sendChatBtn.click();
    }
  });
});