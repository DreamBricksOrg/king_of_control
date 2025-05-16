import serial
import time


class ArduinoSerialSender:
    START_BYTE = 242
    END_BYTE = 243
    NUM_BYTES = 6

    def __init__(self, port, baudrate=115200, timeout=1):
        try:
            self.ser = serial.Serial(port, baudrate, timeout=timeout)
        except serial.SerialException:
            print(f"Could not open serial: {port}")
            exit(1)
        #time.sleep(0.5)  # Give Arduino time to reset after serial connection

    def send_bytes(self, b0, b1, b2, b3, b4, b5):
        data = [b0, b1, b2, b3, b4, b5]
        if not all(0 <= b <= 255 for b in data):
            raise ValueError("All byte values must be between 0 and 255.")

        packet = bytearray([self.START_BYTE] + data + [self.END_BYTE])
        self.ser.write(packet)

    def read_serial(self):
        while self.ser.in_waiting > 0:
            line = self.ser.readline().decode(errors='ignore').strip()
            if line:
                print(f"Received: {line}")

    def close(self):
        if self.ser.is_open:
            self.ser.close()


# Example Usage
if __name__ == "__main__":
    port = "COM16"
    sender = None
    sender = ArduinoSerialSender(port=port, baudrate=115200)  # Replace with your actual port, e.g., "/dev/ttyUSB0" on Linux

    try:
        #time.sleep(3)
        sender.read_serial()
        print("Sending data...")
        for col in range(3):
            for row in range(8):
                sender.send_bytes(1, col, row, 255, 255, 255)
                time.sleep(0.2)

        sender.send_bytes(1, 0, 7, 255, 255, 0)
        time.sleep(.5)
        sender.send_bytes(1, 1, 7, 255, 255, 0)
        time.sleep(.5)
        sender.send_bytes(1, 2, 7, 255, 255, 0)
        time.sleep(.5)
        sender.send_bytes(1, 1, 6, 255, 255, 0)
        time.sleep(.5)
        sender.send_bytes(1, 0, 6, 255, 255, 0)
        time.sleep(.5)
        sender.send_bytes(1, 0, 5, 255, 255, 0)
        time.sleep(.5)
        sender.send_bytes(1, 1, 5, 255, 255, 0)
        time.sleep(.5)
        sender.send_bytes(1, 2, 5, 255, 255, 0)
        time.sleep(1)
        sender.send_bytes(0, 0, 0, 0, 0, 0)
        sender.read_serial()
        print("Packet sent.")
        #while True:
        #    sender.read_serial()
    finally:
        sender.close()


class DummyArduinoSerialSender:
    START_BYTE = 242
    END_BYTE = 243
    NUM_BYTES = 6

    def __init__(self):
        pass

    def send_bytes(self, b0, b1, b2, b3, b4, b5):
        print(f"send_bytes({b0}, {b1}, {b2}, {b3}, {b4}, {b5}")

    def read_serial(self):
        pass

    def close(self):
        pass
