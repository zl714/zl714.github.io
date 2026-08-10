import logging
from urllib.parse import quote_plus

from pymongo import ASCENDING, MongoClient
from pymongo.errors import DuplicateKeyError, PyMongoError


logger = logging.getLogger("animal_shelter_database")


class AnimalShelter(object):
    """CRUD operations for the Animal collection in MongoDB."""

    MAX_READ_LIMIT = 5000

    def __init__(
        self,
        username,
        password,
        host="localhost",
        port=27017,
        db="aac",
        col="animals",
    ):
        if not username or not password:
            raise ValueError("MongoDB username and password are required.")

        safe_username = quote_plus(username)
        safe_password = quote_plus(password)
        connection_string = (
            f"mongodb://{safe_username}:{safe_password}@{host}:{port}/"
            f"{db}?authSource={db}"
        )
        self.client = MongoClient(
            connection_string,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
        )
        self.database = self.client[db]
        self.collection = self.database[col]

    # Create
    def create(self, data):
        if not isinstance(data, dict) or not data:
            return False
        try:
            result = self.collection.insert_one(data)
            return result.acknowledged
        except DuplicateKeyError:
            logger.warning("Create rejected a duplicate animal record.")
            return False
        except PyMongoError:
            logger.exception("MongoDB create operation failed.")
            raise

    # Read
    def read(
        self,
        query,
        projection=None,
        sort=None,
        skip=0,
        limit=MAX_READ_LIMIT,
    ):
        if not isinstance(query, dict):
            return []
        if projection is not None and not isinstance(projection, dict):
            raise ValueError("Projection must be a dictionary or None.")
        if not isinstance(skip, int) or skip < 0:
            raise ValueError("Skip must be a nonnegative integer.")
        if limit is not None and (not isinstance(limit, int) or limit < 1):
            raise ValueError("Limit must be a positive integer or None.")

        safe_limit = (
            self.MAX_READ_LIMIT
            if limit is None
            else min(limit, self.MAX_READ_LIMIT)
        )

        try:
            cursor = self.collection.find(
                query,
                projection if projection is not None else {"_id": False},
            )
            if sort:
                cursor = cursor.sort(sort)
            if skip:
                cursor = cursor.skip(skip)
            return list(cursor.limit(safe_limit))
        except PyMongoError:
            logger.exception("MongoDB read operation failed.")
            raise

    def count(self, query):
        if not isinstance(query, dict):
            return 0
        try:
            return self.collection.count_documents(query)
        except PyMongoError:
            logger.exception("MongoDB count operation failed.")
            raise

    def distinct(self, field, query=None):
        if not isinstance(field, str) or not field:
            return []
        if query is not None and not isinstance(query, dict):
            return []
        try:
            return self.collection.distinct(field, query or {})
        except PyMongoError:
            logger.exception("MongoDB distinct operation failed.")
            raise

    def breed_counts(self, query):
        if not isinstance(query, dict):
            return []
        pipeline = [
            {"$match": query},
            {"$match": {"breed": {"$nin": [None, ""]}}},
            {"$group": {"_id": "$breed", "count": {"$sum": 1}}},
            {"$sort": {"count": -1, "_id": 1}},
        ]
        try:
            return [
                {"breed": item["_id"], "count": item["count"]}
                for item in self.collection.aggregate(pipeline)
            ]
        except PyMongoError:
            logger.exception("MongoDB breed-count query failed.")
            raise

    def ensure_rescue_index(self):
        """Create the one compound index used by rescue searches."""
        try:
            return self.collection.create_index(
                [
                    ("animal_type", ASCENDING),
                    ("breed", ASCENDING),
                    ("age_upon_outcome_in_weeks", ASCENDING),
                ],
                name="rescue_search_idx",
            )
        except PyMongoError:
            logger.exception("MongoDB rescue index could not be verified.")
            raise

    # Update
    def update(self, query, new_values):
        if not isinstance(query, dict) or not query:
            logger.warning("Update rejected an empty or invalid query.")
            return 0
        if not isinstance(new_values, dict) or not new_values:
            return 0
        try:
            result = self.collection.update_many(query, {"$set": new_values})
            return result.modified_count
        except PyMongoError:
            logger.exception("MongoDB update operation failed.")
            raise

    # Delete
    def delete(self, query):
        if not isinstance(query, dict) or not query:
            logger.warning("Delete rejected an empty or invalid query.")
            return 0
        try:
            result = self.collection.delete_many(query)
            return result.deleted_count
        except PyMongoError:
            logger.exception("MongoDB delete operation failed.")
            raise
