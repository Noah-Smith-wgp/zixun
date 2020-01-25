import random
import re
from flask import request, current_app, make_response, jsonify, session
from flask_restful import Api, Resource, reqparse

from project import db
from project.libs.captcha.captcha import captcha
from project.libs.yuntongxun.ccp_sms import CCP
from project.models.models import User
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


def check_mobile(value):

    if not re.match(r'1[3-9]\d{9}', value):
        raise ValueError('手机号不正确')
    return value


class SmsCodeResource(Resource):
    """短信验证码"""
    def post(self):

        parse = reqparse.RequestParser()
        parse.add_argument('mobile', location='json', required=True, type=check_mobile, help='手机号不正确')
        parse.add_argument('image_code', location='json', required=True)
        parse.add_argument('image_code_id', location='json', required=True)

        args = parse.parse_args()

        mobile = args.get('mobile')
        image_code = args.get('image_code')
        image_code_id = args.get('image_code_id')

        # 提取发送短信的标记 60秒避免频繁请求短信验证码
        send_flag = current_app.redis_store.get('send_flag_%s' % mobile)
        # 判断发送短信的标记是否存在（如果存在：频繁发送短信。反之，频率正常）
        if send_flag:
            return jsonify(errno=RET.DATAEXIST, errmsg="发送短信过于频繁")

        try:
            server_image_code = current_app.redis_store.get('img_' + image_code_id)
            if server_image_code:
                server_image_code = server_image_code.decode()
                current_app.redis_store.delete('img_' + image_code_id)
            else:
                return jsonify(errno=RET.NODATA, errmsg="验证码已过期")
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="获取图片验证码失败")

        if image_code.lower() != server_image_code.lower():
            return jsonify(errno=RET.DATAERR, errmsg="验证码输入错误")

        try:
            user = User.query.filter_by(mobile=mobile).first()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="数据库查询错误")
        if user:
            # 该手机已被注册
            return jsonify(errno=RET.DATAEXIST, errmsg="该手机已被注册")

        # 生成短信验证码：生成6位数验证码
        sms_code = '%06d' % random.randint(0, 999999)
        current_app.logger.info('短信验证码为:' + sms_code)

        current_app.redis_store.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        current_app.redis_store.setex('send_flag_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)

        # 发送短信验证码
        CCP().send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES // 60], 1)

        return jsonify(errno=RET.OK, errmsg="发送成功")


class RegisterResource(Resource):
    """注册"""
    def post(self):

        parse = reqparse.RequestParser()
        parse.add_argument('mobile', location='json', required=True, type=check_mobile)
        parse.add_argument('smscode',location='json', required=True)
        parse.add_argument('password', location='json', required=True)

        args = parse.parse_args()

        mobile = args.get('mobile')
        smscode = args.get('smscode')
        password = args.get('password')

        try:
            server_smscode = current_app.redis_store.get('sms_%s' % mobile)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="获取本地验证码失败")

        if not server_smscode:
            # 短信验证码过期
            return jsonify(errno=RET.NODATA, errmsg="短信验证码过期")

        if smscode != server_smscode.decode():
            return jsonify(errno=RET.DATAERR, errmsg="短信验证码错误")

        try:
            current_app.redis_store.delete('sms_%s' % mobile)
        except Exception as e:
            current_app.logger.error(e)

        user = User()
        user.nick_name = mobile
        user.mobile = mobile
        user.password = password

        try:
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)
            return jsonify(errno=RET.DATAERR, errmsg="数据保存错误")

        # 状态保持
        session["user_id"] = user.id
        session["nick_name"] = user.nick_name
        session["mobile"] = user.mobile

        return jsonify(errno=RET.OK, errmsg="OK")


verify_api.add_resource(ImageCodeResource, '/image_code')
verify_api.add_resource(SmsCodeResource, '/sms_code')
verify_api.add_resource(RegisterResource, '/register')
