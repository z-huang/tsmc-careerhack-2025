document.addEventListener('DOMContentLoaded', function () {
	// 全局變量聲明
	let historyCounter = 0;
	let curMeetingId = 1;
	let audioStream;
	let mediaRecorder;
	let ws;
	let isRecording = false;
	let currentTranslations = {};

	// DOM 元素獲取
	const newTranscriptBtn = document.getElementById('newTranscriptBtn');
	const todayHistoryBlocks = document.querySelector('.sidebar-section .history-blocks');
	const transcriptArea = document.getElementById('transcriptArea');
	const terminologyList = document.getElementById('terminologyList');
	const sidebar = document.getElementById('leftsidebar');
	const mainContent = document.getElementById('mainContent');
	const toggleBtn = document.getElementById('toggleSidebar');
	const startBtn = document.getElementById('startBtn');
	const chatBtn = document.querySelector('.chat-btn');
	const chatPopup = document.getElementById('chatPopup');
	const closeChatBtn = document.getElementById('closeChatBtn');
	const chatInput = document.getElementById('chatInput');
	const sendChatBtn = document.getElementById('sendChatBtn');
	const chatMessages = document.getElementById('chatMessages');

	// 檢查必要的 DOM 元素
	if (!newTranscriptBtn || !todayHistoryBlocks) {
		console.error('找不到必要的 DOM 元素');
		return;
	}

	// 初始化現有的 history blocks
	document.querySelectorAll('.history-block').forEach(block => {
		initializeHistoryBlock(block);
	});

	// 翻譯相關功能
	function loadTranslations(lang) {
		fetch('./translations.json')
			.then(response => response.json())
			.then(data => {
				if (data[lang]) {
					currentTranslations = data[lang];
					applyTranslations(data[lang]);
					updateRecordButtonText(isRecording);
				}
			})
			.catch(error => console.error('Error loading translations:', error));
	}

	function applyTranslations(translations) {
		document.querySelectorAll('[data-i18n]').forEach(el => {
			const key = el.getAttribute('data-i18n');
			if (translations[key]) {
				el.textContent = translations[key];
			}
		});

		document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
			const key = el.getAttribute('data-i18n-placeholder');
			if (translations[key]) {
				el.setAttribute('placeholder', translations[key]);
			}
		});
	}

	// 語言切換初始化
	const dropdownLinks = document.querySelectorAll('.dropdown-content a');
	let currentLang = 'cmn-Hant-TW';
	loadTranslations(currentLang);

	dropdownLinks.forEach(link => {
		if (link.getAttribute('data-lang') === currentLang) {
			link.classList.add('active');
		}

		link.addEventListener('click', async (e) => {
			e.preventDefault();
			const selectedLang = e.target.getAttribute('data-lang');
			currentLang = selectedLang;

			dropdownLinks.forEach(link => link.classList.remove('active'));
			e.target.classList.add('active');

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
					loadTranslations(currentLang);
				}
			} catch (error) {
				console.error('Error setting language:', error);
			}
		});
	});

	// History Block 相關功能
	function createHistoryBlock(meetingId, title, date) {
		const newBlockId = `history-block-${meetingId}`;
		const newBlock = document.createElement('div');
		newBlock.className = 'history-block';
		newBlock.id = newBlockId;

		newBlock.innerHTML = `
            <div class="history-content">
                <div class="title">${title}</div>
                <div class="timestamp">${date}</div>
            </div>
            <div class="history-menu-btn">⋮</div>
            <div class="history-menu">
                <div class="history-menu-item">Rename</div>
                <div class="history-menu-item">Delete</div>
                <div class="history-menu-item" id="downloadBtn">Download</div>
            </div>
        `;

		todayHistoryBlocks.prepend(newBlock);
		initializeHistoryBlock(newBlock);

		newBlock.addEventListener('click', function (e) {
			if (e.target.classList.contains('history-menu-btn') || e.target.closest('.history-menu')) {
				return;
			}
			fetchTranscript(meetingId);
			curMeetingId = meetingId;
		});

		newBlock.style.animation = 'highlight 1s ease';
	}

	function initializeHistoryBlock(block) {
		const menuBtn = block.querySelector('.history-menu-btn');
		const menu = block.querySelector('.history-menu');
		const downloadBtn = block.querySelector('.history-menu-item#downloadBtn');

		menuBtn.addEventListener('click', function (e) {
			e.stopPropagation();
			menu.classList.toggle('show');
		});

		downloadBtn?.addEventListener('click', async function (e) {
			e.stopPropagation();
			const meetingId = block.id.replace('history-block-', '');

			try {
				const response = await fetch(`http://localhost:8000/download/${meetingId}`, {
					method: 'GET',
				});

				if (response.ok) {
					const blob = await response.blob();
					const url = window.URL.createObjectURL(blob);
					const a = document.createElement('a');
					a.href = url;
					a.download = `meeting-${meetingId}.txt`;
					document.body.appendChild(a);
					a.click();
					window.URL.revokeObjectURL(url);
					document.body.removeChild(a);
				} else {
					console.error('Download failed');
				}
			} catch (error) {
				console.error('Error downloading file:', error);
			}

			menu.classList.remove('show');
		});

		document.addEventListener('click', function (e) {
			if (!menu.contains(e.target) && !menuBtn.contains(e.target)) {
				menu.classList.remove('show');
			}
		});
	}

	// 新增 Transcript 按鈕事件
	newTranscriptBtn.addEventListener('click', async function () {
		try {
			const response = await fetch('http://localhost:8000/new_meeting', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({})
			});

			const data = await response.json();

			if (data && data.meeting_id) {
				const meetingId = data.meeting_id;
				const meetingTopic = data.topic || "Untitled Meeting";
				const meetingDate = data.date || new Date().toISOString().split('T')[0];

				console.log(`New Meeting Created - ID: ${meetingId}, Topic: ${meetingTopic}, Date: ${meetingDate}`);
				createHistoryBlock(meetingId, meetingTopic, meetingDate);
			} else {
				console.error("No meeting ID returned.");
			}
		} catch (error) {
			console.error("Error creating new meeting:", error);
		}
	});
	// 錄音相關功能
	function startWebSocket() {
		ws = new WebSocket(`ws://localhost:8000/ws/transcript/${curMeetingId}`);
		ws.onopen = () => console.log('WebSocket connected.');
		ws.onmessage = (message) => {
			console.log('Received from server:', message.data);

			const data = JSON.parse(message.data);
			const text = data.text;
			const id = data.block_id;

			const chatMessages = document.getElementById('transcriptArea');
			let existingMsgDiv = document.getElementById(`msg-${id}`);

			if (existingMsgDiv) {
				existingMsgDiv.textContent = text;
			} else {
				const serverMsgDiv = document.createElement('div');
				serverMsgDiv.className = 'server-message';
				serverMsgDiv.id = `msg-${id}`;
				serverMsgDiv.textContent = text;
				chatMessages.appendChild(serverMsgDiv);
			}

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

			mediaRecorder.start(1000);
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

	function updateRecordButtonText(isRecording) {
		if (isRecording) {
			startBtn.innerHTML = `<span class="btn-icon">■</span> <span data-i18n="stop">${currentTranslations.stop}</span>`;
		} else {
			startBtn.innerHTML = `<span class="btn-icon">●</span> <span data-i18n="record">${currentTranslations.record}</span>`;
		}
	}

	startBtn.addEventListener('click', function () {
		if (!isRecording) {
			startWebSocket();
			startStreaming();
		} else {
			stopStreaming();
			setTimeout(function () {
				ws.close();
			}, 5000);
		}
		isRecording = !isRecording;
		updateRecordButtonText(isRecording);
	});
	// Sidebar 切換功能
	toggleBtn.addEventListener('click', function () {
		sidebar.classList.toggle('collapsed');
		mainContent.classList.toggle('expanded');

		if (sidebar.classList.contains('collapsed')) {
			toggleBtn.innerHTML = '☰';
		} else {
			toggleBtn.innerHTML = '←';
		}
	});

	// Chat 相關功能
	function toggleChatPopup() {
		chatPopup.classList.toggle('show');
	}

	chatBtn.addEventListener('click', toggleChatPopup);

	closeChatBtn.addEventListener('click', (e) => {
		e.stopPropagation();
		chatPopup.classList.remove('show');
	});

	// 聊天發送功能
	sendChatBtn.addEventListener('click', async () => {
		const text = chatInput.value.trim();
		if (!text) return;

		const userMsgDiv = document.createElement('div');
		userMsgDiv.style.margin = '10px 0';
		userMsgDiv.style.fontWeight = 'bold';
		userMsgDiv.textContent = `User: ${text}`;
		chatMessages.appendChild(userMsgDiv);

		chatInput.value = '';

		const aiMsgDiv = document.createElement('div');
		aiMsgDiv.style.margin = '10px 0';
		aiMsgDiv.style.color = '#00ffcc';
		aiMsgDiv.style.fontWeight = 'bold';
		aiMsgDiv.textContent = `AI: ... (Generating response)`;
		chatMessages.appendChild(aiMsgDiv);

		chatMessages.scrollTop = chatMessages.scrollHeight;

		try {
			const response = await fetch('http://localhost:8000/chat', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					meeting_id: curMeetingId,
					prompt: text
				}),
			});

			const responseData = await response.json();

			if (responseData && responseData.result) {
				aiMsgDiv.textContent = `AI: ${responseData.result}`;
			} else {
				aiMsgDiv.textContent = `AI: (Error retrieving response)`;
			}
		} catch (error) {
			console.error("Error fetching AI response:", error);
			aiMsgDiv.textContent = `AI: (Failed to retrieve response)`;
		}

		chatMessages.scrollTop = chatMessages.scrollHeight;
	});

	// Enter 鍵發送聊天訊息
	chatInput.addEventListener('keypress', (e) => {
		if (e.key === 'Enter') {
			e.preventDefault();
			sendChatBtn.click();
		}
	});

	// Terminology 展開/收起功能
	const termBlocks = document.querySelectorAll('.term-block');
	termBlocks.forEach(block => {
		const header = block.querySelector('.term-header');
		header.addEventListener('click', () => {
			block.classList.toggle('expanded');
		});
	});

	// Fetch Transcript 功能
	async function fetchTranscript(meetingId) {
		console.log(`Fetching transcript for meeting ID: ${meetingId}`);

		try {
			const response = await fetch(`http://localhost:8000/meeting_contents/${meetingId}`);
			const data = await response.json();

			if (data && Array.isArray(data)) {
				transcriptArea.innerHTML = '';
				const blocks = {};

				data.forEach(item => {
					if (item.message.trim()) {
						if (!blocks[item.block_id]) {
							blocks[item.block_id] = [];
						}
						blocks[item.block_id].push(item.message);
					}
				});

				Object.keys(blocks).sort((a, b) => a - b).forEach(blockId => {
					const blockDiv = document.createElement('div');
					blockDiv.className = 'transcript-block';
					blockDiv.textContent = blocks[blockId].join(' ');
					transcriptArea.appendChild(blockDiv);
				});

				transcriptArea.style.display = 'block';
				terminologyList.style.display = 'block';
			} else {
				console.error("No transcript data found.");
			}
		} catch (error) {
			console.error("Error fetching transcript data:", error);
		}
	}

	// Demo 初始化
	const initializeDemo = () => {
		const trainingBlock = document.getElementById('training-wav');

		if (trainingBlock && transcriptArea && terminologyList) {
			let isShowing = false;

			trainingBlock.addEventListener('click', function (e) {
				if (e.target.classList.contains('history-menu-btn') ||
					e.target.closest('.history-menu')) {
					return;
				}

				if (!isShowing) {
					transcriptArea.style.display = 'block';
					terminologyList.style.display = 'block';
					isShowing = true;
				} else {
					transcriptArea.style.display = 'none';
					terminologyList.style.display = 'none';
					isShowing = false;
				}
			});
		}
	};

	// 初始化 Demo
	initializeDemo();
});

// 添加動畫樣式
const style = document.createElement('style');
style.textContent = `
    @keyframes highlight {
        0% { background-color: #2c2d31; }
        100% { background-color: transparent; }
    }
`;
document.head.appendChild(style);