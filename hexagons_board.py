from arduino_serial_sender import ArduinoSerialSender


class HexagonsBoard:
    def __init__(self, port, baudrate):
        self.sender = ArduinoSerialSender(port, baudrate)

    def set_hexagon(self, col, row, color):
        self.sender.send_bytes(1, col, row, *color)

    def clear(self):
        self.sender.send_bytes(0, 0, 0, 0, 0, 0)


# Example Usage
if __name__ == "__main__":
    import time
    port = "COM16"
    sender = HexagonsBoard(port=port, baudrate=115200)  # Replace with your actual port, e.g., "/dev/ttyUSB0" on Linux

    print("Sending data...")
    for row in range(8):
        for col in range(3):
            sender.set_hexagon(col, row, (255, 255, 255))
            time.sleep(0.2)

    time.sleep(1)
    sender.clear()