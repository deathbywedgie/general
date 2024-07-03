"""
Using a custom storage class to change stuff...
but not a great example, because you can pass json args when calling TinyDB
"""

from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware
import json
from typing import Dict, Any


class PrettyJSONStorage(JSONStorage):
    def write(self, data: Dict[str, Dict[str, Any]]):
        """
        Write data to the file in pretty-printed JSON format.
        """
        with open(self._handle.name, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, separators=(',', ': '))


# Use the custom storage class with caching middleware for better performance
root_db = TinyDB('pretty_db.json', storage=CachingMiddleware(PrettyJSONStorage))

table1 = root_db.table("table1")
table2 = root_db.table("table2")

for table in (table1, table2):
    # Insert data into the database
    table.insert({'name': 'John', 'age': 22, 'location': 'New York'})
    table.insert({'name': 'Jane', 'age': 28, 'location': 'Chicago'})
    table.insert({'name': 'Doe', 'age': 32, 'location': 'San Francisco'})

root_db.close()