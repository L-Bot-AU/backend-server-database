import socket
import random
from Crypto.Cipher import AES

SERVER_IP = "127.0.0.1" # "192.168.137.62"
JNRCONNECT_PORT = 9482
SNRCONNECT_PORT = 11498

class ConnServer:
    def __init__(self, SERVER_IP=SERVER_IP, PORT=SNRCONNECT_PORT):
        print("Connecting")
        self.SERVER_SOCK = (SERVER_IP, PORT)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(self.SERVER_SOCK)
        
        print("Authorising...")
        self.aesdec = AES.new(b"automate_egggggg", AES.MODE_ECB)
        message = self.sock.recv(16)
        self.sock.send(self.aesdec.decrypt(message))
        print("Authorised!")

    def send(self, msg):
        if msg >= 0:
            msg = "+" + msg
        msg = str(msg)
        try:
            self.sock.send(msg.encode("latin-1") + b"\n")
        except (ConnectionResetError, ConnectionAbortedError):
            print("Lost connection :'(")
            self.__init__(*self.SERVER_SOCK)
            self.send(msg)

    def update(self, num):
        self.send(0)
        self.send(num)


class StubConnServer:
    def __init__(self, SERVER_IP=SERVER_IP, PORT=SNRCONNECT_PORT):
        print(f"Connection established with {SERVER_IP}:{PORT}")

    def send(self, msg):
        print(f"Sending: '{msg}'")

    def add(self, n : int):
        self.send("+"+str(n))

    def sub(self, n : int):
        self.send("-"+str(n))

if __name__ == "__main__":
    jnr_server = ConnServer(SERVER_IP, SNRCONNECT_PORT)
    print("Finished!")
    
    while True: # included here to avoid the race condition of the program quitting before anything is actually sent
        n = int(input())
        jnr_server.send(0)
        jnr_server.send(n)
