from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from getData import getData
from threading import Timer
import datetime
import json
import os


load_dotenv()


app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY"),
    SECURITY_PASSWORD=os.environ.get("SECURITY_PASSWORD"),
    SQLALCHEMY_TRACK_MODIFICATIONS=True,
    SQLALCHEMY_DATABASE_URI="sqlite:///site.db"
)
db = SQLAlchemy(app)


days = ["monday", "tuesday", "wednesday", "thursday", "friday"]
times = ["Morning", "Break 1", "Break 2"]
# weeks = ["A", "B", "C"]
cycledays = days
# cycledays = [day+week for day in days for week in weeks]


def daily_update_loop():
    print("hello")
    week = 1 # TODO: find way of getting week of term from date
    term = 1 # TODO: find way of getting term today

    for day in days:
        predData = getData(term, week, days.index(day) + 1)
        for data in Data.query.filter_by(day=day).all():
            data.expected = (predData[2*times.index(data.time)] + predData[2*times.index(data.time)+1]) // 2

    db.session.commit()
    current = datetime.datetime.now()
    new = current.replace(day=current.day, hour=1, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
    secs = (new - current).total_seconds()
    Timer(secs, daily_update_loop).start()


class Data(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.String(10), nullable=False)
    time = db.Column(db.String(10), nullable=False)
    expected = db.Column(db.Integer, default=0)


    @db.validates("expected")
    def validate_expected(self, key, count):
        assert count >= 0
        return count


class Date(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.datetime.now, nullable=False)
    day = db.Column(db.String(10), default=lambda :days[date.weekday()], nullable=False)
    value = db.Column(db.Integer, default=0)

    
    @db.validates("value")
    def valid_value(self, key, count):
        assert count >= 0
        return count


class Count(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    snrvalue = db.Column(db.Integer, default=0)
    jnrvalue = db.Column(db.Integer, default=0)


    @db.validates("snrvalue")
    def valid_snrvalue(self, key, count):
        assert count >= 0
        return count


    @db.validates("jnrvalue")
    def valid_jnrvalue(self, key, count):
        assert count >= 0
        return count


@app.route("/<lib>Count")
def count(lib):
    if lib == "snr":
        return str(Count.query.first().snrvalue)
    else:
        return str(Count.query.first().jnrvalue)


@app.route("/predictions")
def get_predictions():
    predictions = [] # can be dictionary if required
    for day in days:
        day_predictions = {}
        for data in Data.query.filter_by(day=day).all():
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
db.create_all()

for day in days:
    for time in times:
        d = Data(day=day, time=time)
        db.session.add(d)

db.session.add(Count())

db.session.commit()

Timer(0, daily_update_loop).start()
#"""    

if __name__ == "__main__":
    app.run()
