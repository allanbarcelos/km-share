import socket
import time
import Quartz
from pynput import keyboard, mouse
import struct

# Configurações
WINDOWS_HOST = '192.168.8.108'
PORT = 5000
EXIT_BORDER = 'left'
UPDATE_INTERVAL = 0.005

# Tela principal
screen = Quartz.CGDisplayBounds(Quartz.CGMainDisplayID())
SCREEN_WIDTH = int(screen.size.width)
SCREEN_HEIGHT = int(screen.size.height)

REMOTE_MODE = False
MAC_CLICK_STATE = {'left': False, 'right': False, 'middle': False}

# Socket UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)

def get_mouse_position():
    event = Quartz.CGEventCreate(None)
    loc = Quartz.CGEventGetLocation(event)
    return int(loc.x), int(loc.y)

def on_key_press(key):
    global REMOTE_MODE
    if key == keyboard.Key.esc and REMOTE_MODE:
        print("[Mac] Saindo do modo remoto")
        REMOTE_MODE = False
        Quartz.CGWarpMouseCursorPosition((SCREEN_WIDTH - 2, SCREEN_HEIGHT // 2))
        sock.sendto(b"\x00", (WINDOWS_HOST, PORT))

def on_click(x, y, button, pressed):
    if REMOTE_MODE:
        btn_code = {
            mouse.Button.left: 1,
            mouse.Button.right: 2,
            mouse.Button.middle: 3
        }.get(button, 0)
        
        if btn_code:
            MAC_CLICK_STATE[button.name] = pressed
            # Envia: Tipo 3 (clique) | Botão | Estado (1=pressed, 0=released)
            packed_data = struct.pack('!BBB', 3, btn_code, int(pressed))
            sock.sendto(packed_data, (WINDOWS_HOST, PORT))

# Listeners
keyboard_listener = keyboard.Listener(on_press=on_key_press)
mouse_listener = mouse.Listener(on_click=on_click)
keyboard_listener.start()
mouse_listener.start()

print(f"[Mac] Servidor iniciado. Pressione ESC para retornar o controle.")

while True:
    try:
        x, y = get_mouse_position()

        if not REMOTE_MODE:
            if (EXIT_BORDER == 'right' and x >= SCREEN_WIDTH - 1) or \
               (EXIT_BORDER == 'left' and x <= 0) or \
               (EXIT_BORDER == 'top' and y <= 0) or \
               (EXIT_BORDER == 'bottom' and y >= SCREEN_HEIGHT - 1):
                print("[Mac] Entrando em modo remoto")
                REMOTE_MODE = True
                sock.sendto(b"\x01", (WINDOWS_HOST, PORT))
                time.sleep(0.1)
        else:
            # Envia coordenadas (Tipo 2) + X/Y
            packed_data = struct.pack('!BHH', 2, x, y)
            sock.sendto(packed_data, (WINDOWS_HOST, PORT))

        # Verificação de retorno
        try:
            sock.settimeout(0.001)
            data, addr = sock.recvfrom(1024)
            if data == b"\x00":
                REMOTE_MODE = False
                Quartz.CGWarpMouseCursorPosition((SCREEN_WIDTH - 2, SCREEN_HEIGHT // 2))
        except socket.timeout:
            pass

        time.sleep(UPDATE_INTERVAL)
    except Exception as e:
        print("[Mac] Erro:", e)
        break

keyboard_listener.stop()
mouse_listener.stop()
sock.close()