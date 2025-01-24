from scrapling.defaults import Fetcher, AsyncFetcher, StealthyFetcher, PlayWrightFetcher
page = StealthyFetcher.fetch('https://baidu.com')
print(page.content)