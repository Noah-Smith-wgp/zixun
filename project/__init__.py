import redis
from flask import Flask
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf

from config import Config, DevelopmentConfig, setup_log

# 记录日志
from project.utils.common import do_index_class

setup_log(DevelopmentConfig)


def get_app(config=Config):
    app = Flask(__name__)

    app.config.from_object(config)

    # db = SQLAlchemy(app)

    redis_store = redis.StrictRedis(host=config.REDIS_HOST, port=config.REDIS_PORT)
    app.redis_store = redis_store

    CSRFProtect(app)

    Session(app)

    # 添加自定义过滤器
    app.add_template_filter(do_index_class, 'index_class')

    return app


app = get_app(DevelopmentConfig)

db = SQLAlchemy(app)


@app.after_request
def after_request(response):
    # 调用函数生成 csrf_token
    csrf_token = generate_csrf()
    # 通过 cookie 将值传给前端
    response.set_cookie("csrf_token", csrf_token)
    return response


from project.apps.index import index_blueprint
app.register_blueprint(index_blueprint)

from project.apps.verification import verify_blueprint
app.register_blueprint(verify_blueprint)

from project.apps.news import news_blueprint
app.register_blueprint(news_blueprint)
