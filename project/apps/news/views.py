from flask import render_template, current_app, abort, g, jsonify, request
from flask_restful import Api, Resource, reqparse

from project.models.models import News, Comment, CommentLike, User
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
    comments = None
    try:
        comments = Comment.query.filter(Comment.news_id == news_id).order_by(Comment.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)

    comment_like_ids = []
    if g.user:
        # 如果当前用户已登录
        try:
            comment_ids = [comment.id for comment in comments]
            if len(comment_ids) > 0:
                # 取到当前用户在当前新闻的所有评论点赞的记录
                comment_likes = CommentLike.query.filter(CommentLike.comment_id.in_(comment_ids),
                                                         CommentLike.user_id == g.user.id).all()
                # 取出记录中所有的评论id
                comment_like_ids = [comment_like.comment_id for comment_like in comment_likes]
        except Exception as e:
            current_app.logger.error(e)

    comment_list = []
    for item in comments if comments else []:
        comment_dict = item.to_dict()
        comment_dict["is_like"] = False
        # 判断用户是否点赞该评论
        if g.user and item.id in comment_like_ids:
            comment_dict["is_like"] = True
        comment_list.append(comment_dict)

    # 当前登录用户是否关注当前新闻作者
    is_followed = False
    # 判断用户是否收藏过该新闻
    is_collected = False
    if g.user:
        if news in g.user.collection_news:
            is_collected = True
        if news.user is not None:
            if news.user.followers.filter(User.id == g.user.id).count() > 0:
                is_followed = True

    data = {
        "news": news.to_dict(),
        "click_news_list": click_news_list,
        "is_collected": is_collected,
        "user_info": g.user.to_dict() if g.user else None,
        "comments": comment_list,
        "is_followed": is_followed
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


class CommentLikeResource(Resource):
    @user_login_data
    def post(self):

        if not g.user:
            return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

            # 获取参数
        comment_id = request.json.get("comment_id")
        news_id = request.json.get("news_id")
        action = request.json.get("action")

        # 判断参数
        if not all([comment_id, news_id, action]):
            return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

        if action not in ("add", "remove"):
            return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

        # 查询评论数据
        try:
            comment = Comment.query.get(comment_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="查询数据失败")

        if not comment:
            return jsonify(errno=RET.NODATA, errmsg="评论数据不存在")

        if action == "add":
            comment_like = CommentLike.query.filter_by(comment_id=comment_id, user_id=g.user.id).first()
            if not comment_like:
                comment_like = CommentLike()
                comment_like.comment_id = comment_id
                comment_like.user_id = g.user.id
                db.session.add(comment_like)
                # 增加点赞条数
                comment.like_count += 1
        else:
            # 删除点赞数据
            comment_like = CommentLike.query.filter_by(comment_id=comment_id, user_id=g.user.id).first()
            if comment_like:
                db.session.delete(comment_like)
                # 减小点赞条数
                comment.like_count -= 1

        try:
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return jsonify(errno=RET.DBERR, errmsg="操作失败")
        return jsonify(errno=RET.OK, errmsg="操作成功")


class FollowedUserResource(Resource):
    @user_login_data
    def post(self):

        """关注/取消关注用户"""
        if not g.user:
            return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

        user_id = request.json.get("user_id")
        action = request.json.get("action")

        if not all([user_id, action]):
            return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

        if action not in ("follow", "unfollow"):
            return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

        # 查询到关注的用户信息
        try:
            target_user = User.query.get(user_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="查询数据库失败")

        if not target_user:
            return jsonify(errno=RET.NODATA, errmsg="未查询到用户数据")

        # 根据不同操作做不同逻辑
        if action == "follow":
            if target_user.followers.filter(User.id == g.user.id).count() > 0:
                return jsonify(errno=RET.DATAEXIST, errmsg="当前已关注")
            target_user.followers.append(g.user)
        else:
            if target_user.followers.filter(User.id == g.user.id).count() > 0:
                target_user.followers.remove(g.user)

        # 保存到数据库
        try:
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="数据保存错误")

        return jsonify(errno=RET.OK, errmsg="操作成功")


news_api.add_resource(NewsCollectResource, '/news_collect')
news_api.add_resource(NewsCommentResource, '/news_comment')
news_api.add_resource(CommentLikeResource, '/comment_like')
news_api.add_resource(FollowedUserResource, '/followed_user')
