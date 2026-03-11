import subprocess, time, os
import RPi.GPIO as gp

DEST_IP = "172.20.10.4"
PORT = {"A": 5000, "B": 5001, "C": 5002, "D": 5003}

# Use the *bitmask* i2cset form that worked for you.
# You confirmed A works with 0x04. Set C to whatever mask you discover.
MASK = {"A": 0x04, "B": 0x05, "C": 0x06, "D": 0x07}  # change C if needed
GPIO = {"A": [0, 0, 1], "B": [1, 0, 1], "C": [0, 1, 0], "D": [1, 1, 0]}

SLICE_MS = 1000  # start with 1000ms while debugging


def select_channel(cam_id: str):
    gpio = GPIO[cam_id]
    print(f"GPIO 0: {gpio[0]}, GPIO 1: {gpio[1]}, GPIO 2: {gpio[2]}")
    gp.output(7, gpio[0])
    gp.output(11, gpio[1])
    gp.output(12, gpio[2])

    print(f"mask: 0x{MASK[cam_id]:02x}")
    os.system(f"i2cset -y 1 0x70 0x00 0x{MASK[cam_id]:02x}")
    time.sleep(0.5)


def send_slice(cam_id: str):
    port = PORT[cam_id]
    # IMPORTANT: don't silence stderr while debugging
    subprocess.run(
        [
            "libcamera-vid",
            "-t",
            str(SLICE_MS),
            "--width",
            "1280",
            "--height",
            "720",
            "--framerate",
            "30",
            "--codec",
            "h264",
            "--inline",
            "--profile",
            "baseline",
            "--bitrate",
            "2000000",
            "-o",
            f"udp://{DEST_IP}:{port}",
        ],
        check=False,
    )


def main():
    gp.setwarnings(False)
    gp.setmode(gp.BOARD)
    gp.setup(7, gp.OUT)
    gp.setup(11, gp.OUT)
    gp.setup(12, gp.OUT)

    cam_ids = ["A", "B"]
    while True:
        for cam in cam_ids:
            print("Switching to", cam)
            select_channel(cam)
            send_slice(cam)


if __name__ == "__main__":
    main()
