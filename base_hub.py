from pybricks.pupdevices import Motor
from pybricks.parameters import Port
from pybricks.tools import wait
from usys import stdin, stdout
from uselect import poll

# --- Initialize motors ---
left_motor = Motor(Port.C)
right_motor = Motor(Port.D)
rotate_motor = Motor(Port.B)

# --- Setup stdin polling ---
keyboard = poll()
keyboard.register(stdin)

while True:
    # Tell PC we are ready
    stdout.buffer.write(b"rdy")

    # Wait until some data arrives
    while not keyboard.poll(0):
        wait(10)

    # Read 3 bytes: one for each motor
    cmd = stdin.buffer.read(3)
    if not cmd or len(cmd) != 3:
        continue  # skip if incomplete

    # Each byte controls a motor: 0 = stop, 1 = forward, 2 = backward
    # Left motor
    if cmd[0] == 0x01:
        left_motor.run_angle(50, 360)
    elif cmd[0] == 0x02:
        left_motor.dc(50, -360 )
    else:
        left_motor.stop()

    # Right motor
    if cmd[1] == 0x01:
        right_motor.dc(50, 360)
    elif cmd[1] == 0x02:
        right_motor.dc(50, -360)
    else:
        right_motor.stop()

    # Rotate motor
    if cmd[2] == 0x01:
        rotate_motor.dc(50)
    elif cmd[2] == 0x02:
        rotate_motor.dc(-50)
    else:
        rotate_motor.stop()

    # Small delay to prevent busy loop
    wait(20)
