import socket
import time
import Quartz
from pynput import keyboard

# Configurações
WINDOWS_HOST = '192.168.8.108'  # IP do Windows
PORT = 5000
EXIT_BORDER = 'left'  # "left", "right", "top", "bottom"

# Tela principal
screen = Quartz.CGDisplayBounds(Quartz.CGMainDisplayID())
SCREEN_WIDTH = int(screen.size.width)
SCREEN_HEIGHT = int(screen.size.height)

REMOTE_MODE = False

# Socket UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

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
        sock.sendto(b"EXIT_REMOTE", (WINDOWS_HOST, PORT))  # UDP: sendto()

keyboard.Listener(on_press=on_key_press).start()

print("[Mac] Servidor UDP iniciado. Pressione ESC para retornar o controle.")

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
                sock.sendto(b"ENTER_REMOTE", (WINDOWS_HOST, PORT))  # UDP: sendto()
                time.sleep(0.1)
        else:
            # Envia coordenadas via UDP
            msg = f"MOVE:{x},{y}"
            sock.sendto(msg.encode(), (WINDOWS_HOST, PORT))  # UDP: sendto()

        # Verifica se recebeu comando de retorno (opcional, UDP não é confiável)
        try:
            sock.settimeout(0.001)
            data, addr = sock.recvfrom(1024)  # UDP: recvfrom()
            if data.decode().strip() == "RETURN_CONTROL":
                REMOTE_MODE = False
                Quartz.CGWarpMouseCursorPosition((SCREEN_WIDTH - 2, SCREEN_HEIGHT // 2))
                print("[Mac] Controle retornado pelo Windows")
        except socket.timeout:
            pass

        time.sleep(0.01)  # Ajustável para maior fluidez (ex: 0.005)
    except Exception as e:
        print("[Mac] Erro:", e)
        break

sock.close()