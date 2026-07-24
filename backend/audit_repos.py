import re

content = open('app/services/repositories/module_service.py').read()

print("=== ModuleService Direct Repository Calls Audit ===")
repos = ['_cases', '_firs', '_leads', '_signals', '_interviews', '_forensics', '_suspects', '_personnel', '_operators']

for repo in repos:
    print(f"\n--- {repo} ---")
    matches = re.finditer(f'self\.{repo}\.(list|get|list_all|list_active)\(', content)
    for m in matches:
        # Find context around the match
        start = max(0, m.start() - 50)
        end = min(len(content), m.end() + 50)
        snippet = content[start:end].replace('\n', ' ')
        print(f"Call: {m.group(0)} Context: ...{snippet}...")

print("\n=== Unrestricted SQL/DB queries ===")
db_matches = re.finditer(r'self\._db\.(query|execute)\(', content)
for m in db_matches:
    start = max(0, m.start() - 50)
    end = min(len(content), m.end() + 50)
    snippet = content[start:end].replace('\n', ' ')
    print(f"DB Call: {m.group(0)} Context: ...{snippet}...")
