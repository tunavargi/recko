from app import db
from models.base import BaseModel


class ArticleIndexed(BaseModel):
    __collection_name__ = "article_indexed"

    def __init__(self, *args, **kwargs):
        self.url = None
        super(ArticleIndexed, self).__init__(*args, **kwargs)

    def save(self):
        self._id = db.article_indexed.insert({"url": self.url})
        return self._id


class ArticleLike(BaseModel):
    __collection_name__ = 'article_likes'

    def __init__(self, *args, **kwargs):
        self.article = {}
        self.article_id = None
        self.title = None
        self.user = None
        self.create_date = None
        self.url = None
        self.nsfw = None
        super(ArticleLike, self).__init__(*args, **kwargs)

    def save(self):
        if self.id:
            db.article_likes.update({"_id": self.id},
                                    {"$set": self.serialize()})
            return self._id
        else:
            self._id = db.article_likes.insert(self.serialize())
        return self._id

    def serialize(self):
        return {'article': self.article,
                "create_date": self.create_date,
                "user": self.user,
                "title": self.title,
                "url": self.url}


class ArticleVisit(BaseModel):
    __collection_name__ = 'article_visits'

    def __init__(self, *args, **kwargs):
        self.article = {}
        self.article_id = None
        self.user = None
        self.nsfw = False
        self.create_date = None
        super(ArticleVisit, self).__init__(*args, **kwargs)

    def save(self):
        if self._id:
            db.article_visits.update({"_id": self._id},
                                     {"$set": self.serialize()})
            return self._id
        else:
            self._id = db.article_visits.insert(self.serialize())
        return self._id

    def serialize(self):
        return {'article': self.article,
                'article_id': self.article_id,
                "nsfw": self.nsfw,
                "user": self.user,
                "create_date": self.create_date,
                "url": self.url}


class Article(BaseModel):

    __collection_name__ = 'articles'

    def __init__(self, *args, **kwargs):
        self.url = None
        self.create_date = None
        self.keywords = []
        self.nsfw = False
        self.content = None
        self.title = None
        super(Article, self).__init__(*args, **kwargs)

    def save(self):
        if self.id:
            db.articles.update({"_id": self._id},
                                {"$set": self.serialize()})
        else:
            self._id = db.articles.insert(self.serialize())
        return self._id

    def serialize(self):
        return {"id": self._id,
                "url": self.url,
                "nsfw": self.nsfw,
                "create_date": self.create_date,
                "keywords": self.keywords,
                "title": self.title,
                "content": self.content}