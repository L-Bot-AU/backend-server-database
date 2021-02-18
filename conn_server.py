import socket
import random
from Crypto.Cipher import AES

SERVER_IP = "192.168.137.1"
JNRCONNECT_PORT = 9482
SMRCONNECT_PORT = 11498

class ConnServer:
    def __init__(self, SERVER_IP, PORT):
        print("Connecting")
        self.SERVER_SOCK = (SERVER_IP, PORT)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(self.SERVER_SOCK)
        print("Connected")
        
        print("Authing")
        self.aesdec = AES.new(b"automate_egggggg", AES.MODE_ECB)
        message = self.sock.recv(16)
        self.sock.send(self.aesdec.decrypt(message))
        print("Authed")

    def send(self, msg):
        self.sock.send(msg.encode("latin-1"))
    
    def add(self, n : int):
        print(f"Sending +{n}")
        self.send("+"+str(n))

    def sub(self, n : int):
        print(f"Sending -{n}")
        self.send("-"+str(n))


class StubConnServer:
    def __init__(self, SERVER_IP, PORT):
        print(f"Connection established with {SERVER_IP}:{PORT}")

    def send(self, msg):
        print(f"Sending: '{msg}'")

    def add(self, n : int):
        self.send("+"+str(n))

    def sub(self, n : int):
        self.send("-"+str(n))

if __name__ == "__main__":
    jnr_server = ConnServer(SERVER_IP, JNRCONNECT_PORT)
    jnr_server.add(10)
    jnr_server.sub(5)
    print("Finished!")
    while True: # included here to avoid the race condition of the program quitting before anything is actually sent
        pass
