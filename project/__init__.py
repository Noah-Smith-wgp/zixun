import redis
from flask import Flask
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

from config import Config, DevelopmentConfig


def get_app(config=Config):
    app = Flask(__name__)

    app.config.from_object(config)

    # db = SQLAlchemy(app)

    redis_store = redis.StrictRedis(host=config.REDIS_HOST, port=config.REDIS_PORT)
    app.redis_store = redis_store

    CSRFProtect(app)

    Session(app)

    return app


app = get_app(DevelopmentConfig)

db = SQLAlchemy(app)
