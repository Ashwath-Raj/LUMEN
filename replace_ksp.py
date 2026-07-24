import os

# The mapping from generic to KSP
MAPPING = {
    "Sector 7G Industrial": "Peenya Industrial Area",
    "Sector 7G, Auxiliary Access Point Alpha": "Peenya Industrial Area, Checkpoint Alpha",
    "Sector 7G": "Peenya Industrial Area",
    "Lower Docks": "Mangaluru Port",
    "Transit Hub North": "Majestic Bus Station",
    "Transit Hub": "Majestic Bus Station",
    "Northside Residential": "Malleshwaram Residential",
    "Northside Industrial": "Peenya Industrial Area",
    "Old Town Commercial": "KR Market",
    "East Canal District": "Indiranagar",
    "District 8": "South Division",
    "District 4": "East Division",
    "Sector 07 Alpha": "Central Division",
    "Jonathan Vance": "R. Sunil Kumar",
    "Sarah Chen": "N. Anjali",
    "Elias Vance": "Rahul Shetty",
    "Marcus Thorne": "Harish Gowda",
    "Elena Rostova": "Priya Desai",
    "James Holden": "Vikram Patil",
    "OP-NIGHTFALL": "OP-KAVACHA",
    "Patrol Unit 7": "Hoysala Patrol 7",
    "Const. R. Hutherford": "PC R. Ramesh",
    "Sgt. M. Chen": "PSI M. Anjali",
    "Chief Inspector": "Circle Inspector (CI)",
    "Senior Intelligence Analyst": "Inspector General of Police (IGP)",
    "Signal Intelligence Officer": "Deputy Superintendent of Police (DySP)",
    "Field Ops Analyst": "Police Sub-Inspector (PSI)",
    "Data Correlation Specialist": "Assistant Sub-Inspector (ASI)",
    "Vance, Elias": "Shetty, Rahul",
    "Chen, Sarah": "Anjali, N.",
}

# Apply replacements to all files in the given extensions
def apply_replacements():
    extensions = ['.js', '.jsx', '.py']
    
    # Exclude directories
    exclude_dirs = ['node_modules', '.venv', '.git', 'alembic', '__pycache__']

    files_to_process = []
    
    base_dir = r"c:\Users\jaswa\Downloads\LUMEN\LUMEN"
    
    for root, dirs, files in os.walk(base_dir):
        # modify dirs in place to skip excluded dirs
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                files_to_process.append(os.path.join(root, file))

    modified_count = 0
    for path in files_to_process:
        if "replace_ksp.py" in path:
            continue
            
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        new_content = content
        # Ensure we process longer strings first to avoid partial replacements!
        sorted_keys = sorted(MAPPING.keys(), key=len, reverse=True)
        
        for k in sorted_keys:
            new_content = new_content.replace(k, MAPPING[k])
            
        if new_content != content:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Modified: {path}")
            modified_count += 1
            
    print(f"Total files modified: {modified_count}")

if __name__ == "__main__":
    apply_replacements()
