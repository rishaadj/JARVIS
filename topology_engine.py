import os
import json
from datetime import datetime

class TopologyEngine:
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.ignored_dirs = {'.git', '__pycache__', 'node_modules', 'model', 'screenshots'}
        self.ignored_files = {'.env', 'audit.log', 'semantic_index.json', 'jarvis_memory.json'}

    def _extract_imports(self, file_path):
        """Extracts local imports from a Python file."""
        import re
        imports = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                patterns = [
                    r"^from\s+([a-zA-Z0-9_\.]+)\s+import",
                    r"^import\s+([a-zA-Z0-9_\.,\s]+)$"
                ]
                for p in patterns:
                    matches = re.findall(p, content, re.MULTILINE)
                    for m in matches:
                        parts = [x.strip().split('.')[0] for x in m.split(',')]
                        imports.extend(parts)
        except:
            pass
        return list(set(imports))

    def get_topology(self):
        nodes = []
        links = []
        
        file_map = {}
        name_map = {}
        counter = 0
        
        file_list = []
        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in self.ignored_dirs]
            for file in files:
                if file in self.ignored_files or file.endswith(('.pyc', '.tmp', '.log')):
                    continue
                rel_path = os.path.relpath(os.path.join(root, file), self.root_dir)
                file_list.append((rel_path, file, os.path.join(root, file)))

        for rel_path, file_name, full_path in file_list:
            file_id = f"file_{counter}"
            file_map[rel_path] = file_id
            
            module_name = os.path.splitext(file_name)[0]
            name_map[module_name] = file_id
            
            nodes.append({
                "id": file_id,
                "name": file_name,
                "type": "file",
                "path": rel_path,
                "size": os.path.getsize(full_path)
            })
            counter += 1

        for rel_path, file_name, full_path in file_list:
            if not file_name.endswith('.py'):
                continue
            source_id = file_map[rel_path]
            found_imports = self._extract_imports(full_path)
            for imp in found_imports:
                if imp in name_map:
                    target_id = name_map[imp]
                    if source_id != target_id:
                        links.append({"source": source_id, "target": target_id, "type": "import"})

        memory_path = os.path.join(self.root_dir, "semantic_index.json")
        if os.path.exists(memory_path):
            try:
                with open(memory_path, "r") as f:
                    memories = json.load(f)
                    for i, mem in enumerate(memories[:12]):
                        mem_id = f"mem_{i}"
                        nodes.append({
                            "id": mem_id,
                            "name": mem['metadata'].get('text', 'Memory')[:30] + "...",
                            "type": "memory",
                            "timestamp": mem['metadata'].get('timestamp')
                        })
                        for rel_path, f_id in file_map.items():
                            if os.path.splitext(os.path.basename(rel_path))[0] in mem['metadata'].get('text', ''):
                                links.append({"source": mem_id, "target": f_id, "type": "context"})
            except:
                pass

        project_node = {"id": "root", "name": "JARVIS_CORE", "type": "project"}
        nodes.insert(0, project_node)
        
        connected_ids = set()
        for l in links:
            connected_ids.add(l['source'])
            connected_ids.add(l['target'])

        for n in nodes:
            if n['id'] != 'root' and n['id'] not in connected_ids:
                links.append({"source": "root", "target": n['id'], "type": "structure"})

        return {"nodes": nodes, "links": links}

if __name__ == "__main__":
    te = TopologyEngine(os.getcwd())
    print(json.dumps(te.get_topology(), indent=2))
