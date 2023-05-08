import pymongo
from env import env
from datetime import datetime

# Environment detection
if env == 'live':
    import config_live
    config = config_live
elif env == 'dev':
    import config_dev
    config = config_dev
else:
    import config_test
    config = config_test

# Connect to database
mongo_client = pymongo.MongoClient(config.db_host, config.db_port)
db = mongo_client[config.db_name]

# Collections structures
employee = {
    'name': '',
    'number': 0,
    'telegram_id': 0,
    'rating': 0,
    'groups': []
}
task = {
    'title': '',
    'description': '',
    'start_date': datetime.min,
    'deadline': datetime.max,
    'operators': [
        {
            'id': 0,
            'status': '',
            'comment': '',
            'charge': 0
        }
    ],
    'status': '',
    'creator': 0
}
db.employee.create_index([('name', 'text')])
db.task.create_index([('title', 'text'), ('description', 'text')])
print('all done')

