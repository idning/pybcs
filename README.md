# 说明
百度云存储(bcs) python sdk

相关文档请参见：
[bcs wiki](http://dev.baidu.com/wiki/bcs)
[百度开放云平台](http://yun.baidu.com/)

# Usage

1. 在yun.baidu.com(服务管理/我的密钥) 申请ak, sk, bucket, 设置quota, 尝试在网页上上传成功
3. 将获得的ak ,sk , bucket填入example.py 
4. ./example.py

# implemented api:
bcs : 
    + list-bucket

bucket :
    + create(需要在yun.baidu.com手动调整quota, 所以不建议使用该api创建bucket)
    + delete 
    + list obj
    + get acl 
    + set acl
    - enable logging

object: 
    + upload by put
    + upload by post
    + delete 
    + get
    + head
    + set meta
    + copy
    + get acl 
    + set acl
    
superfile(object):
    + create
    
client use pybcs:
    + bcs log


# wish-list: 
    * 支持代理
    * 限速
    * https 支持
    * 如果用户没有装pycurl，应该可以使用httplib实现的httpclient
