from project.models.models import User, News, Category
from project.utils import constants
from project.utils.common import user_login_data
from project.utils.response_code import RET
from . import index_blueprint
from flask import render_template, current_app, session, request, jsonify, g
from flask_restful import Api, Resource

index_api = Api(index_blueprint)


# 网站图标展示
@index_blueprint.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/favicon.ico')


@index_blueprint.route('/')
@user_login_data
def index():

    # 点击排行
    news_list = None
    try:
        news_list = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)

    click_news_list = []
    for news in news_list if news_list else []:
        click_news_list.append(news.to_basic_dict())

    # 新闻分类
    categories = Category.query.all()

    categories_dicts = []
    for category in categories:
        categories_dicts.append(category.to_dict())

    data = {
        "user_info": g.user.to_dict() if g.user else None,
        "click_news_list": click_news_list,
        "categories": categories_dicts
    }

    return render_template('news/index.html', data=data)


class NewsListResource(Resource):

    def get(self):

        page = request.args.get('page', '1')
        per_page = request.args.get('per_page', constants.HOME_PAGE_MAX_NEWS)
        category_id = request.args.get('cid', '1')

        try:
            page = int(page)
            per_page = int(per_page)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

        # 查询数据并分页
        filters = [News.status == 0]
        # 如果分类id不为0，那么添加分类id的过滤
        if category_id != "0":
            filters.append(News.category_id == category_id)

        try:
            paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page, per_page, False)
            items = paginate.items
            total_page = paginate.pages
            current_page = paginate.page
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="数据查询失败")

        news_list = []
        for news in items:
            news_list.append(news.to_basic_dict())

        return jsonify(errno=RET.OK, errmsg="OK", totalPage=total_page, currentPage=current_page, newsList=news_list,
                       cid=category_id)


index_api.add_resource(NewsListResource, '/news_list')
