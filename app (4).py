"""Serves the Exfiltration Sentinel dashboard on port 8086.

Run:  python app.py        (or: uvicorn app:app --port 8086)
Open: http://localhost:8086
"""
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse

BASE = Path(__file__).parent
app = FastAPI(title="Exfiltration Sentinel")


@app.get("/")
def index():
    return FileResponse(BASE / "index.html")


@app.get("/health")
def health():
    return {"status": "ok", "port": 8086}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8086)
