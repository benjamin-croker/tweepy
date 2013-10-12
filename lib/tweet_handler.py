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


def search_term(query, tweet_group, db_dict, no_RT=False, search_count=50):
    """ searches for a single term and stores the results in the database

        returns the list of tweets
    """
    if no_RT:
        query += urllib.quote(" exclude:retweets")
    query += "&count={0}".format(search_count)

    logging.info("Searching for {0}".format(query))
    # encode the query for use in a url
    url = "https://api.twitter.com/1.1/search/tweets.json?q={0}".format(query)
    print url
    json_data = json.load(twitterreq(url, "GET"))
    logging.info("Searching for {0} completed".format(query))

    if not "statuses" in json_data:
        logging.error("Error {0}".format(json_data))

    # save the results
    tweets = json_data["statuses"]
    for tweet in tweets:
        db.insert_tweet(db_dict, tweet, tweet_group)

    logging.info("Results written")
    return tweets


def search_all_terms(filename, db_dict, no_RT=False):
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

            query = urllib.quote(term)
            search_term(query, group, db_dict, no_RT)


def search_all_trends(WOEID, db_dict, no_RT=False):
    """ finds all the hashtags for the given WOEID then runs a search on
        each of them
    """
    logging.info("Getting trends for WOEID {0}".format(WOEID))
    # encode the query for use in a url
    url = "https://api.twitter.com/1.1/trends/place.json?id={0}".format(WOEID)
    # the data returned is in a single-element list for some reason
    json_data = json.load(twitterreq(url, "GET"))

    # the data returned is in a single-element list for some reason
    for trend in json_data[0]["trends"]:
        if "query" in trend and trend["query"]:
            search_term(trend["query"], "{0}_{1}".format(WOEID, trend["name"]), db_dict, no_RT)


def dump_tweets(con, format="csv"):
    """ writes the tweets to the reports folder.
        format must be one of csv or json
    """
    tweets, header = db.get_tweets(con)
    if format == "json":
        with open(os.path.join("reports", "tweets.json"), "wb") as f:
            f.write(json.dumps(tweets))

    elif format == "csv":
        with open(os.path.join("reports", "tweets.csv"), "wb") as f:
            writer = csv.writer(f, delimiter=",")

            writer.writerow(header)
            for tweet in tweets:
                writer.writerow([tweet[k].encode("utf-8") for k in header])
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

                if type(row[0])==unicode:
                    row[0] = row[0].encode("utf-8")
                writer.writerow(row)
    else:
        raise Exception("Format must be csv or json")


def dump_sentiment_frequencies(con, format="csv"):
    """ writes the sentiment frequencies to the "reports" folder.
        Format must be one of csv or json
    """
    tweets, _ = db.get_tweets(con)
    sent_freqs = analysis.sentiment_frequency(tweets)

    if format == "json":
        with open(os.path.join("reports", "sent_freq.json"), "wb") as f:
            f.write(json.dumps(sent_freqs))

    elif format == "csv":
        with open(os.path.join("reports", "sent_freq.csv"), "wb") as f:
            writer = csv.writer(f, delimiter=",")

            writer.writerow(["sentiment"] + ["{0}_frequency".format(f["label"])
                    for f in sent_freqs])

            for i in range(len(sent_freqs[0]["data"])):
                row = [sent_freqs[0]["data"][i][0]]
                row += [group["data"][i][1] for group in sent_freqs]

                if type(row[0])==unicode:
                    row[0] = row[0].encode("utf-8")
                writer.writerow(row)
    else:
        raise Exception("Format must be csv or json")

