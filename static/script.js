/* ===========================================================
   JARVIS HUD — Controller Script
   Deep Integration: State sync, telemetry, voice reactivity
   =========================================================== */

const socket = io();

// === DOM REFS ===
const transcript   = document.getElementById('transcript');
const userInput     = document.getElementById('user-input');
const sendBtn       = document.getElementById('send-btn');
const thinking      = document.getElementById('thinking-indicator');
const neuralState   = document.getElementById('neural-state');
const coreStateLabel = document.getElementById('core-state-label');
const coreStateSub  = document.getElementById('core-state-sub');

// === STATE ===
let cmdHistory = [];
let historyIdx = -1;
let processingStartTs = null;
const startTime = Date.now();

// =============================================================
//  1. CLOCK / UPTIME
// =============================================================
setInterval(() => {
    const now = new Date();
    const el = document.getElementById('live-time');
    const ms = document.getElementById('live-millis');
    if (el) el.textContent = now.toLocaleTimeString('en-US', { hour12: false });
    if (ms) ms.textContent = '.' + now.getMilliseconds().toString().padStart(3, '0');

    const d = Date.now() - startTime;
    const h = String(Math.floor(d / 3600000)).padStart(2, '0');
    const m = String(Math.floor((d % 3600000) / 60000)).padStart(2, '0');
    const s = String(Math.floor((d % 60000) / 1000)).padStart(2, '0');
    const u = document.getElementById('uptime-val');
    if (u) u.textContent = `${h}:${m}:${s}`;
}, 200);

// =============================================================
//  2. TRANSCRIPT HELPERS
// =============================================================
function typeMessage(text, className) {
    const p = document.createElement('p');
    p.className = className;
    transcript.appendChild(p);

    let i = 0;
    const speed = Math.max(8, Math.min(20, 800 / text.length)); // Adaptive speed
    const interval = setInterval(() => {
        p.textContent = text.slice(0, i);
        i++;
        transcript.scrollTop = transcript.scrollHeight;
        if (i > text.length) clearInterval(interval);
    }, speed);
}

function addUser(text) {
    const p = document.createElement('p');
    p.className = 'user-msg';
    p.textContent = `> ${text}`;
    transcript.appendChild(p);
    transcript.scrollTop = transcript.scrollHeight;
}

function addSystemLog(msg) {
    const p = document.createElement('p');
    p.className = 'system-msg';
    const t = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
    p.innerHTML = `<span class="log-time">[${t}]</span> <span class="log-tag">SYS//</span> ${msg}`;
    transcript.appendChild(p);
    transcript.scrollTop = transcript.scrollHeight;
}

// =============================================================
//  3. SEND / INPUT HANDLING
// =============================================================
function sendMessage() {
    const text = userInput.value.trim();
    if (!text) return;

    addUser(text);
    thinking.classList.remove('hidden');
    socket.emit('ui_command', text);

    cmdHistory.push(text);
    historyIdx = cmdHistory.length;
    userInput.value = '';
}

sendBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') { sendMessage(); return; }
    if (e.key === 'ArrowUp') {
        if (historyIdx > 0) { historyIdx--; userInput.value = cmdHistory[historyIdx]; }
        e.preventDefault();
    }
    if (e.key === 'ArrowDown') {
        if (historyIdx < cmdHistory.length - 1) { historyIdx++; userInput.value = cmdHistory[historyIdx]; }
        else { historyIdx = cmdHistory.length; userInput.value = ''; }
        e.preventDefault();
    }
});

// =============================================================
//  4. CORE STATE MANAGEMENT (Deep HUD Integration)
// =============================================================
const STATE_MAP = {
    processing: { label: 'PROCESSING',  sub: 'Neural pathway active...', neural: 'THINK_CYCLE ACTIVE', bodyClass: 'state-thinking' },
    action:     { label: 'EXECUTING',   sub: 'Skill dispatch in progress', neural: 'EXECUTOR ENGAGED', bodyClass: 'state-action' },
    speaking:   { label: 'SPEAKING',    sub: 'Audio synthesis active', neural: 'VOICE OUTPUT ACTIVE', bodyClass: 'state-speaking' },
    idle:       { label: 'STANDBY',     sub: 'GEMINI-2.5-FLASH-LITE // READY', neural: 'NEURAL LINK ESTABLISHED', bodyClass: '' },
};

function setHUDState(state) {
    const cfg = STATE_MAP[state] || STATE_MAP.idle;
    const body = document.body;

    // Remove old state classes
    Object.values(STATE_MAP).forEach(s => { if (s.bodyClass) body.classList.remove(s.bodyClass); });

    // Apply new
    if (cfg.bodyClass) body.classList.add(cfg.bodyClass);
    if (coreStateLabel) coreStateLabel.textContent = cfg.label;
    if (coreStateSub) coreStateSub.textContent = cfg.sub;
    if (neuralState) neuralState.textContent = cfg.neural;

    // Thinking indicator
    if (state === 'processing') {
        thinking.classList.remove('hidden');
    } else {
        thinking.classList.add('hidden');
    }
}

// =============================================================
//  5. SOCKET EVENT HANDLERS
// =============================================================

// --- Messages ---
socket.on('new_message', (data) => {
    if (data.sender === 'jarvis') {
        setHUDState('idle');
        typeMessage(`JARVIS >> ${data.text}`, 'jarvis-msg');
    } else if (data.sender === 'user') {
        addUser(data.text);
    }
});

socket.on('system_log', (msg) => {
    addSystemLog(msg);
});

// --- State Changes ---
socket.on('state_change', (state) => {
    if (state === 'processing') {
        processingStartTs = Date.now();
        setHUDState('processing');
    } else if (state === 'action') {
        setHUDState('action');
    } else {
        // Compute latency
        if (processingStartTs) {
            const ms = Date.now() - processingStartTs;
            const el = document.getElementById('latency-val');
            if (el) el.textContent = `${ms}ms`;
            processingStartTs = null;
        }
        setHUDState('idle');
    }
});

// --- System Metrics ---
function clamp(n, lo, hi) { return Math.max(lo, Math.min(hi, n)); }

socket.on('system_status', (data) => {
    const s = data && data.status ? data.status : null;
    if (!s) return;

    const cpu = clamp(Number(s.cpu || 0), 0, 100);
    const ram = clamp(Number(s.ram || 0), 0, 100);

    const cpuBar = document.getElementById('cpu-bar');
    const memBar = document.getElementById('mem-bar');
    const cpuVal = document.getElementById('cpu-val');
    const memVal = document.getElementById('mem-val');

    if (cpuBar) {
        cpuBar.style.width = `${cpu}%`;
        cpuBar.className = `fill ${cpu > 90 ? 'critical' : cpu > 70 ? 'warning' : ''}`;
    }
    if (memBar) {
        memBar.style.width = `${ram}%`;
        memBar.className = `fill ${ram > 90 ? 'critical' : ram > 70 ? 'warning' : ''}`;
    }
    if (cpuVal) cpuVal.textContent = `${cpu}%`;
    if (memVal) memVal.textContent = `${ram}%`;

    // Battery
    if (s.battery) {
        const b = s.battery;
        const battBar = document.getElementById('batt-bar');
        const battVal = document.getElementById('batt-val');
        if (battBar) battBar.style.width = `${b.percent}%`;
        if (battVal) battVal.textContent = `${b.percent}%${b.power_plugged ? ' AC' : ''}`;
    }

    // Overall status
    const statusEl = document.getElementById('status-text');
    if (statusEl) {
        if (cpu > 90 || ram > 90) {
            statusEl.textContent = 'CRITICAL';
            statusEl.style.color = 'var(--accent-pink)';
        } else {
            statusEl.textContent = 'ONLINE';
            statusEl.style.color = '';
        }
    }
});

// --- Voice Level (Arc Reactor Reactivity) ---
socket.on('voice_level', (data) => {
    const level = data.level || 0;
    const core = document.querySelector('.core-circle');
    const glow = document.getElementById('core-glow');
    const rings = document.querySelectorAll('.ring');

    if (level > 5) setHUDState('speaking');

    if (core) {
        const r = 28 + (level / 8);
        core.setAttribute('r', r);
    }

    if (glow) {
        glow.style.opacity = 0.3 + (level / 150);
        glow.style.filter = `blur(${30 + level / 4}px)`;
    }

    rings.forEach((ring, i) => {
        const extra = level / (250 + i * 60);
        ring.style.opacity = 0.25 + extra;
    });
});

// --- Visual Awareness ---
socket.on('visual_awareness', (data) => {
    const img = document.getElementById('last-scan-img');
    const ctx = document.getElementById('observer-context');
    if (img && data.image_path) img.src = data.image_path + '?t=' + Date.now();
    if (ctx && data.context) ctx.textContent = data.context;
});

// --- Gesture Status ---
socket.on('gesture_status', (data) => {
    const dot = document.getElementById('gesture-dot');
    if (!dot) return;
    if (data.status === 'TRACKING') {
        dot.classList.add('online');
    } else {
        dot.classList.remove('online');
    }
});

// --- Agent Status ---
socket.on('agent_status', (data) => {
    const li = document.querySelector(`li[data-agent="${data.agent}"]`);
    if (!li) return;
    const dot = li.querySelector('.status-dot');
    const isActive = data.status.toLowerCase().includes('active') || data.status.toLowerCase().includes('new goal');
    if (isActive) {
        dot.classList.add('online');
        li.classList.add('active');
    } else {
        dot.classList.remove('online');
        li.classList.remove('active');
    }
});

// --- Auth (Legacy Support) ---
socket.on('auth_success', () => {
    const overlay = document.getElementById('auth-overlay');
    if (overlay) overlay.style.display = 'none';
    localStorage.setItem('jarvis_auth', 'true');
});
socket.on('auth_failure', () => {});
if (localStorage.getItem('jarvis_auth') === 'true') {
    const overlay = document.getElementById('auth-overlay');
    if (overlay) overlay.style.display = 'none';
}

// =============================================================
//  6. SIMULATED DATA STREAM (Makes HUD feel alive)
// =============================================================
const DATA_STREAM_LINES = [
    'ACK >> Neural handshake verified',
    'SYNC >> Memory buffer: 12.4MB / 128MB',
    'PING >> Gemini endpoint latency: 42ms',
    'SCAN >> Filesystem watcher: 3 active hooks',
    'CORE >> Priority queue depth: 0',
    'AUTH >> Session token valid [exp: 23:59]',
    'VOSK >> Recognition model: en-IN-16kHz',
    'AUDIO >> edge-tts voice: en-GB-RyanNeural',
    'SAFE >> Environment: DEVELOPMENT',
    'SKILL >> 26 modules loaded (0 errors)',
    'SYNC >> Episodic memory: 847 entries',
    'NET >> Network interface: connected',
    'GPU >> Compute: integrated (MediaPipe ready)',
    'TICK >> Autonomous loop: 1.2s interval',
];

function startDataStream() {
    const el = document.getElementById('data-stream');
    if (!el) return;

    let lines = [];
    setInterval(() => {
        const line = DATA_STREAM_LINES[Math.floor(Math.random() * DATA_STREAM_LINES.length)];
        const t = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
        lines.push(`[${t}] ${line}`);
        if (lines.length > 6) lines.shift();
        el.textContent = lines.join('\n');
    }, 3000);
}

startDataStream();

// =============================================================
//  7. UTILITY FUNCTIONS
// =============================================================
function hapticFeedback(ms = 50) {
    if (window.navigator && window.navigator.vibrate) {
        window.navigator.vibrate(ms);
    }
}

function emergencyHalt() {
    if (confirm('INITIATE_SYSTEM_HALT? All active tasks will be terminated.')) {
        socket.emit('ui_command', 'Emergency Halt: Shutdown all processes');
        hapticFeedback(200);
    }
}