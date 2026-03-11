#!/usr/bin/env python3
import os
import time
import subprocess
import RPi.GPIO as gp

PIN_S0 = 7
PIN_S1 = 11
PIN_S2 = 12

I2C_BUS = 1
I2C_ADDR = 0x70

GPIO_STATE = {
    "A": (0, 0, 1),
    "B": (1, 0, 1),
    "C": (0, 1, 0),
    "D": (1, 1, 0),
}

I2C_MASKS = [0x04, 0x05, 0x06, 0x07]
OUTDIR = "./mux_scan"
SETTLE_SEC = 0.8
CAPTURE_TIMEOUT_SEC = 6  # prevents hangs


def kill_camera_users():
    # script should be run with sudo, so no sudo needed here
    subprocess.run(["pkill", "-9", "-f", "libcamera"], check=False)
    subprocess.run(["pkill", "-9", "-f", "rpicam"], check=False)
    time.sleep(0.3)


def set_gpio(cam_id: str) -> None:
    s0, s1, s2 = GPIO_STATE[cam_id]
    gp.output(PIN_S0, s0)
    gp.output(PIN_S1, s1)
    gp.output(PIN_S2, s2)


def set_i2c_mask(mask: int) -> None:
    # Bitmask write (the form you proved works): i2cset -y 1 0x70 0x04
    cmd = ["i2cset", "-y", str(I2C_BUS), hex(I2C_ADDR), hex(mask)]
    subprocess.run(
        cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )


def capture(path: str) -> tuple[bool, str]:
    cmd = ["libcamera-still", "--nopreview", "-t", "500", "-o", path]
    try:
        r = subprocess.run(
            cmd,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=CAPTURE_TIMEOUT_SEC,
        )
        ok = r.returncode == 0 and os.path.exists(path) and os.path.getsize(path) > 0
        return ok, r.stdout[-4000:]  # tail for debugging
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT"


def main():
    os.makedirs(OUTDIR, exist_ok=True)

    gp.setwarnings(False)
    gp.setmode(gp.BOARD)
    gp.setup(PIN_S0, gp.OUT)
    gp.setup(PIN_S1, gp.OUT)
    gp.setup(PIN_S2, gp.OUT)

    print("Cleaning up any camera processes...")
    kill_camera_users()

    results = []

    for cam in ["A", "B", "C", "D"]:
        print(f"\n=== Testing GPIO select {cam} (pins {GPIO_STATE[cam]}) ===")
        set_gpio(cam)
        time.sleep(0.2)

        for mask in I2C_MASKS:
            print(f"  Testing I2C mask 0x{mask:02x} ... ", end="", flush=True)

            # ensure nothing is holding the pipeline from previous test
            kill_camera_users()

            set_i2c_mask(mask)
            time.sleep(SETTLE_SEC)

            out = os.path.join(OUTDIR, f"{cam}_mask{mask:02x}.jpg")
            ok, log = capture(out)

            if ok:
                print(f"OK -> {out}")
            else:
                print("FAIL")
                # if it hung or wedged, reset before continuing
                if log == "TIMEOUT":
                    print("    (libcamera-still timed out; resetting pipeline)")
                    kill_camera_users()
                # cleanup empty file
                try:
                    if os.path.exists(out):
                        os.remove(out)
                except Exception:
                    pass

            results.append((cam, mask, ok))

    print("\nSummary (OK combinations):")
    for cam, mask, ok in results:
        if ok:
            print(f"  {cam} + mask 0x{mask:02x}")

    print(f"\nImages saved in: {OUTDIR}")


if __name__ == "__main__":
    main()
