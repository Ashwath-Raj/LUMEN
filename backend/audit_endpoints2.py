import os, re
from collections import defaultdict

routers_dir = 'app/api/routers'
endpoints = []

for f in os.listdir(routers_dir):
    if f.endswith('.py'):
        content = open(os.path.join(routers_dir, f)).read()
        router_prefix = ""
        m = re.search(r'APIRouter\(prefix=["\']([^"\']+)["\']', content)
        if m: router_prefix = m.group(1)
        
        matches = re.findall(r'@router\.(get|post|put|delete)\(\s*[\'\"]([^\'\"]+)[\'\"]\s*\)\s*def\s+([a-zA-Z0-9_]+)\(.*?_op\s*=\s*Depends\(get_current_operator\).*?\):([\s\S]*?)(?=@router|$)', content)
        
        for method, path, func_name, body in matches:
            full_path = router_prefix + path
            service_calls = re.findall(r'ModuleService.*?\.([a-zA-Z0-9_]+)', body)
            endpoints.append((f, method.upper(), full_path, func_name, service_calls))

print("=== PROTECTED ENDPOINTS AND MODULE SERVICE CALLS ===")
for f, method, path, func_name, calls in sorted(endpoints, key=lambda x: x[2]):
    print(f"{f:18} | {method:6} | {path:35} | {func_name:25} | {calls}")
