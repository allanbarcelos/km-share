import socket
import pyautogui

HOST = '0.0.0.0'  # Escuta em todas as interfaces
PORT = 5000
ENTRY_BORDER = 'right'  # Borda de entrada/saída

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

# Socket UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HOST, PORT))
print("[Windows] Aguardando mensagens UDP...")

remote_mode = False
mac_addr = None  # Guarda o endereço do Mac para respostas

while True:
    try:
        data, addr = sock.recvfrom(1024)  # UDP: recvfrom()
        data = data.decode().strip()
        mac_addr = addr  # Atualiza o endereço do Mac

        if data == "ENTER_REMOTE":
            remote_mode = True
            print("[Windows] Modo remoto ativado")
        elif data == "EXIT_REMOTE":
            remote_mode = False
            print("[Windows] Modo remoto desativado")
        elif data.startswith("MOVE:") and remote_mode:
            try:
                coords = data[5:].split(',')
                x, y = int(coords[0]), int(coords[1])
                pyautogui.moveTo(x, y)

                # Verifica se o mouse saiu da tela (retorna controle)
                screenWidth, screenHeight = pyautogui.size()
                if ENTRY_BORDER == "left" and x <= 0:
                    sock.sendto(b"RETURN_CONTROL", mac_addr)  # UDP: sendto()
                elif ENTRY_BORDER == "right" and x >= screenWidth - 1:
                    sock.sendto(b"RETURN_CONTROL", mac_addr)
                elif ENTRY_BORDER == "top" and y <= 0:
                    sock.sendto(b"RETURN_CONTROL", mac_addr)
                elif ENTRY_BORDER == "bottom" and y >= screenHeight - 1:
                    sock.sendto(b"RETURN_CONTROL", mac_addr)
            except Exception as e:
                print("[Windows] Erro ao mover mouse:", e)
    except Exception as e:
        print("[Windows] Erro geral:", e)
        break

sock.close()