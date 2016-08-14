import redis
from bson import ObjectId
from pymongo import MongoClient
from scipy.spatial import distance

from config import REDIS_HOST, DB_NAME, MONGO_HOST, MONGO_PORT
client = MongoClient(host=MONGO_HOST, port=MONGO_PORT)

redisconn = redis.StrictRedis(host=REDIS_HOST, port=6379, db=0)
db = client[DB_NAME]

def calculate_euclidaen_distance(new_article, matched_article):
    "Calculate the euclidaen distance between matched url and recored url"

    new_article_kws = {i["name"]: i["score"] for i in new_article["keywords"] if i['score'] >= 50}
    matched_article_kws = {i["name"]: i["score"] for i in matched_article["keywords"] if i['score'] >= 50}
    all_keywords = [i for i in [i["name"] for i in new_article["keywords"] if i["score"] >= 50]] + [i for i in [i["name"] for i in matched_article["keywords"] if i["score"] >= 50]]
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
            article = db.articles.find_one({"_id": ObjectId(id[1])})
            words = [i["name"] for i in article["keywords"] if i['score'] > 45]
            matching_urls = db.articles.find({"keywords.name": {"$in": words}, "_id": {"$ne": ObjectId(id[1])}})
            for i in matching_urls:
                dst = calculate_euclidaen_distance(article, i)
                db.article_match.insert_one({"match1": article['_id'],
                                             "match2": i['_id'],
                                             "dst": dst})
                db.article_match.insert_one({"match2": article['_id'],
                                             "match1": i['_id'],
                                             "dst": dst})
        except Exception as e:
            print(e)
if __name__ == "__main__":
    calculater()