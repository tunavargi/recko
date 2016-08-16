import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))

from models.articles import Article, ArticleLike, ArticleIndexed
from app import db

duplicate = set()


for article in Article.q.all():
    if article.url in duplicate:
        db.articles.remove({"_id": article.id})
        print article.id
    duplicate.add(article.url)
