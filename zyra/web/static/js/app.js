/**
 * ZYRA Web Dashboard Frontend JavaScript Application
 */

document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const chatViewport = document.getElementById("chatViewport");
    const commandInput = document.getElementById("commandInput");
    const sendBtn = document.getElementById("sendBtn");
    const micToggleBtn = document.getElementById("micToggleBtn");
    const orbContainer = document.getElementById("orbContainer");
    const voiceStatusText = document.getElementById("voiceStatusText");
    const confirmationBanner = document.getElementById("confirmationBanner");
    const confirmDescText = document.getElementById("confirmDescText");
    const btnConfirmAction = document.getElementById("btnConfirmAction");
    const btnCancelAction = document.getElementById("btnCancelAction");
    const dockSections = document.getElementById("dockSections");
    const mediaCountText = document.getElementById("mediaCountText");
    const systemStateText = document.getElementById("systemStateText");
    
    // Settings Modal Elements
    const settingsModal = document.getElementById("settingsModal");
    const openSettingsBtn = document.getElementById("openSettingsBtn");
    const closeSettingsBtn = document.getElementById("closeSettingsBtn");
    const saveSettingsBtn = document.getElementById("saveSettingsBtn");
    const ttsToggle = document.getElementById("ttsToggle");
    const startupToggle = document.getElementById("startupToggle");
    const ttsRateSlider = document.getElementById("ttsRateSlider");
    const rateValueLabel = document.getElementById("rateValueLabel");
    const apiKeyInput = document.getElementById("apiKeyInput");

    let isListening = false;
    let recognition = null;

    // --- Web Speech API Recognition ---
    if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = "en-IN";

        recognition.onstart = () => {
            isListening = true;
            micToggleBtn.classList.add("active");
            orbContainer.classList.add("listening");
            voiceStatusText.innerText = "Listening to your voice...";
        };

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            if (transcript.trim()) {
                submitCommand(transcript.trim());
            }
        };

        recognition.onerror = () => {
            stopListeningState();
        };

        recognition.onend = () => {
            stopListeningState();
        };
    }

    function stopListeningState() {
        isListening = false;
        micToggleBtn.classList.remove("active");
        orbContainer.classList.remove("listening");
        voiceStatusText.innerText = "Ready for commands";
    }

    // Toggle Mic
    micToggleBtn.addEventListener("click", () => {
        if (!recognition) {
            alert("Web Speech API is not supported in this browser. Please type commands directly.");
            return;
        }
        if (isListening) {
            recognition.stop();
        } else {
            try {
                recognition.start();
            } catch (e) {
                recognition.stop();
            }
        }
    });

    // --- Submit Command ---
    async function submitCommand(cmd) {
        if (!cmd) return;
        commandInput.value = "";
        appendMessage("user", cmd);
        scrollToBottom();

        setSystemState("Processing...", "warn");
        voiceStatusText.innerText = "FRIDAY is executing...";

        try {
            const resp = await fetch("/api/command", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ command: cmd })
            });
            const data = await resp.json();

            if (data.success) {
                appendMessage("assistant", data.response);
                if (data.pending_confirmation) {
                    showConfirmation(data.confirmation_description);
                } else {
                    hideConfirmation();
                }
            } else {
                appendMessage("assistant", "Error: " + (data.error || "Unable to execute."));
            }
        } catch (err) {
            appendMessage("assistant", "Connection error: Could not reach FRIDAY server.");
        } finally {
            setSystemState("Ready", "success");
            voiceStatusText.innerText = "Ready for commands";
            scrollToBottom();
        }
    }

    // Send on click or Enter
    sendBtn.addEventListener("click", () => {
        submitCommand(commandInput.value.trim());
    });
    commandInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            submitCommand(commandInput.value.trim());
        }
    });

    // --- Confirmation Actions ---
    async function handleConfirm(action) {
        try {
            const resp = await fetch("/api/confirm", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ action: action })
            });
            const data = await resp.json();
            hideConfirmation();
            appendMessage("assistant", data.response);
            scrollToBottom();
        } catch (err) {
            alert("Error confirming action.");
        }
    }

    btnConfirmAction.addEventListener("click", () => handleConfirm("yes"));
    btnCancelAction.addEventListener("click", () => handleConfirm("no"));

    function showConfirmation(desc) {
        confirmDescText.innerText = desc || "Action requires verification to proceed.";
        confirmationBanner.classList.remove("hidden");
    }

    function hideConfirmation() {
        confirmationBanner.classList.add("hidden");
    }

    // --- Chat Rendering ---
    function appendMessage(role, text) {
        const msgDiv = document.createElement("div");
        msgDiv.className = `message ${role === "user" ? "user-msg" : "system-msg"}`;

        const avatar = document.createElement("div");
        avatar.className = "avatar";
        avatar.innerHTML = role === "user" ? '<i class="fa-solid fa-user"></i>' : '<i class="fa-solid fa-robot"></i>';

        const bubble = document.createElement("div");
        bubble.className = "bubble";
        bubble.innerText = text;

        msgDiv.appendChild(avatar);
        msgDiv.appendChild(bubble);
        chatViewport.appendChild(msgDiv);
    }

    function scrollToBottom() {
        chatViewport.scrollTop = chatViewport.scrollHeight;
    }

    function setSystemState(text, state) {
        systemStateText.innerText = text;
        const dot = document.querySelector(".status-dot");
        if (state === "warn") {
            dot.style.background = "#ff9800";
            dot.style.boxShadow = "0 0 8px #ff9800";
        } else {
            dot.style.background = "#00e676";
            dot.style.boxShadow = "0 0 8px #00e676";
        }
    }

    // --- Load Quick Actions ---
    async function loadQuickActions() {
        try {
            const resp = await fetch("/api/quick-actions");
            const categories = await resp.json();
            dockSections.innerHTML = "";

            categories.forEach(cat => {
                const catDiv = document.createElement("div");
                catDiv.className = "dock-category";

                const title = document.createElement("h5");
                title.innerText = cat.category;
                catDiv.appendChild(title);

                const itemsDiv = document.createElement("div");
                itemsDiv.className = "dock-items";

                cat.items.forEach(item => {
                    const btn = document.createElement("button");
                    btn.className = `quick-btn ${item.risky ? "risky" : ""}`;
                    btn.innerHTML = `<i class="fa-solid fa-${item.icon}"></i> ${item.label}`;
                    btn.addEventListener("click", () => submitCommand(item.cmd));
                    itemsDiv.appendChild(btn);
                });

                catDiv.appendChild(itemsDiv);
                dockSections.appendChild(catDiv);
            });
        } catch (e) {
            console.error("Failed to load quick actions", e);
        }
    }

    // --- Load Status Polling ---
    async function updateStatus() {
        try {
            const resp = await fetch("/api/status");
            const data = await resp.json();

            if (data.media_indexer_ready) {
                mediaCountText.innerText = `${data.media_indexed_count} Media Indexed`;
            } else {
                mediaCountText.innerText = "Indexing Media...";
            }

            if (data.pending_confirmation) {
                showConfirmation(data.pending_description);
            }

            ttsToggle.checked = data.tts_enabled;
            startupToggle.checked = data.startup_enabled;
            ttsRateSlider.value = data.tts_rate;
            rateValueLabel.innerText = `${data.tts_rate} WPM`;
        } catch (e) {
            // Server offline or starting up
        }
    }

    // --- Settings Modal Handlers ---
    openSettingsBtn.addEventListener("click", () => {
        settingsModal.classList.remove("hidden");
    });
    closeSettingsBtn.addEventListener("click", () => {
        settingsModal.classList.add("hidden");
    });
    ttsRateSlider.addEventListener("input", (e) => {
        rateValueLabel.innerText = `${e.target.value} WPM`;
    });

    saveSettingsBtn.addEventListener("click", async () => {
        const payload = {
            tts_enabled: ttsToggle.checked,
            startup_enabled: startupToggle.checked,
            tts_rate: parseInt(ttsRateSlider.value, 10)
        };
        if (apiKeyInput && apiKeyInput.value.trim()) {
            payload.api_key = apiKeyInput.value.trim();
        }
        await fetch("/api/config", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        settingsModal.classList.add("hidden");
    });

    // Initial setups
    loadQuickActions();
    updateStatus();
    setInterval(updateStatus, 4000);
});
