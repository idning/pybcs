#!/usr/bin/env python
#coding:utf8

import urllib, sys, os
try:
    import json
except:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)))
    import simplejson as json
import logging

import re
import sys
import time
import hmac
import base64
import hashlib
import commands

import config
from common import PyCurlHTTPC 
from common import HttplibHTTPC 
from common import CurlHTTPC

from bucket import Bucket

from common import *

class BCS:
    def __init__(self, host, ak , sk, 
            httpclient_class=HttplibHTTPC, 
            #httpclient_class=PyCurlHTTPC, 
            ):
        self.logger = logging.getLogger('pybcs')
        self.host = host
        self.ak = ak
        self.sk = sk
        
        self.get_url=self.sign('GET', '', '/')
        if (httpclient_class == PyCurlHTTPC):
            try:
                import pycurl
            except :
                self.logger.warn('no pycurl installed , use Httplib instead')
                httpclient_class = HttplibHTTPC

        if (httpclient_class == CurlHTTPC):
            import platform
            sysstr = platform.system()
            if(sysstr =="Windows"):
                httpclient_class = HttplibHTTPC
                
        self.c = httpclient_class()

    @network
    def list_buckets(self):
        rst = self.c.get(self.get_url)
        text = rst['body']
        j = json.loads(text)
        return [self.bucket(b['bucket_name'].encode(config.ENCODING)) for b in j]

    def bucket(self, bucket_name):
        b = Bucket(self, bucket_name)
        return b

    #M(必选): request method. eg: PUT,GET,POST,DELETE,HEAD
    #B(必选): bucketname
    #O(必选): objectname
    #T(可选): 访问时间范围
    #I(可选):  访问ip限制
    #S(可选): 操作object大小限制
    #NOTICE: 请保证输入统一，比如B,O都应该同为unicode或同为utf8
    def sign(self, M, B, O, T=None, I=None, S=None):
        flag = ''
        s =  ''
        if M :   flag+='M'; s += 'Method=%s\n' % M; 
        if B :   flag+='B'; s += 'Bucket=%s\n' % B; 
        if O :   flag+='O'; s += 'Object=%s\n' % O; 
        if T :   flag+='T'; s += 'Time=%s\n'   % T; 
        if I :   flag+='I'; s += 'Ip=%s\n'     % I; 
        if S :   flag+='S'; s += 'Size=%s\n'   % S; 

        s = '\n'.join([flag, s])
        
        def h(sk, body):
            digest = hmac.new(sk, body, hashlib.sha1).digest()
            t = base64.encodestring(digest)
            return urllib.quote(t.strip())

        sign = h(self.sk, s)
        return '%s/%s%s?sign=%s:%s:%s' % (
                self.host, B, O, flag, self.ak, sign)
                
