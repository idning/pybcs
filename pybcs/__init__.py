import logging

from bcs import BCS
from bucket import Bucket

#modules should import
__all__ = ['bcs', 'bucket', 'object']


from common import NotImplementException
from common import HTTPException

from common import CurlHTTPC
from common import PyCurlHTTPC
from common import HttplibHTTPC
from common import system
from common import md5_for_file

from common import init_logging

#init_logging(logging.INFO, True, log_file_path='log/bcs.log')
init_logging()
logger = logging.getLogger('pybcs')
