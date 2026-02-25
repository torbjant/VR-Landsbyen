from pybricks.pupdevices import Motor
from pybricks.parameters import Direction, Port
from pybricks.tools import wait
from pybricks.parameters import Color
from pybricks.hubs import TechnicHub


# Standard MicroPython modules
from usys import stdin, stdout
from uselect import poll



hub = TechnicHub()

# hue = 0
# saturation = 100
# brightness = 100

# ---- Initialize Motors ----
left_motor = Motor(Port.C, positive_direction=Direction.COUNTERCLOCKWISE)
right_motor = Motor(Port.D)
rotation_motor = Motor(Port.B, positive_direction=Direction.COUNTERCLOCKWISE)

def convert_byte_to_duty_cycle(byte):
    return ((byte / 127) - 1) * 100

while True:

    # Let the remote program know we are ready for a command.
    stdout.buffer.write(b"rdy")


    # Read three bytes.
    cmd = stdin.buffer.read(4)

    if not cmd:
        continue
    # hub.light.on(Color(hue, brightness, saturation))
    #
    # # Decide what to do based on the command.
    # if cmd[0] == 0x01:
    #     hue += 1
    #     if hue > 360:
    #         hue = 0
    # elif cmd[0] == 0x02:
    #     hue -= 1
    #     if hue < 0:
    #         hue = 360
    #
    # if cmd[1] == 0x01:
    #     saturation += 1
    #     if saturation > 100:
    #         saturation = 100
    # elif cmd[1] == 0x02:
    #     saturation -= 1
    #     if saturation < 0:
    #         saturation = 0
    #
    # if cmd[2] == 0x01:
    #     brightness += 1
    #     if brightness > 100:
    #         brightness = 100
    # elif cmd[2] == 0x02:
    #     brightness -= 1
    #     if brightness < 0:
    #         brightness = 0

    left_speed = convert_byte_to_duty_cycle(cmd[0])
    right_speed = convert_byte_to_duty_cycle(cmd[1])
    rotation_speed = convert_byte_to_duty_cycle(cmd[2])

    # Apply speeds
    left_motor.dc(left_speed)
    right_motor.dc(right_speed)
    rotation_motor.dc(rotation_speed)

    if cmd[3] == 0x01:
        break

# Stop motors when exiting
left_motor.stop()
right_motor.stop()
rotation_motor.stop()