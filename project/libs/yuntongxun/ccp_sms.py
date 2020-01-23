# -*- coding:utf-8 -*-

# import ssl
# ssl._create_default_https_context =ssl._create_stdlib_context # 解决Mac开发环境下，网络错误的问题


from project.libs.yuntongxun.CCPRestSDK import REST

# 说明：主账号，登陆云通讯网站后，可在"控制台-应用"中看到开发者主账号ACCOUNT SID
_accountSid = '8a216da86e011fa3016e888fda404da5'

# 说明：主账号Token，登陆云通讯网站后，可在控制台-应用中看到开发者主账号AUTH TOKEN
_accountToken = '4bb6da233f53468ea468bd1ae9fe0114'

# 请使用管理控制台首页的APPID或自己创建应用的APPID
_appId = '8a216da86e011fa3016e8cd6fdf750b9'

# 说明：请求地址，生产环境配置成app.cloopen.com
_serverIP = 'sandboxapp.cloopen.com'

# 说明：请求端口 ，生产环境为8883
_serverPort = "8883"

# 说明：REST API版本号保持不变
_softVersion = '2013-12-26'


# 发送模板短信
def send_template_sms(to, datas, tempId):
    """
    云通讯官方提供的发送短信代码实例
    :param to: 手机号码
    :param datas: 内容数据 格式为列表 例如：['123456', '5']，如不需替换请填 ''
    :param tempId: 模板Id
    :return: 成功、失败
    """
    # 初始化REST SDK
    rest = REST(_serverIP, _serverPort, _softVersion)
    rest.setAccount(_accountSid, _accountToken)
    rest.setAppId(_appId)

    # 调用发送短信的接口函数
    result = rest.sendTemplateSMS(to, datas, tempId)
    print(result)


class CCP(object):
    """发送短信的单例类：初始化并提供单例"""
    # 单例设计模式保证内存当中有且只有一个实例化对象

    def __new__(cls, *args, **kwargs):
        # new方法初始化并提供单例
        # 判断是否存在类属性_instance，_instance是类CCP的唯一对象，即单例
        # hasattr('要判断的类对象', '单例属性名')
        if not hasattr(CCP, "_instance"):
            # 如果没有单例，就new一个
            # cls:表示当前类对象CCP，我们将创建出来的对象绑定到CCP
            cls._instance = super(CCP, cls).__new__(cls, *args, **kwargs)

            # rest = REST(_serverIP, _serverPort, _softVersion)
            # cls._instance.rest = rest
            # 初始化REST_SDK：保证rest对象跟单例是同生共死的
            cls._instance.rest = REST(_serverIP, _serverPort, _softVersion)
            cls._instance.rest.setAccount(_accountSid, _accountToken)
            cls._instance.rest.setAppId(_appId)

        return cls._instance

    def send_template_sms(self, to, datas, temp_id):
        """
        发送模板短信单例方法
        :param to: 注册手机号
        :param datas: 模板短信内容数据，格式为列表，例如：['123456', 5]，如不需替换请填 ''
        :param temp_id: 模板编号，默认免费提供id为1的模板
        :return: 发短信结果
        """
        # 调用发送短信的接口函数
        result = self.rest.sendTemplateSMS(to, datas, temp_id)
        if result.get("statusCode") == "000000":
            # 返回0，表示发送短信成功
            return 0
        else:
            # 返回-1，表示发送失败
            return -1


if __name__ == '__main__':
    # 注意：测试的短信模板编号为1
    # send_template_sms('18211672297', ['111111', 5], 1)

    CCP().send_template_sms('18211672297', ['123456', 5], 1)
