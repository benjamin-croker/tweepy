"""
database.py:
    File for connecting to an sqlite database to store the data
"""
import os
import cPickle
import sys
import logging


def _warning_prompt(db_filename):
    """ displays a warning to the user since the database will be deleted
    """
    print("WARNING: This will delete your the database: {0}".format(db_filename))
    return raw_input("Type 'yes' to proceed, or anything else to quit: ")


def reset(db_filename, warning_input=_warning_prompt):
    """ creates a new sqlite database with the given file name.
        any existing database will be overwritten

        warning_input is a function which takes a database name and returns
        "yes" if the user wants to delete the database
    """
    if warning_input(db_filename) != "yes":
        print("quitting")
        sys.exit()

    logging.info("Setting up the database")
    # remove the file if it exists
    try:
        os.remove(db_filename)
    except OSError:
        pass

    # create empty lists for tweets and users so append operations can be performed
    db_dict = dict(filename=db_filename)
    db_dict["tweets"] = []
    db_dict["users"] = []
    db_dict["graphs"] = []
    close_db_connection(db_dict)


def open_db_connection(db_filename):
    """ remember to close this at the end
    """
    with open(db_filename, "rb") as f:
        return cPickle.load(f)


def close_db_connection(db_dict):
    """ will commit changes as well
    """
    with open(db_dict["filename"], "wb") as f:
        cPickle.dump(db_dict, f)


def insert_tweet(db_dict, tweet, tweet_group, sentiment=""):
    """ Inserts the tweet data (as a json object) into the database, adding "tweet_group"
        and "sentiment" key/value pairs. Returns True if the insertion was successful
    """
    # add the tweet group and sentiment
    tweet["tweet_group"] = tweet_group
    tweet["sentiment"] = sentiment
    db_dict["tweets"].append(tweet)

    # this will always return True. The interface was designed so that failure conditions
    # (which would return false) could be added in later
    return True


def insert_user(db_dict, user, user_group):
    """ inserts the user data (as a json object) into the database, adding "user_group"
        key/value pair. Returns True if the insertion was successful
    """
    # add the user group
    user["user_group"] = user_group
    db_dict["users"].append(user)

    # this will always return True. The interface was designed so that failure conditions
    # (which would return false) could be added in later
    return True


def update_sentiments(db_dict, sent_func, update_all=True):
    """ updates all the sentiments in the database. The calculation is performed
        by the sentFunc, which takes the tweet string and returns a sentiment tag

        if update_all is True, then all sentiments are calculated,
        otherwise only tweets with blank sentiment strings are calculated
    """
    # the shelve dictionary lists are immutable
    tweets = db_dict["tweets"]
    for tweet in tweets:
        if update_all or len(tweet["text"]) == 0:
            tweet["sentiment"] = sent_func(tweet["text"])
    db_dict["tweets"] = tweets


def get_tweets(db_dict):
    """ returns a dict of all the tweets
    """
    return db_dict["tweets"]


def get_users(db_dict):
    """ returns a dict of all the users
    """
    return db_dict["users"]


def get_tweet_groups(db_dict):
    """ returns a list of all the tweet groups
    """
    return list(set([tweet["tweet_group"] for tweet in db_dict["tweets"]]))


