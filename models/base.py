from app import db
from bson import ObjectId


class classproperty(property):
    def __get__(self, cls, owner):
        return classmethod(self.fget).__get__(None, owner)()


class BaseModel(object):
    def __init__(self, *args, **kwargs):
        self._id = None
        for key, value in kwargs.items():
            try:
                setattr(self, key, value)
            except AttributeError:
                print ("Cant set attribute %s: %s" % (key,value))

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        if value:
            self._id = value

    def serialize(self):
        return {
            "id": self.id,
        }

    @classproperty
    def q(cls):
        """
        :rtype: BlockingQuery
        """
        return BlockingQuery(cls, database=db)

class BlockingQuery(object):

    def __init__(self, model, database):
        self.model = model
        self.database = database
        self._filters = {}
        self._sort_params = None
        self._limit = None
        self._skip = None
        self._distinct = None

    def filter_by(self, **kwargs):
        self._filters.update(kwargs)
        return self

    def filter(self, filters):
        self._filters.update(filters)
        return self

    def sort(self, *args):
        self._sort_params = args
        return self

    def limit(self, i):
        self._limit = i
        return self

    def remove(self):
        assert self._filters
        return self.collection.remove(self._filters)

    def skip(self, i):
        self._skip = i
        return self

    def distinct(self, i):
        self._distinct = i
        return self


    def chunked_all(self):
        last_id = None
        finished = False
        while not finished:
            if last_id:
                self._filters.update({'_id': {'$gt': last_id}})

            cursor = self.collection.find(self._filters)
            cursor.sort('_id', 1)
            cursor.limit(100)
            ret = []
            for data in cursor:
                obj = self.model(**data)
                ret.append(obj)
                last_id = obj._id
            for obj in ret:
                yield obj
            if not ret:
                finished = True

    @property
    def collection(self):
        return self.database[self.model.__collection_name__]

    def count(self):
        cursor = self.collection.find(self._filters)
        return cursor.count()

    def find(self):
        cursor = self.collection.find(self._filters)
        if self._sort_params:
            cursor.sort(*self._sort_params)
        if self._limit:
            cursor.limit(self._limit)
        if self._skip:
            cursor.skip(self._skip)

        if self._distinct:
            cursor.distinct(self._distinct)

        for data in cursor:
            obj = self.model(**data)
            yield obj

    def all(self):
        return self.find()

    def first(self):
        return self.find_one()

    def one(self):
        c = list(self.limit(2).find())
        assert len(c) > 0, "you wanted one but db returned None"
        assert len(c) == 1, "you wanted only one but db returned more than one"
        return c[0]

    def find_one(self):
        if self._sort_params or self._skip:
            self._limit = 1
            objects = self.find()
            if objects:
                return list(objects)[0]
            else:
                return None
        else:
            data = self.collection.find_one(self._filters)
            if not data:
                return data
            else:
                obj = self.model(**data)
                return obj

    def fetch_by_id(self, identifier):
        """
        returns Model instance if found from database
        """
        return self.filter_by(_id=ObjectId(identifier)).find_one()

    def find_distinct(self, field, callback):
        """
        returns distinct results of given field
        """
        distinct_field_values = self.collection.find(self._filters).distinct(field)
        objects = self.filter({field: {'$in': distinct_field_values}}).find()
        return objects