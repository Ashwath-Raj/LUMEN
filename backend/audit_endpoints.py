import os, re
routers_dir = 'app/api/routers'
for f in os.listdir(routers_dir):
    if f.endswith('.py'):
        content = open(os.path.join(routers_dir, f)).read()
        endpoints = re.findall(r'@router\.(get|post|put|delete)\(\s*[\'\"]([^\'\"]+)[\'\"]\s*\)\s*def\s+([a-zA-Z0-9_]+)\(.*?\):([\s\S]*?)(?=@router|$)', content)
        for method, path, func_name, body in endpoints:
            if any(k in path.lower() or k in func_name.lower() for k in ['case', 'fir', 'signal', 'intelligence', 'lead', 'hotspot']):
                service_calls = re.findall(r'ModuleService.*?\.([a-zA-Z0-9_]+)', body)
                print(f"{f} | {method.upper()} {path} | {func_name} | {service_calls}")
