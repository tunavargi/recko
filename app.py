import json
from datetime import datetime
from random import randint

import redis
import requests
from bson import ObjectId
from bson.json_util import dumps

from flask import Flask
from flask import request
from config import EMBEDLY_API_KEY, REDIS_HOST, DB_NAME
from pymongo import MongoClient


app = Flask(__name__)
client = MongoClient()
redisconn = redis.StrictRedis(host=REDIS_HOST, port=6379, db=0)
db = client[DB_NAME]


def get_keywords(url):
    req_url = "https://api.embedly.com/1/extract"
    response = requests.get(req_url, params={"url": url,
                                         "key": EMBEDLY_API_KEY})
    result = response.json()
    return result.get("keywords"), result.get("content")


@app.route('/teach', methods=['GET'])
def teach():
    data = request.args
    url = data.get("url")
    keywords, content = get_keywords(url)
    if not db.articles.find_one({"url": url}):
        item = db.articles.insert_one({"url": url,
                                     "create_date": datetime.now(),
                                     "keywords": keywords,
                                     "content": content})

        redisconn.rpush("queue", str(item.inserted_id))
        return json.dumps({"url": item.inserted_id })
    return json.dumps({"message": "Nothing inserted"})

@app.route('/neighbors/<string:id>', methods=["GET"])
def neighbors(id):
    query = {"$or":[{"match1": ObjectId(id)}, {"match2": ObjectId(id)}]}
    similar = db.article_match.find(query).sort([("dst", -1)])
    match_ids = [i["match1"] if i["match1"] == ObjectId(id) else i["match2"] for i in similar]
    if match_ids:
        match_id = match_ids[randint(0, len(match_ids)-1)]
        article = db.articles.find_one({"_id": ObjectId(match_id)})
        return dumps({"url": article["url"]})
    return json.dumps({})

if __name__ == "__main__":
    app.run(debug=True)
