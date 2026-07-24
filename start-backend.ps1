# LUMEN — Start both servers in split terminals
# Usage: run each block in a separate PowerShell terminal

# Terminal 1 — FastAPI backend
Write-Host "Starting FastAPI backend on http://localhost:8000" -ForegroundColor Cyan
Set-Location api
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 — Vite frontend
# Set-Location ../client
# npm run dev
