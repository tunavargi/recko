from random import randint

import bcrypt
from app import db
from config import CRYPTING_PASSWORD
from models.base import BaseModel


class User(BaseModel):

    __collection_name__ = 'users'

    def __init__(self, *args, **kwargs):
        self.visited = []
        self.articles = []
        self.email = None
        super(User, self).__init__(*args, **kwargs)

    def set_password(self, password):
        hash = bcrypt.hashpw(password, CRYPTING_PASSWORD)
        self.password = hash
        self.save()

    def set_email(self, email):
        self.email = self.save()

    def serialize(self):
        return {'id': self.id,
                'visited': self.visited,
                "token": self.token,
                "email": self.email,
                "articles": self.articles}

    def random_article(self, nsfw=False):
        filters = {"_id": {"$nin": self.visited, "nsfw": nsfw}}
        count = db.articles.find(filters).count()
        if not count:
            return None
        random = randint(0, count-1)
        article = db.articles.find(filters).limit(1).skip(random)
        if article:
            return article[0]
        else:
            return db.articles.findOne()

    def save(self):
        if self.id:
            db.users.update({"_id": self.id},
                            {"$set": self.serialize()})
        else:
            db.users.insert(self.serialize())

    def like(self, article):
        if not article.id not in self.articles:
            db.users.update({"_id": self.id},
                            {"$push": {"articles": article.id}})

    def visit(self, article):
        if article.id not in self.visited:
            db.users.update({"_id": self.id},
                            {"$push": {"visited": article.id}})