import scrapy
from pymongo import MongoClient
from datetime import datetime
#from scrapy.http import FormRequest
from scrapy.crawler import CrawlerProcess
from scrapy.spidermiddlewares.httperror import HttpError
from scrapy.core.downloader.handlers.http11 import TunnelError
from twisted.internet.error import TimeoutError
from twisted.web._newclient import ResponseNeverReceived
import sys


class TorCrawler(scrapy.Spider):
    name = "tc"
    #handle_httpstatus_list = [404, 502, 503, 504]

    num_processed = 1

    def __init__(self):
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client["DWProject"]["DW_URLs"]

    def start_requests(self):
        count = 0
        urls = self.db.find({'visited': False}, {'url': 1}).limit(30)

        for u in urls:
            url = u['url']

            if "http://http://" in url:
                url = url[7:]

            if url[-6:] == ".onion":
                url = url + "/"
            elif url[-1:] == "/" and url[-7:] != ".onion/":
                url = url[:-1]

            if "http://" not in url and "https://" not in url:
                url = "http://" + url

            if url != u['url']:
                check = self.db.find_one({'url': url}, {"_id": 1})

                if check is not None:
                    self.db.remove({'url': url})

                self.db.update_one(
                    {'url': u['url']},
                    {
                        '$set': {
                            'url': url
                        }
                    }
                )

            #pproxy -l http://:8181 -r socks5://127.0.0.1:9050 -vv
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                errback=self.errback_url,
                dont_filter=True,
                cb_kwargs=dict(og_url=url),
                meta=
                {
                    'dont_filter': True,
                    'dont_retry': True,
                    'download_timeout': 20,
                    'dont_cache': True,
                    'headers':
                        {
                            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.84 Safari/537.36',
                        }
                }
            )
            
            count += 1


    def parse(self, response, og_url):
        print("Parsed")
        # Returns the site's url, the url it was redirected too if applicable and the site's raw html

        if response.request.url != og_url:
            redirects = response.request.url
        else:
            redirects = None

        if response.status >= 500:
            yield {
                'url': og_url,
                'redirects': redirects,
                'response': response,
                'status': response.status
            }
        else:
            yield {
                'url': og_url,
                'redirects': redirects,
                'response': response,
                'status': response.status
            }
        try:
            self.db.close()
        except:
            pass

    def errback_url(self, error):
        print("Err")
        print(error.value)
        print("ERROR full:", repr(error))

        url = ""

        status = 0
        if error.check(HttpError):
            # these exceptions come from HttpError spider middleware
            # you can get the non-200 response

            res = error.value.response

            url = res.url

            err_res = str(error.value.response)
            err_list = err_res.replace('<', '').replace('>', '').split(' ')
            # print(err_list)
            status = int(err_list[0])

        elif error.check(TimeoutError):
            status = 408

        elif error.check(ResponseNeverReceived):
            status = 503

        elif error.check(TunnelError):
            status = 504
            
        else:
            status = 0

        try:
            url = error.value.response.url
            #print("res url:", url)
            url = error.request.url
            #print("req url:", url)
        except:
            try:
                url = error.request.url
                #print("req url:", url)
            except:
                pass

        redirects = None

        if error.request.meta.get('redirect_urls'):
            url = error.request.meta.get('redirect_urls')[0]

            if error.request.url != url:
                redirects = error.request.url


        if "https://" in url:
            print("url")
            new_url = url
            try:
                self.db.update_one(
                    {'url': url},  # Where item is the URL
                    {
                        '$set': {
                            'url': new_url,
                            'redirects': redirects,
                            'status': status,
                            'dateLastChecked': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                            'visited': True
                        }
                    },
                )
            except Exception as e:
                print("ERROR:", e)

        elif "http://" in url:
            new_url = url.replace('http://', 'https://')
            check = self.db.find_one({'url': new_url}, {"_id": 1}) # If already in db, remove current entry

            if check is None:
                try:
                    self.db.update_one(
                        {'url': url},  # Where item is the URL
                        {
                            '$set':
                                {
                                    'url': new_url,
                                    'redirects': redirects,
                                    'status': status,
                                    'dateLastChecked': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                                    'visited': False
                                },
                        }
                    )
                except Exception as e:
                    print("ERROR:", e)
            else:
                self.db.remove({'url': url})

        try:
            self.client.close()
        except:
            pass

    def close(self, reason):
        try:
            self.client.close()
        except:
            pass
        #sys.exit()
