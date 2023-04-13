import json
import pickle
from base64 import b64encode, b64decode

from django.db import models
from parser.coding import Code


class CodeField(models.Field):

    def db_type(self, connection):
        return 'text'

    def from_db_value(self, value, expression, connection):
        if value is None or value == '':
            return Code()
        try:
            v = pickle.loads(b64decode(value))
        except:
            return Code()
        # if not hasattr(v, 'flags'):  # for legacy tasks
        #     v.flags = {'build': '', 'run': ''}
        return v

    def to_python(self, value):
        if isinstance(value, Code):
            return value
        return self.from_db_value(value, None, None)

    def get_prep_value(self, value):
        return b64encode(pickle.dumps(value))


class JSONField(models.Field):
    'Keeps a JSON-serializable object as a text in the database.'

    def db_type(self, connection):
        return 'text'

    def from_db_value(self, value, expression, connection):
        try:
            return json.loads(value)
        except:
            return None

    def to_python(self, value):
        if value is None:
            return None
        return self.from_db_value(value, None, None)

    def get_prep_value(self, value):
        return json.dumps(value)


class LongJSONField(JSONField):
    'Similar to JSONField, but with LONGTEXT type'

    def db_type(self, connection):
        return 'longtext'
