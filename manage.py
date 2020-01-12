from flask import Flask

app = Flask(__name__)


class Config(object):
    """配置类"""
    DEBUG = True


app.config.from_object(Config)


@app.route('/')
def index():
    return 'index'


if __name__ == '__main__':
    app.run()
