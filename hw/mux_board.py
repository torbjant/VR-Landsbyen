import os
import time
import socket
import signal
import threading
import subprocess

import RPi.GPIO as gp

LAPTOP_IP = "192.168.12.1"
BROADCAST_PORT = 5003
CONTROL_PORT = 5004
FPS = 50

adapter_info = {
    "A": {"i2c_cmd": "i2cset -y 1 0x70 0x04", "gpio_sta": [0, 0, 1]},
    "C": {"i2c_cmd": "i2cset -y 1 0x70 0x01", "gpio_sta": [0, 1, 0]},
}

running = True


def setup_gpio():
    gp.setwarnings(False)
    gp.setmode(gp.BOARD)
    gp.setup(7, gp.OUT)
    gp.setup(11, gp.OUT)
    gp.setup(12, gp.OUT)


def select_channel(cam_id: str):
    gpio = adapter_info[cam_id]["gpio_sta"]
    gp.output(7, gpio[0])
    gp.output(11, gpio[1])
    gp.output(12, gpio[2])

    # Set the multiplexer channel
    subprocess.run(
        adapter_info[cam_id]["i2c_cmd"].split(),
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Let the hardware settle
    time.sleep(0.3)


class VideoSwitcher:
    def __init__(self, initial_cam="A"):
        self.current_cam = initial_cam
        self.proc = None
        self.lock = threading.Lock()

    def start_stream(self):
        select_channel(self.current_cam)

        cmd = [
            "rpicam-vid",
            "-n",
            "-t",
            "0",
            "--camera",
            "1",
            "--sync",
            "client",
            "--inline",
            "--low-latency",
            "--framerate",
            str(FPS),
            "--codec",
            "h264",
            "-o",
            f"udp://{LAPTOP_IP}:{BROADCAST_PORT}",
        ]

        self.proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print(f"Streaming camera {self.current_cam}")

    def stop_stream(self):
        if self.proc is None:
            return

        try:
            self.proc.terminate()
            self.proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait()
        finally:
            self.proc = None

    def switch_camera(self):
        with self.lock:
            next_cam = "C" if self.current_cam == "A" else "A"
            print(f"Switching {self.current_cam} -> {next_cam}")

            self.stop_stream()
            self.current_cam = next_cam
            time.sleep(0.2)
            self.start_stream()

    def cleanup(self):
        with self.lock:
            self.stop_stream()


def udp_listener(switcher: VideoSwitcher):
    global running

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", CONTROL_PORT))
    sock.settimeout(1.0)

    print(f"Listening for control packets on UDP {CONTROL_PORT}")

    while running:
        try:
            data, addr = sock.recvfrom(1024)
            print(f"Received {data!r} from {addr}")
            switcher.switch_camera()
        except socket.timeout:
            continue
        except Exception as e:
            if running:
                print(f"UDP listener error: {e}")

    sock.close()


def handle_exit(signum, frame):
    global running
    running = False


def main():
    global running

    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    setup_gpio()

    switcher = VideoSwitcher(initial_cam="A")
    switcher.start_stream()

    listener_thread = threading.Thread(
        target=udp_listener,
        args=(switcher,),
        daemon=True,
    )
    listener_thread.start()

    try:
        while running:
            time.sleep(0.5)
    finally:
        switcher.cleanup()
        gp.cleanup()


if __name__ == "__main__":
    main()
