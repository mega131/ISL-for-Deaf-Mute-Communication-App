// Global State
let socket = null;
let username = "User";
let userRole = "deaf_mute"; // 'deaf_mute' or 'hearing'
let activeRoom = "Public Room 1";
let lastReceivedMessageText = "";
let lastReceivedMessageTranslated = "";

// Multilingual Configuration
let currentLang = 'en';
const SUPPORTED_LANGS = {
    'en': { name: 'English', locale: 'en-US' },
    'hi': { name: 'हिन्दी (Hindi)', locale: 'hi-IN' },
    'ta': { name: 'தமிழ் (Tamil)', locale: 'ta-IN' },
    'te': { name: 'తెలుగు (Telugu)', locale: 'te-IN' },
    'mr': { name: 'मराठी (Marathi)', locale: 'mr-IN' },
    'bn': { name: 'বাংলা (Bengali)', locale: 'bn-IN' },
    'gu': { name: 'ગુજરાતી (Gujarati)', locale: 'gu-IN' },
    'kn': { name: 'ಕನ್ನಡ (Kannada)', locale: 'kn-IN' },
    'ml': { name: 'മലയാളം (Malayalam)', locale: 'ml-IN' },
    'pa': { name: 'ਪੰਜਾਬੀ (Punjabi)', locale: 'pa-IN' },
    'es': { name: 'Español', locale: 'es-ES' },
    'fr': { name: 'Français', locale: 'fr-FR' },
    'de': { name: 'Deutsch', locale: 'de-DE' },
    'ar': { name: 'العربية', locale: 'ar-SA' }
};

function getLanguageName(code) {
    return SUPPORTED_LANGS[code] ? SUPPORTED_LANGS[code].name : (code || 'EN').toUpperCase();
}

// Webcam state polling interval
let stateInterval = null;

// Hearing user webcam streaming state
let localMediaStream = null;
let captureInterval = null;

// Speech synthesis voice
let synth = window.speechSynthesis;

// Speech recognition setup
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;
let isRecording = false;

if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.lang = 'en-US';
    recognition.interimResults = false;
}

// Sign Translation Slideshow variables
let visualizerTimer = null;
let currentPlaylist = [];
let playlistIndex = 0;
const DISPLAY_TIME = 1200; // ms per sign image

document.addEventListener("DOMContentLoaded", () => {
    setupRoleSelector();
    setupLanguageSelector();
    setupChatControls();
    setupSpeechRecognition();
    setupCallControls();
});

// Setup Language Selector dropdowns
function setupLanguageSelector() {
    const modalSelect = document.getElementById("modal-language-select");
    const appSelect = document.getElementById("app-language-select");

    if (modalSelect) {
        modalSelect.addEventListener("change", (e) => {
            currentLang = e.target.value;
            if (appSelect) appSelect.value = currentLang;
            updateLanguageSettings();
        });
    }

    if (appSelect) {
        appSelect.addEventListener("change", (e) => {
            currentLang = e.target.value;
            if (modalSelect) modalSelect.value = currentLang;
            updateLanguageSettings();
        });
    }
}

function updateLanguageSettings() {
    const config = SUPPORTED_LANGS[currentLang] || SUPPORTED_LANGS['en'];
    if (recognition) {
        recognition.lang = config.locale;
    }
    const composerInput = document.getElementById("composer-input");
    if (composerInput) {
        if (currentLang === 'hi') {
            composerInput.placeholder = "संदेश टाइप करें... (Type in English or हिन्दी)";
        } else if (currentLang === 'ta') {
            composerInput.placeholder = "செய்தியை தட்டச்சு செய்யவும்... (Type text)";
        } else if (currentLang === 'te') {
            composerInput.placeholder = "సందేశాన్ని టైప్ చేయండి... (Type text)";
        } else {
            composerInput.placeholder = `Type a message (${config.name})...`;
        }
    }
}

// 1. Role Selection Modal logic
function setupRoleSelector() {
    const modal = document.getElementById("role-modal");
    const joinBtn = document.getElementById("btn-join-chat");
    const nameInput = document.getElementById("username-input");
    const roleBtns = document.querySelectorAll(".role-btn");

    roleBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            roleBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            userRole = btn.getAttribute("data-role");
        });
    });

    joinBtn.addEventListener("click", () => {
        const inputName = nameInput.value.trim();
        if (!inputName) {
            alert("Please enter your name!");
            return;
        }

        username = inputName;
        
        // Sync selected language from modal
        const modalSelect = document.getElementById("modal-language-select");
        if (modalSelect) {
            currentLang = modalSelect.value;
            const appSelect = document.getElementById("app-language-select");
            if (appSelect) appSelect.value = currentLang;
            updateLanguageSettings();
        }

        modal.style.display = "none";
        document.querySelector(".app-layout").style.display = "flex";

        // Update sidebar display
        document.getElementById("user-display-name").textContent = username;
        const roleLabel = document.getElementById("user-display-role");
        
        // Configure layouts and settings role-specifically
        const drawer = document.getElementById("visualizer-drawer");
        const toggleBtn = document.getElementById("toggle-camera-btn");
        toggleBtn.style.display = "inline-flex";

        // Configure layout for WhatsApp Video Call Room
        document.querySelector(".videocall-container").style.display = "flex";

        if (userRole === "deaf_mute") {
            roleLabel.textContent = "Deaf / Mute User";
            roleLabel.style.backgroundColor = "var(--accent-color)";
            
            const primaryLabel = document.getElementById("primary-video-label");
            if (primaryLabel) primaryLabel.textContent = "Hearing User (Face Feed)";
            const secondaryLabel = document.getElementById("secondary-video-label");
            if (secondaryLabel) secondaryLabel.textContent = "You (Deaf/Mute Signs)";
            const overlay = document.getElementById("deaf-prediction-overlay");
            if (overlay) overlay.style.display = "flex";
            
            const preview = document.getElementById("composer-preview");
            if (preview) preview.style.display = "flex";
            const draftActions = document.querySelector(".draft-actions");
            if (draftActions) draftActions.style.display = "grid";
            const quickPhrases = document.getElementById("quick-phrases-box");
            if (quickPhrases) quickPhrases.style.display = "block";
            
            // Native OpenCV video stream runs automatically at /video_feed
            const laptopImg = document.getElementById("laptop-video-feed");
            if (laptopImg) {
                laptopImg.src = "/video_feed";
                laptopImg.style.display = "block";
            }
            const laptopPlaceholder = document.getElementById("laptop-placeholder");
            if (laptopPlaceholder) laptopPlaceholder.style.display = "none";
            
            startPredictionPolling();
            
            // Show right side visualizer drawer
            if (drawer) drawer.style.display = "flex";
            if (toggleBtn) toggleBtn.innerHTML = `<i class="fa-solid fa-video-slash"></i> Hide Normal Panel`;
        } else {
            roleLabel.textContent = "Hearing / Mobile User";
            roleLabel.style.backgroundColor = "var(--bg-bubble-sent)";
            
            const primaryLabel = document.getElementById("primary-video-label");
            if (primaryLabel) primaryLabel.textContent = "You (Hearing Face)";
            const secondaryLabel = document.getElementById("secondary-video-label");
            if (secondaryLabel) secondaryLabel.textContent = "Deaf/Mute User (Signs)";
            const overlay = document.getElementById("deaf-prediction-overlay");
            if (overlay) overlay.style.display = "flex";
            
            const preview = document.getElementById("composer-preview");
            if (preview) preview.style.display = "none";
            const draftActions = document.querySelector(".draft-actions");
            if (draftActions) draftActions.style.display = "none";
            const quickPhrases = document.getElementById("quick-phrases-box");
            if (quickPhrases) quickPhrases.style.display = "none";
            
            // Ensure live video feed is connected on mobile and laptop
            const laptopImg = document.getElementById("laptop-video-feed");
            if (laptopImg) {
                laptopImg.src = "/video_feed";
                laptopImg.style.display = "block";
            }
            const mobImg = document.getElementById("mobile-video-feed");
            if (mobImg) {
                mobImg.src = "/video_feed";
                mobImg.style.display = "block";
            }
            
            // Start prediction polling to sync prediction states
            startPredictionPolling();
            
            // Try capturing local camera for hearing user if supported
            startLocalCamera("hearing");
            
            // Show right side normal panel for hearing user as well
            if (drawer) drawer.style.display = "flex";
            if (toggleBtn) toggleBtn.innerHTML = `<i class="fa-solid fa-video-slash"></i> Hide Normal Panel`;
        }

        // On mobile/narrow screens, default to Chat & Text view
        if (window.innerWidth <= 880 || /Mobi|Android|iPhone|iPad/i.test(navigator.userAgent)) {
            const chatArea = document.querySelector(".chat-area");
            const laptopSidebar = document.getElementById("laptop-sidebar");
            const rightDrawer = document.getElementById("visualizer-drawer");
            if (chatArea) chatArea.style.display = "flex";
            if (laptopSidebar) laptopSidebar.style.display = "none";
            if (rightDrawer) rightDrawer.style.display = "none";
            
            const tabs = document.querySelectorAll(".mobile-tab-btn");
            tabs.forEach(t => t.classList.remove("active"));
            const activeTab = document.querySelector('.mobile-tab-btn[data-target="chat-area"]');
            if (activeTab) activeTab.classList.add("active");

            // If on HTTP on mobile and role is hearing, show HTTPS switcher so they can enable front camera
            if (window.location.protocol === "http:" && userRole === "hearing") {
                const httpsBanner = document.getElementById("mobile-https-banner");
                if (httpsBanner) httpsBanner.style.display = "block";
            }
        }

        // Connect to Socket.IO
        initSocket();
    });
}

// 2. Initialize Socket.IO connection
function initSocket() {
    socket = io();

    socket.on("connect", () => {
        console.log("Connected to server via WebSocket!");
        socket.emit("join", { username: username, role: userRole });
        document.getElementById("room-status").textContent = "Connected. Click on any message to see its signs.";
    });

    // Load Chat History
    socket.on("history", (history) => {
        const container = document.getElementById("message-container");
        container.innerHTML = ""; // Clear loader
        if (history.length === 0) {
            addSystemMessage("Welcome to the chat room! Send a message to start communicating.");
        } else {
            history.forEach(msg => appendMessageBubble(msg));
        }
        scrollToBottom();
    });

    socket.on("receive_message", (msg) => {
        appendMessageBubble(msg);
        scrollToBottom();

        // Update live call subtitles overlay with multilingual translation if present
        const captionText = document.getElementById("live-caption-text");
        if (captionText) {
            if (msg.translated_text && msg.translated_text !== msg.text) {
                captionText.textContent = `${msg.sender}: ${msg.text} (${msg.translated_text})`;
            } else {
                captionText.textContent = `${msg.sender}: ${msg.text}`;
            }
        }
        
        // Enable Call quick-buttons for this message
        lastReceivedMessageText = msg.text;
        lastReceivedMessageTranslated = msg.translated_text || "";
        document.getElementById("btn-call-audio").disabled = false;
        document.getElementById("btn-call-sign").disabled = false;
        document.getElementById("btn-call-read").disabled = false;

        // FEEDBACK AUTOMATION: If Deaf/Mute user receives a message from a Hearing user, automatically translate it to sign language
        if (userRole === "deaf_mute" && msg.role === "hearing" && msg.sender !== username) {
            // 1. Speak aloud (in target language if translated)
            const speakTxt = (msg.translated_text && currentLang !== 'en') ? msg.translated_text : msg.text;
            const speakLocale = (msg.translated_text && currentLang !== 'en') ? (SUPPORTED_LANGS[currentLang]?.locale || 'en-US') : 'en-US';
            speakMessage(speakTxt, speakLocale);
            // 2. Play sign animation automatically
            playSignSlideshow(msg.text);
        }
    });

    socket.on("user_joined", (data) => {
        const roleStr = data.role === "deaf_mute" ? "Deaf/Mute" : "Hearing";
        addSystemMessage(`${data.username} (${roleStr}) joined the chat.`);
        
        if (data.role === "hearing") {
            const normalPlaceholder = document.getElementById("normal-placeholder");
            const normalFeed = document.getElementById("normal-video-feed");
            if (normalPlaceholder && (!normalFeed || normalFeed.style.display === "none")) {
                normalPlaceholder.innerHTML = `
                    <i class="fa-solid fa-user-check" style="color: #38bdf8; font-size: 2.2rem;"></i>
                    <span style="color: #f1f5f9; font-weight: 600; font-size: 0.9rem;">${data.username} Joined</span>
                    <small style="color: #38bdf8;">Hearing User Active</small>
                `;
            }
        }
    });

    socket.on("chat_cleared", () => {
        document.getElementById("message-container").innerHTML = "";
        addSystemMessage("Chat history has been cleared.");
    });

    socket.on("receive_hearing_frame", (data) => {
        if (!data || !data.frame) return;
        
        // Update Normal User face video on the right panel
        const normalFeed = document.getElementById("normal-video-feed");
        if (normalFeed) {
            normalFeed.src = data.frame;
            normalFeed.style.display = "block";
            const placeholder = document.getElementById("normal-placeholder");
            if (placeholder) placeholder.style.display = "none";
        }
        // Legacy compatibility
        if (userRole === "deaf_mute") {
            const img = document.getElementById("primary-video-feed");
            if (img) img.src = data.frame;
        }
    });

    socket.on("receive_deaf_frame", (data) => {
        if (!data || !data.frame) return;
        
        // 1. Update Laptop User video on the left panel
        const laptopFeed = document.getElementById("laptop-video-feed");
        if (laptopFeed) {
            laptopFeed.src = data.frame;
            laptopFeed.style.display = "block";
            const placeholder = document.getElementById("laptop-placeholder");
            if (placeholder) placeholder.style.display = "none";
        }

        // 2. Update Mobile live video feed banner inside chat area
        const mobFeed = document.getElementById("mobile-video-feed");
        if (mobFeed) {
            mobFeed.src = data.frame;
            mobFeed.style.display = "block";
            const mobBox = document.getElementById("mobile-live-video-box");
            if (mobBox && (window.innerWidth <= 880 || /Mobi|Android|iPhone|iPad/i.test(navigator.userAgent))) {
                mobBox.style.display = "block";
            }
        }

        // 3. Legacy compatibility elements
        const secFeed = document.getElementById("secondary-video-feed");
        if (secFeed && userRole === "deaf_mute") {
            secFeed.src = data.frame;
        } else if (userRole === "hearing") {
            const priFeed = document.getElementById("primary-video-feed");
            if (priFeed) priFeed.src = data.frame;
        }
    });
}

// 3. Chat Controls & Message Sending
function setupChatControls() {
    const sendBtn = document.getElementById("btn-send-message");
    const inputField = document.getElementById("composer-input");
    const clearBtn = document.getElementById("btn-clear-chat");
    const closeVisualizerBtn = document.getElementById("close-translator-btn");

    // Send on click
    sendBtn.addEventListener("click", () => {
        sendMessage();
    });

    // Send on Enter keypress
    inputField.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            sendMessage();
        }
    });

    // Sync typed text to server's current_word buffer
    inputField.addEventListener("input", () => {
        if (userRole === "deaf_mute") {
            const val = inputField.value;
            const draftBox = document.getElementById("draft-text");
            if (draftBox) {
                draftBox.textContent = val;
            }
            fetch("/action", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ action: "set", word: val })
            }).catch(e => console.error("Error setting server word:", e));
        }
    });

    // Clear room history
    clearBtn.addEventListener("click", () => {
        if (confirm("Are you sure you want to clear chat room history for all users?")) {
            socket.emit("clear_chat");
        }
    });

    // Close translation drawer
    closeVisualizerBtn.addEventListener("click", () => {
        stopSignSlideshow();
    });

    // Toggle camera and visualizer drawer
    const toggleCamBtn = document.getElementById("toggle-camera-btn");
    const visualizerDrawer = document.getElementById("visualizer-drawer");
    toggleCamBtn.addEventListener("click", () => {
        if (visualizerDrawer.style.display === "none") {
            visualizerDrawer.style.display = "flex";
            toggleCamBtn.innerHTML = `<i class="fa-solid fa-video-slash"></i> Hide Camera & Sign`;
        } else {
            visualizerDrawer.style.display = "none";
            toggleCamBtn.innerHTML = `<i class="fa-solid fa-video"></i> Show Camera & Sign`;
        }
    });

    // Draft actions (webcam preview controls)
    document.getElementById("btn-draft-send").addEventListener("click", () => {
        sendMessage();
    });
    document.getElementById("btn-draft-add").addEventListener("click", () => {
        performDraftAction("add");
    });
    document.getElementById("btn-draft-back").addEventListener("click", () => {
        performDraftAction("backspace");
    });
    document.getElementById("btn-draft-clear").addEventListener("click", () => {
        performDraftAction("clear");
    });

    // Quick Phrases handlers (instantly send phrase text)
    const phraseBtns = document.querySelectorAll(".btn-phrase");
    phraseBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            const phrase = btn.getAttribute("data-phrase");
            if (phrase) {
                // Set the value and send
                const inputField = document.getElementById("composer-input");
                inputField.value = phrase;
                sendMessage();
            }
        });
    });
    // Mobile text composer handlers
    const mobileSendBtn = document.getElementById("btn-mobile-send");
    const mobileInput = document.getElementById("mobile-quick-input");
    if (mobileSendBtn && mobileInput) {
        mobileSendBtn.addEventListener("click", () => {
            const txt = mobileInput.value.trim();
            if (txt) {
                sendMessage(txt);
                mobileInput.value = "";
            }
        });
        mobileInput.addEventListener("keypress", (e) => {
            if (e.key === "Enter") {
                const txt = mobileInput.value.trim();
                if (txt) {
                    sendMessage(txt);
                    mobileInput.value = "";
                }
            }
        });
    }

    // Mobile quick replies chips
    const replyBtns = document.querySelectorAll(".btn-quick-reply");
    replyBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            const txt = btn.getAttribute("data-text");
            if (txt) {
                sendMessage(txt);
            }
        });
    });

    // Mobile HTTPS switcher button
    const switchHttpsBtn = document.getElementById("btn-switch-https");
    if (switchHttpsBtn) {
        switchHttpsBtn.addEventListener("click", () => {
            const host = window.location.hostname;
            // Switch to port 5001 (secure HTTPS server)
            window.location.href = `https://${host}:5001/`;
        });
    }

    // Mobile navigation tabs
    const tabBtns = document.querySelectorAll(".mobile-tab-btn");
    tabBtns.forEach(tab => {
        tab.addEventListener("click", () => {
            tabBtns.forEach(t => t.classList.remove("active"));
            tab.classList.add("active");
            const targetId = tab.getAttribute("data-target");
            
            const panels = ["laptop-sidebar", "chat-area", "visualizer-drawer"];
            panels.forEach(id => {
                const el = document.getElementById(id) || document.querySelector("." + id);
                if (el) {
                    if (id === targetId || el.classList.contains(targetId)) {
                        el.style.display = "flex";
                    } else {
                        el.style.display = "none";
                    }
                }
            });
        });
    });
}

// Send local message (supports main input or direct custom text)
function sendMessage(overrideText) {
    const inputField = document.getElementById("composer-input");
    const text = (typeof overrideText === "string" ? overrideText : (inputField ? inputField.value : "")).trim();
    if (!text) return;

    socket.emit("send_message", {
        text: text,
        sender: username,
        role: userRole,
        target_lang: currentLang
    });

    if (typeof overrideText !== "string" && inputField) {
        inputField.value = "";
    }

    // If Deaf/Mute user, clear the server-side text buffer as well
    if (userRole === "deaf_mute") {
        performDraftAction("clear");
    }
}

// Perform actions on the webcam text compilation buffer
function performDraftAction(actionType) {
    fetch("/action", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: actionType })
    })
    .then(res => res.json())
    .then(data => {
        document.getElementById("draft-text").textContent = data.current_word;
        // Also keep sync with composer input if editing (only for Deaf/Mute user)
        if (userRole === "deaf_mute") {
            document.getElementById("composer-input").value = data.current_word;
        }
    });
}

// 4. Polling Webcam Sign Language Predictor State
let jsLastPred = "?";
let jsStableSince = null;

function startPredictionPolling() {
    if (stateInterval) clearInterval(stateInterval);
    
    stateInterval = setInterval(() => {
        fetch("/state")
        .then(res => res.json())
        .then(data => {
            // Update draft box
            const draftBox = document.getElementById("draft-text");
            draftBox.textContent = data.current_word;
            
            // Sync current draft to the input box automatically (only for Deaf/Mute user when not active typing/focusing)
            if (userRole === "deaf_mute") {
                const composerInput = document.getElementById("composer-input");
                if (composerInput && document.activeElement !== composerInput) {
                    composerInput.value = data.current_word;
                }
            }

            // Update prediction details
            const predChar = document.getElementById("pred-char");
            const predConf = document.getElementById("pred-conf-score");
            if (predChar) predChar.textContent = data.current_prediction;
            if (predConf) predConf.textContent = `(${Math.round(data.confidence * 100)}%)`;

            // Also update mobile live banner prediction HUD
            const mobChar = document.getElementById("mobile-pred-char");
            const mobConf = document.getElementById("mobile-pred-conf");
            if (mobChar) mobChar.textContent = data.current_prediction;
            if (mobConf) mobConf.textContent = `(${Math.round(data.confidence * 100)}%)`;

            // Local stability loader calculations
            const curPred = data.current_prediction;
            const bar = document.getElementById("autofill-bar");
            
            if (curPred !== "?") {
                if (curPred !== jsLastPred) {
                    jsLastPred = curPred;
                    jsStableSince = Date.now();
                    bar.style.width = "0%";
                } else {
                    const elapsed = (Date.now() - jsStableSince) / 1000;
                    const progress = Math.min(1.0, elapsed / 1.5);
                    bar.style.width = `${progress * 100}%`;
                }
            } else {
                jsLastPred = "?";
                jsStableSince = null;
                bar.style.width = "0%";
            }
        })
        .catch(err => console.log("State polling error:", err));
    }, 200);
}

// 5. DOM Rendering Helper functions
function appendMessageBubble(msg) {
    const container = document.getElementById("message-container");
    const isMe = msg.sender === username;
    
    const bubble = document.createElement("div");
    bubble.className = `msg-bubble ${isMe ? 'sent' : 'recv'}`;
    
    // Sender Name
    const senderSpan = document.createElement("span");
    senderSpan.className = "msg-sender";
    senderSpan.textContent = isMe ? "You" : msg.sender;
    bubble.appendChild(senderSpan);

    // Message Text (Original)
    const textSpan = document.createElement("span");
    textSpan.className = "msg-text";
    textSpan.textContent = msg.text;
    bubble.appendChild(textSpan);

    // Multilingual Translation Container
    const transDiv = document.createElement("div");
    transDiv.className = "msg-translation-box";
    let activeTranslation = msg.translated_text || "";

    function renderTranslationUI() {
        if (activeTranslation && activeTranslation.trim() !== msg.text.trim()) {
            const langCode = msg.target_lang || currentLang;
            transDiv.innerHTML = `<span class="trans-pill"><i class="fa-solid fa-language"></i> ${getLanguageName(langCode)}</span> <span class="trans-content">${activeTranslation}</span>`;
            transDiv.style.display = "flex";
        } else {
            transDiv.style.display = "none";
        }
    }
    renderTranslationUI();
    bubble.appendChild(transDiv);

    // Footer containing actions
    const footerDiv = document.createElement("div");
    footerDiv.className = "msg-footer";

    // Play Sign button
    const signBtn = document.createElement("button");
    signBtn.className = "btn-bubble-action";
    signBtn.innerHTML = `<i class="fa-solid fa-hands-asl-interpreting"></i> Sign`;
    signBtn.title = "View ISL sign animation";
    signBtn.addEventListener("click", () => {
        playSignSlideshow(msg.text);
    });
    footerDiv.appendChild(signBtn);

    // Read Aloud / Listen button (Speaks translated voice if active)
    const speechBtn = document.createElement("button");
    speechBtn.className = "btn-bubble-action";
    speechBtn.innerHTML = `<i class="fa-solid fa-volume-high"></i> Listen`;
    speechBtn.title = "Listen to audio aloud";
    speechBtn.addEventListener("click", () => {
        if (activeTranslation && transDiv.style.display !== "none" && currentLang !== 'en') {
            const locale = SUPPORTED_LANGS[currentLang]?.locale || 'en-US';
            speakMessage(activeTranslation, locale);
        } else {
            speakMessage(msg.text, 'en-US');
        }
    });
    footerDiv.appendChild(speechBtn);

    // On-demand Multilingual Translate button
    const transBtn = document.createElement("button");
    transBtn.className = "btn-bubble-action";
    transBtn.innerHTML = `<i class="fa-solid fa-language"></i> Translate`;
    transBtn.title = "Translate message";
    transBtn.addEventListener("click", () => {
        if (activeTranslation && transDiv.style.display !== "none") {
            transDiv.style.display = "none";
        } else {
            transBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Translating...`;
            fetch("/translate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text: msg.text, target_lang: currentLang })
            })
            .then(res => res.json())
            .then(data => {
                activeTranslation = data.translated;
                msg.target_lang = currentLang;
                msg.translated_text = data.translated;
                renderTranslationUI();
                transBtn.innerHTML = `<i class="fa-solid fa-language"></i> Translate`;
            })
            .catch(err => {
                console.error("Translation request error:", err);
                transBtn.innerHTML = `<i class="fa-solid fa-language"></i> Translate`;
            });
        }
    });
    footerDiv.appendChild(transBtn);

    // Time
    const timeSpan = document.createElement("span");
    timeSpan.className = "msg-time";
    timeSpan.textContent = msg.time;
    footerDiv.appendChild(timeSpan);

    bubble.appendChild(footerDiv);
    container.appendChild(bubble);
}

function addSystemMessage(text) {
    const container = document.getElementById("message-container");
    const bubble = document.createElement("div");
    bubble.className = "msg-system";
    bubble.textContent = text;
    container.appendChild(bubble);
    scrollToBottom();
}

function scrollToBottom() {
    const container = document.getElementById("message-container");
    container.scrollTop = container.scrollHeight;
}

// 6. Text-to-Speech (Web Speech API) with Multi-language Voice support
function speakMessage(text, langLocale = 'en-US') {
    if (!synth) return;
    if (synth.speaking) {
        synth.cancel();
    }
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.lang = langLocale;

    // Pick best matching native voice if available in user's browser
    const voices = synth.getVoices();
    if (voices && voices.length > 0) {
        const langPrefix = langLocale.split('-')[0].toLowerCase();
        const matchedVoice = voices.find(v => v.lang.toLowerCase().startsWith(langPrefix));
        if (matchedVoice) {
            utterance.voice = matchedVoice;
        }
    }
    synth.speak(utterance);
}

// 7. Speech Recognition (Speech-to-Text) for Hearing Users
function setupSpeechRecognition() {
    const micBtn = document.getElementById("btn-mic-composer");
    const inputField = document.getElementById("composer-input");

    if (!recognition) {
        micBtn.style.display = "none"; // Hide button if API is not supported in current browser
        const composerOptions = document.querySelector(".composer-options");
        if (composerOptions) {
            composerOptions.style.display = "none";
        }
        return;
    }

    recognition.onstart = () => {
        isRecording = true;
        micBtn.classList.add("recording");
        micBtn.innerHTML = `<i class="fa-solid fa-microphone-slash"></i>`;
        inputField.placeholder = "Listening... speak clearly.";
    };

    recognition.onend = () => {
        isRecording = false;
        micBtn.classList.remove("recording");
        micBtn.innerHTML = `<i class="fa-solid fa-microphone"></i>`;
        inputField.placeholder = "Type a message...";
    };

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        inputField.value = transcript;
        inputField.focus();
        
        // Auto-send if the Speak & Send option is checked
        const speakSendCheckbox = document.getElementById("chk-speak-send");
        if (speakSendCheckbox && speakSendCheckbox.checked) {
            sendMessage();
        }
    };

    recognition.onerror = (e) => {
        console.error("Speech Recognition Error:", e);
        recognition.stop();
    };

    micBtn.addEventListener("click", () => {
        if (isRecording) {
            recognition.stop();
        } else {
            recognition.start();
        }
    });
}

// 8. Sign Language Playlist Player (Text-to-Sign slideshow)
function playSignSlideshow(text) {
    stopSignSlideshow(); // Reset active playbacks

    // Auto-open visualizer drawer if closed
    const drawer = document.getElementById("visualizer-drawer");
    if (drawer && drawer.style.display === "none") {
        drawer.style.display = "flex";
        const toggleCamBtn = document.getElementById("toggle-camera-btn");
        if (toggleCamBtn) {
            toggleCamBtn.innerHTML = `<i class="fa-solid fa-video-slash"></i> Hide Camera & Sign`;
        }
    }

    if (!text.trim()) return;

    // Show the floating translation card overlay
    document.getElementById("sign-visualizer-box").style.display = "flex";

    document.getElementById("playback-text").textContent = text;
    document.getElementById("visualizer-img").style.display = "none";
    document.getElementById("visualizer-video").style.display = "none";
    document.getElementById("visualizer-placeholder").style.display = "flex";
    document.getElementById("placeholder-char").textContent = "...";

    // Call backend to compile the playlist of signs (words and fallbacks)
    fetch("/text_to_sign", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: text })
    })
    .then(res => res.json())
    .then(data => {
        currentPlaylist = data.playlist || [];
        playlistIndex = 0;
        if (currentPlaylist.length === 0) {
            stopSignSlideshow();
            return;
        }
        nextSignFrame();
    })
    .catch(err => {
        console.error("Error fetching signs:", err);
        stopSignSlideshow();
    });
}

function nextSignFrame() {
    const img = document.getElementById("visualizer-img");
    const video = document.getElementById("visualizer-video");
    const placeholder = document.getElementById("visualizer-placeholder");

    if (playlistIndex >= currentPlaylist.length) {
        // Playback finished, reset visuals to done
        document.getElementById("visualizer-progress-bar").style.width = "100%";
        img.style.display = "none";
        video.style.display = "none";
        video.src = "";
        placeholder.style.display = "flex";
        document.getElementById("placeholder-char").textContent = "✓";
        document.getElementById("playback-char").textContent = "Done";
        return;
    }

    const item = currentPlaylist[playlistIndex];
    document.getElementById("playback-char").textContent = item.label;
    document.getElementById("playback-index").textContent = `${playlistIndex + 1} / ${currentPlaylist.length}`;

    // Update progress bar
    const progressPercent = (playlistIndex / currentPlaylist.length) * 100;
    document.getElementById("visualizer-progress-bar").style.width = `${progressPercent}%`;

    const isVideo = item.file.toLowerCase().endsWith('.mp4');

    if (isVideo) {
        // Hide image and placeholder, show video
        img.style.display = "none";
        placeholder.style.display = "none";
        video.style.display = "block";
        
        video.onended = () => {
            video.onended = null;
            video.onerror = null;
            playlistIndex++;
            nextSignFrame();
        };
        video.onerror = () => {
            console.error("Video load error for:", item.file);
            video.onended = null;
            video.onerror = null;
            playlistIndex++;
            nextSignFrame();
        };
        
        video.src = `/signs/${item.file}`;
        video.load();
        video.play().catch(e => {
            console.warn("Video autoplay blocked by browser policy, using timeout fallback.", e);
            // Fallback for autoplay blocks
            if (visualizerTimer) clearTimeout(visualizerTimer);
            visualizerTimer = setTimeout(() => {
                video.onended = null;
                video.onerror = null;
                playlistIndex++;
                nextSignFrame();
            }, 3000);
        });
    } else {
        // Hide video, show image
        video.style.display = "none";
        video.src = "";
        
        const tempImg = new Image();
        tempImg.onload = () => {
            img.src = `/signs/${item.file}`;
            img.style.display = "block";
            placeholder.style.display = "none";
        };
        tempImg.onerror = () => {
            img.style.display = "none";
            placeholder.style.display = "flex";
            document.getElementById("placeholder-char").textContent = item.label;
        };
        tempImg.src = `/signs/${item.file}`;

        playlistIndex++;
        const delay = (item.type === "word") ? 2000 : DISPLAY_TIME;
        if (visualizerTimer) clearTimeout(visualizerTimer);
        visualizerTimer = setTimeout(nextSignFrame, delay);
    }
}

function stopSignSlideshow() {
    if (visualizerTimer) {
        clearTimeout(visualizerTimer);
        visualizerTimer = null;
    }
    
    // Stop and clear video element
    const video = document.getElementById("visualizer-video");
    if (video) {
        video.pause();
        video.src = "";
        video.style.display = "none";
        video.onended = null;
        video.onerror = null;
    }
    
    currentPlaylist = [];
    playlistIndex = 0;
    
    // Hide the floating translation card overlay
    document.getElementById("sign-visualizer-box").style.display = "none";
    
    document.getElementById("visualizer-progress-bar").style.width = "0%";
    document.getElementById("visualizer-img").style.display = "none";
    const placeholder = document.getElementById("visualizer-placeholder");
    placeholder.style.display = "flex";
    document.getElementById("placeholder-char").textContent = "?";
    document.getElementById("playback-text").textContent = "-";
    document.getElementById("playback-char").textContent = "-";
    document.getElementById("playback-index").textContent = "0 / 0";
}

// 9. Hearing / Local Camera Streamer
async function startLocalCamera(roleType) {
    stopLocalCamera();

    const isMobile = /Mobi|Android|iPhone|iPad/i.test(navigator.userAgent);

    // Check if getUserMedia is supported
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        console.log("navigator.mediaDevices is not available in this context (e.g. mobile HTTP). Text Mode Active.");
        if (window.location.protocol === "http:" && (isMobile || window.innerWidth <= 880)) {
            const httpsBanner = document.getElementById("mobile-https-banner");
            if (httpsBanner) httpsBanner.style.display = "block";
        }
        const status = document.getElementById("room-status");
        if (status) {
            status.textContent = "Connected. Mobile Text Mode Active — watch live signs and send messages.";
        }
        return;
    }

    const video = document.createElement('video');
    video.autoplay = true;
    video.playsInline = true;
    video.setAttribute('playsinline', '');
    video.muted = true;
    
    const canvas = document.createElement('canvas');
    canvas.width = 320;
    canvas.height = 240;
    const ctx = canvas.getContext('2d');

    // Prioritize front-facing user camera for mobile phones
    const constraintList = isMobile ? [
        { video: { facingMode: "user" }, audio: false },
        { video: { facingMode: { ideal: "user" }, width: { ideal: 480 } }, audio: false },
        { video: true, audio: false }
    ] : [
        { video: { width: { ideal: 640 }, height: { ideal: 480 } }, audio: false },
        { video: true, audio: false },
        { video: { facingMode: "user" }, audio: false }
    ];

    let stream = null;
    let lastError = null;

    for (const constraints of constraintList) {
        try {
            stream = await navigator.mediaDevices.getUserMedia(constraints);
            if (stream) break;
        } catch (err) {
            lastError = err;
        }
    }

    if (!stream) {
        console.log("Front face camera could not be started for hearing user (Text mode active):", lastError);
        const status = document.getElementById("room-status");
        if (status) {
            status.textContent = "Connected. Mobile Texting Active — watch live signs and send messages.";
        }
        return;
    }

    localMediaStream = stream;
    video.srcObject = stream;
    try {
        await video.play();
    } catch(e) {
        console.warn("Video play exception:", e);
    }
    
    // Hide https banner if active
    const httpsBanner = document.getElementById("mobile-https-banner");
    if (httpsBanner) httpsBanner.style.display = "none";

    // Show self PiP on mobile so the user can see their own face
    const selfPip = document.getElementById("mobile-self-pip");
    if (selfPip) selfPip.style.display = "block";

    // Clear any previous error banner
    const status = document.getElementById("room-status");
    if (status && status.textContent.includes("Camera")) {
        status.textContent = "Camera active. Click on any message to see its signs.";
    }

    // Define capture frame rate and target socket event
    const emitEventName = (roleType === "deaf_mute") ? "deaf_frame" : "hearing_frame";
    const intervalMs = 150; // ~7 FPS for smooth mobile face streaming
    
    captureInterval = setInterval(() => {
        if (video.readyState >= 2) {
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            const dataURL = canvas.toDataURL('image/jpeg', 0.45);
            if (socket && socket.connected) {
                socket.emit(emitEventName, { frame: dataURL });
            }
            
            // For hearing users, show their own local stream on the normal face frame
            if (roleType === "hearing") {
                const normalImg = document.getElementById("normal-video-feed");
                if (normalImg) {
                    normalImg.src = dataURL;
                    normalImg.style.display = "block";
                    const placeholder = document.getElementById("normal-placeholder");
                    if (placeholder) placeholder.style.display = "none";
                }
                const mobileSelfImg = document.getElementById("mobile-self-feed");
                if (mobileSelfImg) {
                    mobileSelfImg.src = dataURL;
                }
                const selfImg = document.getElementById("secondary-video-feed");
                if (selfImg) {
                    selfImg.src = dataURL;
                }
            }
        }
    }, intervalMs);
    console.log(`Local camera streaming started for ${roleType} role.`);
}

function stopLocalCamera() {
    if (captureInterval) clearInterval(captureInterval);
    if (localMediaStream) {
        localMediaStream.getTracks().forEach(track => track.stop());
    }
    console.log("Local camera streaming stopped.");
}

function showCameraWarning(customMsg) {
    const status = document.getElementById("room-status");
    if (status) {
        status.innerHTML = `
            <span style="color: #ff5555; font-weight: bold; display: inline-flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                <i class="fa-solid fa-triangle-exclamation"></i> ${customMsg || "Camera in use or permission denied."}
                <button type="button" id="btn-retry-camera" class="btn btn-outline" style="padding: 2px 8px; font-size: 0.72rem; color: #ff5555; border-color: #ff5555; cursor: pointer; border-radius: 6px;">
                    <i class="fa-solid fa-rotate-right"></i> Retry Camera
                </button>
            </span>
        `;
        const retryBtn = document.getElementById("btn-retry-camera");
        if (retryBtn) {
            retryBtn.addEventListener("click", () => {
                status.textContent = "Connecting to camera...";
                stopLocalCamera();
                startLocalCamera(userRole);
            });
        }
    }
}

// 10. WhatsApp call screen buttons control
function setupCallControls() {
    const audioBtn = document.getElementById("btn-call-audio");
    const signBtn = document.getElementById("btn-call-sign");
    const readBtn = document.getElementById("btn-call-read");

    audioBtn.addEventListener("click", () => {
        if (lastReceivedMessageText) {
            const txt = (lastReceivedMessageTranslated && currentLang !== 'en') ? lastReceivedMessageTranslated : lastReceivedMessageText;
            const locale = (lastReceivedMessageTranslated && currentLang !== 'en') ? (SUPPORTED_LANGS[currentLang]?.locale || 'en-US') : 'en-US';
            speakMessage(txt, locale);
        }
    });

    signBtn.addEventListener("click", () => {
        if (lastReceivedMessageText) {
            playSignSlideshow(lastReceivedMessageText);
        }
    });

    readBtn.addEventListener("click", () => {
        if (lastReceivedMessageText) {
            showLargeReadOverlay(lastReceivedMessageText);
        }
    });
}

function showLargeReadOverlay(text) {
    let overlay = document.getElementById("read-focus-overlay");
    if (!overlay) {
        overlay = document.createElement("div");
        overlay.id = "read-focus-overlay";
        overlay.style.cssText = "position:fixed;top:0;left:0;width:100vw;height:100vh;background:rgba(15,23,42,0.95);display:flex;flex-direction:column;justify-content:center;align-items:center;z-index:9999;padding:40px;";
        
        const textBox = document.createElement("div");
        textBox.id = "read-focus-text";
        textBox.style.cssText = "font-size:2.8rem;font-weight:700;color:#f8fafc;text-align:center;max-width:800px;line-height:1.4;margin-bottom:40px;word-break:break-word;";
        overlay.appendChild(textBox);
        
        const closeBtn = document.createElement("button");
        closeBtn.className = "btn btn-primary";
        closeBtn.innerHTML = '<i class="fa-solid fa-circle-xmark"></i> Close';
        closeBtn.style.padding = "15px 30px";
        closeBtn.style.fontSize = "1.2rem";
        closeBtn.addEventListener("click", () => {
            overlay.style.display = "none";
        });
        overlay.appendChild(closeBtn);
        
        document.body.appendChild(overlay);
    }
    
    document.getElementById("read-focus-text").textContent = text;
    overlay.style.display = "flex";
}

// Cleanup camera streams on page unload/refresh
window.addEventListener('beforeunload', () => {
    stopLocalCamera();
});
window.addEventListener('pagehide', () => {
    stopLocalCamera();
});

