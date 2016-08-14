from app import db
from models.base import BaseModel


class Article(BaseModel):

    __collection_name__ = 'articles'

    def __init__(self, *args, **kwargs):
        self.url = None
        self.create_date = None
        self.keywords = []
        self.content = None
        super(Article, self).__init__(*args, **kwargs)

    def save(self):
        if self.id:
            db.articles.update({"_id": self.id},
                                {"$set": self.serialize()})
            return self._id
        else:
            inserted_id = db.articles.insert(self.serialize())
            return inserted_id

    def serialize(self):
        return {'id': self.id,
                'url': self.url,
                "create_date": self.create_date,
                "keywords": self.keywords,
                "content": self.content}



class ArticleMatch(BaseModel):

    __collection_name__ = 'article_matches'

    def __init__(self, *args, **kwargs):
        self.match1 = None
        self.match2 = None
        self.dst = 0

    def serialize(self):
        return {"id": self.id,
                "match1": self.match1,
                "match2": self.match2,
                "dst": self.dst}

    def save(self):
        if self.id:
            db.article_matches.update({"_id": self.id},
                            {"$set": self.serialize()})
        else:
            db.article_matches.insert(self.serialize())