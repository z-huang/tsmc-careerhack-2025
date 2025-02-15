document.addEventListener('DOMContentLoaded', function () {

	// Load translations from JSON file
	function loadTranslations(lang) {
		fetch('./translations.json')
			.then(response => response.json())
			.then(data => {
				if (data[lang]) {
					applyTranslations(data[lang]);
				}
			})
			.catch(error => console.error('Error loading translations:', error));
	}

	// Apply translations to UI elements
	function applyTranslations(translations) {
		// Update elements with data-i18n
		document.querySelectorAll('[data-i18n]').forEach(el => {
			const key = el.getAttribute('data-i18n');
			if (translations[key]) {
				el.textContent = translations[key];
			}
		});

		// Update placeholders
		document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
			const key = el.getAttribute('data-i18n-placeholder');
			if (translations[key]) {
				el.setAttribute('placeholder', translations[key]);
			}
		});
	}

	const sidebar = document.getElementById('leftsidebar');
	const mainContent = document.getElementById('mainContent');
	const toggleBtn = document.getElementById('toggleSidebar');
	const chatBtn = document.querySelector('.chat-btn');
	const chatPopup = document.getElementById('chatPopup');
	const closeChatBtn = document.getElementById('closeChatBtn');

	// drop down list for "Language" button
	const dropdownLinks = document.querySelectorAll('.dropdown-content a');
	const languageBtn = document.querySelector('.language-btn');
	let currentLang = 'cmn-Hant-TW'; // 設置默認語言為中文

	loadTranslations(currentLang);

	// 添加 active 類到默認語言選項
	dropdownLinks.forEach(link => {
		if (link.getAttribute('data-lang') === currentLang) {
			link.classList.add('active');
		}

		link.addEventListener('click', async(e) => {
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

			try {
                const response = await fetch('http://localhost:8000/set_language', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ language: currentLang })
                });

                const data = await response.json();
                if (data.success) {
                    console.log(`Language changed to: ${selectedLang}`);
                    loadTranslations(currentLang);
                } else {
                    console.error("Failed to set language on the server.");
                }
            } catch (error) {
                console.error('Error setting language:', error);
            }

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

	const newTranscriptBtn = document.getElementById('newTranscriptBtn');
	const todayHistoryBlocks = document.querySelector('.sidebar-section .history-blocks');

	// 新增除錯訊息
	console.log('按鈕元素:', newTranscriptBtn);
	console.log('歷史區塊容器:', todayHistoryBlocks);

	if (!newTranscriptBtn || !todayHistoryBlocks) {
		console.error('找不到必要的 DOM 元素');
		return;
	}

	newTranscriptBtn.addEventListener('click', function () {
		const newBlock = document.createElement('div');
		newBlock.className = 'history-block';

		const currentTime = new Date().toLocaleTimeString();

		// 修改 block 內容結構
		newBlock.innerHTML = `
			<div class="history-content">
				<div class="title">Untitled</div>
				<div class="timestamp">${currentTime}</div>
			</div>
			<div class="history-menu-btn">⋮</div>
			<div class="history-menu">
				<div class="history-menu-item">Rename</div>
				<div class="history-menu-item">Delete</div>
			</div>
		`;

		// 添加選單點擊事件
		const menuBtn = newBlock.querySelector('.history-menu-btn');
		const menu = newBlock.querySelector('.history-menu');

		menuBtn.addEventListener('click', function (e) {
			e.stopPropagation(); // 防止觸發 block 的點擊事件
			menu.classList.toggle('show');
		});

		// 點擊其他地方時關閉選單
		document.addEventListener('click', function (e) {
			if (!menu.contains(e.target) && !menuBtn.contains(e.target)) {
				menu.classList.remove('show');
			}
		});

		// 將新區塊插入到容器中
		if (todayHistoryBlocks.firstChild) {
			todayHistoryBlocks.insertBefore(newBlock, todayHistoryBlocks.firstChild);
		} else {
			todayHistoryBlocks.appendChild(newBlock);
		}

		// 添加點擊事件和動畫效果
		newBlock.addEventListener('click', function () {
			const transcriptArea = document.getElementById('transcriptArea');
			transcriptArea.innerHTML = '';
		});

		newBlock.style.animation = 'highlight 1s ease';
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

    let audioStream;
    let mediaRecorder;
    let ws;
    let isRecording = false;

    function startWebSocket() {
        ws = new WebSocket('ws://localhost:8000/ws/transcript/2');
        ws.onopen = () => console.log('WebSocket connected.');
        // ws.onmessage = (message) => console.log('Received from server:', message.data);
        ws.onmessage = (message) => {
            console.log('Received from server:', message.data);

            const data = JSON.parse(message.data);
            const text = data.text;
            const id = data.block_id;
        
            const chatMessages = document.getElementById('transcriptArea');

            // Check if a message with the same block_id already exists
            let existingMsgDiv = document.getElementById(`msg-${id}`);

            if (existingMsgDiv) {
                // If a message with the same ID exists, update it
                existingMsgDiv.textContent = text;
            } else {
                // Create a new message div
                const serverMsgDiv = document.createElement('div');
                serverMsgDiv.className = 'server-message'; // Add a class for styling
                serverMsgDiv.id = `msg-${id}`; // Assign unique ID based on block_id
                serverMsgDiv.textContent = text;

                // Append the new message to the chat area
                chatMessages.appendChild(serverMsgDiv);
            }
        
            // Auto-scroll to the latest message
            chatMessages.scrollTop = chatMessages.scrollHeight;
        };
        
    }

    async function startStreaming() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            audioStream = stream;
            
            const audioTrack = stream.getAudioTracks()[0];
            const audioSettings = audioTrack.getSettings();
            console.log(`Sample Rate: ${audioSettings.sampleRate} Hz`);
            console.log(`Channels: ${audioSettings.channelCount || "Unknown"}`);

            mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });

            mediaRecorder.ondataavailable = (event) => {
                if (ws.readyState === WebSocket.OPEN) {
                    ws.send(event.data);
                }
            };

            mediaRecorder.start(1000); // Collect audio in 1000ms chunks
            console.log('Streaming started...');
        } catch (error) {
            console.error("Error accessing microphone:", error);
        }
    }

    function stopStreaming() {
        if (mediaRecorder) {
            mediaRecorder.stop();
        }
        if (audioStream) {
            audioStream.getTracks().forEach(track => track.stop());
        }
        console.log('Streaming stopped.');
    }

    const startBtn = document.getElementById('startBtn');
    startBtn.addEventListener('click', function () {
        if (!isRecording) {
            startWebSocket();
            startStreaming();
            startBtn.innerHTML = `<span class="btn-icon">■</span> <span data-i18n="stop">Stop</span>`;
        } else {
            stopStreaming();
            ws.close;
            startBtn.innerHTML = `<span class="btn-icon">●</span> <span data-i18n="record">Record</span>`;
        }
        isRecording = !isRecording;
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

