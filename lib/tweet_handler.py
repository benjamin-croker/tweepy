import oauth2 as oauth
import urllib2 as urllib
import json
import logging
import signal
import csv
import os

import database as db
import analysis
from data import auth

oauth_token = oauth.Token(key=auth.access_token_key, secret=auth.access_token_secret)
oauth_consumer = oauth.Consumer(key=auth.consumer_key, secret=auth.consumer_secret)


# set up a handler to catch ctrl-c events
def ctrl_c_handler(signum, frame):
    print("Exiting")
    exit(0)


signal.signal(signal.SIGINT, ctrl_c_handler)


def twitterreq(url, http_method="GET", parameters=[]):
    """ Construct, sign, and open a twitter request
        using the hard-coded credentials above.
    """
    req = oauth.Request.from_consumer_and_token(oauth_consumer,
                                                token=oauth_token,
                                                http_method=http_method,
                                                http_url=url,
                                                parameters=parameters)

    req.sign_request(oauth.SignatureMethod_HMAC_SHA1(), oauth_consumer, oauth_token)

    if http_method == "POST":
        encoded_post_data = req.to_postdata()
    else:
        encoded_post_data = None
        url = req.to_url()

    opener = urllib.OpenerDirector()
    opener.add_handler(urllib.HTTPHandler())
    opener.add_handler(urllib.HTTPSHandler())
    response = opener.open(url, encoded_post_data)

    return response


def search_tweets(term, tweet_group, db_dict, no_RT=False, search_count=50):
    """ searches for tweets containing the given term and stores them in the database

        returns the list of tweet objects
    """
    query_params = "?q={0}&count={1}".format(urllib.quote(term), search_count)
    if no_RT:
        query_params += urllib.quote(" exclude:retweets")

    logging.info("Searching tweets about {0}".format(term))

    # encode the query for use in a url
    query_url = "https://api.twitter.com/1.1/search/tweets.json{0}".format(query_params)

    logging.info("Twitter API call: {0}".format(query_url))
    json_data = json.load(twitterreq(query_url, "GET"))
    logging.info("Searching for {0} completed".format(term))

    if not "statuses" in json_data:
        logging.error("Error {0}".format(json_data))

    # save the results
    tweets = json_data["statuses"]
    for tweet in tweets:
        db.insert_tweet(db_dict, tweet, tweet_group)

    logging.info("Results written to database")
    return tweets


def search_users(term, user_group, db_dict, search_count=50):
    """ searches for users who have recently posted tweets with containing the term and
        stores them in the database

        returns the list of user objects
    """
    query_params = "?q={0}&count={1}".format(urllib.quote(term), search_count)
    # don't include retweets when searching for users
    query_params += urllib.quote(" exclude:retweets")

    logging.info("Searching for users who tweeted about {0}".format(term))

    # encode the query for use in a url
    query_url = "https://api.twitter.com/1.1/search/tweets.json{0}".format(query_params)

    logging.info("Twitter API call: {0}".format(query_url))
    json_data = json.load(twitterreq(query_url, "GET"))
    logging.info("Searching for {0} completed".format(term))

    if not "statuses" in json_data:
        logging.error("Error {0}".format(json_data))

    # save the results
    tweets = json_data["statuses"]
    # extract the user object from the tweet object
    users = [tweet["user"] for tweet in tweets]

    for user in users:
        db.insert_user(db_dict, user, user_group)

    logging.info("Results written to database")
    return users


def search_top_users(term, user_group, db_dict, search_count=20):
    """ Searches for the top users matching a specific term, and stores
        them in the database. Use search_users for users currently tweeting
        about a specific topic

        returns a list of user objects
    """
    query_params = "?q={0}&count={1}".format(urllib.quote(term), search_count)

    logging.info("Searching for top users for {0}".format(term))

    # encode the query for use in a url
    query_url = "https://api.twitter.com/1.1/users/search.json{0}".format(query_params)

    logging.info("Twitter API call: {0}".format(query_url))
    json_data = json.load(twitterreq(query_url, "GET"))
    logging.info("Searching for {0} completed".format(term))

    # save the results
    users = json_data

    for user in users:
        db.insert_user(db_dict, user, user_group)
        if "screen_name" in user and user["screen_name"]:
            print("{0}:{1}".format(user["screen_name"], user_group))

    logging.info("Results written to database")
    return users


def search_user_tweets(screen_name, user_group, db_dict, search_count=200):
    """ Searches for the top users matching a specific term, and stores
        them in the database. Use search_users for users currently tweeting
        about a specific topic

        returns a list of user objects
    """
    query_params = "?screen_name={0}&count={1}".format(screen_name, search_count)

    logging.info("Searching for tweets by {0}".format(screen_name))

    # encode the query for use in a url
    query_url = "https://api.twitter.com/1.1/statuses/user_timeline.json{0}".format(query_params)

    logging.info("Twitter API call: {0}".format(query_url))
    json_data = json.load(twitterreq(query_url, "GET"))
    logging.info("Searching for {0} completed".format(screen_name))

    # save the results
    tweets = json_data

    for tweet in tweets:
        db.insert_tweet(db_dict, tweet, user_group)

    logging.info("Results written to database")
    return tweets


def search_multiple_terms(filename, db_dict, no_RT=False):
    """ opens a file, which contains one search term per line,
        and runs a search for each term
    """
    with open(filename) as f:
        for line in f.readlines():
            # split the line into a query and group
            # check the line to see if it's formatted correctly
            if len(line.split(":")) != 2:
                raise Exception("Error in search term \n {0} \n Line must be formatted as <term>:<group>")
            [term, group] = line.split(":")
            if group.endswith("\n"):
                group = group[:-1]

            search_tweets(term, group, db_dict, no_RT)


def search_multiple_users(filename, db_dict):
    """ opens a file, which contains one search term per line,
        and runs a search for each term
    """
    with open(filename) as f:
        for line in f.readlines():
            # split the line into a query and group
            # check the line to see if it's formatted correctly
            if len(line.split(":")) != 2:
                raise Exception("Error in search term \n {0} \n Line must be formatted as <term>:<group>")
            [term, group] = line.split(":")
            if group.endswith("\n"):
                group = group[:-1]

            search_user_tweets(term, group, db_dict)


def search_trends(WOEID):
    """ finds all the hashtags for the given WOEID then runs a search on
        each of them
    """
    logging.info("Getting trends for WOEID {0}".format(WOEID))

    # encode the query for use in a url
    query_url = "https://api.twitter.com/1.1/trends/place.json?id={0}".format(WOEID)

    json_data = json.load(twitterreq(query_url, "GET"))

    # For each trend, output a line in the format <search_query>:<WOEID>_<trend name>
    # the data returned is in a single-element list for some reason
    for trend in json_data[0]["trends"]:
        if "name" in trend and trend["name"]:
            print("{0}:{1}".format(trend["name"], WOEID))


def dump_tweets(db_dict, report_format="csv"):
    """ writes the tweets to the reports folder.
        format must be one of csv or json
    """
    header = ["id_str", "text", "created_at", "tweet_group", "sentiment"]
    tweets = db.get_tweets(db_dict)
    if report_format == "json":
        with open(os.path.join("reports", "tweets.json"), "wb") as f:
            f.write(json.dumps(tweets))

    elif report_format == "csv":
        with open(os.path.join("reports", "tweets.csv"), "wb") as f:
            writer = csv.writer(f, delimiter=",")

            writer.writerow(header)
            for tweet in tweets:
                writer.writerow([tweet[k].encode("utf-8") for k in header])
    else:
        raise Exception("Format must be csv or json")


def dump_users(db_dict, report_format="csv"):
    """ writes the tweets to the reports folder.
        format must be one of csv or json
    """
    header = ["id_str", "screen_name", "user_group"]
    users = db.get_users(db_dict)
    if report_format == "json":
        with open(os.path.join("reports", "users.json"), "wb") as f:
            f.write(json.dumps(users))

    elif report_format == "csv":
        with open(os.path.join("reports", "users.csv"), "wb") as f:
            writer = csv.writer(f, delimiter=",")

            writer.writerow(header)
            for user in users:
                writer.writerow([user[k].encode("utf-8") for k in header])
    else:
        raise Exception("Format must be csv or json")


def dump_word_frequencies(db_dict, report_format="csv"):
    """ writes the word frequencies to the "reports" folder.
        Format must be one of csv or json
    """
    tweets = db.get_tweets(db_dict)
    word_freqs = analysis.word_frequency(tweets)

    if report_format == "json":
        with open(os.path.join("reports", "word_freq.json"), "wb") as f:
            f.write(json.dumps(word_freqs))

    elif report_format == "csv":
        with open(os.path.join("reports", "word_freq.csv"), "wb") as f:
            writer = csv.writer(f, delimiter=",")

            writer.writerow(["word"] + ["{0}_frequency".format(f["label"])
                                        for f in word_freqs])

            for i in range(len(word_freqs[0]["data"])):
                row = [word_freqs[0]["data"][i][0]]
                row += [group["data"][i][1] for group in word_freqs]

                if type(row[0]) == unicode:
                    row[0] = row[0].encode("utf-8")
                writer.writerow(row)
    else:
        raise Exception("Format must be csv or json")


def dump_sentiment_frequencies(con, report_format="csv"):
    """ writes the sentiment frequencies to the "reports" folder.
        Format must be one of csv or json
    """
    tweets = db.get_tweets(con)
    sent_freqs = analysis.sentiment_frequency(tweets)

    if report_format == "json":
        with open(os.path.join("reports", "sent_freq.json"), "wb") as f:
            f.write(json.dumps(sent_freqs))

    elif report_format == "csv":
        with open(os.path.join("reports", "sent_freq.csv"), "wb") as f:
            writer = csv.writer(f, delimiter=",")

            writer.writerow(["sentiment"] + ["{0}_frequency".format(f["label"])
                                             for f in sent_freqs])

            for i in range(len(sent_freqs[0]["data"])):
                row = [sent_freqs[0]["data"][i][0]]
                row += [group["data"][i][1] for group in sent_freqs]

                if type(row[0]) == unicode:
                    row[0] = row[0].encode("utf-8")
                writer.writerow(row)
    else:
        raise Exception("Format must be csv or json")

