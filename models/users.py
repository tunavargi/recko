from collections import defaultdict
from random import randint

from datetime import datetime

import bcrypt
from app import db
from config import CRYPTING_PASSWORD
from models.articles import Article, ArticleLike, ArticleVisit
from models.base import BaseModel
from scipy.spatial import distance


class User(BaseModel):

    __collection_name__ = 'users'

    def __init__(self, *args, **kwargs):
        self.email = None
        self.password = None
        self.token = None
        super(User, self).__init__(*args, **kwargs)


    def set_email(self, email):
        db.users.update({"_id": self._id},
                        {"$set": {"email": email}})

    def set_token(self, token):
        db.users.update({"_id": self._id},
                        {"$set": {"token": token}})

    def set_password(self, password):
        password = password.encode("utf-8")
        hash = bcrypt.hashpw(b"%s" % password, CRYPTING_PASSWORD)
        db.users.update({"_id": self._id},
                         {"$set": {"password": hash}})

    def check_password(self, password):
        password = password.encode("utf-8")
        hash = bcrypt.hashpw(b'%s' % password, CRYPTING_PASSWORD)
        return hash == self.password

    def serialize(self):
        return {'id': self.id,
                "email": self.email}

    def random_article(self, nsfw=False):
        visited_ids = [i.article for i in self.visits]
        filters = {"_id": {"$nin": visited_ids},
                   "nsfw": nsfw}
        count = Article.q.filter(filters).count()
        if not count:
            return None
        random = randint(0, count-1)
        article = Article.q.filter(filters).limit(1).skip(random).first()
        if article:
            return article
        return None

    def calculate_euclidaen_distance(self, user_keywords, matched_article):
        "Calculate the euclidaen distance between matched url and recored url"
        new_article_kws = {i['name']: i['score'] for i in user_keywords if i['score'] >= 25}
        matched_article_kws = {i['name']: i['score'] for i in matched_article.keywords if i['score'] >= 25}
        all_keywords = [i for i in [i["name"] for i in user_keywords if i["score"] >= 25]] + \
                       [i for i in [i["name"] for i in matched_article.keywords if i["score"] >= 25]]

        a = tuple([new_article_kws.get(i, 0) for i in all_keywords])
        b = tuple([matched_article_kws.get(i, 0) for i in all_keywords])
        try:
            dst = distance.euclidean(a,b)
            return dst
        except:
            return 0

    def suggested_articles(self, nsfw=False):
        visited_ids = [i.article_id for i in self.visits]
        likes = self.likes
        liked_kws = [i.article.get("keywords") for i in likes]
        user_keywords = defaultdict(int)
        counts = defaultdict(int)
        for keywords in liked_kws:
            for keyword in keywords:
                user_keywords[keyword["name"]] += keyword["score"]
                counts[keyword["name"]] += 1

        mean_keywords = [{"name": i, "score": v/counts[i]}
                         for i, v in user_keywords.items()
                         if v/counts[i] > 25]


        mean_keys = [i["name"] for i in mean_keywords]
        filters = {"_id": {"$nin": visited_ids},
                   "keywords.name": {"$in": mean_keys}}
        not_visited_closest_articles = Article.q.filter(filters).sort([("_id", -1)]).limit(10).all()
        smallest_distance = 1000
        closest = None
        for not_visited_article in not_visited_closest_articles:
            distance = self.calculate_euclidaen_distance(mean_keywords, not_visited_article)

            if distance:
                if distance < smallest_distance:
                    smallest_distance = distance
                    closest = not_visited_article
        return closest


    def save(self):
        if self._id:
            db.users.update({"_id": self._id},
                            {"$set": self.serialize()})
        else:
            self._id = db.users.insert(self.serialize())
        return self._id


    def like(self, article):
        # LIKE THE ARTICLE
        if article not in self.likes:
            article_like = ArticleLike(**{"create_date": datetime.utcnow(),
                                          "url": article.url,
                                          "user": self._id,
                                          "nsfw": article.nsfw,
                                          "title": article.title,
                                          "article": article.serialize(),
                                          "article_id": article._id})
            article_like.save()


    @property
    def likes(self):
        articles = ArticleLike.q.filter({"user": self._id}).sort([("_id", -1)]).limit(10).all()
        return list(articles)

    @property
    def visits(self):
        articles = ArticleVisit.q.filter({"user": self._id}).all()
        return list(articles)


    def visit(self, article):
        # ADD THE ARTICLE AS VISITED
        if article not in self.visits:
            article_visit = ArticleVisit(**{"create_date": datetime.utcnow(),
                                            "url": article.url,
                                            "user": self._id,
                                            "nsfw": article.nsfw,
                                            "article": article.serialize(),
                                            "article_id": article.id})
            article_visit.save()
        return article