import socket
import random
from Crypto.Cipher import AES

SERVER_IP = "127.0.0.1" # "192.168.137.62"
JNRCONNECT_PORT = 9482
SNRCONNECT_PORT = 11498

class ConnServer:
    """
    Creates a connection between the current computer and the server

    attributes:
    sock: the raw socket object used for connecting
    aesdec: object used for decrypting message with AES ECB key

    methods:
    send: sends a string to the server
    update: sends a numerical update to the server (calls send)
    """
    def __init__(self, SERVER_IP=SERVER_IP, PORT=SNRCONNECT_PORT):
        """
        Initialises connection with server with specified IP and PORT

        SERVER_IP: the IP address to connect to (default is a defined global variable)
        PORT: the port in the IP address to connect to (default is the senior library port)
        """
        print("Connecting")
        # initialise socket and connect to server socket
        self.SERVER_SOCK = (SERVER_IP, PORT)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(self.SERVER_SOCK)
        
        print("Authorising...")
        # receive random bytes and decrypt it for authorisation
        self.aesdec = AES.new(b"automate_egggggg", AES.MODE_ECB)
        message = self.sock.recv(16)
        self.sock.send(self.aesdec.decrypt(message))
        print("Authorised!")

    def send(self, msg):
        try:
            # send update
            self.sock.send(msg.encode("latin-1"))
        except (ConnectionResetError, ConnectionAbortedError):
            # if there is a connection error, connect to the socket and send the update again
            print("Lost connection :'(")
            self.__init__(*self.SERVER_SOCK)
            self.send(msg)

    def update(self, num):
        # if the number is non-negative, add a + in front of it (to deal with weird bug where multiple requests would merge into one, so the server can just call eval())
        if num >= 0:
            num = "+" + str(num)
        else:
            num = str(num)
        self.send("+0") # for some reason, if the server socket closes, only the second request will recognise this. Thus, a "dummy" request must first be sent
        self.send(num)


class StubConnServer:
    """
    Stub class for testing the person counter without internet
    """
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
        jnr_server.send(n)
