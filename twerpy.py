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


if args.which == "setup":
    setup.setup_db(db_filename)

elif args.which == "search-tweets":
    db_dict = db.open_db_connection(db_filename)
    tweet_handler.search_multiple_terms(args.filename, db_dict, args.no_RT)
    db.close_db_connection(db_dict)

elif args.which == "search-trends":
    if args.group:
        group = args.group
    else:
        group = args.WOEID
    tweet_handler.search_trends(args.WOEID, group)

elif args.which == "calc-sentiment":
    db_dict = db.open_db_connection(db_filename)
    cl_filename = os.path.join(data_dir_path, auth.default_cl_filename)
    classifier = analysis.load_sentiment(cl_filename)

    db.update_sentiments(db_dict, lambda text: analysis.classify_sentiment(classifier, text))
    db.close_db_connection(db_dict)

elif args.which == "search-top-users":
    db_dict = db.open_db_connection(db_filename)
    if args.group:
        group = args.group
    else:
        group = args.term
    tweet_handler.search_top_users(args.term, group, db_dict)
    db.close_db_connection(db_dict)

elif args.which == "search-user-tweets":
    db_dict = db.open_db_connection(db_filename)
    tweet_handler.search_multiple_users(args.filename, db_dict)
    db.close_db_connection(db_dict)

elif args.which == "dump-tweets":
    if args.json:
        report_format = "json"
    else:
        report_format = "csv"

    if args.group:
        group = args.group
    else:
        group = None

    db_dict = db.open_db_connection(db_filename)
    tweet_handler.dump_tweets(db_dict, group, report_format)
    db.close_db_connection(db_dict)

elif args.which == "dump-users":
    if args.json:
        report_format = "json"
    else:
        report_format = "csv"

    if args.group:
        group = args.group
    else:
        group = None

    db_dict = db.open_db_connection(db_filename)
    tweet_handler.dump_users(db_dict, group, report_format)
    db.close_db_connection(db_dict)

elif args.which == "report":
    if args.json:
        report_format = "json"
    else:
        report_format = "csv"

    db_dict = db.open_db_connection(db_filename)
    tweet_handler.dump_word_frequencies(db_dict, report_format)
    tweet_handler.dump_sentiment_frequencies(db_dict, report_format)
    db.close_db_connection(db_dict)






