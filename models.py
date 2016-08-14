import bcrypt
from config import CRYPTING_PASSWORD
from app import db

class Article(object):
    url = None
    create_date = None
    content = None



class ArticleMatch(object):

class User(object):
    id = None
    visited = []
    articles = []
    token = None
    email = None
    password = None

    def __init__(self, **kwargs):
        self.id = kwargs.get("_id")
        self.visited = kwargs.get("visited")
        self.articles = kwargs.get("articles")
        self.email = kwargs.get("email")

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

    def save(self):
        if self.id:
            db.users.update({"_id": self.id},
                            {"$set": self.serialize()})
        else:
            db.users.insert(self.serialize())

    def like(self, article):
        if not article.id not in self.articles:
            db.users.push({"articles": article.id})

    def visit(self, article):
        if article.id not in self.visited:
            db.users.push({"visited": self.id})