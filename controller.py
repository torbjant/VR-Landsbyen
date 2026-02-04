import subprocess
import pygame
import sys

DEVICE_ADDRESS_BASE_HUB = "XX:XX:XX:XX:XX:XX"
DEVICE_ADDRESS_CRANE_HUB = "XX:XX:XX:XX:XX:XX"

pygame.init()
pygame.joystick.init()
screen = pygame.display.set_mode((200, 200))

js = pygame.joystick.Joystick(0)
js.init()

proc = subprocess.Popen(
    [sys.executable, "ble_sender.py", DEVICE_ADDRESS_BASE_HUB, DEVICE_ADDRESS_CRANE_HUB],
    stdin=subprocess.PIPE,
    text=True
)

clock = pygame.time.Clock()

while True:
    pygame.event.pump()

    y_left = js.get_axis(0)
    x_left = js.get_axis(1)
    y_right = js.get_axis(2)
    x_right = js.get_axis(3)

    if js.get_button(4):
        data_base = [
            int((x_right + 1) * 127),
            int((y_right + 1) * 127),
            int((y_left + 1) * 127),
        ]
        data_crane = [127, 127, js.get_button(1), js.get_button(0)]
    else:
        data_base = [
            int((y_right + 1) * 127),
            127,
            127
        ]
        data_crane = [
            int((y_right + 1) * 127),
            int((y_left + 1) * 127),
            js.get_button(1),
            js.get_button(0)
        ]

    line = ",".join(map(str, data_base + data_crane)) + "\n"
    proc.stdin.write(line)
    proc.stdin.flush()

    clock.tick(50)
