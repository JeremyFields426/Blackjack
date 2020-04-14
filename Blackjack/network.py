import socket


class Network:
    def __init__(self, ip):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = ip
        self.port = 5555
        self.address = (self.host, self.port)
        self.id = self.connect()

    def connect(self):
        self.client.connect(self.address)

        return self.client.recv(1024).decode()

    def send(self, data):
        try:
            self.client.send(str.encode(data))
            reply = self.client.recv(1024).decode()
            return reply
        except socket.error as e:
            return str(e)
