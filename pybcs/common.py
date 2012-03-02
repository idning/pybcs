#!/usr/bin/env python
#coding:utf8
import urllib
import urllib2
import httplib
import cookielib
import os
import re
import sys
import time
import logging as _logging
import hmac
import base64
import hashlib
import commands
import mimetypes

from cStringIO import StringIO
#from abc import abstractmethod
from urlparse import urlparse

logger = _logging.getLogger('pybcs')

import config

try:
    import pycurl
except:
    pass

#this is a function decorator, 
def network(func):
    if not hasattr(func, 'attr') : 
        func.attr = []
    func.attr += ['network']
    return func

class FileSystemException(Exception):
    def __init__(self, msg=''):
        Exception.__init__(self)
        self.msg = msg
    def __str__(self):
        return 'FileSystemException: ' + str(self.msg)

class NotImplementException(Exception):
    def __init__(self, msg=''):
        Exception.__init__(self)
        self.msg = msg
    def __str__(self):
        return 'NotImplementException: ' + str(self.msg)

###########################################################
# http client
###########################################################
class HTTPException(Exception):
    def __init__(self, resp, msg=None):
        Exception.__init__(self)
        self.resp = resp
        self.msg = msg
    def __str__(self):
        return 'HTTPExecption: ' + str(self.resp) + str(self.msg)

class HTTPC:
    ''' define the http client interface'''
    def __init__(self):
        pass
        
    def get(self, url, headers={}):
        pass

    def head(self, url, headers={}):
        pass

    def put(self, url, body='', headers={}):
        pass

    def post(self, url, body='', headers={}):
        pass

    def delete(self, url, headers={}):
        pass

    def get_file(self, url, local_file, headers={}):
        pass

    def put_file(self, url, local_file, headers={}):
        pass

    def post_file(self, url, local_file, headers={}):
        pass

    def _parse_resp_headers(self, resp_header):
        (status, header) = resp_header.split('\r\n\r\n') [-2] . split('\r\n', 1)
        status = int(status.split(' ')[1])

        header = [i.split(':', 1) for i in header.split('\r\n') ]
        header = [i for i in header if len(i)>1 ]
        header = [[a.strip().lower(), b.strip()]for (a,b) in header ]
        return (status, dict(header) )

class CurlHTTPC(HTTPC):
    def __init__(self, tmp_dir='/tmp/pybcs/'):
        self.tmp_dir = tmp_dir
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir) 
        
    def get(self, url, headers={}):
        return self._curl('curl -X "GET" %s "%s" '% 
                (self._headers2txt(headers), url))

    def head(self, url, headers={}):
        return self._curl('curl -X "HEAD" %s "%s" '% 
                (self._headers2txt(headers), url))

    def put(self, url, body='', headers={}):
        body=body.replace('"', '\\"')
        return self._curl('curl -X "PUT" %s "%s" -d "%s"'% 
                (self._headers2txt(headers), url, body))

    def post(self, url, body='', headers={}):
        return self._curl('curl -X "POST" %s "%s" -d "%s"'% 
                (self._headers2txt(headers), url, body))

    def delete(self, url, headers={}):
        return self._curl('curl -X "DELETE" %s "%s" '% 
                (self._headers2txt(headers), url))

    def get_file(self, url, local_file, headers={}):
        return self._curl('curl -X "GET" %s  "%s" '% 
                (self._headers2txt(headers), url),  local_file)

    def put_file(self, url, local_file, headers={}):
        return self._curl('curl -X "PUT" %s "%s" -T %s'% 
                (self._headers2txt(headers), url, local_file))

    def post_file(self, url, local_file, headers={}):
        return self._curl('curl -X "POST" %s "%s" -F "file=@%s" '% 
                (self._headers2txt(headers), url, local_file))

    def _random_tmp_file(self, key):
        from datetime import datetime
        name = str(datetime.now())
        name = name.replace(' ', '_')
        name = name.replace(':', '_')
        name = name.replace('.', '_')
        return self.tmp_dir + key + name

    def _headers2txt(self, headers):
        return ' '.join( [' -H "%s: %s" '%(k,v) for k,v in headers.items()])

    def _curl(self, cmd, body_file=None):
        try:
            rst = self._curl_ll(cmd, body_file)
            return rst
        except Exception, e:
            raise HTTPException('detail: ' + str(e))




    # why use curl :
    # easy for debug on console
    #TODO: try-catch, retry
    def _curl_ll(self, cmd, body_file=None):
        if not body_file:
            body_file = self._random_tmp_file('body') 
        header_file = self._random_tmp_file('header')  

        logger.info('%s -v > %s' % (cmd, body_file))
        cmd = cmd.replace('curl', 'curl > %s --dump-header %s -s'%(body_file, header_file) ) 
        logger.debug(cmd)
        #commands.getoutput(cmd)
        (exitstatus, outtext) = commands.getstatusoutput(cmd)
        errs = [ 1792, # couldn't connect to host
                ]
        if (exitstatus in errs) : 
            raise HTTPException(None, 'error on curl: (%s, %s) on %s' % (exitstatus, outtext, cmd) )

        resp_header = file(header_file).read()
        resp_body_size = os.path.getsize(body_file)
        if  resp_body_size < config.READ_BODY_TO_MEMORY:
            resp_body = file(body_file).read()
        else:
            resp_body = '' 
        
        logger.debug(resp_header)
        logger.debug(shorten(resp_body, 80))

        status, header = self._parse_resp_headers(resp_header)
        
        rst = { 'status': status, 
                'header' : header, 
                'body': resp_body, 
                'body_size': resp_body_size, 
                'body_file': body_file, 
                }

        if (status in [200, 206]): 
            return rst
        else:
            raise HTTPException(rst)

            
class PyCurlHTTPC(HTTPC):
    def __init__(self, proxy = None, limit_rate = 0):
        # limit rate
        pass
		
    def get(self, url, headers={}):
        self._init_curl('GET', url, headers)
        return self._do_request()

    def head(self, url, headers={}):
        self._init_curl('HEAD', url, headers)
        return self._do_request()

    def delete(self, url, headers={}):
        self._init_curl('DELETE', url, headers)
        return self._do_request()

    def get_file(self, url, local_file, headers={}):
        self._init_curl('GET', url, headers, local_file)
        return self._do_request()

    def put(self, url, body='', headers={}):
        self._init_curl('PUT', url, headers)
        req_buf =  StringIO(body)
        self.c.setopt(pycurl.INFILESIZE, len(body)) 
        self.c.setopt(pycurl.READFUNCTION, req_buf.read)
        return self._do_request()

    def post(self, url, body='', headers={}):
        self._init_curl('POST', url, headers)
        req_buf =  StringIO(body)
        self.c.setopt(pycurl.READFUNCTION, req_buf.read)
        return self._do_request()

    def put_file(self, url, local_file, headers={}):
        self._init_curl('PUT', url, headers)
        filesize = os.path.getsize(local_file) 
        self.c.setopt(pycurl.INFILESIZE, filesize) 
        self.c.setopt(pycurl.INFILE, open(local_file)) 
        return self._do_request()

    def post_file(self, url, local_file, headers={}):
        self._init_curl('POST', url, headers)
        values = [
             ("name", "TODO, add a field in post func"),
             ("file1", (pycurl.FORM_FILE, local_file)),
             ("btn", "submit"),
        ]
        self.c.setopt(pycurl.HTTPPOST, values)
        return self._do_request()

    def _do_request(self):
        self.c.perform()
        resp_header = self.c.resp_header_buf.getvalue()
        resp_body = self.c.resp_body_buf.getvalue()
        status = self.c.getinfo(pycurl.HTTP_CODE)

        status, headers = self._parse_resp_headers(resp_header)
        self.c.close()
        
        rst = { 'status': status, 
                'header' : headers, 
                'body': resp_body, 
                'body_file': self.c.resp_body_file, 
                }
        if (status in [200, 206]): 
            return rst
        else:
            raise HTTPException(rst)

    def _init_curl(self, verb, url, headers, 
            resp_body_file=None):
        logger.info('pycurl -X "%s" "%s" ', verb, url)
        self.c = pycurl.Curl()
        self.c.resp_header_buf = None
        self.c.resp_body_buf = None
        self.c.resp_body_file = None

        self.c.setopt(pycurl.DEBUGFUNCTION, self._curl_log)
        self.c.setopt(pycurl.VERBOSE, 1)
        self.c.setopt(pycurl.FOLLOWLOCATION, 1)
        self.c.setopt(pycurl.MAXREDIRS, 10)
        #self.c.setopt(pycurl.CONNECTTIMEOUT, 100)
        #self.c.setopt(pycurl.TIMEOUT, 60*60*3)

        self.c.unsetopt(pycurl.CUSTOMREQUEST)
        if verb == 'GET' : self.c.setopt(pycurl.HTTPGET, True)
        elif verb == 'PUT' : self.c.setopt(pycurl.UPLOAD , True)
        elif verb == 'POST' : self.c.setopt(pycurl.POST  , True)
        elif verb == 'HEAD' : self.c.setopt(pycurl.NOBODY, True)
        elif verb == 'DELETE' : self.c.setopt(pycurl.CUSTOMREQUEST, 'DELETE')
        else: raise KeyError('unknown verb ' + verb)

        self.c.setopt(pycurl.URL, url)

        if headers:
            headers = ['%s: %s'%(k, v) for (k,v) in headers.items()]
            self.c.setopt(pycurl.HTTPHEADER, headers)

        self.c.resp_header_buf = StringIO()
        self.c.resp_body_buf = StringIO()
        self.c.setopt(pycurl.HEADERFUNCTION,    self.c.resp_header_buf.write)

        if resp_body_file: 
            self.c.resp_body_file = resp_body_file 
            f = file(resp_body_file, "wb")
            self.c.setopt(pycurl.WRITEDATA, f)
        else:
            self.c.setopt(pycurl.WRITEFUNCTION,     self.c.resp_body_buf.write)
        '''
        #proxy
        if request.proxy_host and request.proxy_port:
            curl.setopt(pycurl.PROXY, request.proxy_host)
            curl.setopt(pycurl.PROXYPORT, request.proxy_port)
            if request.proxy_username:
                credentials = '%s:%s' % (request.proxy_username,
                        request.proxy_password)
                curl.setopt(pycurl.PROXYUSERPWD, credentials)
        else:
            curl.setopt(pycurl.PROXY, '')  

        '''

        #self.c.setopt(pycurl.MAX_RECV_SPEED_LARGE, limit_rate)

        #c1.setopt(pycurl.COOKIEFILE, "/tmp/cookiefile.txt");
        #c1.setopt(pycurl.COOKIEJAR, "/tmp/cookiefile.txt");
        #c1.setopt(pycurl.SSL_VERIFYPEER, 0) #https
        #c1.setopt(pycurl.SSL_VERIFYHOST, 0) #https
        #self.c.setopt(c.MAX_RECV_SPEED_LARGE, limit_rate)

    
    def _curl_log(self, debug_type, debug_msg):
        curl_out = [    pycurl.INFOTYPE_HEADER_OUT,         #2  find this out from pycurl.c
                        pycurl.INFOTYPE_DATA_OUT,           #4
                        pycurl.INFOTYPE_SSL_DATA_OUT]       #6
        curl_in  =  [   pycurl.INFOTYPE_HEADER_IN,          #1
                        pycurl.INFOTYPE_DATA_IN,            #3
                        pycurl.INFOTYPE_SSL_DATA_IN]        #5
        curl_info = [   pycurl.INFOTYPE_TEXT]               #0 

        if debug_type in curl_out:
            logger.debug("> %s" % debug_msg.strip())
        elif debug_type in curl_in:
            logger.debug("< %s" % debug_msg.strip())
        else:
            logger.debug("I %s" % (debug_msg.strip()) )


class HttplibHTTPC(HTTPC):
    def __init__(self):
        pass
        
    #used by small response (get/put), not get_file
    def request(self, verb, url, data, headers={}):
        response = self.send_request(verb, url, data, headers)
        resp_body = response.read()
        
        for (k, v) in response.getheaders():
            logger.debug('%s: %s' % (k, v))
        rst = { 'status': response.status, 
                'header' : dict(response.getheaders()), 
                'body': resp_body, 
                'body_file': None, 
                }
        if (response.status in [200, 206]): 
            return rst
        else:
            raise HTTPException(rst)

    #used by all 
    def send_request(self, verb, url, data, headers={}):
        logger.info('httplibcurl -X "%s" "%s" ', verb, url)
        for (k, v) in headers.items():
            logger.debug('%s: %s' % (k, v))
        logger.debug('\n')
        logger.debug(shorten(data, 102400))
        o = urlparse(url)
        host = o.netloc
        path = o.path
        if o.query: 
            path+='?'
            path+=o.query

        conn = httplib.HTTPConnection(host)
        conn.request(verb, path, data, headers)
        response = conn.getresponse()
        return response

    def get(self, url, headers={}):
        return self.request('GET', url, '', headers)

    def head(self, url, headers={}):
        return self.request('HEAD', url, '', headers)

    def put(self, url, body='', headers={}):
        return self.request('PUT', url, body, headers)

    def post(self, url, body='', headers={}):
        return self.request('POST', url, body, headers)

    def delete(self, url, headers={}):
        return self.request('DELETE', url, '', headers)

    def get_file(self, url, local_file, headers={}):
        response = self.send_request('GET', url, '', headers)
        fout = open(local_file, 'wb')
        CHUNK = 1024*256
        while  True:
            data = response.read(CHUNK)
            if not data:
                break
            fout.write(data)
        fout.close()
        rst = { 'status':  response.status, 
                'header' : dict(response.getheaders()), 
                'body':    None, 
                'body_file': local_file, 
                }
        if (response.status in [200, 206]): 
            return rst
        else:
            raise HTTPException(rst)

    def put_file(self, url, local_file, headers={}):
        return self.put(url, file(local_file).read(), headers)

    def post_file(self, url, local_file, headers={}):
        fields = []
        f = ('uploadedfile', os.path.basename(local_file), open(local_file).read())
        content_type, body = encode_multipart_formdata(fields, [f])
        headersnew = { 'Content-Type' : content_type,
                'Content-Length': str(len(body))}
        headers.update(headersnew)
        #req = urllib2.Request(url, body, headers)
        return self.post(url, body, headers) 

###########################################################
# sign system

###########################################################
# color system
###########################################################
class bcolors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'

    def disable(self):
        self.HEADER = ''
        self.BLUE = ''
        self.GREEN = ''
        self.YELLOW = ''
        self.RED = ''
        self.ENDC = ''

def to_red(s):       return  bcolors.RED+ str(s) + bcolors.ENDC
def to_yellow(s):    return  bcolors.YELLOW+ str(s) + bcolors.ENDC
def to_green(s):     return  bcolors.GREEN + str(s) + bcolors.ENDC
def to_blue(s):      return  bcolors.BLUE+ str(s) + bcolors.ENDC


###########################################################
# misc
###########################################################
def shorten(s, l=80):
    if len(s)<=l:
        return s
    return s[:l-3] + '...'

def system(cmd):
    logger.info(cmd)
    r = commands.getoutput(cmd)
    logger.debug(r)
    return r

def md5_for_file(f, block_size=2**20):
    f = open(f, 'rb')
    md5 = hashlib.md5()
    while True:
        data = f.read(block_size)
        if not data:
            break
        md5.update(data)
    return md5.digest()


'''
multipart 
    content_type, body = encode_multipart_formdata(fields, files)
    headers = { 'content-type' : content_type,
            'content-length': str(len(body))}
    req = urllib2.Request(url, body, headers)

'''

def encode_multipart_formdata(fields, files):
    """
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files
    Return (content_type, body) ready for httplib.HTTP instance
    """
    BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'
    CRLF = '\r\n'
    L = []
    for (key, value) in fields:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"' % key)
        L.append('')
        L.append(value)
    for (key, filename, value) in files:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
        L.append('Content-Type: %s' % get_content_type(filename))
        L.append('')
        L.append(value)
    L.append('--' + BOUNDARY + '--')
    L.append('')
    body = CRLF.join(L)
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY                                                                                             
    return content_type, body

def get_content_type(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'



'''
set_level 设为
'''
def init_logging(set_level = _logging.INFO, 
        console = True,
        log_file_path = None):

    logger.setLevel(_logging.DEBUG)
    logger.propagate = False # it's parent will not print log (especially when client use a 'root' logger)
    for h in logger.handlers:
        logger.removeHandler(h)
    if console:
        fh = _logging.StreamHandler()
        fh.setLevel(set_level)
        formatter = _logging.Formatter("%(message)s")
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    if log_file_path:
        fh = _logging.FileHandler(log_file_path)
        fh.setLevel(set_level)
        formatter = _logging.Formatter("%(asctime)-15s %(levelname)s  %(message)s")
        fh.setFormatter(formatter)
        logger.addHandler(fh)


