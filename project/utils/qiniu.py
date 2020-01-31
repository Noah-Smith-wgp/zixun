from qiniu import Auth, put_data
import logging


# Access Key 和 Secret Key
QINIU_ACCESS_KEY = 'hjL-pqbOr_9UrGQPc3G8F2OKRDp5UJ87VxgEkdSo'
QINIU_SECRET_KEY = 'eT7GGmP0t9xE-yuzmdSoASonmPMz8qJb7kpBwBCL'
QINIU_BUCKET_NAME = 'noah-smith'


def qiniu_upload(data):
    """七牛云存储上传文件"""
    if not data:
        return None
    try:
        # 创建对象
        q = Auth(access_key=QINIU_ACCESS_KEY, secret_key=QINIU_SECRET_KEY)

        # 生成上传 Token，可以指定过期时间等
        token = q.upload_token(QINIU_BUCKET_NAME)
        # print(token)

        # 上传文件
        ret, info = put_data(token, None, data)
    except Exception as e:
        logging.error(e)
        raise e
    else:
        if info and info.status_code != 200:
            print(info)
            raise Exception("上传文件到七牛失败")

        # 返回七牛中保存的图片名，这个图片名也是访问七牛获取图片的路径
        key = ret['key']
        print(key)
        return key


if __name__ == '__main__':
    file_name = input("输入上传的文件")
    with open(file_name, "rb") as f:
        qiniu_upload(f.read())
