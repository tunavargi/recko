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

application = Flask(__name__, static_url_path='/static')

redisconn = redis.StrictRedis(host=REDIS_HOST, port=6379, db=0)
client = MongoClient(host=MONGO_HOST, port=MONGO_PORT, connect=False)
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
    from models.users import User
    email = None
    password = None
    if request.json:
        email = request.json.get("email")
        password = request.json.get("password")
    if not (email and password):
        token = "tok-%s" % uuid.uuid4().hex
        user = User(**{})
        user.save()
        user.set_token(token)
    else:
        user = User.q.filter_by(email=email).first()
        if not user:
            return Response(status=403)
        check = user.check_password(password)
        if not check:
            return Response(status=403)
        token = user.token
    return Response(json_encode({"token": token,
                                 "email": email}))


@application.route("/signup", methods=["POST"])
def signup():
    from models.users import User
    email = request.json.get("email")
    password = request.json.get("password")
    token = request.args.get("token")

    if not (email and password):
        return Response(status=400)

    # check if same email is not used
    email_exists= User.q.filter_by(email=email).first()
    if email_exists:
        return Response(status=400)

    # set username and password
    user = User.q.filter_by(token=token).first()
    if not user:
        return Response(status=403)

    user.set_email(email)
    user.set_password(password)
    return Response(status=201)


@application.route("/likes", methods=["GET"])
def likes():
    from models.users import User
    token = request.args.get("token")
    offset = request.args.get("offset", 0)

    if not token:
        return Response(status=403)
    user = User.q.filter_by(token=token).first()
    if not user:
        return Response(status=403)

    from models.articles import ArticleLike
    article_likes = ArticleLike.q.filter({"user": user.id}).\
        sort([("_id", -1)]).skip(offset).all()

    bundle = [{"url": i.url, "title": i.title} for i in article_likes]
    return Response(json_encode({"articles": bundle}))


@application.route("/like", methods=["POST"])
def like():
    from models.users import User
    token = request.args.get("token")
    url_id = request.json.get("url")
    if not token:
        return Response(status=403)
    user = User.q.filter_by(token=token).first()
    if not user:
        return Response(status=403)

    from models.users import Article
    article = Article.q.fetch_by_id(url_id)

    user.like(article)
    return Response(json_encode({"message": "liked"}))


@application.route("/next", methods=["GET"])
def _next():
    from models.users import User

    token = request.args.get("token")
    nsfw = request.args.get("nsfw")
    nsfw = nsfw == 'true'
    if not token:
        return Response(status=403)
    user = User.q.filter_by(token=token).first()
    if not user:
        return Response(status=403)

    if not len(user.likes) >= 5:
        # IF USER LIKED ARTICLES ARE NOT MORE THAN 5
        # RETURN RANDOM
        article = user.random_article(nsfw=nsfw)
        if not article:
            return Response(status=404)

        user.visit(article)
        return Response(json_encode({'article': article.serialize()}),
                        mimetype="application/json")

    suggested_articles = user.suggested_articles(nsfw=nsfw)
    if not suggested_articles:
        article = user.random_article(nsfw=nsfw)
        if not article:
            return Response(status=404)
        user.visit(article)
        return Response(json_encode({'article': article.serialize()}),
                        mimetype="application/json")

    random = randint(0, len(suggested_articles)-1)
    random_suggested = suggested_articles[random]
    visited_article = user.visit(random_suggested)
    return Response(json_encode({"article": visited_article.serialize()}),
                    mimetype="application/json")

@application.route('/')
def index():
    return render_template('index.html')

@application.route('/about')
def about():
    return render_template('about.html')

@application.route('/mylikes')
def likes_template():
    return render_template('likes.html')

@application.route('/login')
def login_template():
    return render_template('login.html')

@application.route('/register')
def register_template():
    return render_template('register.html')

@application.route('/nsfw')
def nsfw():
    return render_template('nsfw.html')

if __name__ == "__main__":
    application.run(debug=True)
