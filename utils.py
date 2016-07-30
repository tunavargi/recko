import datetime
import json
import re

from bson import ObjectId

RFC_2822_DATETIME_RE = re.compile(r"([A-Za-z]{3}), ([0-9]{2}) ([A-Za-z]{3}) ([0-9]{4}) ([0-9]{2})\:([0-9]{2})\:([0-9]{2}) ([-|+][0-9]{4})")
RFC_2822_DATE_RE = re.compile(r"([A-Za-z]{3}), ([0-9]{2}) ([A-Za-z]{3}) ([0-9]{4})")
RFC_2822_DATETIME_FORMAT = "%a, %d %b %Y %H:%M:%S %z"
RFC_2822_DATE_FORMAT = "%a, %d %b %Y"


class ExtendedJSONEncoder(json.JSONEncoder):
    """
    Extended JSON encoder that is capable of encoding the following:

        * datetime
        * date
        * ObjectId
    """
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime(RFC_2822_DATETIME_FORMAT)
        elif isinstance(obj, datetime.date):
            return obj.strftime(RFC_2822_DATE_FORMAT)
        elif isinstance(obj, ObjectId):
            return str(obj)

        return super(ExtendedJSONEncoder, self).default(obj)


def json_encode(value):
    """
    Encodes value into a JSON string
    """
    return json.dumps(
        value,
        cls=ExtendedJSONEncoder
    )