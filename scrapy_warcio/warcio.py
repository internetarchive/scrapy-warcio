'''
ScrapyWarcIo class
~~~~~~~~~~~~~~~~~~
'''

import logging
import os
import socket
import sys
import uuid

from datetime import datetime

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

import magic
import yaml

from hanzo import warctools  # internetarchive/warctools
from scrapy import __version__ as scrapy_version


def _bytes(val):
    '''
    always returns bytes from str or bytes
    '''
    return val if isinstance(val, bytes) else bytes(val, 'utf-8')


def _str(val):
    '''
    always returns string from str or bytes
    '''
    return val if isinstance(val, str) else str(val, 'utf-8')


def warc_date():
    '''
    returns UTC now in WARC-Date format (YYYY-mm-ddTHH:ii:ssZ)
    '''
    return datetime.utcnow().isoformat() + 'Z'


class ScrapyWarcIo:

    '''
    Scrapy DownloaderMiddleware WARC input/output methods
    '''

    REQUIRED = [
        'collection',
        'description',
        'max_warc_size',
        'operator',
        'robots',
        'user_agent',
        'warc_dest',
        'warc_prefix',
        'warc_spec']
    WARC_LINE_SEP = '\r\n'
    WARC_SERIAL_ZFILL = 5

    warc_dest = None
    warc_fname = None
    warc_count = 0
    warc_size = 0

    def __init__(self):
        self.log = logging.getLogger(__name__)
        self.max_serial = int('9' * self.WARC_SERIAL_ZFILL)
        self.req_date_set = False

        with open(os.environ.get('SCRAPY_WARCIO_SETTINGS')) as sfh:
            self.config = yaml.safe_load(sfh.read())

        for item in self.REQUIRED:
            if self.config.get(item) is None:
                raise ValueError(
                    'required config item: {} is None'.format(item))

    def bump_serial(self, content_bytes):
        '''
        increment WARC serial number and create a new WARC file iff
        file size + (uncompressed) additional content may exceed
        max_warc_size in settings

        :param  content_bytes  size in bytes of new content (uncompressed)
        '''
        create_new_warc = False

        if self.warc_fname is None:
            create_new_warc = True
        else:
            if os.path.exists(self.warc_fname):
                self.warc_size = os.stat(self.warc_fname).st_size
                estimate = self.warc_size + content_bytes
                if estimate >= self.config['max_warc_size']:
                    create_new_warc = True

        if create_new_warc:
            self.warc_fname = self.warcfile()
            self.log.info('New WARC file: %s', self.warc_fname)
            self.write_warcinfo()
            self.warc_count += 1

    @staticmethod
    def __record_id():
        '''
        returns WARC-Record-ID (globally unique UUID) as a string
        '''
        return '<urn:uuid:{}>'.format(uuid.uuid1())

    def get_headers(self, record):
        '''
        returns WARC record headers as a string from Scrapy object

        if record.method, returns request headers
        if record.status, returns response headers
        else raises ValueError

        :param  record  <scrapy.http.Request> or <scrapy.http.Response>
        '''
        if not hasattr(record, 'headers'):
            return ''

        if hasattr(record, 'method'):  # request record
            purl = urlparse(record.url)
            http_line = ' '.join([record.method, purl.path, 'HTTP/1.0'])
        elif hasattr(record, 'status'):  # response record
            http_line = ' '.join(['HTTP/1.0', str(record.status)])
        else:
            raise ValueError('Unable to form http_line from record.')

        headers = [http_line]

        for key in record.headers:
            val = record.headers[key]
            headers.append('{}: {}'.format(_str(key), _str(val)))

        return self.WARC_LINE_SEP.join(headers)

    def warcfile(self):
        '''
        returns new WARC filename from warc_prefix setting and current
        WARC count. WARC filename format compatible with
        internetarchive/draintasker warc naming #1:
        {TLA}-{timestamp}-{serial}-{fqdn}.warc.gz

        raises IOError if WARC file exists
        '''
        if self.warc_count > self.max_serial:
            raise ValueError('warc_count: {} exceeds max_serial: {}'.format(
                self.warc_count, self.max_serial))

        tla = self.config['warc_prefix']
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        serial = str(self.warc_count).zfill(self.WARC_SERIAL_ZFILL)
        fqdn = socket.gethostname().split('.')[0]

        warc_name = '-'.join([tla, timestamp, serial, fqdn]) + '.warc.gz'
        warc_dest = self.config['warc_dest'] or ''

        if warc_dest and not os.path.exists(warc_dest):
            raise IOError('warc_dest not found: {}'.format(warc_dest))

        fname = os.path.join(warc_dest, warc_name)

        if os.path.exists(fname):
            raise IOError('WARC file exists: {}'.format(fname))

        return fname

    def write(self, response, request):
        '''
        write WARC-Type: response, then WARC-Type: request records
        from Scrapy response and request

        Notes:
        1) It is customary to write the request record immediately
           after the response record to protect against a
           request-response pair spanning more than one WARC file.
        2) The WARC-Date of the response must be identical to the
           WARC-Date of the request.

        :param  response  <scrapy.http.Response>
        :param  request   <scrapy.http.Request>
        '''
        if not hasattr(response, 'status'):
            raise ValueError('Response missing HTTP status')

        if not hasattr(response, 'body'):
            raise ValueError('Response missing body')

        if not hasattr(request, 'method'):
            raise ValueError('Request missing method')

        if not hasattr(request, 'meta'):
            raise ValueError('Request missing meta')

        if not request.meta.get('WARC-Date'):
            raise ValueError('Request missing WARC-Date')

        record_id = self.__record_id()

        warc_headers = [
            ('WARC-Type', 'response'),
            ('WARC-Target-URI', response.url),
            ('WARC-Date', request.meta['WARC-Date']),
            ('WARC-Record-ID', record_id),
        ]

        body = response.body
        mimetype = magic.from_buffer(body, mime=True)
        content = '{}{}{}'.format(self.get_headers(response),
                                  self.WARC_LINE_SEP * 2,
                                  _str(body))

        if mimetype:
            warc_headers.append(('WARC-Identified-Payload-Type', mimetype))

        # write response
        self.write_record(headers=warc_headers,
                          content_type='application/http;msgtype=response',
                          content=content)

        self.write_request(request, record_id)

    def write_record(self, headers, content_type, content):
        '''
        write WARC record (of any type) to WARC GZ file

        :param  headers       list of header tuples [('foo', 'bar')]
        :param  content_type  WARC Content-Type header string
        :param  content       WARC payload
        '''
        self.bump_serial(sys.getsizeof(content))

        bheaders = []
        for key, val in headers:
            bheaders.append((_bytes(key), _bytes(val)))

        with open(self.warc_fname, 'ab') as _fh:
            record = warctools.WarcRecord(
                headers=bheaders,
                content=(_bytes(content_type), _bytes(content)))

            record.write_to(_fh, gzip=True)

            self.log.info('Wrote %s bytes (%s) to file: %s',
                          _fh.tell(), content_type, self.warc_fname)

    def write_request(self, request, concurrent_to):
        '''
        write WARC-Type: request record from Scrapy response

        :param  request        <scrapy.http.Request>
        :param  concurrent_to  response WARC-Record-ID
        '''
        warc_headers = [
            ('WARC-Type', 'request'),
            ('WARC-Target-URI', request.url),
            ('WARC-Date', request.meta['WARC-Date']),
            ('WARC-Record-ID', self.__record_id()),
            ('WARC-Concurrent-To', concurrent_to),
        ]

        content = '{}{}{}'.format(self.get_headers(request),
                                  self.WARC_LINE_SEP * 2,
                                  _str(request.body))

        self.write_record(headers=warc_headers,
                          content_type='application/http;msgtype=request',
                          content=content)

    def write_warcinfo(self):
        '''
        write WARC-Type: warcinfo record
        '''
        headers = [
            ('WARC-Type', 'warcinfo'),
            ('WARC-Date', warc_date()),
            ('WARC-Filename', self.warc_fname),
            ('WARC-Record-ID', self.__record_id()),
        ]

        content = [
            'software: Scrapy/{} (+https://scrapy.org)'.format(scrapy_version),
            'ip: {}'.format(socket.gethostbyname(socket.gethostname())),
            'hostname: {}'.format(socket.gethostname()),
            'format: WARC file version 1.0',
            'conformsTo: {}'.format(self.config['warc_spec']),
            'operator: {}'.format(self.config['operator']),
            'isPartOf: {}'.format(self.config['collection']),
            'description: {}'.format(self.config['description']),
            'robots: {}'.format(self.config['robots']),
            'http-header-user-agent: {}'.format(self.config['user_agent']),
        ]

        self.write_record(headers=headers,
                          content_type='application/warc-fields',
                          content=self.WARC_LINE_SEP.join(content))
