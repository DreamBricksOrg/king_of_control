from arduino_serial_sender import ArduinoSerialSender


class HexagonsBoard:
    def __init__(self, port, baudrate):
        self.sender = ArduinoSerialSender(port, baudrate)

    def set_hexagon(self, col, row, color):
        self.sender.send_bytes(1, col, row, *color)

    def clear(self):
        self.sender.send_bytes(0, 0, 0, 0, 0, 0)
