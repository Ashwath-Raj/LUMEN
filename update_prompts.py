import os
import glob

def append_ksp_context():
    prompt_dir = r"c:\Users\jaswa\Downloads\LUMEN\LUMEN\backend\app\ai\prompts"
    ksp_context = (
        " You are assisting the Karnataka State Police (KSP). "
        "Use Indian policing terminology, BNS (Bharatiya Nyaya Sanhita) references where applicable, "
        "and consider Karnataka geography (all 31 districts, Bengaluru, Mysuru, etc.) and Indian English formatting."
    )
    
    files = glob.glob(os.path.join(prompt_dir, "*.py"))
    
    for path in files:
        if "__init__" in path:
            continue
            
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        modified = False
        for i, line in enumerate(lines):
            if line.startswith("SYSTEM_PROMPT = "):
                if "Karnataka State Police" not in line:
                    # Append right before the closing quote
                    if line.endswith('"\n'):
                        lines[i] = line[:-2] + ksp_context + '"\n'
                        modified = True
                    elif line.endswith('"\r\n'):
                        lines[i] = line[:-3] + ksp_context + '"\r\n'
                        modified = True
                        
        if modified:
            with open(path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            print(f"Modified SYSTEM_PROMPT in {path}")

if __name__ == "__main__":
    append_ksp_context()
