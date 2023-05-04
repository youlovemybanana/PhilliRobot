import pymongo


class Mongo:

    def __init__(self, host, port, name):
        # Connect to database
        mongo_client = pymongo.MongoClient(host, port)
        self.db = mongo_client[name]
        self.per_page = 10

    def insert(self, collection, data):
        if type(data) == list:
            return self.db[collection].insert_many(data)
        elif type(data) == dict:
            return self.db[collection].insert_one(data)
        else:
            return None

    def find(self, collection, query=None, page=1, sort_by='_id', sort_order='desc'):
        page = int(page)
        return self.db[collection]\
                   .find(query if query else {})\
                   .sort(sort_by, 1 if sort_order == 'desc' else -1)\
                   .skip((page-1)*self.per_page)\
                   .limit(self.per_page)

    def count(self, collection, query=None):
        return self.db[collection].count_documents(query if query else {})

    def page_count(self, collection, query=None):
        return int(self.count(collection, query)/self.per_page)+1

    def update(self, collection, query, update):
        self.db[collection].update_many(query, update)

    def delete(self, collection, query):
        self.db[collection].delete_many(query)

