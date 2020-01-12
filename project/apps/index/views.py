from . import index_buleprint
from flask import render_template, current_app


# 网站图标展示
@index_buleprint.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/favicon.ico')


@index_buleprint.route('/')
def index():
    return render_template('news/index.html')
