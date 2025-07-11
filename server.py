import socket
import time
import Quartz
from pynput import keyboard
import struct

# Configurações
WINDOWS_HOST = '192.168.8.108'  # IP do Windows
PORT = 5000
EXIT_BORDER = 'left'  # "left", "right", "top", "bottom"
UPDATE_INTERVAL = 0.005  # Taxa de atualização mais rápida

# Tela principal
screen = Quartz.CGDisplayBounds(Quartz.CGMainDisplayID())
SCREEN_WIDTH = int(screen.size.width)
SCREEN_HEIGHT = int(screen.size.height)

REMOTE_MODE = False

# Socket UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)  # Aumentar buffer de envio

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
        sock.sendto(b"\x00", (WINDOWS_HOST, PORT))  # Byte único para EXIT_REMOTE

keyboard.Listener(on_press=on_key_press).start()

print(f"[Mac] Servidor UDP iniciado (Taxa: {1/UPDATE_INTERVAL:.0f}Hz). Pressione ESC para retornar o controle.")

while True:
    try:
        x, y = get_mouse_position()

        if not REMOTE_MODE:
            if (
                (EXIT_BORDER == 'right' and x >= SCREEN_WIDTH - 1) or
                (EXIT_BORDER == 'left' and x <= 0) or
                (EXIT_BORDER == 'top' and y <= 0) or
                (EXIT_BORDER == 'bottom' and y >= SCREEN_HEIGHT - 1)
            ):
                print("[Mac] Entrando em modo remoto")
                REMOTE_MODE = True
                sock.sendto(b"\x01", (WINDOWS_HOST, PORT))  # Byte único para ENTER_REMOTE
                time.sleep(0.1)
        else:
            # Envia coordenadas compactadas (2 shorts = 4 bytes)
            packed_data = struct.pack('!BHH', 2, x, y)  # [Tipo, X, Y]
            sock.sendto(packed_data, (WINDOWS_HOST, PORT))

        # Verificação de retorno não bloqueante
        try:
            sock.settimeout(0.001)
            data, addr = sock.recvfrom(1024)
            if data == b"\x00":  # RETURN_CONTROL
                REMOTE_MODE = False
                Quartz.CGWarpMouseCursorPosition((SCREEN_WIDTH - 2, SCREEN_HEIGHT // 2))
                print("[Mac] Controle retornado pelo Windows")
        except socket.timeout:
            pass

        time.sleep(UPDATE_INTERVAL)
    except Exception as e:
        print("[Mac] Erro:", e)
        break

sock.close()