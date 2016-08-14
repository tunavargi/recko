from datetime import datetime
import time
import feedparser
import redis
import requests
from config import DB_NAME, REDIS_HOST, EMBEDLY_API_KEY
from pymongo import MongoClient

from config import REDIS_HOST, DB_NAME, MONGO_HOST, MONGO_PORT
client = MongoClient(host=MONGO_HOST, port=MONGO_PORT)

redisconn = redis.StrictRedis(host=REDIS_HOST, port=6379, db=0)
db = client[DB_NAME]

reddit_nsfw = [
    "https://www.reddit.com/r/WatchItForThePlot/.json",
    "https://www.reddit.com/r/datgap/.json",
    "https://www.reddit.com/r/NSFW_GIF/.json",
    "https://www.reddit.com/r/nsfw_gifs/.json",
    "https://www.reddit.com/r/lesbian/.json",
    "https://www.reddit.com/r/boobs/.json",
    "https://www.reddit.com/r/gifsgonewild/.json",
    "https://www.reddit.com/r/stockings/.json",
    "https://www.reddit.com/r/realgirls/.json",
]

reddit_feeds = [
    "http://www.reddit.com/r/python/.json",
    "http://www.reddit.com/r/database/.json",
    "http://www.reddit.com/r/devops/.json",
    "http://www.reddit.com/r/programming/.json",
    "http://www.reddit.com/r/ruby/.json",
    "http://www.reddit.com/r/history/.json",
    "http://www.reddit.com/r/science/.json",
    "http://www.reddit.com/r/InternetIsBeautiful/.json",
    "http://www.reddit.com/r/nutrition/.json",
    "http://www.reddit.com/r/philosophy/.json",
    "http://www.reddit.com/r/politics/.json",
    "http://www.reddit.com/r/worldnews/.json",
    "http://www.reddit.com/r/news/.json",
    "http://www.reddit.com/r/technology/.json",
    "http://www.reddit.com/r/nba/.json",
    "http://www.reddit.com/r/soccer/.json",
    "http://www.reddit.com/r/baseball/.json",
    "http://www.reddit.com/r/formula1/.json",
    "http://www.reddit.com/r/nfl/.json",
    "http://www.reddit.com/r/lgbt/.json",
]

wired_feeds = [
    "http://www.wired.com/category/gear/feed/",
    "http://www.wired.com/category/reviews/feed/",
    "http://www.wired.com/category/science/feed/",
    "http://www.wired.com/category/science-blogs/feed/",
    "http://www.wired.com/category/security/feed/",
    "http://www.wired.com/category/transportation/feed/"
]


def go_embedly(url):
    print url
    req_url = "https://api.embedly.com/1/extract"
    response = requests.get(req_url,
                            params={"url": url,
                                    "key": EMBEDLY_API_KEY})

    result = response.json()
    embed_url = "https://api.embedly.com/1/oembed"
    embed_response = requests.get(embed_url, params={"url": url,
                                               "key": EMBEDLY_API_KEY})
    content = embed_response.json()


    imgur = False
    if content.get("url"):
        imgur = "imgur" in content.get("url")
    if imgur:
        return result.get("keywords"), content["url"]
    elif content.get("html"):
        return result.get("keywords"), content["html"]
    else:
        return result.get("keywords"), result.get("content")


def teach(url,
          hardcoded_keywords=None,
          nsfw=False):

    if not db.articles.find_one({"url": url}):
        keywords, content = go_embedly(url)
        print keywords, content
        if content:
            item = db.articles.insert_one({"url": url,
                                               "create_date": datetime.now(),
                                               "keywords": keywords if keywords else hardcoded_keywords,
                                               "nsfw": nsfw,
                                               "content": content})
            redisconn.rpush("queue", str(item.inserted_id))
            print item.inserted_id

def teach_reddit():
    for feed in reddit_feeds:
        d = requests.get(feed, headers={'User-agent': 'Reko2-par2ser'})
        d = d.json()
        for child in d['data']["children"]:
            url = child['data']["url"]
            if "reddit" not in url:
                teach(child["data"]["url"])

def teach_nsfw():
    for feed in reddit_nsfw:
        d = requests.get(feed, headers={'User-agent': 'Reko2-par2ser'})
        d = d.json()
        for child in d['data']["children"]:
            url = child['data']["url"]
            if "reddit" not in url:
                teach(child["data"]["url"],
                      hardcoded_keywords=[{"name":feed, "score": 100}], nsfw=True)



def teach_wired():
    for feed in wired_feeds:
        d = feedparser.parse(r'%s' % feed)
        for child in d["entries"]:
            teach(child["links"][0]["href"])

def wired():
    teach_wired()

def reddit():
    teach_reddit()

def nsfw():
    teach_nsfw()

def teacher():
    nsfw()
    reddit()
    wired()

teacher()