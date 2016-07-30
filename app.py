import json
import uuid
from datetime import datetime
from random import randint

import redis
import requests
from bson import ObjectId
from bson import json_util

from flask import Flask, Response, render_template
from flask import request
from config import EMBEDLY_API_KEY, REDIS_HOST, DB_NAME
from pymongo import MongoClient
from utils import json_encode

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
    url_id = request.json.get("url")
    if not token:
        return Response(status=403)
    user = db.users.find_one({"token": token})
    if not user:
        return Response(status=403)

    liked = user['articles'][:100]
    article = db.articles.find_one({"_id": ObjectId(url_id)})

    if not article["_id"] in liked:
        liked.append(article["_id"])
    db.users.update({"token":token},
                    {"$set": {"articles": liked}})

    return Response(json_encode({"message" : "liked"}))


@app.route('/teach', methods=['GET'])
def teach():
    data = request.args
    url = data.get("url")
    _url, keywords, content = go_embedly(url)
    if not db.articles.find_one({"url": _url}):
        if content:
            item = db.articles.insert_one({"url": _url,
                                         "create_date": datetime.now(),
                                         "keywords": keywords,
                                         "content": content})

        redisconn.rpush("queue", str(item.inserted_id))
        return json_encode({"url": item.inserted_id })
    return json_encode({"message": "Nothing inserted"})

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
        article_id = article['_id']
        visited = user.get('visited', [])
        visited.append(article_id)
        db.users.update({"token": token}, {"$set": {"visited": visited}})
        return Response(json_encode({'article': article}),mimetype="application/json")

    query = {"$and":[{"match1": {"$nin": user["visited"]}},
                     {"match2": {"$nin": user["visited"]}}]}

    similar = db.article_match.find(query).sort([("dst", 1)])
    similar = list(similar)

    if not similar:
        article = get_random()
        user['visited'].append(article['_id'])
        db.users.update({"token": token}, {"$set": {"visited": user['visited']}})
        return Response(json_encode({'article': article}),mimetype="application/json")

    match_ids = [i["match1"] if i["match1"] in user["visited"] else i["match2"] for i in similar]
    articles = db.articles.find({"_id": {"$in": match_ids}})
    user['visited'].append(articles[0]['_id'])
    db.users.update({"token": token}, {"$set": {"visited": user['visited']}})
    return Response(json_encode({"article": articles[0]}), mimetype="application/json")


@app.route('/neighbors/<string:id>', methods=["GET"])
def neighbors(id):
    query = {"$or":[{"match1": ObjectId(id)}, {"match2": ObjectId(id)}]}
    similar = db.article_match.find(query).sort([("dst", 1)])
    match_ids = [i["match1"] if i["match1"] == ObjectId(id) else i["match2"] for i in similar]
    articles = db.articles.find({"_id": {"$in": match_ids}})
    return Response(json_encode({"articles": articles}))

@app.route('/')
def index():
    return render_template('index.html')


if __name__ == "__main__":
    app.run(debug=True)
