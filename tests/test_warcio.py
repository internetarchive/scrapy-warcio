'''
Scrapy WARC I/O basic unit tests
'''

from datetime import datetime

import scrapy_warcio


def test_bytes():
    assert isinstance(scrapy_warcio.warcio._bytes('FOO'), bytes)


def test_str():
    assert isinstance(scrapy_warcio.warcio._str(b'FOO'), str)


def test_warc_date():
    date = scrapy_warcio.warcio.warc_date()
    obj = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%fZ')
    assert isinstance(obj, datetime)


def test_warc_write():
    pass
