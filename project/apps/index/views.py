from project.models.models import User
from . import index_buleprint
from flask import render_template, current_app, session


# 网站图标展示
@index_buleprint.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/favicon.ico')


@index_buleprint.route('/')
def index():
    # 获取当前登录用户的id
    user_id = session.get('user_id')
    # 通过id获取当前用户
    user = None
    if user_id:
        try:
            user = User.query.get(user_id)
        except Exception as e:
            current_app.logger.error(e)

    return render_template('news/index.html', data={"user_info": user.to_dict() if user else None})
