# --------------------
# WINDOWS (Cliente)
# --------------------
# Requisitos:
# pip install pyautogui

import socket
import pyautogui

HOST = '0.0.0.0'
PORT = 5000
ENTRY_BORDER = 'right'  # onde "sai" para o Mac

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((HOST, PORT))
sock.listen(1)
print("[Windows] Aguardando conexão...")
conn, addr = sock.accept()
print(f"[Windows] Conectado ao {addr}")

remote_mode = False

while True:
    try:
        data = conn.recv(1024).decode().strip()
        if not data:
            break

        if data == "ENTER_REMOTE":
            remote_mode = True
            print("[Windows] Modo remoto ativado")
        elif data == "EXIT_REMOTE":
            remote_mode = False
            print("[Windows] Modo remoto desativado")
        elif data.startswith("MOVE:") and remote_mode:
            coords = data[5:].split(',')
            x, y = int(coords[0]), int(coords[1])
            pyautogui.moveTo(x, y)

            # Detecta se saiu da tela (para retornar ao Mac)
            screenWidth, screenHeight = pyautogui.size()
            if ENTRY_BORDER == "left" and x <= 0:
                conn.send(b"RETURN_CONTROL\n")
            elif ENTRY_BORDER == "right" and x >= screenWidth - 1:
                conn.send(b"RETURN_CONTROL\n")
            elif ENTRY_BORDER == "top" and y <= 0:
                conn.send(b"RETURN_CONTROL\n")
            elif ENTRY_BORDER == "bottom" and y >= screenHeight - 1:
                conn.send(b"RETURN_CONTROL\n")
    except Exception as e:
        print("[Windows] Erro:", e)
        break

conn.close()
sock.close()
