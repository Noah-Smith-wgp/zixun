from flask import render_template, current_app, abort

from project.models.models import News
from project.utils import constants
from . import news_blueprint


@news_blueprint.route('/<int:news_id>')
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

    data = {
        "news": news.to_dict(),
        "click_news_list": click_news_list,
    }

    return render_template('news/detail.html', data=data)
