import argparse
import serial
import sys
import time
from typing import Optional

"""
Send radio commands to master_everything.ino over the Pi <-> ESP AMA0 link.

The firmware expects a two-step sequence:
  1) send the line: RADIO
  2) send the actual command line within ~1 second

Supported firmware commands today:
  - MODE FM
  - MODE AM
  - VOLUP
  - VOLDN
  - SEEKUP
  - SEEKDN

Unsupported by the current firmware:
  - TUNE <value>
  - STEPUP <value>
  - STEPDN <value>
  - STATUS
"""

SERIAL_PORT = "/dev/ttyAMA0"
BAUD_RATE = 115200
SERIAL_TIMEOUT = 1.0
RESPONSE_WINDOW_SEC = 1.2

SUPPORTED_COMMANDS = {
    "VOLUP",
    "VOLDN",
    "SEEKUP",
    "SEEKDN",
    "MODE FM",
    "MODE AM",
    "STATUS",
    "HELP"
}

def normalize_command(command: str) -> str:
    return " ".join(command.strip().split()).upper()


def validate_command(command: str) -> Optional[str]:
    if not command:
        return "Empty command"

    head = command.split(" ", 1)[0]

    # Allow parameterized commands
    if head in {"TUNE", "STEPUP", "STEPDN"}:
        return None

    if command in SUPPORTED_COMMANDS:
        return None

    return f"Unsupported command: {command}"

def send_radio_command(command: str, port: str = SERIAL_PORT, baud_rate: int = BAUD_RATE) -> str:
    normalized = normalize_command(command)
    error = validate_command(normalized)
    if error:
        raise ValueError(error)

    with serial.Serial(port, baud_rate, timeout=SERIAL_TIMEOUT) as ser:
        ser.reset_input_buffer()
        ser.reset_output_buffer()

        ser.write(b"RADIO\n")
        ser.flush()
        time.sleep(0.08)

        ser.write((normalized + "\n").encode("utf-8"))
        ser.flush()

        deadline = time.time() + RESPONSE_WINDOW_SEC
        lines = []
        while time.time() < deadline:
            raw = ser.readline().decode("utf-8", errors="ignore").strip()
            if not raw:
                continue
            lines.append(raw)
            if raw.startswith("RADIO_OK") or raw.startswith("RADIO_ERR"):
                return raw

        if lines:
            return "\n".join(lines)
        return "NO_RESPONSE"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send a radio command to the ESP radio firmware")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Command to send, e.g. MODE FM")
    parser.add_argument("--port", default=SERIAL_PORT, help=f"Serial port (default: {SERIAL_PORT})")
    parser.add_argument("--baud", type=int, default=BAUD_RATE, help=f"Baud rate (default: {BAUD_RATE})")
    args = parser.parse_args()

    if not args.command:
        print("Usage: python3 radio_send_updated.py MODE FM", file=sys.stderr)
        sys.exit(2)

    command = " ".join(args.command)
    try:
        print(send_radio_command(command, port=args.port, baud_rate=args.baud))
    except Exception as exc:
        print(f"Serial Error: {exc}", file=sys.stderr)
        sys.exit(1)
