import oauth2 as oauth
import urllib2 as urllib
import json
import logging
import signal
import csv
import os
import time

import database as db
from data import user_settings
from data import twitter_settings

oauth_token = oauth.Token(key=user_settings.access_token_key, secret=user_settings.access_token_secret)
oauth_consumer = oauth.Consumer(key=user_settings.consumer_key, secret=user_settings.consumer_secret)


# set up a handler to catch ctrl-c events
def ctrl_c_handler(signum, frame):
    print("Exiting")
    exit(0)


signal.signal(signal.SIGINT, ctrl_c_handler)


def twitterreq(url, http_method="GET", parameters=()):
    """ Constructs, signs and opens a twitter request

        returns the data as a json encoded variable
    """
    # convert the parameters to a list. The default argument is a tuple,
    # since it is good practice to have non-mutable default arguments
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
    try:
        json_response = json.load(response)
    except ValueError:
        logging.error("Received invalid twitter API response: {0}".format(response))
        raise
    return json_response


def search_tweets(term, tweet_group, db_con, no_RT=False,
                  search_count=twitter_settings.max_search_tweets_count):
    """ searches for tweets containing the given term and stores them in the database

        returns the list of tweet objects
    """
    query_params = "?q={0}&count={1}".format(urllib.quote(term), search_count)
    if no_RT:
        query_params += urllib.quote(" exclude:retweets")

    logging.info("Searching tweets about {0}".format(term))

    # encode the query for use in a url
    query_url = "https://api.twitter.com/1.1/search/tweets.json{0}".format(query_params)

    logging.debug("Twitter API call: {0}".format(query_url))
    json_data = twitterreq(query_url, "GET")
    logging.info("Searching for {0} completed".format(term))

    if not "statuses" in json_data:
        logging.error("Error {0}".format(json_data))

    # save the results
    tweets = json_data["statuses"]
    for tweet in tweets:
        db.insert_tweet(db_con, tweet, tweet_group)

    logging.info("Results written to database")
    return tweets


def search_users(term, user_group, db_con,
                 search_count=twitter_settings.max_search_tweets_count):
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

    logging.debug("Twitter API call: {0}".format(query_url))
    json_data = twitterreq(query_url, "GET")
    logging.info("Searching for {0} completed".format(term))

    if not "statuses" in json_data:
        logging.error("Error {0}".format(json_data))

    # save the results
    tweets = json_data["statuses"]
    # extract the user object from the tweet object
    users = [tweet["user"] for tweet in tweets]

    for user in users:
        db.insert_user(db_con, user, user_group)

    logging.info("Results written to database")
    return users


def search_top_users(term, user_group, db_con,
                     search_count=twitter_settings.max_users_search_count):
    """ Searches for the top users matching a specific term, and stores
        them in the database. Use search_users for users currently tweeting
        about a specific topic

        returns a list of user objects
    """
    query_params = "?q={0}&count={1}".format(urllib.quote(term), search_count)

    logging.info("Searching for top users for {0}".format(term))

    # encode the query for use in a url
    query_url = "https://api.twitter.com/1.1/users/search.json{0}".format(query_params)

    logging.debug("Twitter API call: {0}".format(query_url))
    json_data = twitterreq(query_url, "GET")
    logging.info("Searching for {0} completed".format(term))

    # save the results
    users = json_data

    for user in users:
        db.insert_user(db_con, user, user_group)
        if "screen_name" in user and user["screen_name"]:
            print("{0}:{1}".format(user["screen_name"], user_group))

    logging.info("Results written to database")
    return users


def search_user_tweets(screen_name, user_group, db_con,
                       search_count=twitter_settings.max_user_timeline_count):
    """ Searches for the top users matching a specific term, and stores
        them in the database. Use search_users for users currently tweeting
        about a specific topic

        returns a list of user objects
    """
    query_params = "?screen_name={0}&count={1}".format(screen_name, search_count)

    logging.info("Searching for tweets by {0}".format(screen_name))

    # encode the query for use in a url
    query_url = "https://api.twitter.com/1.1/statuses/user_timeline.json{0}".format(query_params)

    logging.debug("Twitter API call: {0}".format(query_url))
    json_data = twitterreq(query_url, "GET")

    # save the results
    tweets = json_data

    for tweet in tweets:
        db.insert_tweet(db_con, tweet, user_group)

    logging.info("Results written to database")
    return tweets


def search_multiple_terms(filename, db_con, no_RT=False,
                          rate_limit=twitter_settings.multiple_search_limit):
    """ opens a file, which contains one search term per line,
        and runs a search for each term

        rate limit sets the number of terms what will be searched before waiting
        15 mins for the next window
    """
    with open(filename) as f:
        # number of terms we've searched for
        n_requests = 0
        for line in f.readlines():
            # split the line into a query and group
            # check the line to see if it's formatted correctly
            if len(line.split(":")) != 2:
                raise Exception("Error in search term \n {0} \n Line must be formatted as <term>:<group>")
            [term, group] = line.split(":")
            if group.endswith("\n"):
                group = group[:-1]

            search_tweets(term, group, db_con, no_RT)

            n_requests += 1
            if n_requests >= rate_limit:
                logging.info("Sleeping for 15 mins to avoid rate limiting")
                time.sleep(900)
                n_requests = 0


def search_multiple_users(filename, db_con,
                          rate_limit=twitter_settings.multiple_search_limit):
    """ opens a file, which contains one search term per line,
        and runs a search for each term

        rate limit sets the number of terms what will be searched before waiting
        15 mins for the next window
    """
    with open(filename) as f:
        # number of users we've searched for
        n_requests = 0
        for line in f.readlines():
            # split the line into a query and group
            # check the line to see if it's formatted correctly
            if len(line.split(":")) != 2:
                raise Exception("Error in search term \n {0} \n Line must be formatted as <term>:<group>")
            [term, group] = line.split(":")
            if group.endswith("\n"):
                group = group[:-1]

            search_user_tweets(term, group, db_con)
            n_requests += 1

            if n_requests >= rate_limit:
                logging.info("Sleeping for 15 mins to avoid rate limiting")
                time.sleep(900)
                n_requests = 0


def search_suggested_users(db_con, rate_limit=twitter_settings.multiple_user_sugg_limit):
    logging.info("Getting suggested users")

    # define the query url to get the suggestion categories
    query_url = "https://api.twitter.com/1.1/users/suggestions.json"
    logging.debug("Twitter API call: {0}".format(query_url))
    json_data = twitterreq(query_url, "GET")

    # get the suggestion slugs (i.e. suggested categories)
    slugs = [d["slug"] for d in json_data]

    # get the users for each slug
    n_requests = 0
    for slug in slugs:
        # define the query url to get the users
        query_url = "https://api.twitter.com/1.1/users/suggestions/{0}.json".format(slug)
        logging.debug("Twitter API call: {0}".format(query_url))
        json_data = twitterreq(query_url, "GET")

        if "users" not in json_data:
            raise Exception("JSON data has no users: {0}".format(json_data))
        users = json_data["users"]

        for user in users:
            db.insert_user(db_con, user, slug)
            if "screen_name" in user and user["screen_name"]:
                print("{0}:{1}".format(user["screen_name"], slug))

        n_requests += 1
        if n_requests >= rate_limit:
                logging.info("Sleeping for 15 mins to avoid rate limiting")
                time.sleep(900)
                n_requests = 0

    logging.info("Results written to database")
    return slugs


def search_trends(WOEID, trend_group):
    """ finds all the hashtags for the given WOEID then runs a search on
        each of them
    """

    logging.info("Getting trends for WOEID {0}".format(WOEID))

    # encode the query for use in a url
    query_url = "https://api.twitter.com/1.1/trends/place.json?id={0}".format(WOEID)

    logging.debug("Twitter API call: {0}".format(query_url))
    json_data = twitterreq(query_url, "GET")

    # For each trend, output a line in the format <search_query>:<WOEID>_<trend name>
    # the data returned is in a single-element list for some reason
    for trend in json_data[0]["trends"]:
        if "name" in trend and trend["name"]:
            print("{0}:{1}".format(trend["name"], trend_group))


def dump_tweets(db_con, group=None, filename=None, report_format="csv"):
    """ writes the tweets to the reports folder.
        format must be one of csv or json
    """
    header = ["id_str", "text", "created_at", "tweet_group", "sentiment"]
    tweets = db.get_tweets(db_con)

    # set a default filename in the reports directory if none is provided
    if filename is None:
        filename = os.path.join("reports", "tweets.{0}".format(report_format))

    # filter the tweets for a specific group if it is given
    if group is not None:
        tweets = [tweet for tweet in tweets if tweet["tweet_group"] == group]

    with open(filename, "wb") as f:
        if report_format == "json":
            f.write(json.dumps(tweets))

        elif report_format == "csv":
            writer = csv.writer(f, delimiter=",")

            writer.writerow(["screen_name"] + header)
            for tweet in tweets:
                writer.writerow([tweet["user"]["screen_name"]] + [tweet[k].encode("utf-8") for k in header])
        else:
            raise Exception("Format must be csv or json")


def dump_users(db_con, group=None, filename=None, report_format="csv"):
    """ writes the tweets to the reports folder.
        format must be one of csv or json
    """
    header = ["id_str", "screen_name", "user_group"]
    users = db.get_users(db_con)

    # set a default filename in the reports directory if none is provided
    if filename is None:
        filename = os.path.join("reports", "tweets.{0}".format(report_format))

    # filter the tweets for a specific group if it is given
    if group is not None:
        users = [user for user in users if user["user_group"] == group]

    with open(filename, "wb") as f:
        if report_format == "json":
            f.write(json.dumps(users))

        elif report_format == "csv":
            writer = csv.writer(f, delimiter=",")

            writer.writerow(header)
            for user in users:
                writer.writerow([user[k].encode("utf-8") for k in header])
        else:
            raise Exception("Format must be csv or json")
