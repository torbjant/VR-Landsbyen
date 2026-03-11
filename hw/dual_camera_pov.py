import subprocess
import time
from picamera2 import Picamera2

LAPTOP_IP = "192.168.12.1"
SERVER_PORT = 5000
CLIENT_PORT = 5001
FPS = 50


def camera_exists() -> bool:
    return len(Picamera2.global_camera_info()) >= 2


def start_server_camera():
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
            f"udp://{LAPTOP_IP}:{SERVER_PORT}",
        ]
    )


def start_client_camera():
    return subprocess.Popen(
        [
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
            f"udp://{LAPTOP_IP}:{CLIENT_PORT}",
        ]
    )


def main():
    if not camera_exists():
        raise RuntimeError("Need 2 cameras connected")

    server = start_server_camera()
    time.sleep(1.0)  # let the sync server come up first
    client = start_client_camera()

    try:
        while True:
            time.sleep(1)

            if server.poll() is not None:
                raise RuntimeError(
                    f"Server camera exited with code {server.returncode}"
                )

            if client.poll() is not None:
                raise RuntimeError(
                    f"Client camera exited with code {client.returncode}"
                )

    except KeyboardInterrupt:
        print("\nStopping cameras...")
    finally:
        for proc in (client, server):
            if proc.poll() is None:
                proc.terminate()

        for proc in (client, server):
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()


if __name__ == "__main__":
    main()
