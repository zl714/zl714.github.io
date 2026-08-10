from pymongo import MongoClient


class AnimalShelter(object):
    """CRUD operations for the Animal collection in MongoDB."""

    def __init__(self, username, password, host='localhost', port=27017, db='aac', col='animals'):
        self.client = MongoClient(
            f'mongodb://{username}:{password}@{host}:{port}/{db}?authSource={db}'
        )
        self.database = self.client[db]
        self.collection = self.database[col]

    # Create
    def create(self, data):
        if data is None or not isinstance(data, dict):
            return False
        try:
            result = self.collection.insert_one(data)
            return result.acknowledged
        except:
            return False

    # Read
    def read(self, query):
        if query is None or not isinstance(query, dict):
            return []
        try:
            return list(self.collection.find(query, {"_id": False}))
        except:
            return []

    # Update
    def update(self, query, new_values):
        if query is None or not isinstance(query, dict):
            return 0
        if new_values is None or not isinstance(new_values, dict):
            return 0
        try:
            result = self.collection.update_many(query, {"$set": new_values})
            return result.modified_count
        except:
            return 0

    # Delete
    def delete(self, query):
        if query is None or not isinstance(query, dict):
            return 0
        try:
            result = self.collection.delete_many(query)
            return result.deleted_count
        except:
            return 0
