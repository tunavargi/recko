import uuid
from datetime import datetime
from random import randint

import redis
import requests
from bson import ObjectId
from bson.json_util import dumps

from flask import Flask, Response
from flask import request
from config import EMBEDLY_API_KEY, REDIS_HOST, DB_NAME
from pymongo import MongoClient


app = Flask(__name__)
client = MongoClient()
redisconn = redis.StrictRedis(host=REDIS_HOST, port=6379, db=0)
db = client[DB_NAME]


def go_embedly(url):
    req_url = "https://api.embedly.com/1/extract"
    response = requests.get(req_url, params={"url": url,
                                         "key": EMBEDLY_API_KEY})
    result = response.json()
    return result.get("url"),result.get("keywords"), result.get("content")


@app.route("/authenticate", methods=["POST"])
def authenticate():
    token = "tok-%s" % uuid.uuid4().hex
    db.users.insert_one({"articles": [],
                         "visited": [],
                         "token": token})
    return token


@app.route("/like", methods=["POST"])
def like():
    token = request.args.get("token")
    url = request.json.get("url")
    if not token:
        return Response(status=403)
    user = db.users.find_one({"token": token})
    if not user:
        return Response(status=403)

    liked = user['articles'][:100]
    if not url in liked:
        liked.append(url)
    db.users.update({"token":token},
                    {"$set": {"articles": liked}})
    return "liked"


@app.route('/teach', methods=['GET'])
def teach():
    data = request.args
    url = data.get("url")
    _url, keywords, content = go_embedly(url)
    if not db.articles.find_one({"url": _url}):
        item = db.articles.insert_one({"url": _url,
                                     "create_date": datetime.now(),
                                     "keywords": keywords,
                                     "content": content})

        redisconn.rpush("queue", str(item.inserted_id))
        return dumps({"url": item.inserted_id })
    return dumps({"message": "Nothing inserted"})

def get_random():
    random = randint(0, db.articles.count())
    article = db.articles.find().limit(1).skip(random)
    if article:
        return article[0]


@app.route("/next", methods=["GET"])
def _next():
    token = request.args.get("token")
    if not token:
        return Response(status=403)
    user = db.users.find_one({"token": token})
    if not user:
        return Response(status=403)
    if not user['articles']:
        article = get_random()
        return Response(dumps({'article': article}))


    query = {"$or":[{"match1": {"$nin": user["visited"]}},
                    {"match2": {"$nin": user["visited"]}}]}

    similar = db.article_match.find(query).sort([("dst", 1)])
    similar = list(similar)
    if not similar:
        article = get_random()
        return Response(dumps({'article': article}))
    return Response(dumps({"article": similar[0]}))


@app.route('/neighbors/<string:id>', methods=["GET"])
def neighbors(id):
    query = {"$or":[{"match1": ObjectId(id)}, {"match2": ObjectId(id)}]}
    similar = db.article_match.find(query).sort([("dst", 1)])
    match_ids = [i["match1"] if i["match1"] == ObjectId(id) else i["match2"] for i in similar]
    articles = db.articles.find({"_id": {"$in": match_ids}})
    return dumps({"articles": articles})

if __name__ == "__main__":
    app.run(debug=True)
