import asyncio
import aiohttp
import csv
from collections import namedtuple, deque
from urllib.parse import urljoin, urldefrag
import logging

from bs4 import BeautifulSoup


log = logging.getLogger(__file__)


Page = namedtuple("Page", "name title url")


class Crawler:
    def __init__(self, seed,
                 loop=None,
                 concurrency=10,
                 patterns=[], exclude=[]):
        self.seed = seed
        self.loop = loop or asyncio.get_event_loop()
        self.concurrency = concurrency
        self.q = asyncio.JoinableQueue()
        self.visited = set()
        self.done = set()

        self.fp = open("produtos.csv", "w")
        self.csv = csv.DictWriter(self.fp,
                                  fieldnames=Page._fields)
        self.csv.writeheader()

        self.add_link(seed)


    def add_link(self, url):
        log.info("add_link({})".format(url))
        if self.should_crawl(url):
            self.q.put_nowait(url)
        else:
            log.info("Refused to add {}".format(url))

    def should_crawl(self, url):
        return url.startswith(self.seed) and url not in self.visited

    def is_product(self, url):
        return url.endswith("/p")

    def store_product(self, page, url):
        """Stores the new found product in the csv"""
        log.info("Storing {} into csv".format(url))
        if url in self.done:
            return

        soup = BeautifulSoup(page, "lxml")
        product_name = soup.find(class_="productName")
        if product_name:
            name = product_name.text
        else:
            name = None
        title = soup.title.text
        page = Page(name=name, title=title, url=url)
        self.done.add(url)
        self.csv.writerow(page._asdict())
        self.fp.flush()

    @asyncio.coroutine
    def get_page(self, url):
        log.info("get_page({})".format(url))
        if self.should_crawl(url):
            response = yield from aiohttp.request('GET', url,
                                                  loop=self.loop)
            page = yield from response.read()
            self.visited.add(url)
            if response.status == 200:
                if self.is_product(url):
                    self.store_product(page, url)
                links = self.extract_links(page)
                for link in links:
                    self.add_link(link)
            return page

    def extract_links(self, html):
        log.debug("extract_links")
        soup = BeautifulSoup(html, "lxml")
        links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            href = urljoin(self.seed, href)
            href, _ = urldefrag(href)
            links.append(href)
        log.info("found {}".format(len(links)))
        return links

    @asyncio.coroutine
    def worker(self):
        log.debug("Starting worker")
        while True:
            url = yield from self.q.get()
            yield from self.get_page(url)
            self.q.task_done()
            logging.debug("{}: done".format(url))

    @asyncio.coroutine
    def crawl(self):
        logging.debug("crawl")
        workers = [asyncio.Task(self.worker(), loop=self.loop)
                   for _ in range(self.concurrency)]
        yield from self.q.join()
        for w in workers:
            w.cancel()
        self.fp.close()
