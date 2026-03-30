import os
import json
from datetime import datetime

class TopologyEngine:
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.ignored_dirs = {'.git', '__pycache__', 'node_modules', 'model', 'screenshots'}
        self.ignored_files = {'.env', 'audit.log', 'semantic_index.json', 'jarvis_memory.json'}

    def get_topology(self):
        nodes = []
        links = []
        
        # 📂 File System Nodes
        file_map = {} # path -> id
        counter = 0
        
        for root, dirs, files in os.walk(self.root_dir):
            # Prune ignored directories
            dirs[:] = [d for d in dirs if d not in self.ignored_dirs]
            
            for file in files:
                if file in self.ignored_files or file.endswith(('.pyc', '.tmp', '.log')):
                    continue
                    
                rel_path = os.path.relpath(os.path.join(root, file), self.root_dir)
                file_id = f"file_{counter}"
                file_map[rel_path] = file_id
                
                nodes.append({
                    "id": file_id,
                    "name": file,
                    "type": "file",
                    "path": rel_path,
                    "size": os.path.getsize(os.path.join(root, file))
                })
                counter += 1

        # 🧠 Semantic Memory Nodes (Simplified)
        memory_path = os.path.join(self.root_dir, "semantic_index.json")
        if os.path.exists(memory_path):
            try:
                with open(memory_path, "r") as f:
                    memories = json.load(f)
                    for i, mem in enumerate(memories[:10]): # Limit to latest 10 for viz clarity
                        mem_id = f"mem_{i}"
                        nodes.append({
                            "id": mem_id,
                            "name": mem['metadata'].get('text', 'Memory')[:30] + "...",
                            "type": "memory",
                            "timestamp": mem['metadata'].get('timestamp')
                        })
                        # Link memories to files they might mention (crude heuristic)
                        for rel_path, f_id in file_map.items():
                            if file_id.split('.')[0] in mem['metadata'].get('text', ''):
                                links.append({"source": mem_id, "target": f_id, "type": "mention"})
            except:
                pass

        # 🔗 Folder Structure Links
        # (This creates a tree-like backbone for the graph)
        # Note: For a "Twin" look, we just link everything to common parent or project root
        project_node = {"id": "root", "name": "JARVIS_CORE", "type": "project"}
        nodes.append(project_node)
        
        for n in nodes:
            if n['id'] != 'root':
                links.append({"source": "root", "target": n['id'], "type": "contains"})

        return {"nodes": nodes, "links": links}

if __name__ == "__main__":
    te = TopologyEngine(os.getcwd())
    print(json.dumps(te.get_topology(), indent=2))
