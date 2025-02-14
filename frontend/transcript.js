document.addEventListener('DOMContentLoaded', function () {
	const sidebar = document.getElementById('leftsidebar');
	const mainContent = document.getElementById('mainContent');
	const toggleBtn = document.getElementById('toggleSidebar');
	const chatBtn = document.querySelector('.chat-btn');
	const chatPopup = document.getElementById('chatPopup');
	const closeChatBtn = document.getElementById('closeChatBtn');

	// drop down list for "Language" button
	const dropdownLinks = document.querySelectorAll('.dropdown-content a');
	let currentLang = 'zh'; // 設置默認語言為中文

	// 添加 active 類到默認語言選項
	dropdownLinks.forEach(link => {
		if (link.getAttribute('data-lang') === currentLang) {
			link.classList.add('active');
		}

		link.addEventListener('click', (e) => {
			e.preventDefault();
			const selectedLang = e.target.getAttribute('data-lang');
			currentLang = selectedLang;

			// 移除所有 active 類
			dropdownLinks.forEach(link => link.classList.remove('active'));
			// 添加 active 類到選中的選項
			e.target.classList.add('active');

			// 更新按鈕文字
			const languageBtn = document.querySelector('.language-btn');
			languageBtn.innerHTML = `<span class="btn-icon">🌐</span> ${e.target.textContent}`;

			// 這裡可以添加語言切換的具體邏輯
			console.log(`Language changed to: ${selectedLang}`);
		});
	});

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

	const searchInput = document.getElementById('searchInput');
	const searchBtn = document.getElementById('searchBtn');
	const searchPopup = document.getElementById('searchPopup');
	const closeSearchBtn = document.getElementById('closeSearchBtn');
	const searchResults = document.getElementById('searchResults');

	function toggleSearchPopup() {
		searchPopup.classList.toggle('show');
	}

	// 監聽搜尋按鈕點擊事件
	searchBtn.addEventListener('click', () => {
		const query = searchInput.value.trim();
		if (!query) return;

		// 模擬搜尋結果
		searchResults.innerHTML = `
      <div>🔎 搜尋關鍵字: <strong>${query}</strong></div>
      <div>📄 找到 3 個相關結果：</div>
      <ul>
        <li>📜 <a href="#">搜尋結果 1</a></li>
        <li>📜 <a href="#">搜尋結果 2</a></li>
        <li>📜 <a href="#">搜尋結果 3</a></li>
      </ul>
    `;

		// 顯示搜尋結果彈出視窗
		toggleSearchPopup();
	});

	// 關閉搜尋視窗
	closeSearchBtn.addEventListener('click', () => {
		searchPopup.classList.remove('show');
	});

	// 監聽 Enter 鍵進行搜尋
	searchInput.addEventListener('keypress', (e) => {
		if (e.key === 'Enter') {
			e.preventDefault();
			searchBtn.click();
		}
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

	// new trascript button
	const newTranscriptBtn = document.getElementById('newTranscriptBtn');
	const sidebarNav = document.querySelector('.sidebar-nav ul');
	let transcriptCount = 1;

	newTranscriptBtn.addEventListener('click', function () {
		// 1. 在側邊欄添加新的 transcript 項目
		const newTranscriptItem = document.createElement('li');
		const currentDate = new Date();
		const timestamp = currentDate.toLocaleTimeString();
		newTranscriptItem.innerHTML = `<a href="#">New Transcript ${timestamp}</a>`;
		sidebarNav.appendChild(newTranscriptItem);

		// 2. 重置主內容區域
		const transcriptArea = document.getElementById('transcriptArea');
		transcriptArea.innerHTML = ''; // 清空現有內容

		// 3. 重置輸入區域和其他元素到默認狀態
		const promptContainer = document.querySelector('.prompt-container');
		promptContainer.querySelector('h1').textContent = 'Transcript';

		// 4. 自動滾動到新建的項目
		newTranscriptItem.scrollIntoView({ behavior: 'smooth' });

		// 5. 為新項目添加視覺反饋
		newTranscriptItem.style.animation = 'highlight 1s ease';
	});
	
	// termination blocks
	const termBlocks = document.querySelectorAll('.term-block');
    
    termBlocks.forEach(block => {
        const header = block.querySelector('.term-header');
        
        header.addEventListener('click', () => {
            // 切換當前區塊的展開狀態
            block.classList.toggle('expanded');
        });
    });
});

const style = document.createElement('style');
style.textContent = `
    @keyframes highlight {
        0% { background-color: #2c2d31; }
        100% { background-color: transparent; }
    }
`;
document.head.appendChild(style);