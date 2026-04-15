import subprocess
import time
from picamera2 import Picamera2

LAPTOP_IP = "192.168.12.1"
PORT = 5002
FPS = 50


def camera_exists() -> bool:
    return len(Picamera2.global_camera_info()) >= 1


def start():
    return subprocess.Popen(
        [
            "rpicam-vid",
            "-n",
            "-t",
            "0",
            "--camera",
            "0",
            "--sync",
            "server",
            "--inline",
            "--low-latency",
            "--framerate",
            str(FPS),
            "--codec",
            "h264",
            "-o",
            f"udp://{LAPTOP_IP}:{PORT}",
        ]
    )


def main():
    if not camera_exists():
        raise RuntimeError("Camera was not detected")

    server = start()

    try:
        while True:
            time.sleep(1)

            if server.poll() is not None:
                raise RuntimeError(
                    f"Server camera exited with code {server.returncode}"
                )

    except KeyboardInterrupt:
        print("\nStopping cameras...")
    finally:
        if server.poll() is None:
            server.terminate()


if __name__ == "__main__":
    main()
