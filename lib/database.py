"""
database.py:
    File for connecting to an sqlite database to store the data
"""
import os
import cPickle
import sys


def _warning_prompt(db_filename):
    """ displays a warning to the user since the database will be deleted
    """
    print("WARNING: This will delete your the database: {0}".format(db_filename))
    return raw_input("Type 'yes' to proceed, or anything else to quit: ")


def _check_unique(l_dict, key, value):
    """ returns true if none of the dictionaries in l_dict have the given
        value for the given key
    """
    return not value in [d[key] for d in l_dict if key in d]

def reset(db_filename, warning_input=_warning_prompt):
    """ creates a new database with the given file name.
        any existing database will be overwritten

        warning_input is a function which takes a database name and returns
        "yes" if the user wants to delete the database
    """
    if warning_input(db_filename) != "yes":
        print("quitting")
        sys.exit()

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
    """ save the database back to disc
    """
    with open(db_dict["filename"], "wb") as f:
        cPickle.dump(db_dict, f)


def insert_tweet(db_dict, tweet, tweet_group, sentiment="", id_key=None):
    """ Inserts the tweet data (as a json object) into the database, adding "tweet_group"
        and "sentiment" key/value pairs. Returns True if the insertion was successful

        id_key is used to enforce uniqueness. If it is given, all tweets in the
        database are checked on that key (e.g. "id_str"), and the tweet will only
        be inserted if it matches
    """
    # add the tweet group and sentiment
    tweet["tweet_group"] = tweet_group
    tweet["sentiment"] = sentiment

    if id_key is None or _check_unique(db_dict["tweets"], id_key, tweet[id_key]):
        db_dict["tweets"].append(tweet)
        return True
    else:
        return False


def insert_user(db_dict, user, user_group, id_key=None):
    """ inserts the user data (as a json object) into the database, adding "user_group"
        key/value pair. Returns True if the insertion was successful

        id_key is used to enforce uniqueness. If it is given, all tweets in the
        database are checked on that key (e.g. "id_str"), and the tweet will only
        be inserted if it matches
    """
    # add the user group
    user["user_group"] = user_group
    db_dict["users"].append(user)

    if id_key is None or _check_unique(db_dict["users"], id_key, user[id_key]):
        db_dict["users"].append(user)
        return True
    else:
        return False


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


