import socket
import pyautogui
import struct
from threading import Thread, Lock
import time

HOST = '0.0.0.0'
PORT = 5000
ENTRY_BORDER = 'right'

class MouseController:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.active = False
        self.lock = Lock()
        self.running = True
        
    def update_position(self, x, y):
        with self.lock:
            self.x = x
            self.y = y
            
    def get_position(self):
        with self.lock:
            return self.x, self.y
            
    def run(self):
        while self.running:
            if self.active:
                x, y = self.get_position()
                try:
                    pyautogui.moveTo(x, y)
                except:
                    pass
            time.sleep(0.001)  # Alta frequência de atualização

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

# Configuração UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HOST, PORT))
sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)  # Aumentar buffer de recepção

# Inicializa controlador de mouse em thread separada
controller = MouseController()
mouse_thread = Thread(target=controller.run)
mouse_thread.daemon = True
mouse_thread.start()

print("[Windows] Aguardando mensagens UDP...")

remote_mode = False
mac_addr = None

try:
    while True:
        data, addr = sock.recvfrom(1024)
        mac_addr = addr
        
        if not data:
            continue
            
        # Decodifica o tipo de mensagem (primeiro byte)
        msg_type = data[0]
        
        if msg_type == 0:  # EXIT_REMOTE
            remote_mode = False
            controller.active = False
            print("[Windows] Modo remoto desativado")
        elif msg_type == 1:  # ENTER_REMOTE
            remote_mode = True
            controller.active = True
            print("[Windows] Modo remoto ativado")
        elif msg_type == 2 and remote_mode:  # MOVE
            try:
                # Desempacota coordenadas (2 shorts = 4 bytes)
                x, y = struct.unpack('!HH', data[1:5])
                controller.update_position(x, y)
                
                # Verifica bordas para retornar controle
                screenWidth, screenHeight = pyautogui.size()
                if (ENTRY_BORDER == "left" and x <= 0) or \
                   (ENTRY_BORDER == "right" and x >= screenWidth - 1) or \
                   (ENTRY_BORDER == "top" and y <= 0) or \
                   (ENTRY_BORDER == "bottom" and y >= screenHeight - 1):
                    sock.sendto(b"\x00", mac_addr)  # RETURN_CONTROL
            except Exception as e:
                print("[Windows] Erro ao processar coordenadas:", e)
except KeyboardInterrupt:
    print("\n[Windows] Desligando...")
finally:
    controller.running = False
    mouse_thread.join()
    sock.close()