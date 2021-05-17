from sqlalchemy import Column, Integer, String, create_engine, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import validates, sessionmaker
from Crypto.Cipher import AES
from getData import getData
import websockets
import threading
import datetime
import asyncio
import random
import base64
import socket
import json
import os


# os.remove("library_usage.db")
engine = create_engine("sqlite:///library_usage.db", echo=False)
Base = declarative_base()

KEY = b'automate_egggggg'
# two seperate objects are required for decrypting and encrypting (PyCryptoDome weirdness)
aesenc = AES.new(KEY, AES.MODE_ECB)
aesdec = AES.new(KEY, AES.MODE_ECB)

days = ["monday", "tuesday", "wednesday", "thursday", "friday"]
times = ["Morning", "Break 1", "Break 2"]
# weeks = ["A", "B", "C"]
cycledays = days
# cycledays = [day+week for day in days for week in weeks]

CLIENT_PORT = 2910 # for library overview website
JNRCOUNTER_PORT = 9482 # for junior library count updates
SNRCOUNTER_PORT = 11498 # for senior library count updates


def restartdb():
    Session = sessionmaker(bind=engine)
    begsession = Session()

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    
    for day in days:
        for time in times:
            d = Data(day=day, time=time)
            begsession.add(d)

    begsession.add(Count())

    begsession.commit()
    print("Reset database")


# TODO: remove this websocket coroutine and replace with socket.io
async def client_help(websocket, path):
    """
    The asynchronous coroutine attached to a websocket which sends the requested data to the library overview website

    websocket: the websocket object which Blair's website will connect to
    path: the path from the socket indicating what information the website wishes to receive (1 of 4 possibilities)
    """
    print(f"Connection received from {websocket} at {path}")
    options = {
        "/snrCount": lambda:str(count("snr")), # return number of people in the senior library
        "/jnrCount": lambda:str(count("jnr")), # return number of people in the junior library
        "/jnrPredictions": lambda:get_predictions("jnr"), # return predicted number of people in junior library
        "/snrPredictions": lambda:get_predictions("snr")  # return predicted number of people in senior library
    }
    await websocket.send(options.get(path, lambda:"Could not recognise action")())


def jnr_updater():
    print("Starting jnr_updater")
    # start session with database
    Session = sessionmaker(bind=engine)
    session = Session()

    # create socket and listen
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("0.0.0.0", JNRCOUNTER_PORT))
    sock.listen(10)

    while True:
        # wait for connection
        client, address = sock.accept()

        # timeout the connection if the client takes to long to send a response
        sock.settimeout(6)

        print(f"Connection from {address[0]} on jnr port")

        # TODO: replace this verification system with SSL
        # create random string of bytes for verification
        plaintext = bytes([random.randint(0, 0xff) for _ in range(16)])

        # send encrypted verification string
        print("Sending verification string")
        client.send(aesenc.encrypt(plaintext) + b"\n")
        try:
            # receive new string and check if the connecting client can decrypt it
            msg = client.recv(16)
            if msg == plaintext:
                print("Verification succeeded")
                while True:
                    # once verification has succeeded, no time limit is required
                    sock.settimeout(None)

                    # receive the update to the number of people in the junior library (+x or -x)
                    print("Recieving message")
                    msg = client.recv(1024)
                    print(msg)
                    inc = eval(msg + b"+0") # add a "+0" at the end in case the string has a trailing + or - (due to weird bug where requests get merged)
                    print(inc)

                    # update the count in the junior library
                    session.query(Count).first().jnrvalue += inc
                    session.commit()
            else:
                # if verification is failed, raise an error and let the try/except statement catch it
                raise Exception("Verification failed")
        except Exception as e:
            socket.settimeout(None)
            # print the error (due to verification taking too long, verification being unsuccessful, client closing the connection or some other unknown error
            print(repr(e), "(recieved from jnr port)")
        client.close()


def snr_updater():
    print("Starting snr_updater")
    # start session with database
    Session = sessionmaker(bind=engine)
    session = Session()

    # create socket and listen
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("0.0.0.0", SNRCOUNTER_PORT))
    sock.listen(10)
    while True:
        # wait for connection
        client, address = sock.accept()

        # timeout the connection if the client takes to long to send a response
        sock.settimeout(6)

        print(f"Connection from {address[0]} on snr port")

        # TODO: replace this verification system with SSL
        # create random string of bytes for verification        
        plaintext = bytes([random.randint(0, 0xff) for _ in range(16)])

        # send encrypted verification string
        print("Sending verification string")
        client.send(aesenc.encrypt(plaintext) + b"\n")
        try:
            # receive new string and check if the connecting client can decrypt it
            msg = client.recv(16)
            if msg == KEY:
                print("Verification succeeded")
                while True:
                    # once verification has succeeded, no time limit is required
                    sock.settimeout(None)

                    # receive the update to the number of people in the senior library (+x or -x)
                    print("Recieving message")
                    msg = client.recv(1024)
                    print(msg)
                    inc = eval(msg + b"0") # add a "+0" at the end in case the string has a trailing + or - (due to weird bug where requests get merged)
                    print(inc)

                    # update the count in the senior library
                    session.query(Count).first().snrvalue += inc
                    session.commit()
                    with open("bleh.txt", "a") as f:
                        # if verification is failed, raise an error and let the try/except statement catch it
                        f.write(f"{session.query(Count).first().snrvalue} {datetime.datetime.now()}\n")
            else:
                raise Exception("Verification failed")
        except Exception as e:
            sock.settimeout(None)
            # print the error (due to verification taking too long, verification being unsuccessful, client closing the connection or some other unknown error
            print(repr(e), "(recieved from snr port)")
        client.close()


# called once every day
def daily_update_loop():
    # start session with database
    Session = sessionmaker(bind=engine)
    session = Session()
    
    week = 1 # TODO: find way of getting week of term from date
    term = 1 # TODO: find way of getting term today

    # loop through each day of the week and update the predicted value on that day
    for day in range(1, 6):
        predData = getData(term, week, day + 1)
        for i, time in enumerate(times):
            data = session.query(Data).filter_by(day=days[day-1], time=time).first()
            # for now, update with the average of the minumum and maximum
            data.jnr_expected = (predData["Jnr"][2*i] + predData["Jnr"][2*i+1]) // 2 
            data.snr_expected = (predData["Snr"][2*i] + predData["Snr"][2*i+1]) // 2

    session.commit()

    # find next time until update
    current = datetime.datetime.now()
    new = current.replace(day=current.day, hour=1, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
    secs = (new - current).total_seconds()

    # wait for that difference in time
    threading.Timer(secs, daily_update_loop).start()


class Data(Base):
    __tablename__ = "data"

    id = Column(Integer, primary_key=True)
    day = Column(String(10), nullable=False)
    time = Column(String(10), nullable=False)
    jnr_expected = Column(Integer, default=0)
    snr_expected = Column(Integer, default=0)


    @validates("jnr_expected")
    def validate_jnrexpected(self, key, count):
        if count < 0:
            return 0
        return count


    @validates("snr_expected")
    def validate_snrexpected(self, key, count):
        if count < 0:
            return 0
        return count


class Count(Base):
    __tablename__ = "count"

    id = Column(Integer, primary_key=True)
    snrvalue = Column(Integer, default=0)
    jnrvalue = Column(Integer, default=0)


    @validates("snrvalue")
    def valid_snrvalue(self, key, count):
        if count < 0:
            return 0
        return count


    @validates("jnrvalue")
    def valid_jnrvalue(self, key, count):
        if count < 0:
            return 0
        return count


class Date(Base):
    __tablename__ = "date"

    id = Column(Integer, primary_key=True)
    date = Column(DateTime, default=datetime.datetime.now)
    time = Column(String(10), nullable=False)
    count = Column(Integer, primary_key=True)


def count(lib):
    Session = sessionmaker(bind=engine)
    session = Session()
    if lib == "snr":
        return session.query(Count).first().snrvalue
    else:
        return session.query(Count).first().jnrvalue


def get_predictions(lib):
    Session = sessionmaker(bind=engine)
    session = Session()
    predictions = {}
    predictions["labels"] = times
    predictions["data"] = [] 
    for day in days:
        day_predictions = []
        for time in times:
            data = session.query(Data).filter_by(day=day, time=time).first()
            if lib == "snr":
                pred = data.snr_expected
            else:
                pred = data.jnr_expected
            day_predictions.append(pred)
        predictions["data"].append(day_predictions)
    return json.dumps(predictions)

"""
@app.route("/<lib>Events")
def events(lib):
    return None


@app.route("/<lib>PastData")
def pastData(lib):
    return "114"


@app.route("/<lib>Noise")
def noise(lib):
    return "114"


@app.route("/<lib>Scanner")
def scanner(lib):
    return "scan"


@app.route("/<lib>CompUse")
def compUse(lib):
    return "5"


@app.route("/<lib>Money")
def money(lib):
    return "WE ARE NOT CRIMINAKLS!!!!!"
"""

#restartdb()

threading.Timer(0, daily_update_loop).start()
"""
threading.Timer(5, plot_data).start()
"""

# TODO: instead of creating a websocket, use socket.io
start_server = websockets.serve(client_help, "0.0.0.0", CLIENT_PORT)

#loop = asyncio.get_event_loop()
#loop.run_until_complete(main())loop.close()
#asyncio.ensure_future(snr_updater())

threading.Thread(target=snr_updater).start()
threading.Thread(target=jnr_updater).start()

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
