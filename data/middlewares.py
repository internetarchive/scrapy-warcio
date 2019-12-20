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
