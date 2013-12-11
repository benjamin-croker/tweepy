"""
database.py:
    File for connecting to an sqlite database to store the data
"""
import os
import cPickle
import sys
import sqlite3
import json

# can't call tweet.text text, as TEXT is a keyword
_create_tables_sql = ["""
CREATE TABLE tweets (
    id_str TEXT,
    tweet_text TEXT,
    created_at TEXT,
    favourite_count INTEGER,
    retweet_count INTEGER,
    user_id_str TEXT,
    tweet_group TEXT,
    PRIMARY KEY (id_str, tweet_group)
);
""",
                      """
CREATE TABLE users (
    id_str TEXT,
    name TEXT,
    screen_name TEXT,
    created_at TEXT,
    description TEXT,
    followers_count INTEGER,
    friends_count INTEGER,
    statuses_count INTEGER,
    user_group TEXT,
    PRIMARY KEY (id_str, user_group)
);
"""]

# 7 fields
_insert_tweet_sql = """
INSERT INTO tweets VALUES (?,?,?,?,?,?,?);
"""

# 9 fields
_insert_user_sql = """
INSERT INTO users VALUES (?,?,?,?,?,?,?,?,?);
"""

_get_all_tweets_sql = """
SELECT * FROM tweets;
"""

_get_group_tweets_sql = """
SELECT * FROM tweets
WHERE tweet_group=?;
"""

_get_all_users_sql = """
SELECT * FROM users;
"""

_get_group_users_sql = """
SELECT * FROM users
WHERE tweet_group=?;
"""

_get_all_tweet_groups_sql = """
SELECT tweet_group FROM tweets GROUP BY tweet_group;
"""

_get_all_user_groups_sql = """
SELECT user_group FROM users GROUP BY user_group;
"""


def _warning_prompt(db_filename):
    """ displays a warning to the user since the database will be deleted
    """
    print("WARNING: This will delete your the database: {0}".format(db_filename))
    return raw_input("Type 'yes' to proceed, or anything else to quit: ")


def tweets_header(con):
    """ returns a list of the headers in the tweets table
    """
    cursor = con.execute(_get_all_tweets_sql)
    return [c[0] for c in cursor.description]


def user_header(con):
    """ returns a list of the headers in the user table
    """
    cursor = con.execute(_get_all_users_sql)
    return [c[0] for c in cursor.description]


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

     # create the database tables
    con = open_db_connection(db_filename)
    for _create_table_sql in _create_tables_sql:
        con.execute(_create_table_sql)
    con.commit()
    con.close()


def open_db_connection(db_filename):
    """ remember to close this at the end
    """
    return sqlite3.connect(db_filename)


def close_db_connection(con):
    """ will commit changes as well
    """
    con.commit()
    con.close()


def insert_tweet(con, tweet, tweet_group):
    """ Inserts the tweet data (passed as a json object) into the database, adding
        "tweet_group" field. Returns True if the insertion was successful.

        If another tweet with the same id and tweet_group is given, it will not be
        inserted.
    """
    # get the fields out of the JSON object, inserting None, if the key doesn't exist
    index_names = ["id_str", "text", "created_at", "favourite_count", "retweet_count"]
    tweet_data = [tweet[i] if i in tweet else None for i in index_names]

    # add the user id (since it needs deep indexing) and tweet_group separately,
    tweet_data += [tweet["user"]["id_str"] if "user" in tweet and "id_str" in tweet["user"] else None,
                   tweet_group]
    try:
        con.execute(_insert_tweet_sql, tweet_data)
        con.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def insert_user(con, user, user_group):
    """ Inserts the tweet data (passed as a json object) into the database, adding
        "tweet_group" field. Returns True if the insertion was successful.

        If another tweet with the same id and tweet_group is given, it will not be
        inserted.
    """
    # get the fields out of the JSON object, inserting None, if the key doesn't exist
    index_names = ["id_str", "name", "screen_name", "created_at", "description",
                   "followers_count", "friends_count", "statuses_count"]
    user_data = [user[i] if i in user else None for i in index_names]

    # add the user_group separately,
    user_data += [user_group]
    try:
        con.execute(_insert_user_sql, user_data)
        con.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def get_tweets(con, group=None):
    """ returns a dict of all the tweets, filtering for the tweet_group if given
    """
    if group is None:
        cursor = con.execute(_get_all_tweets_sql)
    else:
        cursor = con.execute(_get_group_tweets_sql, group)
    tweets = cursor.fetchall()

    return [dict((cursor.description[i][0], value) for i, value in enumerate(row))
            for row in tweets], tweets_header(con)


def get_users(con, group=None):
    """ returns a dict of all the users, filtering for the tweet_group if given
    """
    if group is None:
        cursor = con.execute(_get_all_users_sql)
    else:
        cursor = con.execute(_get_group_users_sql, group)
    users = cursor.fetchall()

    return [dict((cursor.description[i][0], value) for i, value in enumerate(row))
            for row in users], user_header(con)


def get_tweet_groups(con):
    """ returns a list of all the search_groups
    """
    cursor = con.execute(_get_all_tweet_groups_sql)
    groups = cursor.fetchall()
    return [g[0] for g in groups]


def get_user_groups(con):
    """ returns a list of all the search_groups
    """
    cursor = con.execute(_get_all_user_groups_sql)
    groups = cursor.fetchall()
    return [g[0] for g in groups]
