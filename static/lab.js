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

// 🔗 GRAPH DATA & PHYSICS
let nodes = [];
let links = [];
let nodeMeshes = {};
let linkMeshes = [];
const nodeGroup = new THREE.Group();
const linkGroup = new THREE.Group();
scene.add(nodeGroup);
scene.add(linkGroup);

// Force-Directed Simulation Variables
const repulsion = 1000;
const attraction = 0.05;
const friction = 0.9;
const centerAtk = 0.01;

// 🎨 LOAD TOPOLOGY
async function loadTopology() {
    try {
        const response = await fetch('/api/topology');
        const data = await response.json();
        nodes = data.nodes.map(n => ({
            ...n,
            x: (Math.random() - 0.5) * 400,
            y: (Math.random() - 0.5) * 400,
            z: (Math.random() - 0.5) * 400,
            vx: 0, vy: 0, vz: 0
        }));
        links = data.links;
        renderGraph();
        document.getElementById('node-count').innerText = nodes.length;
    } catch (e) {
        console.error("Topology Load Error:", e);
    }
}

function renderGraph() {
    // Clear old
    while(nodeGroup.children.length) nodeGroup.remove(nodeGroup.children[0]);
    while(linkGroup.children.length) linkGroup.remove(linkGroup.children[0]);
    nodeMeshes = {};
    linkMeshes = [];

    // Create Nodes
    nodes.forEach(n => {
        let size = 2;
        let color = 0x00f3ff; // File (Cyan)
        if (n.type === 'memory') { color = 0xff00ff; size = 1.5; } // Memory (Magenta)
        if (n.type === 'project') { color = 0xffff00; size = 5; } // Root (Yellow)

        const geometry = new THREE.SphereGeometry(size, 8, 8);
        const material = new THREE.MeshBasicMaterial({ 
            color: color,
            transparent: true,
            opacity: 0.8
        });
        const sphere = new THREE.Mesh(geometry, material);
        sphere.position.set(n.x, n.y, n.z);
        
        nodeGroup.add(sphere);
        nodeMeshes[n.id] = sphere;
    });

    // Create Links
    links.forEach(l => {
        const material = new THREE.LineBasicMaterial({ 
            color: l.type === 'import' ? 0x00f3ff : 0x555555, 
            transparent: true, 
            opacity: 0.2 
        });
        const geometry = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(), new THREE.Vector3()]);
        const line = new THREE.Line(geometry, material);
        linkGroup.add(line);
        linkMeshes.push({ line, source: l.source, target: l.target });
    });
}

// 🤖 SWARM MONITOR & NEURAL PULSE
socket.on('agent_status', (data) => {
    // data: { agent: 'planner', status: 'Thinking about X...' }
    const logId = `${data.agent}-log`;
    const logEl = document.getElementById(logId);
    if (logEl) {
        const p = document.createElement('div');
        p.className = 'log-entry';
        const time = new Date().toLocaleTimeString('en-US', { hour12: false });
        p.innerHTML = `<span class="time">[${time}]</span> ${data.status}`;
        logEl.prepend(p);
        
        // Neural Pulse: Find a node related to the agent and pulse it
        pulseAgentNode(data.agent);
    }
});

function pulseAgentNode(agentType) {
    // Find a node that matches the agent name roughly
    const targetNodeId = nodes.find(n => n.name.toLowerCase().includes(agentType))?.id || 'root';
    const mesh = nodeMeshes[targetNodeId];
    if (mesh) {
        const originalScale = mesh.scale.x;
        mesh.scale.set(3, 3, 3);
        mesh.material.opacity = 1;
        setTimeout(() => {
            mesh.scale.set(originalScale, originalScale, originalScale);
            mesh.material.opacity = 0.8;
        }, 500);
    }
}

// ⚙️ PHYSICS ENGINE (Simplified 3D Force)
function updatePhysics() {
    // 1. Repulsion
    for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
            const n1 = nodes[i];
            const n2 = nodes[j];
            const dx = n1.x - n2.x;
            const dy = n1.y - n2.y;
            const dz = n1.z - n2.z;
            const distSq = dx*dx + dy*dy + dz*dz + 0.1;
            const force = repulsion / distSq;
            const fx = (dx / Math.sqrt(distSq)) * force;
            const fy = (dy / Math.sqrt(distSq)) * force;
            const fz = (dz / Math.sqrt(distSq)) * force;
            n1.vx += fx; n1.vy += fy; n1.vz += fz;
            n2.vx -= fx; n2.vy -= fy; n2.vz -= fz;
        }
    }

    // 2. Attraction (Spring)
    links.forEach(l => {
        const s = nodes.find(n => n.id === l.source);
        const t = nodes.find(n => n.id === l.target);
        if (s && t) {
            const dx = t.x - s.x;
            const dy = t.y - s.y;
            const dz = t.z - s.z;
            s.vx += dx * attraction; s.vy += dy * attraction; s.vz += dz * attraction;
            t.vx -= dx * attraction; t.vy -= dy * attraction; t.vz -= dz * attraction;
        }
    });

    // 3. Center Gravity & Update
    nodes.forEach(n => {
        n.vx -= n.x * centerAtk;
        n.vy -= n.y * centerAtk;
        n.vz -= n.z * centerAtk;

        n.vx *= friction; n.vy *= friction; n.vz *= friction;
        n.x += n.vx; n.y += n.vy; n.z += n.vz;

        if (nodeMeshes[n.id]) {
            nodeMeshes[n.id].position.set(n.x, n.y, n.z);
        }
    });

    // 4. Update Link Lines
    linkMeshes.forEach(lm => {
        const s = nodes.find(n => n.id === lm.source);
        const t = nodes.find(n => n.id === lm.target);
        if (s && t) {
            const positions = lm.line.geometry.attributes.position.array;
            positions[0] = s.x; positions[1] = s.y; positions[2] = s.z;
            positions[3] = t.x; positions[4] = t.y; positions[5] = t.z;
            lm.line.geometry.attributes.position.needsUpdate = true;
        }
    });
}

// 🔄 ANIMATION LOOP
function animate() {
    requestAnimationFrame(animate);
    updatePhysics();
    nodeGroup.rotation.y += 0.0005;
    linkGroup.rotation.y += 0.0005;
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
