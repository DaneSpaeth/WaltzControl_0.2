import socket


class NETPowerConnector():
    """Connects to NET Power Control via UDP.
    """

    def __init__(self):
        self.user = 'admin'
        self.password = 'clearskies'

    def send_to_power_control(self, message):
        """Send string message to Power Control via UDP.

           Input: message as string.
           Output: None
        """
        # Specifiy NET Power Control's IP and Port
        UDP_IP = "147.142.111.231"
        UDP_TO_PORT = 75
        # Context Manager to close Connection automatically
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as conn:
            conn.sendto(message.encode(), (UDP_IP, UDP_TO_PORT))

    def listen_to_power_control():
        """Receive message from Power Control.

           Input: None
           Output: Received data as string.
           """
        UDP_FROM_PORT = 7700
        # Context Manager to close Connection automatically
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as conn:
            conn.bind(('', UDP_FROM_PORT))
            data, addr = conn.recvfrom(1024)  # 1024 is buffersize
            data = data.decode()
        return data

    def turn_on_relay(self, number):
        """Turn on relay on NET Power Control.

           Input: relay number as int.
        """
        number = str(number)
        message = 'Sw_on' + number + self.user + self.password
        self.send_to_power_control(message)

    def turn_off_relay(self, number):
        """Turn off relay on NET Power Control.

           Input: relay number as int.
        """
        number = str(number)
        message = 'Sw_off' + number + self.user + self.password
        self.send_to_power_control(message)

    def ask_state(self):
        """Get current state of Power control.

           Input: None
           Output: String representing State.
        """
        message = "wer da?"
        self.send_to_power_control(message)
        reply = self.listen_to_power_control()
        return reply
