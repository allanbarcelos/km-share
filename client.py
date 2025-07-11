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
        self.button_states = {'left': False, 'right': False, 'middle': False}
        
    def update_position(self, x, y):
        with self.lock:
            self.x = x
            self.y = y
            
    def update_button(self, button, state):
        with self.lock:
            btn_name = {
                1: 'left',
                2: 'right',
                3: 'middle'
            }.get(button, None)
            if btn_name:
                self.button_states[btn_name] = bool(state)
            
    def get_state(self):
        with self.lock:
            return self.x, self.y, self.button_states.copy()
            
    def run(self):
        prev_states = {'left': False, 'right': False, 'middle': False}
        while self.running:
            if self.active:
                x, y, curr_states = self.get_state()
                
                # Movimento
                try:
                    pyautogui.moveTo(x, y)
                except:
                    pass
                
                # Cliques
                for btn in ['left', 'right', 'middle']:
                    if curr_states[btn] != prev_states[btn]:
                        if curr_states[btn]:
                            pyautogui.mouseDown(button=btn)
                        else:
                            pyautogui.mouseUp(button=btn)
                        prev_states[btn] = curr_states[btn]
            
            time.sleep(0.001)

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
print(f"[Windows] IP: {local_ip}:{PORT}")

# Configuração UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HOST, PORT))
sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)

# Inicializa controlador
controller = MouseController()
mouse_thread = Thread(target=controller.run)
mouse_thread.daemon = True
mouse_thread.start()

print("[Windows] Aguardando mensagens...")

remote_mode = False
mac_addr = None

try:
    while True:
        data, addr = sock.recvfrom(1024)
        mac_addr = addr
        
        if not data:
            continue
            
        msg_type = data[0]
        
        if msg_type == 0:  # EXIT_REMOTE
            remote_mode = False
            controller.active = False
        elif msg_type == 1:  # ENTER_REMOTE
            remote_mode = True
            controller.active = True
        elif msg_type == 2 and remote_mode:  # MOVE
            x, y = struct.unpack('!HH', data[1:5])
            controller.update_position(x, y)
            
            # Verifica bordas
            screenWidth, screenHeight = pyautogui.size()
            if (ENTRY_BORDER == "left" and x <= 0) or \
               (ENTRY_BORDER == "right" and x >= screenWidth - 1) or \
               (ENTRY_BORDER == "top" and y <= 0) or \
               (ENTRY_BORDER == "bottom" and y >= screenHeight - 1):
                sock.sendto(b"\x00", mac_addr)
        elif msg_type == 3 and remote_mode:  # CLICK
            button, state = struct.unpack('!BB', data[1:3])
            controller.update_button(button, state)
            
except KeyboardInterrupt:
    print("\n[Windows] Desligando...")
finally:
    controller.running = False
    mouse_thread.join()
    sock.close()