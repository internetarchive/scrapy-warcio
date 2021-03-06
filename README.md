Scrapy Warcio
=============

A Web Archive
[WARC](https://iipc.github.io/warc-specifications/specifications/warc-format/warc-1.0/)
I/O module for Scrapy

[![travis-ci](https://travis-ci.com/internetarchive/scrapy-warcio.svg?branch=master)](https://travis-ci.com/internetarchive/scrapy-warcio)


Install
-------

```shell
$ pip install scrapy-warcio
```


Usage
-----

1. Create a project and spider:<br>
   https://docs.scrapy.org/en/latest/intro/tutorial.html

```
$ scrapy startproject <project>
$ cd <project>
$ scrapy genspider <spider> example.com
```

2. Copy and edit `scrapy_warcio` distributed `settings.yml` with your
   configuration settings:

```yaml
---
warc_spec: https://iipc.github.io/warc-specifications/specifications/warc-format/warc-1.0/
max_warc_size: 10000000000  # 10GB

collection: ~ # collection name
description: ~ # collection description
operator: ~ # operator email address
robots: ~  # robots policy (obey or ignore)
user_agent: ~ # your user-agent
warc_prefix: ~ # WARC filename prefix
warc_dest: ~ # WARC files destination
...
```

3. Export `SCRAPY_WARCIO_SETTINGS=/path/to/settings.yml`

4. Add `WarcioDownloaderMiddleware` (distributed as `middlewares.py`)
   to your `<project>/<project>/middlewares.py`:

```python
import scrapy_warcio


class WarcioDownloaderMiddleware:

    def __init__(self):
        self.warcio = scrapy_warcio.ScrapyWarcIo()

    def process_request(self, request, spider):
        request.meta['WARC-Date'] = scrapy_warcio.warc_date()
        return None

    def process_response(self, request, response, spider):
        self.warcio.write(response, request)
        return response
```

5. Enable `WarcioDownloaderMiddleware` in `<project>/<project>/settings.py`:

```
DOWNLOADER_MIDDLEWARES = {
    '<project>.middlewares.WarcioDownloaderMiddleware': 543,
}
```

6. Validate your warcs with `internetarchive/warctools`:

```shell
$ warcvalid WARC.warc.gz
```

7. Upload your WARC(s) to your favorite web archive!


Help
----

```shell
$ pydoc scrapy_warcio
```

or

```python
>>> help(scrapy_warcio)
```


TODO
----

Making this a Scrapy extension may make it more useful:<br>
https://docs.scrapy.org/en/latest/topics/extensions.html


@internetarchive
