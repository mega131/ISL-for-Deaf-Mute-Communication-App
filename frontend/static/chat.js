// Global State
let socket = null;
let username = "User";
let userRole = "deaf_mute"; // 'deaf_mute' or 'hearing'
let activeRoom = "Public Room 1";

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
    setupChatControls();
    setupSpeechRecognition();
});

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
        modal.style.display = "none";
        document.querySelector(".app-layout").style.display = "flex";

        // Update sidebar display
        document.getElementById("user-display-name").textContent = username;
        const roleLabel = document.getElementById("user-display-role");
        
        // Configure layouts and settings role-specifically
        const webcamStreamImg = document.getElementById("webcam-stream");
        const drawer = document.getElementById("visualizer-drawer");
        const toggleBtn = document.getElementById("toggle-camera-btn");
        toggleBtn.style.display = "inline-flex";

        if (userRole === "deaf_mute") {
            roleLabel.textContent = "Deaf / Mute User";
            roleLabel.style.backgroundColor = "var(--accent-color)";
            
            // Deaf person needs to see webcam preview and the hearing user's camera feed
            document.getElementById("webcam-drawer-box").style.display = "flex";
            document.getElementById("hearing-webcam-box").style.display = "flex";
            document.getElementById("composer-preview").style.display = "flex";
            document.querySelector(".draft-actions").style.display = "grid";
            document.getElementById("quick-phrases-box").style.display = "block";
            
            // Set source to laptop camera feed and start prediction
            webcamStreamImg.src = "/video_feed";
            startPredictionPolling();
            
            // Show drawer by default for deaf person
            drawer.style.display = "flex";
            toggleBtn.innerHTML = `<i class="fa-solid fa-video-slash"></i> Hide Camera & Sign`;
        } else {
            roleLabel.textContent = "Hearing User";
            roleLabel.style.backgroundColor = "var(--bg-bubble-sent)";
            
            // Hearing person needs to see the deaf user's webcam preview inside the drawer
            document.getElementById("webcam-drawer-box").style.display = "flex";
            document.getElementById("hearing-webcam-box").style.display = "none";
            document.getElementById("composer-preview").style.display = "none";
            document.querySelector(".draft-actions").style.display = "none";
            document.getElementById("quick-phrases-box").style.display = "none";
            
            // Set source to laptop camera feed and start prediction polling (to see overlays)
            webcamStreamImg.src = "/video_feed";
            startPredictionPolling();
            
            // Start capturing local camera to stream back to the deaf user
            startHearingUserCamera();
            
            // Hide drawer by default for hearing person to keep mobile keyboard and layout spacious
            drawer.style.display = "none";
            toggleBtn.innerHTML = `<i class="fa-solid fa-video"></i> Show Camera & Sign`;
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

        // FEEDBACK AUTOMATION: If Deaf/Mute user receives a message from a Hearing user, automatically translate it to sign language
        if (userRole === "deaf_mute" && msg.role === "hearing" && msg.sender !== username) {
            // 1. Speak aloud
            speakMessage(msg.text);
            // 2. Play sign animation automatically
            playSignSlideshow(msg.text);
        }
    });

    socket.on("user_joined", (data) => {
        const roleStr = data.role === "deaf_mute" ? "Deaf/Mute" : "Hearing";
        addSystemMessage(`${data.username} (${roleStr}) joined the chat.`);
    });

    socket.on("chat_cleared", () => {
        document.getElementById("message-container").innerHTML = "";
        addSystemMessage("Chat history has been cleared.");
    });

    socket.on("receive_hearing_frame", (data) => {
        if (userRole === "deaf_mute") {
            const img = document.getElementById("hearing-webcam-stream");
            if (img) {
                img.src = data.frame;
            }
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
}

// Send local message
function sendMessage() {
    const inputField = document.getElementById("composer-input");
    const text = inputField.value.trim();
    if (!text) return;

    socket.emit("send_message", {
        text: text,
        sender: username,
        role: userRole
    });

    inputField.value = "";

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
            
            // Sync current draft to the input box automatically (only for Deaf/Mute user)
            if (userRole === "deaf_mute") {
                const composerInput = document.getElementById("composer-input");
                if (composerInput) {
                    composerInput.value = data.current_word;
                }
            }

            // Update prediction details
            const predChar = document.getElementById("pred-char");
            const predConf = document.getElementById("pred-conf-score");
            predChar.textContent = data.current_prediction;
            predConf.textContent = `(${Math.round(data.confidence * 100)}%)`;

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

    // Message Text
    const textSpan = document.createElement("span");
    textSpan.className = "msg-text";
    textSpan.textContent = msg.text;
    bubble.appendChild(textSpan);

    // Footer containing actions
    const footerDiv = document.createElement("div");
    footerDiv.className = "msg-footer";

    // Play Sign button
    const signBtn = document.createElement("button");
    signBtn.className = "btn-bubble-action";
    signBtn.innerHTML = `<i class="fa-solid fa-hands-asl-interpreting"></i> Sign`;
    signBtn.addEventListener("click", () => {
        playSignSlideshow(msg.text);
    });
    footerDiv.appendChild(signBtn);

    // Read Aloud button
    const speechBtn = document.createElement("button");
    speechBtn.className = "btn-bubble-action";
    speechBtn.innerHTML = `<i class="fa-solid fa-volume-high"></i> Listen`;
    speechBtn.addEventListener("click", () => {
        speakMessage(msg.text);
    });
    footerDiv.appendChild(speechBtn);

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

// 6. Text-to-Speech (Web Speech API)
function speakMessage(text) {
    if (!synth) return;
    if (synth.speaking) {
        synth.cancel();
    }
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
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

// 9. Hearing User Local Camera Streamer
function startHearingUserCamera() {
    const video = document.createElement('video');
    video.autoplay = true;
    video.playsInline = true;
    
    const canvas = document.createElement('canvas');
    canvas.width = 320;
    canvas.height = 240;
    const ctx = canvas.getContext('2d');
    
    // Attempt camera access (works in secure contexts or unsafely-treated-insecure-origins)
    navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user" },
        audio: false
    })
    .then(stream => {
        localMediaStream = stream;
        video.srcObject = stream;
        
        // Broadcast local frame over socket room at ~7 FPS
        captureInterval = setInterval(() => {
            if (video.readyState === video.HAVE_ENOUGH_DATA) {
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                const dataURL = canvas.toDataURL('image/jpeg', 0.4);
                if (socket && socket.connected) {
                    socket.emit('hearing_frame', { frame: dataURL });
                }
            }
        }, 150);
        console.log("Hearing user local camera streaming started.");
    })
    .catch(err => {
        console.error("Error accessing Hearing user camera:", err);
        addSystemMessage("Hearing user camera access blocked. To stream your face, enable camera permissions or flags.");
    });
}

function stopHearingUserCamera() {
    if (captureInterval) clearInterval(captureInterval);
    if (localMediaStream) {
        localMediaStream.getTracks().forEach(track => track.stop());
    }
    console.log("Hearing user local camera streaming stopped.");
}
