from pybricks.hubs import TechnicHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port
from pybricks.tools import wait
from pybricks.bluetooth import BLEUART

hub = TechnicHub()
boom = Motor(Port.A)
jib = Motor(Port.B)
hoist = Motor(Port.D)
uart = BLEUART()

while True:
    if uart.any():
        data = uart.read(3)
        boom.run((data[0] - 127) * 5)
        jib.run((data[1] - 127) * 5)
        hoist.run((data[2] - 127) * 5)
    wait(20)
