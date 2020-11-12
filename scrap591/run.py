import scrapy
from scrapy.crawler import CrawlerProcess
from scrap591.spiders.a591 import A591Spider


if __name__ == "__main__":
    process = CrawlerProcess(settings={
        "FEEDS": {
            "items.json": {"format": "json"},
        },
    })

    process.crawl(A591Spider)
    process.start() # the script will block here until the crawling is finished
