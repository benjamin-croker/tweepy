import logging
import os
import sys

from lib import setup

# set up the arguments
args = setup.setup_parser().parse_args()
# set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

# if we're doing a setup, run that then quit
if args.which == "setup" and args.database is None:
    setup.setup_all()
    sys.exit(0)

# if we're not running a basic setup, we need to import other files
from data import auth
from lib import database as db
from lib import analysis, tweet_handler

# find the absolute path of the database file
data_dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
if args.database:
    db_filename = os.path.join(data_dir_path, args.database)
else:
    db_filename = os.path.join(data_dir_path, auth.default_db_filename)

db_dict = db.open_db_connection(db_filename)

if args.which == "setup":
    # there should be an args.database argument if execution reaches here
    setup.setup_db(db_filename)

elif args.which == "search-terms":
    tweet_handler.search_multiple_terms(args.filename, db_dict, args.no_RT)

elif args.which == "search-trends":
    tweet_handler.search_trends(args.WOEID, db_dict)

elif args.which == "calc-sentiment":
    cl_filename = os.path.join(data_dir_path, auth.default_cl_filename)
    classifier = analysis.load_sentiment(cl_filename)
    
    db.update_sentiments(db_dict, lambda text: analysis.classify_sentiment(classifier, text))

elif args.which == "report":
    tweet_handler.dump_tweets(db_dict)
    tweet_handler.dump_tweets(db_dict, "json")

    tweet_handler.dump_word_frequencies(db_dict)
    tweet_handler.dump_word_frequencies(db_dict, "json")

    tweet_handler.dump_sentiment_frequencies(db_dict)
    tweet_handler.dump_sentiment_frequencies(db_dict, "json")
    
db.close_db_connection(db_dict)






