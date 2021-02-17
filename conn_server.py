import socket
import random
from Crypto.Cipher import AES


class ConnServer:
    def __init__(self, SERVER_IP="127.0.0.1", PORT=4485):
        self.SERVER_SOCK = (SERVER_IP, PORT)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.ioctl(socket.SIO_KEEPALIVE_VALS, (1, 32400000, 5000))
        self.sock.connect(self.SERVER_SOCK)
        self.aesdec = AES.new(b"automate_egggggg", AES.MODE_ECB)
        message = self.sock.recv(1024)
        self.sock.send(self.aesdec.decrypt(message))

    def send(self, msg):
        self.sock.send(msg.encode("latin-1"))

    def add(self, n):
        self.send(str(n))

    def sub(self, n):
        self.send("-"+str(n))


class StubConnServer:
    def __init__(self, SERVER_IP="127.0.0.1", PORT=4485):
        print(f"Connection established with {SERVER_IP}:{PORT}")

    def send(self, msg):
        print(f"Sending: '{msg}'")

    def add(self, n):
        self.send(str(n))

    def sub(self, n):
        self.send("-"+str(n))

