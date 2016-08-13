from datetime import datetime
import time
import feedparser
import redis
import requests
from config import DB_NAME, REDIS_HOST, EMBEDLY_API_KEY
from pymongo import MongoClient

client = MongoClient()
redisconn = redis.StrictRedis(host=REDIS_HOST, port=6379, db=0)
db = client[DB_NAME]

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

wired_feeds = ["http://www.wired.com/category/gear/feed/",
               "http://www.wired.com/category/reviews/feed/",
               "http://www.wired.com/category/science/feed/",
               "http://www.wired.com/category/science-blogs/feed/",
               "http://www.wired.com/category/security/feed/",
               "http://www.wired.com/category/transportation/feed/",
               ]

def go_embedly(url):
    req_url = "https://api.embedly.com/1/extract"
    response = requests.get(req_url, params={"url": url,
                                         "key": EMBEDLY_API_KEY})
    result = response.json()
    return result.get("keywords"), result.get("content")

def teach(url):
    if not db.articles.find_one({"url": url}):
        keywords, content = go_embedly(url)
        if content:
            item = db.articles.insert_one({"url": url,
                                               "create_date": datetime.now(),
                                               "keywords": keywords,
                                               "content": content})
            redisconn.rpush("queue", str(item.inserted_id))
            print item.inserted_id

def teach_reddit():
    for feed in reddit_feeds:
        d = requests.get(feed, headers={'User-agent': 'Reko-parser'})
        d = d.json()
        for child in d['data']["children"]:
            url = child['data']["url"]
            if "reddit" not in url:
                teach(child["data"]["url"])

def teach_wired():
    for feed in wired_feeds:
        d = feedparser.parse(r'%s' % feed)
        for child in d["entries"]:
            teach(child["links"][0]["href"])

if __name__ == "__main__":
    while True:
        teach_wired()
        teach_reddit()
        time.sleep(60*60*3)
