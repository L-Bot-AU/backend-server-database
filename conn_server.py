import socket
import random
from Crypto.Cipher import AES


class ConnServer:
    def __init__(self, SERVER_IP="127.0.0.1", PORT=5000):
        self.SERVER_SOCK = (SERVER_IP, PORT)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(self.SERVER_SOCK)
        self.aesdec = AES.new(b"automate_egggggg", AES.MODE_ECB)
        message = self.sock.recv(16)
        self.sock.send(self.aesdec.decrypt(message))

    def send(self, msg):
        self.sock.send(msg.encode("latin-1"))
        

    def add(self, n):
        self.send("+"+str(n))

    def sub(self, n):
        self.send("-"+str(n))


class StubConnServer:
    def __init__(self, SERVER_IP="127.0.0.1", PORT=5000):
        print(f"Connection established with {SERVER_IP}:{PORT}")

    def send(self, msg):
        print(f"Sending: '{msg}'")

    def add(self, n):
        self.send(str(n))

    def sub(self, n):
        self.send("-"+str(n))

if __name__ == "__main__":
    jnr_server = ConnServer(PORT=9482)
    jnr_server.add(10)
    jnr_server.sub(5)
    while True: # included here to avoid the race condition of the program quitting before anything is actually sent
        pass

