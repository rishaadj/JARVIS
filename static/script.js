const socket = io();

const transcript = document.getElementById('transcript');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const thinking = document.getElementById('thinking-indicator');

let history = [];
let historyIndex = -1;

// For HUD latency measurement: time from "processing" -> next jarvis response.
let processingStartTs = null;

// CLOCK & UPTIME
const startTime = Date.now();
setInterval(() => {
    const now = new Date();
    document.getElementById('live-time').innerText = now.toLocaleTimeString('en-US', { hour12: false });

    const uptimeMs = Date.now() - startTime;
    const hours = Math.floor(uptimeMs / 3600000).toString().padStart(2, '0');
    const mins = Math.floor((uptimeMs % 3600000) / 60000).toString().padStart(2, '0');
    const secs = Math.floor((uptimeMs % 60000) / 1000).toString().padStart(2, '0');
    document.getElementById('uptime-val').innerText = `${hours}h ${mins}m ${secs}s`;
}, 1000);

// TYPE EFFECT FOR JARVIS
function typeMessage(text, className) {
    const p = document.createElement('p');
    p.className = className;
    transcript.appendChild(p);

    let i = 0;
    const interval = setInterval(() => {
        p.textContent = text.slice(0, i);
        i++;
        transcript.scrollTop = transcript.scrollHeight;
        if (i > text.length) clearInterval(interval);
    }, 15);
}

// ADD USER MESSAGE TO UI
function addUser(text) {
    const p = document.createElement('p');
    p.className = 'user-msg';
    p.innerText = `SR_INPUT >> ${text}`;
    transcript.appendChild(p);
    transcript.scrollTop = transcript.scrollHeight;
}

// SEND COMMAND TO BACKEND
function sendMessage() {
    const text = userInput.value.trim();
    if (!text) return;

    // UI Updates
    addUser(text);
    thinking.classList.remove('hidden');

    // Emit to Python 'ui_command'
    socket.emit('ui_command', text);

    // History Logic
    history.push(text);
    historyIndex = history.length;
    userInput.value = '';
}

sendBtn.onclick = sendMessage;

userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});

// HISTORY NAVIGATION (Arrow keys)
userInput.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowUp') {
        if (historyIndex > 0) {
            historyIndex--;
            userInput.value = history[historyIndex];
        }
    }
    if (e.key === 'ArrowDown') {
        if (historyIndex < history.length - 1) {
            historyIndex++;
            userInput.value = history[historyIndex];
        } else {
            userInput.value = '';
        }
    }
});

// SOCKET LISTENERS
socket.on('new_message', (data) => {
    if (data.sender === 'jarvis') {
        thinking.classList.add('hidden'); // Hide indicator when response arrives
        typeMessage(`JARVIS >> ${data.text}`, 'jarvis-msg');
    } else if (data.sender === 'user') {
        addUser(data.text);
    }
});

socket.on('system_log', (msg) => {
    const p = document.createElement('p');
    p.className = 'system-msg';
    const time = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
    p.innerHTML = `<span class="log-time">[${time}]</span> <span class="log-tag">SYS//</span> ${msg}`;
    transcript.appendChild(p);
    transcript.scrollTop = transcript.scrollHeight;
});

socket.on('state_change', (state) => {
    console.log("Core State Change:", state);
    const body = document.body;
    body.className = body.className.replace(/\bstate-\S+/g, ''); // Clean old state classes
    
    if (state === 'processing') {
        processingStartTs = Date.now();
        thinking.classList.remove('hidden');
        body.classList.add('state-thinking');
    } else if (state === 'action') {
        body.classList.add('state-action');
    } else {
        if (processingStartTs) {
            const ms = Date.now() - processingStartTs;
            const latencyEl = document.getElementById('latency-val');
            if (latencyEl) latencyEl.innerText = `${ms}ms`;
        }
        processingStartTs = null;
        thinking.classList.add('hidden');
        body.classList.remove('state-thinking', 'state-action');
    }
});

// VISUAL AWARENESS (NEW)
socket.on('visual_awareness', (data) => {
    const imgEl = document.getElementById('last-scan-img');
    const ctxEl = document.getElementById('observer-context');
    
    if (imgEl && data.image_path) {
        imgEl.src = data.image_path + "?t=" + Date.now(); // Cache bust
    }
    
    if (ctxEl && data.context) {
        ctxEl.innerText = data.context;
    }
});

// GESTURE STATUS (NEW)
socket.on('gesture_status', (data) => {
    const dot = document.getElementById('gesture-dot');
    if (!dot) return;
    
    if (data.status === 'TRACKING') {
        if (!dot.classList.contains('online')) {
            dot.classList.add('online');
            dot.style.background = 'var(--accent-pink)';
            hapticFeedback(100);
        }
    } else {
        dot.classList.remove('online');
        dot.style.background = '#333';
    }
});

function clamp(n, min, max) {
    return Math.max(min, Math.min(max, n));
}

socket.on('system_status', (data) => {
    // Expected payload: { status: { cpu: number, ram: number, battery: {percent, power_plugged} | null } }
    const status = data && data.status ? data.status : null;
    if (!status) return;

    const cpu = clamp(Number(status.cpu || 0), 0, 100);
    const ram = clamp(Number(status.ram || 0), 0, 100);

    const cpuFill = document.getElementById('cpu-bar');
    const memFill = document.getElementById('mem-bar');
    if (cpuFill) cpuFill.style.width = `${cpu}%`;
    if (memFill) memFill.style.width = `${ram}%`;

    const statusText = document.getElementById('status-text');
    if (statusText) {
        const critical = cpu > 90 || ram > 90;
        statusText.innerText = critical ? 'CRITICAL' : 'ACTIVE';
    }
});

// 🛡️ Milestone 4: AUTH & REMOTE
let currentPin = "";
const authOverlay = document.getElementById('auth-overlay');
const pinDisplay = document.getElementById('pin-display');

function addPin(num) {
    if (currentPin.length < 4) {
        currentPin += num;
        updatePinDisplay();
        hapticFeedback();
    }
}

function clearPin() {
    currentPin = "";
    updatePinDisplay();
    hapticFeedback();
}

function updatePinDisplay() {
    pinDisplay.innerText = "*".repeat(currentPin.length) || "****";
}

function checkPin() {
    socket.emit('verify_pin', { pin: currentPin });
    hapticFeedback();
}

socket.on('auth_success', () => {
    authOverlay.style.display = 'none';
    localStorage.setItem('jarvis_auth', 'true');
});

socket.on('auth_failure', () => {
    currentPin = "";
    updatePinDisplay();
    alert("ACCESS_DENIED: Invalid Credentials");
});

// Auto-unlock if previously authed (simpler UX for same device)
if (localStorage.getItem('jarvis_auth') === 'true') {
    authOverlay.style.display = 'none';
}

function emergencyHalt() {
    if (confirm("INITIATE_SYSTEM_HALT? All active tasks will be terminated.")) {
        socket.emit('ui_command', "Emergency Halt: Shutdown all processes");
        hapticFeedback(200);
    }
}

function hapticFeedback(ms = 50) {
    if (window.navigator && window.navigator.vibrate) {
        window.navigator.vibrate(ms);
    }
}