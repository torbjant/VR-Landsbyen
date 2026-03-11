import os, time, subprocess
import RPi.GPIO as gp
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput

DEST_IP = "192.168.12.1"
DEST_PORT = 5000
FIFO = "/tmp/cam.h264"


adapter_info = {
    "A": {"i2c_cmd": "i2cset -y 1 0x70 0x04", "gpio_sta": [0, 0, 1]},
    "B": {"i2c_cmd": "i2cset -y 1 0x70 0x08", "gpio_sta": [1, 0, 1]},
    "C": {"i2c_cmd": "i2cset -y 1 0x70 0x01", "gpio_sta": [0, 1, 0]},
    "D": {"i2c_cmd": "i2cset -y 1 0x70 0x02", "gpio_sta": [1, 1, 0]},
}


def select_channel(cam_id: str):
    gpio = adapter_info[cam_id]["gpio_sta"]
    gp.output(7, gpio[0])
    gp.output(11, gpio[1])
    gp.output(12, gpio[2])
    os.system(adapter_info[cam_id]["i2c_cmd"])
    time.sleep(0.5)


def send_slice(cam):
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
            f"udp://{DEST_IP}:{PORT[cam]}",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def main():
    gp.setwarnings(False)
    gp.setmode(gp.BOARD)
    gp.setup(7, gp.OUT)
    gp.setup(11, gp.OUT)
    gp.setup(12, gp.OUT)

    # recreate FIFO
    try:
        os.unlink(FIFO)
    except FileNotFoundError:
        pass
    os.mkfifo(FIFO)

    picam2 = Picamera2()
    picam2.configure(picam2.create_video_configuration(main={"size": (1280, 720)}))
    picam2.start()
    time.sleep(0.3)

    encoder = H264Encoder(bitrate=2_000_000, repeat=True)  # repeat SPS/PPS
    f = open(FIFO, "wb")  # IMPORTANT: buffered file object
    picam2.start_recording(encoder, FileOutput(f))

    try:
        while True:
            cam_ids = ["A", "C"]
            for id in cam_ids:
                select_channel(id)
                send_slice(id)
    finally:
        try:
            picam2.stop_recording()
        except Exception:
            pass
        try:
            picam2.stop()
        except Exception:
            pass
        try:
            f.close()
        except Exception:
            pass
        ff.terminate()
        ff.wait(timeout=2)

    # # Start ffmpeg first (it will open FIFO for reading)
    # ff = subprocess.Popen([
    #     "ffmpeg",
    #     "-loglevel", "warning",
    #     "-fflags", "nobuffer",
    #     "-flags", "low_delay",
    #     "-probesize", "2000000",
    #     "-analyzeduration", "2000000",
    #     "-f", "h264",
    #     "-i", FIFO,
    #     "-c", "copy",
    #     "-f", "mpegts",
    #     f"udp://{DEST_IP}:{DEST_PORT}?pkt_size=1316"
    # ])


#     try:
#         while True:
#             time.sleep(1)
#     finally:
#         try:
#             picam2.stop_recording()
#         except Exception:
#             pass
#         try:
#             picam2.stop()
#         except Exception:
#             pass
#         try:
#             f.close()
#         except Exception:
#             pass
#         ff.terminate()
#         ff.wait(timeout=2)
#
if __name__ == "__main__":
    main()
