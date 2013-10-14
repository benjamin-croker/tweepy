import argparse
import logging
import os

import analysis
import database as db

def setup_parser():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    # set up arguments for the setup command
    setup_parser = subparsers.add_parser("setup",
            help="Set up the authentification, database and sentiment classifier")
    setup_parser.add_argument("-d", "--database", help="Set up database only. Specify DB filename in data directory")
    setup_parser.set_defaults(which="setup")

    # set up arguments for the search-terms command
    term_parser = subparsers.add_parser("search-terms",
            help="Search for terms in the given file")
    term_parser.add_argument("filename")
    term_parser.add_argument("-d", "--database",
            help="Specify DB filename in the 'data' directory")
    term_parser.add_argument("--no_RT",
            help="do not include retweets in the search", action="store_true")
    term_parser.set_defaults(which="search-terms")

    # set up arguments for the search-trends command
    trends_parser = subparsers.add_parser("search-trends",
            help="Search trending terms for the given WOEID")
    trends_parser.add_argument("WOEID")
    trends_parser.add_argument("-d", "--database",
            help="Specify DB filename in the 'data' directory")
    trends_parser.set_defaults(which="search-trends")

    # set up arguments for the calc-sentiment command
    calc_parser = subparsers.add_parser("calc-sentiment",
            help="Calculates the sentiment for all tweets in the database")
    calc_parser.add_argument("-d", "--database",
            help="Specify DB filename in the 'data' directory")
    calc_parser.add_argument("--force",
            help="Recalculate the sentiment for each tweet, even if it is already calculated")
    calc_parser.set_defaults(which="calc-sentiment")

    # set up arguments for the report command
    report_parser = subparsers.add_parser("report",
            help="Writes CSV (default) or JSON reports to the 'reports' directory")
    report_parser.add_argument("-d", "--database",
            help="Specify DB filename in 'data' directory")
    report_parser.set_defaults(which="report")

    return parser


def setup_db(db_filename):
    logging.info("Creating new database file {0} in data directory".format(db_filename))
    db.reset(db_filename)


def setup_all():
    def _join_to_data_dir(filename):
        # this file is  tweepy/lib/setup.py, so navigate to tweepy/
        # the join with data/ to get tweepy/data/
        return os.path.join(
                os.path.dirname(os.path.dirname(
                        os.path.abspath(__file__))),
                "data", filename)

    access_token_key = raw_input("Enter access token key: ")
    access_token_secret = raw_input("Enter access token secret: ")
    consumer_key = raw_input("Enter consumer key: ")
    consumer_secret = raw_input("Enter consumer secret: ")

    default_db_filename = raw_input("Enter default database file name\n" +
                                  "Leave blank to use 'tweets.db'")
    if len(default_db_filename) == 0:
        default_db_filename = "tweets.db"

    with open(_join_to_data_dir("auth.py"), "w") as authFile:
        authFile.write("access_token_key = \"{0}\"\n".format(access_token_key))
        authFile.write("access_token_secret = \"{0}\"\n".format(access_token_secret))
        authFile.write("consumer_key = \"{0}\"\n".format(consumer_key))
        authFile.write("consumer_secret = \"{0}\"\n".format(consumer_secret))
        authFile.write("default_db_filename = \"{0}\"\n".format(default_db_filename))
        authFile.write("default_cl_filename = \"{0}\"\n".format("movies.cl"))


    db.reset(_join_to_data_dir(default_db_filename))

    logging.info("Training sentiment classifier")
    analysis.train_sentiment(_join_to_data_dir("movies.cl"))
