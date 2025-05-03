from arduino_serial_sender import ArduinoSerialSender


class HexagonsBoard:
    def __init__(self, port, baudrate):
        self.sender = ArduinoSerialSender(port, baudrate)

    def set_hexagon(self, col, row, color):
        self.sender.send_bytes(1, col, row, *color)

    def set_goal(self, color):
        self.sender.send_bytes(2, *color, 0, 0)

    def clear(self):
        self.sender.send_bytes(0, 0, 0, 0, 0, 0)


# Example Usage
if __name__ == "__main__":
    import time
    import parameters as param
    port = param.ARDUINO_COM_PORT
    sender = HexagonsBoard(port=port, baudrate=115200)  # Replace with your actual port, e.g., "/dev/ttyUSB0" on Linux

    print("Sending data...")
    while True:
        color = (255, 0, 0)
        for row in range(8):
            num_cols = 3 if row % 2 else 2
            for col in range(num_cols):
                sender.set_hexagon(col, row, color)
                time.sleep(0.2)
        sender.set_goal(color)

        color = (0, 255, 0)
        for row in range(8):
            num_cols = 3 if row % 2 else 2
            for col in range(num_cols):
                sender.set_hexagon(col, row, color)
                time.sleep(0.2)
        sender.set_goal(color)

        color = (0, 0, 255)
        for row in range(8):
            num_cols = 3 if row % 2 else 2
            for col in range(num_cols):
                sender.set_hexagon(col, row, color)
                time.sleep(0.2)
        sender.set_goal(color)

        color = (255, 255, 255)
        for row in range(8):
            num_cols = 3 if row % 2 else 2
            for col in range(num_cols):
                sender.set_hexagon(col, row, color)
                time.sleep(0.2)
        sender.set_goal(color)

        time.sleep(1)
        sender.clear()