import cPickle
import nltk
from nltk.tokenize import RegexpTokenizer
from nltk.corpus import movie_reviews
from nltk.classify import NaiveBayesClassifier
import os
import logging


def word_frequency(tweets, min_length=4):
    # use a regular expression tokeniser
    tokenizer = RegexpTokenizer(r'\w+')

    # get a list of the search groups. Format the labels as {search_group}_group
    search_groups = list(set(["{0}_group".format(t["search_group"]) for t in tweets]))

    # make a dictionary with a frequency distribution object for each group
    group_fds = dict([(group, nltk.FreqDist()) for group in ["total"] + search_groups])

    for tweet in tweets:
        for word in tokenizer.tokenize(tweet["tweet_text"].lower()):
            if len(word) >= min_length:
                group_fds["total"].inc(word)
                group_fds["{0}_group".format(tweet["search_group"])].inc(word)

    # get a list of all the words, in decreasing frequency order
    words = group_fds["total"].keys()

    word_freqs = []
    # make sure the total frequency count comes first
    for group in ["total"] + [k for k in group_fds if k != "total"]:
        word_freqs.append(dict([
                ("label", group),
                ("data", [[word, group_fds[group][word]] for word in words])
            ]))

    return word_freqs


def load_sentiment(filename):
    with open(filename, "rb") as f:
        return cPickle.load(f)


def _word_features(words):
    return dict([(word, True) for word in words])


def train_sentiment(filename):
    # train a classifier based on the movie review data, based on the method found at
    # http://streamhacker.com/2010/05/10/text-classification-sentiment-analysis-naive-bayes-classifier/


    def _get_nltk_dir():
    # this file is tweepy/lib/analysis.py, so navigate to tweepy/
    # the join with nltk_data/ to get tweepy/nltk_data/
        return os.path.join(
                os.path.dirname(os.path.dirname(
                        os.path.abspath(__file__))),
                "nltk_data")

    nltk.data.path.append(_get_nltk_dir())
    try:
        posReviews = movie_reviews.fileids("pos")
        negReviews = movie_reviews.fileids("neg")
    except LookupError:
        logging.info("Downloading training data for the sentiment classifier")
        nltk.download("movie_reviews", download_dir=_get_nltk_dir())
        posReviews = movie_reviews.fileids("pos")
        negReviews = movie_reviews.fileids("neg")

    posFeatures = [(_word_features(movie_reviews.words(fileids=[f])), "pos") for f in posReviews]
    negFeatures = [(_word_features(movie_reviews.words(fileids=[f])), "neg") for f in negReviews]

    trainingFeatures = posFeatures+negFeatures

    classifier = NaiveBayesClassifier.train(trainingFeatures)

    # save the classifiers
    with open(filename, "wb") as f:
        cPickle.dump(classifier, f)

    return classifier


def classify_sentiment(classifier, text, neutral_threshold = 0.3):
    tokenizer = RegexpTokenizer(r'\w+')
    words = tokenizer.tokenize(text)

    # return neutral if the difference between P(pos) and P(neg) is neutral_threshold
    dist = classifier.prob_classify(_word_features(words))
    if abs(dist.prob("pos") - dist.prob("neg")) < neutral_threshold:
        return "neutral"
    else:
        return dist.max()


def sentiment_frequency(tweets):

    # get a list of the search groups. Format the labels as {search_group}_group
    search_groups = list(set(["{0}_group".format(t["search_group"]) for t in tweets]))

    # make a dictionary with a frequency distribution object for each group
    group_fds = dict([(group, nltk.FreqDist()) for group in ["total"] + search_groups])

    for tweet in tweets:
        group_fds["total"].inc(tweet["sentiment"])
        group_fds["{0}_group".format(tweet["search_group"])].inc(tweet["sentiment"])

    sent_freqs = []
    # make sure the total frequency count comes first
    for group in ["total"] + [k for k in group_fds if k != "total"]:
        sent_freqs.append(dict([
                ("label", group),
                ("data", [[word, group_fds[group][word]] for word in ["pos", "neg", "neutral"]])
            ]))

    return sent_freqs


