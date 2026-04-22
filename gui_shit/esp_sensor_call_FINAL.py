import argparse
import serial
import time
from typing import List, Optional, Tuple, Union

SERIAL_PORT = "/dev/ttyAMA0"
BAUD_RATE = 115200

TIMEOUT = 2.5
HEARTBEAT_TIMEOUT = 25.0

BATTERY_TIMEOUT = 0.35
PLUGSTATUS_TIMEOUT = 0.25
BATTERY_MAX_WAIT = 0.8
PLUGSTATUS_MAX_WAIT = 0.5

CMD_SENSOR_1 = 1
CMD_SENSOR_2 = 2
CMD_HEARTBEAT = 3
CMD_LDR = 4
CMD_BATTERY = 5
CMD_PLUG_STATUS = 6


class SensorProtocolError(RuntimeError):
    pass


class SensorClient:
    def __init__(self, port: str = SERIAL_PORT, baud_rate: int = BAUD_RATE, timeout: float = TIMEOUT):
        self.port = port
        self.baud_rate = baud_rate
        self.timeout = timeout

    def _open(self, timeout: Optional[float] = None) -> serial.Serial:
        if timeout is None:
            timeout = self.timeout
        return serial.Serial(self.port, self.baud_rate, timeout=timeout, write_timeout=timeout)

    @staticmethod
    def _decode_line(ser: serial.Serial) -> str:
        return ser.readline().decode("utf-8", errors="ignore").strip()

    def _send_command(self, ser: serial.Serial, command_num: int) -> None:
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        ser.write(f"{command_num}\n".encode("utf-8"))
        ser.flush()

    def _read_until_prefix(self, ser: serial.Serial, prefix: str, max_lines: int = 80) -> str:
        for _ in range(max_lines):
            line = self._decode_line(ser)
            if not line:
                continue
            if line.startswith(prefix):
                return line.split(":", 1)[1].strip()
            if line.endswith("_ERR"):
                raise SensorProtocolError(line)
        raise SensorProtocolError(f"Timed out waiting for prefix: {prefix}")
    def _read_until_prefix_or_none(
        self,
        ser: serial.Serial,
        prefix: str,
        max_wait: float,
        max_lines: int = 80,
    ) -> Optional[str]:
        deadline = time.monotonic() + max_wait
        lines_seen = 0

        while time.monotonic() < deadline and lines_seen < max_lines:
            line = self._decode_line(ser)
            if not line:
                continue

            lines_seen += 1

            if line.startswith(prefix):
                return line.split(":", 1)[1].strip()

            if line.endswith("_ERR"):
                print(f"Sensor protocol error while waiting for {prefix}: {line}")
                return None

            if line in {"NOT_FOUND", "NA", "NO_BATTERY", "NO_CHARGER", "BAT_FAIL", "PLUG_FAIL"}:
                return None

        return None
    def read_temp_humidity(self, command_num: int, label: str) -> Tuple[str, str]:
        with self._open() as ser:
            self._send_command(ser, command_num)
            temp = self._read_until_prefix(ser, f"{label}_TEMP:")
            hum = self._read_until_prefix(ser, f"{label}_HUM:")
            return temp, hum

    def read_sensor1(self) -> Tuple[str, str]:
        return self.read_temp_humidity(CMD_SENSOR_1, "S1")

    def read_sensor2(self) -> Tuple[str, str]:
        return self.read_temp_humidity(CMD_SENSOR_2, "S2")

    def read_ldr(self) -> str:
        with self._open() as ser:
            self._send_command(ser, CMD_LDR)
            return self._read_until_prefix(ser, "LDR:")

    def read_heartbeat(self) -> Optional[float]:
        with self._open() as ser:
            self._send_command(ser, CMD_HEARTBEAT)

            readings: List[int] = []
            started = False
            ser.timeout = 1.0

            import time
            deadline = time.time() + HEARTBEAT_TIMEOUT
            while time.time() < deadline:
                line = self._decode_line(ser)
                if not line:
                    continue
                if line == "HB_START":
                    started = True
                    readings = []
                    continue
                if line == "HB_END":
                    if readings:
                        return sum(readings) / len(readings)
                    return None
                if started and line.startswith("HB:"):
                    try:
                        readings.append(int(line.split(":", 1)[1].strip()))
                    except ValueError:
                        continue

            raise SensorProtocolError("Timed out waiting for heartbeat session to complete")

    def read_battery(self) -> Optional[Tuple[str, str]]:
        try:
            with self._open(timeout=BATTERY_TIMEOUT) as ser:
                self._send_command(ser, CMD_BATTERY)

                voltage = self._read_until_prefix_or_none(ser, "BAT_V:", BATTERY_MAX_WAIT)
                if voltage is None:
                    return None

                state_of_charge = self._read_until_prefix_or_none(ser, "BAT_P:", BATTERY_MAX_WAIT)
                if state_of_charge is None:
                    return None

                return voltage, state_of_charge

        except Exception as e:
            print(f"Battery read failed: {e}")
            return None
    def read_plugstatus(self) -> Optional[str]:
        try:
            with self._open(timeout=PLUGSTATUS_TIMEOUT) as ser:
                self._send_command(ser, CMD_PLUG_STATUS)
                return self._read_until_prefix_or_none(ser, "PLUG_STAT:", PLUGSTATUS_MAX_WAIT)

        except Exception as e:
            print(f"Plug status read failed: {e}")
            return None


def call_data(
    tempHum: bool = False,
    sensor2: bool = False,
    hb: bool = False,
    lux: bool = False,
    battery: bool = False,
    plugstatus: bool = False,
    port: str = SERIAL_PORT,
) -> Union[Tuple[str, str], str, float, None]:
    """
    Backward-compatible wrapper for the existing UI.

    Mapping to master_everything.ino:
      tempHum=True   -> command 1 -> Sensor 1 temp/humidity
      sensor2=True   -> command 2 -> Sensor 2 temp/humidity
      hb=True        -> command 3 -> heartbeat session average BPM
      lux=True       -> command 4 -> LDR reading

    temp_internal is not implemented by the current firmware.
    """
    client = SensorClient(port=port)

    if tempHum:
        return client.read_sensor1()
    if sensor2:
        return client.read_sensor2()
    if hb:
        return client.read_heartbeat()
    if lux:
        return client.read_ldr()
    if battery:
        return client.read_battery()
    if plugstatus:
        return client.read_plugstatus()
    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Read sensor data from master_everything.ino")
    parser.add_argument("--temphum", action="store_true", help="Read sensor 1 temperature and humidity")
    parser.add_argument("--sensor2", action="store_true", help="Read sensor 2 temperature and humidity")
    parser.add_argument("--lux", action="store_true", help="Read LDR value")
    parser.add_argument("--hb", action="store_true", help="Read heartbeat average BPM")
    parser.add_argument("--battery", action="store_true", help="Read battery stats")
    parser.add_argument("--plugstatus", action="store_true", help="detect wall power connected")
    parser.add_argument("--port", default=SERIAL_PORT, help=f"Serial port (default: {SERIAL_PORT})")
    args = parser.parse_args()

    result = call_data(
        tempHum=args.temphum,
        sensor2=args.sensor2,
        hb=args.hb,
        lux=args.lux,
        battery=args.battery,
        plugstatus=args.plugstatus,
        port=args.port,
    )
    print(result)
