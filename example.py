#!/usr/bin/env python
#coding:utf8

import pybcs 
import logging

#设置日志级别
pybcs.init_logging(logging.INFO)



AK='YOUR-AK-HERE'
SK='YOUR-SK-HERE'
BUCKET='test-bucket'

bcs = pybcs.BCS('http://bcs.duapp.com/', AK, SK, pybcs.CurlHTTPC)

lst = bcs.list_buckets()
print '---------------- list of bucket : '
for b in lst:
    print b
print '---------------- list end'

#声明一个bucket
b = bcs.bucket('test-bucket')

#创建bucket (创建后需要在yun.baidu.com 手动调整quota, 否则无法上传下载)
#b.create()

#获取bucket acl, 内容是json
print b.get_acl()['body']

#将bucket 设置为公有可读写
#b.make_public()

#申明一个object
o = b.object('/object_name_should_start_with_slash')

#将本地的README 文件上传到
o.put_file('README.md')

#下载文件到 README.download
o.get_to_file('README.download')

o.delete()
