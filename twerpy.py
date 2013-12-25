import logging
import os
import sys

from lib import setup

# set up the arguments
args = setup.gen_parser().parse_args()

# set up logging
if args.debug:
    level = logging.DEBUG
else:
    level = logging.INFO
logging.basicConfig(level=level, format='%(asctime)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

# if we're doing a setup, run that then quit
if args.which == "setup" and args.database is None:
    setup.setup_all()
    sys.exit(0)

# if we're not running a basic setup, we need to import other files
from data import user_settings
from lib import database as db
from lib import tweet_handler

# find the absolute path of the database file
data_dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

if args.database:
    db_filename = os.path.join(data_dir_path, args.database)
else:
    db_filename = os.path.join(data_dir_path, user_settings.default_db_filename)


if args.which == "setup":
    setup.setup_db(db_filename)

elif args.which == "search-tweets":
    db_con = db.open_db_connection(db_filename)
    tweet_handler.search_multiple_terms(args.filename, db_con, args.no_RT)
    db.close_db_connection(db_con)

elif args.which == "search-trends":
    if args.group:
        group = args.group
    else:
        group = args.WOEID
    tweet_handler.search_trends(args.WOEID, group)

elif args.which == "search-top-users":
    db_con = db.open_db_connection(db_filename)
    if args.group:
        group = args.group
    else:
        group = args.term
    tweet_handler.search_top_users(args.term, group, db_con)
    db.close_db_connection(db_con)

elif args.which == "search-user-tweets":
    db_con = db.open_db_connection(db_filename)
    tweet_handler.search_multiple_users(args.filename, db_con)
    db.close_db_connection(db_con)

elif args.which == "search-suggested-users":
    db_con = db.open_db_connection(db_filename)
    tweet_handler.search_suggested_users(db_con)

elif args.which == "dump-tweets":
    if args.json:
        report_format = "json"
    else:
        report_format = "csv"

    db_con = db.open_db_connection(db_filename)
    tweet_handler.dump_tweets(db_con, args.group, args.output, report_format)
    db.close_db_connection(db_con)

elif args.which == "dump-users":
    if args.json:
        report_format = "json"
    else:
        report_format = "csv"

    db_con = db.open_db_connection(db_filename)
    tweet_handler.dump_users(db_con, args.group, args.output, report_format)
    db.close_db_connection(db_con)