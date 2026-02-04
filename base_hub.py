from pybricks.hubs import TechnicHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port
from pybricks.tools import wait
from pybricks.bluetooth import BLEUART

hub = TechnicHub()
rotate = Motor(Port.B)
right_forward = Motor(Port.D)
left_forward = Motor(Port.C)
uart = BLEUART()

while True:
    if uart.any():
        data = uart.read(3)
        rotate.run((data[0] - 127) * 5)
        right_forward.run((data[1] - 127) * 5)
        left_forward.run((data[2] - 127) * 5)
    wait(20)
