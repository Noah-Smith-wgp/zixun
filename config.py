import logging
from logging.handlers import RotatingFileHandler

import redis


class Config(object):
    """配置类"""
    DEBUG = True
    SECRET_KEY = "EjpNVSNQTyGi1VvWECj9TvC/+kq3oujee2kTfQUs8yCM6xX9Yjq52v54g+HVoknA"

    # 数据库配置
    SQLALCHEMY_DATABASE_URI = 'mysql://python:mysql@122.51.161.120:3306/zixun'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # 请求结束之后进行数据自动提交
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True

    # redis配置
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379

    # session配置
    SESSION_TYPE = "redis"  # 指定 session 保存到 redis 中
    SESSION_USE_SIGNER = True  # 让 cookie 中的 session_id 被加密签名处理
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)  # 使用 redis 的实例
    PERMANENT_SESSION_LIFETIME = 86400  # session 的有效期，单位是秒

    # 默认日志等级
    LOG_LEVEL = logging.DEBUG


class DevelopmentConfig(Config):

    DEBUG = True


class ProductionConfig(Config):

    DEBUG = False

    LOG_LEVEL = logging.ERROR


def setup_log(config):
    """配置日志"""

    # 设置日志的记录等级
    logging.basicConfig(level=config.LOG_LEVEL)  # 调试debug级
    # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
    file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024 * 1024 * 100, backupCount=10)
    # 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
    formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter)
    # 为全局的日志工具对象（flask app使用的）添加日志记录器
    logging.getLogger().addHandler(file_log_handler)
