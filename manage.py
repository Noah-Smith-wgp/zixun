import redis
from flask import Flask
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

app = Flask(__name__)


class Config(object):
    """配置类"""
    DEBUG = True
    SECRET_KEY = "EjpNVSNQTyGi1VvWECj9TvC/+kq3oujee2kTfQUs8yCM6xX9Yjq52v54g+HVoknA"

    # 数据库配置
    SQLALCHEMY_DATABASE_URI = 'mysql://python:mysql@122.51.161.120:3306/zixun'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # redis配置
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379

    # session配置
    SESSION_TYPE = "redis"  # 指定 session 保存到 redis 中
    SESSION_USE_SIGNER = True  # 让 cookie 中的 session_id 被加密签名处理
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)  # 使用 redis 的实例
    PERMANENT_SESSION_LIFETIME = 86400  # session 的有效期，单位是秒


app.config.from_object(Config)
db = SQLAlchemy(app)
redis_store = redis.StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT)
CSRFProtect(app)
Session(app)

manager = Manager(app)
Migrate(app, db)
manager.add_command('db', MigrateCommand)


@app.route('/')
def index():
    return 'index'


if __name__ == '__main__':
    # app.run()
    manager.run()
