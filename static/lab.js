// 🔬 HOLOGRAPHIC LAB LOGIC
const socket = io();

// 🌐 THREE.JS SCENE SETUP
const container = document.getElementById('canvas-container');
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, container.offsetWidth / container.offsetHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });

renderer.setSize(container.offsetWidth, container.offsetHeight);
container.appendChild(renderer.domElement);

const controls = new THREE.OrbitControls(camera, renderer.domElement);
camera.position.z = 200;

// 🔗 GRAPH DATA
let nodes = [];
let links = [];
const nodeGroup = new THREE.Group();
const linkGroup = new THREE.Group();
scene.add(nodeGroup);
scene.add(linkGroup);

// 🎨 LOAD TOPOLOGY
async function loadTopology() {
    try {
        const response = await fetch('/api/topology');
        const data = await response.json();
        renderGraph(data);
        document.getElementById('node-count').innerText = data.nodes.length;
    } catch (e) {
        console.error("Topology Load Error:", e);
    }
}

function renderGraph(data) {
    // Clear old
    while(nodeGroup.children.length) nodeGroup.remove(nodeGroup.children[0]);
    while(linkGroup.children.length) linkGroup.remove(linkGroup.children[0]);

    const nodeMap = {};

    // Create Nodes
    data.nodes.forEach(n => {
        const geometry = new THREE.SphereGeometry(2, 8, 8);
        const material = new THREE.MeshBasicMaterial({ 
            color: n.type === 'file' ? 0x00f3ff : 0xff00ff,
            transparent: true,
            opacity: 0.8
        });
        const sphere = new THREE.Mesh(geometry, material);
        
        // Random layout (Stark-style floating cloud)
        sphere.position.set(
            (Math.random() - 0.5) * 300,
            (Math.random() - 0.5) * 300,
            (Math.random() - 0.5) * 300
        );
        
        nodeGroup.add(sphere);
        nodeMap[n.id] = sphere.position;
    });

    // Create Links
    const material = new THREE.LineBasicMaterial({ color: 0x00f3ff, transparent: true, opacity: 0.2 });
    data.links.forEach(l => {
        const start = nodeMap[l.source];
        const end = nodeMap[l.target];
        if (start && end) {
            const geometry = new THREE.BufferGeometry().setFromPoints([start, end]);
            const line = new THREE.Line(geometry, material);
            linkGroup.add(line);
        }
    });
}

// 🤖 SWARM MONITOR
socket.on('agent_update', (data) => {
    // data: { agent: 'researcher'|'coder'|'sentinel', message: '...' }
    const logId = `${data.agent}-log`;
    const logEl = document.getElementById(logId);
    if (logEl) {
        const p = document.createElement('div');
        p.className = 'log-entry';
        const time = new Date().toLocaleTimeString('en-US', { hour12: false });
        p.innerHTML = `<span class="time">[${time}]</span> ${data.message}`;
        logEl.prepend(p);
        
        // Visual feedback on the graph? 
        // Maybe pulse a random node.
    }
});

// 🔄 ANIMATION LOOP
function animate() {
    requestAnimationFrame(animate);
    nodeGroup.rotation.y += 0.001;
    linkGroup.rotation.y += 0.001;
    controls.update();
    renderer.render(scene, camera);
}

window.addEventListener('resize', () => {
    camera.aspect = container.offsetWidth / container.offsetHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(container.offsetWidth, container.offsetHeight);
});

loadTopology();
animate();
