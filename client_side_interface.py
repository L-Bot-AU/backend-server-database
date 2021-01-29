from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import validates, sessionmaker
from getData import getData
from threading import Timer
import websockets
import datetime
import asyncio
import socket
import json
import os


engine = create_engine("sqlite:///library_usage.db", echo="debug")
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()


days = ["monday", "tuesday", "wednesday", "thursday", "friday"]
times = ["Morning", "Break 1", "Break 2"]
# weeks = ["A", "B", "C"]
cycledays = days
# cycledays = [day+week for day in days for week in weeks]

COUNTER_PORT = 9482


async def client_help(websocket, path):
    options = {
        "/snrCount": lambda :str(count("snr")),
        "/jnrCount": lambda :str(count("jnr")),
        "/predictions": get_predictions
    }

    await websocket.send(options.get(path, lambda :"Could not recognise action")())


def daily_update_loop():
    print("hello")
    week = 1 # TODO: find way of getting week of term from date
    term = 1 # TODO: find way of getting term today

    for day in days:
        predData = getData(term, week, days.index(day) + 1)
        for data in session.query(Data).filter_by(day=day).all():
            data.expected = (predData[2*times.index(data.time)] + predData[2*times.index(data.time)+1]) // 2

    session.commit()
    current = datetime.datetime.now()
    new = current.replace(day=current.day, hour=1, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
    secs = (new - current).total_seconds()
    Timer(secs, daily_update_loop).start()


class Data(Base):
    __tablename__ = "data"

    id = Column(Integer, primary_key=True)
    day = Column(String(10), nullable=False)
    time = Column(String(10), nullable=False)
    expected = Column(Integer, default=0)


    @validates("expected")
    def validate_expected(self, key, count):
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
    if lib == "snr":
        return session.query(Count).first().snrvalue
    else:
        return session.query(Count).first().jnrvalue


def get_predictions():
    predictions = [] # can be dictionary if required
    for day in days:
        day_predictions = {}
        for data in session.query(Data).filter_by(day=day).all():
            day_predictions[data.time] = data.expected
        predictions.append(day_predictions)
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
#"""
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)

for day in days:
    for time in times:
        d = Data(day=day, time=time)
        session.add(d)

session.add(Count())

session.commit()

Timer(0, daily_update_loop).start()
#"""

start_server = websockets.serve(client_help, "0.0.0.0", 2910)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(("0.0.0.0", COUNTER_PORT))
sock.listen(10)

while True:
    client, address = sock.accept()
    
    print(f"Connection from {addr}")

    client.send("test")
    client.close()
