# WINDOWS (Cliente)
import socket
import pyautogui

HOST = '0.0.0.0'
PORT = 5000
ENTRY_BORDER = 'right'

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'

local_ip = get_local_ip()
print(f"[Windows] IP da máquina: {local_ip}:{PORT}")

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((HOST, PORT))
sock.listen(1)
print("[Windows] Aguardando conexão...")
conn, addr = sock.accept()
print(f"[Windows] Conectado ao {addr}")

remote_mode = False
buffer = ""

screenWidth, screenHeight = pyautogui.size()

while True:
    try:
        chunk = conn.recv(1024).decode()
        if not chunk:
            break

        buffer += chunk
        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            data = line.strip()

            if data == "ENTER_REMOTE":
                remote_mode = True
                print("[Windows] Modo remoto ativado")
            elif data == "EXIT_REMOTE":
                remote_mode = False
                print("[Windows] Modo remoto desativado")
            elif data.startswith("MOVE_NORM:") and remote_mode:
                try:
                    coords = data[10:].split(',')
                    norm_x, norm_y = float(coords[0]), float(coords[1])
                    x = int(norm_x * screenWidth)
                    y = int(norm_y * screenHeight)
                    print(f"[Windows] Posicionando mouse em ({x}, {y})")
                    pyautogui.moveTo(x, y)

                    # Verifica borda de saída
                    if ENTRY_BORDER == "left" and x <= 0:
                        conn.send(b"RETURN_CONTROL\n")
                    elif ENTRY_BORDER == "right" and x >= screenWidth - 1:
                        conn.send(b"RETURN_CONTROL\n")
                    elif ENTRY_BORDER == "top" and y <= 0:
                        conn.send(b"RETURN_CONTROL\n")
                    elif ENTRY_BORDER == "bottom" and y >= screenHeight - 1:
                        conn.send(b"RETURN_CONTROL\n")
                except Exception as e:
                    print("[Windows] Erro ao processar MOVE_NORM:", e)
    except Exception as e:
        print("[Windows] Erro geral:", e)
        break

conn.close()
sock.close()
