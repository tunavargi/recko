import os, sys

sys.path.append(os.path.join(os.path.dirname(__file__), '../'))

from models.articles import Article, ArticleLike
from app import db


for article in Article.q.all():
    if article.title:
        print article.title
        db.article_likes.update({"article": article._id},
                                {"$set": {"title": article.title}},
                                multi=True)
