import os

def search_generic():
    extensions = ['.js', '.jsx', '.py', '.md']
    exclude_dirs = ['node_modules', '.venv', '.git', 'alembic', '__pycache__', 'dist']
    keywords = ["Sector 7G", "Lower Docks", "Transit Hub", "OP-NIGHTFALL", "Jonathan Vance", "Sarah Chen", "District 8"]
    
    base_dir = r"c:\Users\jaswa\Downloads\LUMEN\LUMEN"
    
    found = False
    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                path = os.path.join(root, file)
                if "search_generic.py" in path or "replace_ksp.py" in path or "update_prompts.py" in path:
                    continue
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        for i, line in enumerate(lines):
                            for kw in keywords:
                                if kw in line:
                                    print(f"Match found in {path}:{i+1}: {line.strip()}")
                                    found = True
                except Exception as e:
                    pass
    if not found:
        print("No matches found. Codebase is clean.")

if __name__ == "__main__":
    search_generic()
