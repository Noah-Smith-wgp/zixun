from flask import request, current_app, make_response, jsonify
from flask_restful import Api, Resource

from project.libs.captcha.captcha import captcha
from project.utils import constants
from project.utils.response_code import RET
from . import verify_buleprint

verify_api = Api(verify_buleprint)


class ImageCodeResource(Resource):
    """获取图片验证码"""
    def get(self):
        # 验证码编号
        code_id = request.args.get('code_id')
        # 生成验证码
        text, image = captcha.generate_captcha()
        try:
            # 保存验证码
            current_app.redis_store.setex('img_' + code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)
        except Exception as e:
            current_app.logger.error(e)
            return make_response(jsonify(errno=RET.DATAERR, errmsg='保存图形验证码失败'))

        response = make_response(image)
        response.headers['Content-Type'] = 'image/jpg'
        return response


verify_api.add_resource(ImageCodeResource, '/image_code')