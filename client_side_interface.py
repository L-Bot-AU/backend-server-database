from sqlalchemy import Column, Integer, String, create_engine
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

key = b'automate_egggggg'
aesenc = AES.new(key, AES.MODE_ECB)
aesdec = AES.new(key, AES.MODE_ECB)

days = ["monday", "tuesday", "wednesday", "thursday", "friday"]
times = ["Morning", "Break 1", "Break 2"]
# weeks = ["A", "B", "C"]
cycledays = days
# cycledays = [day+week for day in days for week in weeks]

CLIENT_PORT = 2910
JNRCOUNTER_PORT = 9482
SNRCOUNTER_PORT = 11498


async def client_help(websocket, path):
    print(f"Connection received from {websocket} at {path}")
    options = {
        "/snrCount": lambda :str(count("snr")),
        "/jnrCount": lambda :str(count("jnr")),
        "/jnrPredictions": get_predictions("jnr"),
        "/snrPredictions": get_predictions("snr")
    }
    await websocket.send(options.get(path, lambda :"Could not recognise action")())


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

        print(f"Connection from {address[0]}:{address[1]}")

        plaintext = bytes([random.randint(0, 0xff) for _ in range(16)])
        client.send(aesenc.encrypt(plaintext))
        try:
            msg = client.recv(16)
            if msg == plaintext:
                print("Verification succeeded")
                while True:
                    sock.settimeout(None)
                    inc = eval(client.recv(1024))
                    session.query(Count).first().jnrvalue += inc
                    session.commit()
        except Exception as e:
            print(e, "(recieved from jnr port)")

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

        print(f"Connection from {address[0]}:{address[1]}")

        plaintext = bytes([random.randint(0, 0xff) for _ in range(16)])
        client.send(aesenc.encrypt(plaintext) + b"\n")
        try:
            msg = client.recv(16)
            if msg == plaintext:
                print("Verification succeeded")
                while True:
                    sock.settimeout(None)
                    inc = eval(client.recv(1024))
                    session.query(Count).first().snrvalue += inc
                    session.commit()
        except Exception as e:
            print(e, "(recieved from snr port)")

        client.close()


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
        assert count >= 0
        return count


    @validates("snr_expected")
    def validate_snrexpected(self, key, count):
        assert count >= 0
        return count


class Count(Base):
    __tablename__ = "count"

    id = Column(Integer, primary_key=True)
    snrvalue = Column(Integer, default=0)
    jnrvalue = Column(Integer, default=0)


    @validates("snrvalue")
    def valid_snrvalue(self, key, count):
        assert count >= 0
        return count


    @validates("jnrvalue")
    def valid_jnrvalue(self, key, count):
        assert count >= 0
        return count


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
"""
Session = sessionmaker(bind=engine)
begsession = Session()

Base.metadata.drop_all(begengine)
Base.metadata.create_all(begengine)

for day in days:
    for time in times:
        d = Data(day=day, time=time)
        begsession.add(d)

begsession.add(Count())

begsession.commit()
"""
threading.Timer(0, daily_update_loop).start()

start_server = websockets.serve(client_help, "0.0.0.0", CLIENT_PORT)

#loop = asyncio.get_event_loop()
#loop.run_until_complete(main())
#loop.close()
#asyncio.ensure_future(snr_updater())

threading.Thread(target=snr_updater).start()
threading.Thread(target=jnr_updater).start()

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
