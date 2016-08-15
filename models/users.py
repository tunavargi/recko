from random import randint

from datetime import datetime

import bcrypt
from app import db
from config import CRYPTING_PASSWORD
from models.articles import Article, ArticleMatch, ArticleLike, ArticleVisit
from models.base import BaseModel


class User(BaseModel):

    __collection_name__ = 'users'

    def __init__(self, *args, **kwargs):
        self.email = None
        self.password = None
        self.token = None
        super(User, self).__init__(*args, **kwargs)

    def set_password(self, password):
        hash = bcrypt.hashpw(password, CRYPTING_PASSWORD)
        db.users.update({"_id": self.id},
                        {"$set": {"password": hash}})


    def set_email(self, email):
        db.users.update({"_id": self.id},
                        {"$set": {"email": email}})

    def set_token(self, token):
        db.users.update({"_id": self.id},
                        {"$set": {"token": token}})

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

    def suggested_articles(self, nsfw=False):
        visited_ids = [i.article for i in self.visits]
        like_ids = [i.article for i in self.likes]

        query = {"match1":{"$in": like_ids},
                 "match2": {"$nin": visited_ids}}

        similar = ArticleMatch.q.filter(query).sort([("dst", 1)]).all()
        similar = list(similar)
        match_ids = [i.match2 for i in similar if i.match2]
        articles = Article.q.filter({"_id": {"$in": match_ids},
                                     "nsfw": nsfw}).all()
        return list(articles)

    def save(self):
        if self.id:
            db.users.update({"_id": self.id},
                            {"$set": self.serialize()})
        else:
            db.users.insert(self.serialize())

    def like(self, article):
        # LIKE THE ARTICLE
        if article not in self.likes:
            article_like = ArticleLike(**{"create_date": datetime.utcnow(),
                                          "url": article.url,
                                          "user": self.id,
                                          "nsfw": article.nsfw,
                                          "article": article.id})
            article_like.save()

    @property
    def likes(self):
        articles = ArticleLike.q.filter({"user": self.id}).all()
        return list(articles)

    @property
    def visits(self):
        articles = ArticleVisit.q.filter({"user": self.id}).all()
        return list(articles)


    def visit(self, article):
        # ADD THE ARTICLE AS VISITED
        if article not in self.visits:
            article_visit = ArticleVisit(**{"create_date": datetime.utcnow(),
                                            "url": article.url,
                                            "user": self.id,
                                            "nsfw": article.nsfw,
                                            "article": article.id})
            article_visit.save()
        return article