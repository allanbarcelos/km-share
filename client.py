import socket
import pyautogui
import struct
from threading import Thread, Lock
import time

# Configuração de segurança
pyautogui.FAILSAFE = False
SAFE_BORDER = 50

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
        self.scroll_queue = []
        
    def update_position(self, x, y):
        with self.lock:
            screen_width, screen_height = pyautogui.size()
            self.x = max(SAFE_BORDER, min(x, screen_width - SAFE_BORDER))
            self.y = max(SAFE_BORDER, min(y, screen_height - SAFE_BORDER))
            
    def update_button(self, button, state):
        with self.lock:
            btn_name = {
                1: 'left',
                2: 'right',
                3: 'middle'
            }.get(button, None)
            if btn_name:
                self.button_states[btn_name] = bool(state)
    
    def add_scroll(self, amount):
        with self.lock:
            self.scroll_queue.append(amount)
            
    def get_state(self):
        with self.lock:
            scrolls = sum(self.scroll_queue) if self.scroll_queue else 0
            self.scroll_queue.clear()
            return self.x, self.y, self.button_states.copy(), scrolls
            
    def run(self):
        prev_states = {'left': False, 'right': False, 'middle': False}
        while self.running:
            if self.active:
                x, y, curr_states, scroll_amount = self.get_state()
                
                # Movimento
                try:
                    pyautogui.moveTo(x, y, _pause=False)
                except Exception as e:
                    print(f"[Erro] Movimento: {e}")
                
                # Cliques
                for btn in ['left', 'right', 'middle']:
                    if curr_states[btn] != prev_states[btn]:
                        try:
                            if curr_states[btn]:
                                pyautogui.mouseDown(button=btn, _pause=False)
                            else:
                                pyautogui.mouseUp(button=btn, _pause=False)
                        except Exception as e:
                            print(f"[Erro] Clique {btn}: {e}")
                        finally:
                            prev_states[btn] = curr_states[btn]
                
                # Scroll
                if scroll_amount:
                    try:
                        pyautogui.scroll(scroll_amount, _pause=False)
                    except Exception as e:
                        print(f"[Erro] Scroll: {e}")
            
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

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HOST, PORT))
sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)

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
            print("[Windows] Modo remoto desativado")
        elif msg_type == 1:  # ENTER_REMOTE
            remote_mode = True
            controller.active = True
            print("[Windows] Modo remoto ativado")
        elif msg_type == 2 and remote_mode:  # MOVE
            try:
                x, y = struct.unpack('!HH', data[1:5])
                controller.update_position(x, y)
                
                screen_width, screen_height = pyautogui.size()
                if (ENTRY_BORDER == "left" and x <= SAFE_BORDER) or \
                   (ENTRY_BORDER == "right" and x >= screen_width - SAFE_BORDER) or \
                   (ENTRY_BORDER == "top" and y <= SAFE_BORDER) or \
                   (ENTRY_BORDER == "bottom" and y >= screen_height - SAFE_BORDER):
                    sock.sendto(b"\x00", mac_addr)
            except Exception as e:
                print(f"[Erro] Movimento recebido: {e}")
        elif msg_type == 3 and remote_mode:  # CLICK
            try:
                button, state = struct.unpack('!BB', data[1:3])
                controller.update_button(button, state)
            except Exception as e:
                print(f"[Erro] Clique recebido: {e}")
        elif msg_type == 4 and remote_mode:  # SCROLL
            try:
                amount = struct.unpack('!h', data[1:3])[0]
                controller.add_scroll(amount)
            except Exception as e:
                print(f"[Erro] Scroll recebido: {e}")
            
except KeyboardInterrupt:
    print("\n[Windows] Desligando...")
except Exception as e:
    print(f"[Erro Fatal] {e}")
finally:
    controller.running = False
    mouse_thread.join()
    sock.close()