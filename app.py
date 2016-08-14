import json
import uuid
from datetime import datetime
from random import randint
import redis
import requests
from bson import ObjectId
from flask import Flask, Response, render_template
from flask import request
from pymongo import MongoClient
from utils import json_encode
from config import EMBEDLY_API_KEY, REDIS_HOST, DB_NAME, MONGO_HOST, MONGO_PORT

application = Flask(__name__)

client = MongoClient(host=MONGO_HOST, port=MONGO_PORT)
redisconn = redis.StrictRedis(host=REDIS_HOST, port=6379, db=0)
db = client[DB_NAME]


def go_embedly(url):
    req_url = "https://api.embedly.com/1/extract"
    response = requests.get(req_url, params={"url": url,
                                         "key": EMBEDLY_API_KEY})
    result = response.json()
    return result.get("url"),result.get("keywords"), \
           result.get("content")


@application.route("/authenticate", methods=["POST"])
def authenticate():
    token = "tok-%s" % uuid.uuid4().hex
    db.users.insert_one({"articles": [],
                         "visited": [],
                         "token": token})
    return Response(token)


@application.route("/like", methods=["POST"])
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
    if not article:
        return Response(status=404)

    if not article["_id"] in liked:
        liked.append(article["_id"])
    db.users.update({"token":token},
                    {"$set": {"articles": liked}})

    return Response(json_encode({"message" : "liked"}))


@application.route('/teach', methods=['GET'])
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

def get_random(user, nsfw=False):
    filters = {"_id": {"$nin": user.get('visited', [])}, "nsfw": nsfw}
    count = db.articles.find(filters).count()
    if not count:
        return None
    random = randint(0, count -1)
    article = db.articles.find(filters).limit(1).skip(random)
    if article:
        return article[0]
    else:
        return db.articles.findOne()

@application.route("/next", methods=["GET"])
def _next():
    token = request.args.get("token")
    nsfw = request.args.get("nsfw")
    nsfw = nsfw == 'true'

    if not token:
        return Response(status=403)
    user = db.users.find_one({"token": token})
    if not user:
        return Response(status=403)

    if not user['articles']:
        article = get_random(user, nsfw=nsfw)
        if not article:
            return Response(status=404)
        article_id = article['_id']
        visited = user.get('visited', [])
        visited.append(article_id)
        db.users.update({"token": token}, {"$set": {"visited": visited}})
        return Response(json_encode({'article': article}),
                        mimetype="application/json")

    query = {"match1":{"$in": user["articles"]},
             "match2": {"$nin": user["visited"]}}

    similar = db.article_match.find(query).sort([("dst", 1)])
    similar = list(similar)
    match_ids = [i["match2"] for i in similar if i["match2"]]
    articles = db.articles.find({"_id": {"$in": match_ids}, "nsfw": nsfw})

    if not articles.count():
        article = get_random(user, nsfw=nsfw)
        if not article:
            return Response(status=404)
        user['visited'].append(article['_id'])
        db.users.update({"token": token}, {"$set": {"visited": user['visited']}})
        return Response(json_encode({'article': article}),mimetype="application/json")

    random = randint(0, articles.count()-1)
    user['visited'].append(articles[random]['_id'])
    db.users.update({"token": token},
                    {"$set": {"visited": user['visited']}})
    return Response(json_encode({"article": articles[random]}),
                    mimetype="application/json")

@application.route('/neighbors/<string:id>', methods=["GET"])
def neighbors(id):
    query = {"$or":[{"match1": ObjectId(id)}, {"match2": ObjectId(id)}]}
    similar = db.article_match.find(query).sort([("dst", 1)])
    match_ids = [i["match1"] if i["match1"] == ObjectId(id) else i["match2"] for i in similar]
    articles = db.articles.find({"_id": {"$in": match_ids}})
    return Response(json_encode({"articles": articles}))

@application.route('/')
def index():
    return render_template('index.html')

if __name__ == "__main__":
    application.run(debug=True)
