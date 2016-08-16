import redis
from bson import ObjectId
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))

from models.articles import Article, ArticleMatch
from scipy.spatial import distance
from config import REDIS_HOST

redisconn = redis.StrictRedis(host=REDIS_HOST, port=6379, db=0)

def calculate_euclidaen_distance(new_article, matched_article):
    "Calculate the euclidaen distance between matched url and recored url"
    new_article_kws = {i['name']: i['score'] for i in new_article.keywords if i['score'] >= 50}
    matched_article_kws = {i['name']: i['score'] for i in matched_article.keywords if i['score'] >= 50}
    all_keywords = [i for i in [i["name"] for i in new_article.keywords if i["score"] >= 50]] + \
                   [i for i in [i["name"] for i in matched_article.keywords if i["score"] >= 50]]

    a = tuple([new_article_kws.get(i, 0) for i in all_keywords])
    b = tuple([matched_article_kws.get(i, 0) for i in all_keywords])
    try:
        dst = distance.euclidean(a,b)
        return dst
    except:
        print a,b


def calculater():
    while True:
        id = redisconn.blpop('queue')
        try:
            article = Article.q.fetch_by_id(id[1])
            words = [i['name'] for i in article.keywords if i.get("score", 0) > 45]
            matching_urls = Article.q.filter({"keywords.name": {"$in": words},
                                              "_id": {"$ne": ObjectId(id[1])}}).all()
            for i in matching_urls:
                dst = calculate_euclidaen_distance(article, i)
                article1 = ArticleMatch(**{"match1": article.id,
                                           "match2": i.id,
                                           "dst":dst})
                article2 = ArticleMatch(**{"match2": article.id,
                                           "match1": i.id,
                                           "dst":dst})
                article1.save()
                article2.save()
                print article.id

        except Exception as e:
            print(e)


if __name__ == "__main__":
    calculater()