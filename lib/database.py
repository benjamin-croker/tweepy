"""
database.py:
    File for connecting to an sqlite database to store the data
"""
import os
import sqlite3
import sys
import logging

_create_tables_sql = ["""
CREATE TABLE tweet (
    id_str TEXT,
    user_id TEXT,
    tweet_text TEXT,
    created_at TEXT,
    search_group TEXT,
    sentiment TEXT,
    PRIMARY KEY (id_str, search_group)
);
""",
"""
CREATE TABLE graph (
    central_user TEXT,
    user_id TEXT,
    user_follows_id TEXT
);
"""]

_insert_sql = """
INSERT INTO tweet VALUES (?,?,?,?,?,?);
"""

_update_sentiment_sql = """
UPDATE tweet SET SENTIMENT=? WHERE id_str=?;
"""

_get_all_tweets_sql = """
SELECT * FROM tweet;
"""

_get_all_tweet_text_sql = """
SELECT tweet_text FROM tweet_text;
"""

_get_all_groups_sql = """
SELECT search_group FROM tweet GROUP BY search_group;
"""

def get_header():
    """ returns a list of the headers in the DB table
    """
    return ["id_str", "user_id", "tweet_text", "created_at", "search_group", "sentiment"]


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


def insert_tweet(con, id_str, user_id, tweet_text, created_at, group, sentiment=""):
    """ attempts to insert the values (passed as a tuple) into the database
        via the connection con.
        True is returned if the entry was created. False is returned if the
        tweet already exists,
    """
    try:
        con.execute(_insert_sql, (id_str, user_id, tweet_text, created_at, group, sentiment))
        con.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def update_sentiments(con, sentFunc, update_all=True):
    """ updates all the sentiments in the database. The calculation is performed
        by the sentFunc, which takes the tweet string and returns a sentiment tag

        if update_all is True, then all sentiments are calculated,
        otherwise only tweets with blank sentiment strings are calculated
    """
    cursor = con.execute(_get_all_tweets_sql)

    # find the columns for tweet text, search term and id
    tweetCol = [d[0] for d in cursor.description].index("tweet_text")
    idCol = [d[0] for d in cursor.description].index("id_str")
    sentCol = [d[0] for d in cursor.description].index("sentiment")

    updates = []

    for row in cursor:
        tweet_text = row[tweetCol]
        id_str = row[idCol]

        if update_all or len(row[sentCol])==0:
            sentiment = sentFunc(tweet_text)
            updates.append((sentiment, id_str))

    con.executemany(_update_sentiment_sql, updates)
    con.commit()


def get_tweets(con):
    """ returns a dict of all the tweets
    """
    cursor = con.execute(_get_all_tweets_sql)
    tweets = cursor.fetchall()
    return [dict((cursor.description[i][0], value) for i, value in enumerate(row)) 
            for row in tweets], get_header()


def search_groups(con):
    """ returns a list of all the search_groups
    """
    cursor = con.execute(_get_all_groups_sql)
    groups = cursor.fetchall()
    return [g[0] for g in groups]

