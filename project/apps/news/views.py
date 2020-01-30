from flask import render_template, current_app, abort, g, jsonify, request
from flask_restful import Api, Resource, reqparse

from project.models.models import News, Comment
from project.utils import constants
from project.utils.common import user_login_data
from project.utils.response_code import RET
from . import news_blueprint
from project import db

news_api = Api(news_blueprint)


@news_blueprint.route('/<int:news_id>')
@user_login_data
def news_detail(news_id):
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        abort(404)

    if not news:
        # 返回数据未找到的页面
        abort(404)

    news.clicks += 1

    # 获取点击排行数据
    news_list = None
    try:
        news_list = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)

    click_news_list = []
    for new in news_list if news_list else []:
        click_news_list.append(new.to_basic_dict())

    # 获取当前新闻的评论
    comments = []
    try:
        comments = Comment.query.filter(Comment.news_id == news_id).order_by(Comment.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)
    comment_list = []
    for item in comments:
        comment_dict = item.to_dict()
        comment_list.append(comment_dict)

    # 判断是否收藏该新闻
    is_collected = False
    if g.user:
        if news in g.user.collection_news:
            is_collected = True

    data = {
        "news": news.to_dict(),
        "click_news_list": click_news_list,
        "is_collected": is_collected,
        "user_info": g.user.to_dict() if g.user else None,
        "comments": comment_list
    }

    return render_template('news/detail.html', data=data)


def check_action(action):
    if action not in ("collect", "cancel_collect"):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    else:
        return action


class NewsCollectResource(Resource):
    @user_login_data
    def post(self):

        user = g.user
        if not user:
            return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

        parse = reqparse.RequestParser()
        parse.add_argument('news_id', location='json', required=True)
        parse.add_argument('action', location='json', required=True, type=check_action)
        args = parse.parse_args()
        news_id = args.get('news_id')
        action = args.get('action')

        try:
            news = News.query.get(news_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="查询数据失败")

        if not news:
            return jsonify(errno=RET.NODATA, errmsg="新闻数据不存在")

        if action == "collect":
            user.collection_news.append(news)
        else:
            user.collection_news.remove(news)

        try:
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return jsonify(errno=RET.DBERR, errmsg="保存失败")
        return jsonify(errno=RET.OK, errmsg="操作成功")


class NewsCommentResource(Resource):
    @user_login_data
    def post(self):

        user = g.user
        if not user:
            return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")
        # 获取参数
        data_dict = request.json
        news_id = data_dict.get("news_id")
        comment_str = data_dict.get("comment")
        parent_id = data_dict.get("parent_id")

        if not all([news_id, comment_str]):
            return jsonify(errno=RET.PARAMERR, errmsg="参数不足")

        try:
            news = News.query.get(news_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="查询数据失败")

        if not news:
            return jsonify(errno=RET.NODATA, errmsg="该新闻不存在")

        # 初始化模型，保存数据
        comment = Comment()
        comment.user_id = user.id
        comment.news_id = news_id
        comment.content = comment_str
        if parent_id:
            comment.parent_id = parent_id

        # 保存到数据库
        try:
            db.session.add(comment)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="保存评论数据失败")

        # 返回响应
        return jsonify(errno=RET.OK, errmsg="评论成功", data=comment.to_dict())


news_api.add_resource(NewsCollectResource, '/news_collect')
news_api.add_resource(NewsCommentResource, '/news_comment')
