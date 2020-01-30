from flask import g, redirect, render_template
from flask_restful import Api, Resource

from project import user_login_data
from . import user_blueprint

user_api = Api(user_blueprint)


@user_blueprint.route('/info')
@user_login_data
def get_user_info():

    user = g.user
    if not user:
        # 用户未登录，重定向到主页
        return redirect('/')

    data = {
        "user_info": user.to_dict(),
    }
    # 渲染模板
    return render_template("news/user.html", data=data)