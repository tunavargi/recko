from random import randint

import bcrypt
from app import db
from config import CRYPTING_PASSWORD
from models.articles import Article, ArticleMatch
from models.base import BaseModel


class User(BaseModel):

    __collection_name__ = 'users'

    def __init__(self, *args, **kwargs):
        self.visited = []
        self.articles = []
        self.email = None
        self.token = None
        self.password = None
        super(User, self).__init__(*args, **kwargs)

    def set_password(self, password):
        password = password.encode("utf-8")
        hash = bcrypt.hashpw(b"%s" % password, CRYPTING_PASSWORD)
        db.photos.update({"_id": self.id}, {"$set": {"password": hash}})

    def check_password(self, password):
        password = password.encode("utf-8")
        hash = bcrypt.hashpw(b'%s' % password, CRYPTING_PASSWORD)
        return hash == self.password

    def set_email(self, email):
        self.email = email
        self.save()

    def serialize(self):
        return {'id': self.id,
                'visited': self.visited,
                "token": self.token,
                "email": self.email,
                "articles": self.articles}

    def random_article(self, nsfw=False):
        filters = {"_id": {"$nin": self.visited},
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
        query = {"match1":{"$in": self.articles},
                 "match2": {"$nin": self.visited}}

        similar = ArticleMatch.q.filter(query).sort([("dst", 1)]).all()
        similar = list(similar)
        match_ids = [i.match2 for i in similar if i.match2]
        articles = Article.q.filter({"_id": {"$in": match_ids}, "nsfw": nsfw}).all()
        return list(articles)

    def save(self):
        if self.id:
            db.users.update({"_id": self.id},
                            {"$set": self.serialize()})
        else:
            db.users.insert(self.serialize())

    def like(self, article):
        # LIKE THE ARTICLE
        if not article.id not in self.articles:
            db.users.update({"_id": self.id},
                            {"$push": {"articles": article.id}})

    def visit(self, article):
        # ADD THE ARTICLE AS VISITED
        if article.id not in self.visited:
            db.users.update({"_id": self.id},
                            {"$push": {"visited": article.id}})
        return article
