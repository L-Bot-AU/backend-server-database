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

CLIENT_PORT = 2910 # for blair's website
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


async def client_help(websocket, path):
    """
    The asynchronous coroutine attached to a websocket which sends the requested data to Blair's website

    websocket: the websocket object which Blair's website will connect to
    path: the path from the socket indicating what information the website wishes to receive (1 of 4 possibilities)
    """
    print(f"Connection received from {websocket} at {path}")
    options = {
        "/snrCount": lambda:str(count("snr")), # return number of people in the senior library
        "/jnrCount": lambda:str(count("jnr")), # return number of people in the junior library
        "/jnrPredictions": lambda:get_predictions("jnr"), # return 
        "/snrPredictions": lambda:get_predictions("snr")
    }
    await websocket.send(options.get(path, lambda:"Could not recognise action")())


def jnr_updater():
    Session = sessionmaker(bind=engine)
    session = Session()
    print("Starting jnr_updater")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("0.0.0.0", JNRCOUNTER_PORT))
    sock.listen(10)
    while True:
        client, address = sock.accept()
        sock.settimeout(6)

        print(f"Connection from {address[0]} on jnr port")

        plaintext = bytes([random.randint(0, 0xff) for _ in range(16)])
        print("Sending verification string")
        client.send(aesenc.encrypt(plaintext) + b"\n")
        try:
            msg = client.recv(16)
            if msg == plaintext:
                print("Verification succeeded")
                while True:
                    sock.settimeout(None)
                    print("Recieving message")
                    msg = client.recv(1024)
                    print(msg)
                    inc = eval(msg + b"+0")
                    print(inc)
                    session.query(Count).first().jnrvalue += inc
                    session.commit()
            else:
                raise Exception("Verification failed")
        except Exception as e:
            print(repr(e), "(recieved from jnr port)")
        client.close()


def snr_updater():
    Session = sessionmaker(bind=engine)
    session = Session()
    print("Starting snr_updater")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("0.0.0.0", SNRCOUNTER_PORT))
    sock.listen(10)
    while True:
        client, address = sock.accept()
        sock.settimeout(6)

        print(f"Connection from {address[0]} on snr port")

        plaintext = bytes([random.randint(0, 0xff) for _ in range(16)])
        print("Sending verification string")
        client.send(aesenc.encrypt(plaintext) + b"\n")
        try:
            msg = client.recv(16)
            if msg == plaintext:
                print("Verification succeeded")
                while True:
                    sock.settimeout(None)
                    print("Recieving message")
                    msg = client.recv(1024)
                    print(msg)
                    inc = eval(msg)
                    print(inc)
                    session.query(Count).first().snrvalue += inc
                    session.commit()
            else:
                raise Exception("Verification failed")
        except Exception as e:
            print(repr(e), "(recieved from snr port)")
        client.close()


def plot_data():
    print(0)
    threading.Timer(5, plot_data).start()


def daily_update_loop():
    Session = sessionmaker(bind=engine)
    session = Session()
    week = 1 # TODO: find way of getting week of term from date
    term = 1 # TODO: find way of getting term today

    for day in days:
        predData = getData(term, week, days.index(day) + 1)
        for time in times:
            data = session.query(Data).filter_by(day=day, time=time).first()
            data.jnr_expected = (predData[2*times.index(data.time)] + predData[2*times.index(data.time)+1]) // 2
            data.snr_expected = 10

    session.commit()
    current = datetime.datetime.now()
    new = current.replace(day=current.day, hour=1, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
    secs = (new - current).total_seconds()
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
    predictions["data"] = [[0 for _ in range(len(times))]]
    for day in days:
        day_predictions = []
        for i, time in enumerate(times):
            data = session.query(Data).filter_by(day=day, time=time).first()
            if lib == "snr":
                pred = data.snr_expected
            else:
                pred = data.jnr_expected
            day_predictions.append(pred)
            if pred > predictions["data"][0][i]:
                predictions["data"][0][i] = pred
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
threading.Timer(5, plot_data).start()

start_server = websockets.serve(client_help, "0.0.0.0", CLIENT_PORT)

#loop = asyncio.get_event_loop()
#loop.run_until_complete(main())
#loop.close()
#asyncio.ensure_future(snr_updater())

threading.Thread(target=snr_updater).start()
threading.Thread(target=jnr_updater).start()

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
