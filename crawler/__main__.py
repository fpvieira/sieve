import asyncio
import logging

import crawler


logging.basicConfig(level=logging.DEBUG)


SEED_URL = "http://www.epocacosmeticos.com.br/"


def main():
    loop = asyncio.get_event_loop()
    c = crawler.Crawler(SEED_URL,
                        concurrency=100,
                        loop=loop)
    loop.run_until_complete(c.crawl())

if __name__ == '__main__':
    main()
