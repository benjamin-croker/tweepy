import unittest
from lib import database as db


class TestDatabaseInit(unittest.TestCase):

    def setup(self):
        db.reset("test.db", lambda x: "yes")
        self.con = db.open_db_connection("test.db")

    def test_reset(self):
        """ check that the database has the correct tables after initialisation,
            and that they are empty
        """
        self.setup()

        # test that the tables are created correctly
        tweets, tweets_header = db.get_tweets(self.con)
        users, users_header = db.get_users(self.con)

        self.assertEqual(tweets_header,
                         ["id_str", "tweet_text", "created_at", "favourite_count",
                         "retweet_count", "user_id_str", "tweet_group"])
        self.assertEqual(users_header,
                         ["id_str", "name", "screen_name", "created_at", "description",
                          "followers_count", "friends_count", "statuses_count", "user_group"])

        # test the database is empty
        self.assertEqual(len(tweets), 0)
        self.assertEqual(len(users), 0)


class TestDatabaseInsert(unittest.TestCase):

    def setup(self):
        db.reset("test.db", lambda x: "yes")
        self.con = db.open_db_connection("test.db")

        self.example_tweets = [{"id_str": u"tweet_id_101",
                                      "user": {"id_str": u"usr_id_111"},
                                      "text": u"I'm a tweet!",
                                      "created_at": u"Mon Sep 24 03:35:21 +0000 2012"},
                               {"id_str": u"tweet_id_101",
                                      "user": {"id_str": u"usr_id_111"},
                                      "text": u"I'm a tweet!",
                                      "created_at": u"Mon Sep 24 03:35:21 +0000 2012"},
                               {"id_str": u"tweet_id_101",
                                      "user": {"id_str": u"usr_id_111"},
                                      "text": u"I'm a tweet!",
                                      "created_at": u"Mon Sep 24 03:35:21 +0000 2012"}]

    def test_no_tweets(self):
        """ tests that there are no tweets immediately after initialisation
        """
        self.setup()
        tweets, _ = db.get_tweets(self.con)
        self.assertEqual(len(tweets), 0)

    def test_tweet_insert(self):
        """ tests that multiple tweets can be written and read back
        """
        self.setup()

        # test with no sentiment
        self.assertTrue(db.insert_tweet(self.con, self.example_tweets[0], "group_1"))

        # read back the tweet, and check it is the same as what was inserted
        # the sentiment and tweet group need to be added
        check_tweet = {"id_str": u"tweet_id_101", "user_id_str": u"usr_id_111",
                       "tweet_text": u"I'm a tweet!","created_at": u"Mon Sep 24 03:35:21 +0000 2012",
                       "tweet_group": u"group_1", "retweet_count": None, "favourite_count": None}
        tweets, _ = db.get_tweets(self.con)
        self.assertEqual(check_tweet, tweets[0])

    def test_persistence(self):
        """ check that a tweet exists after the database is closed then opened
        """
        self.setup()
        self.test_tweet_insert()

        # close then open
        db.close_db_connection(self.con)
        self.con = db.open_db_connection("test.db")

        check_tweet = {"id_str": u"tweet_id_101", "user_id_str": u"usr_id_111",
                       "tweet_text": u"I'm a tweet!","created_at": u"Mon Sep 24 03:35:21 +0000 2012",
                       "tweet_group": u"group_1", "retweet_count": None, "favourite_count": None}
        tweets, _ = db.get_tweets(self.con)
        self.assertEqual(check_tweet, tweets[0])

    def test_multiple_insert(self):
        """ test that multiple tweets can be added, including ones with sentiment
        """
        self.setup()

        self.assertTrue(db.insert_tweet(self.con, self.example_tweets[0], "group_1"))
        self.assertTrue(db.insert_tweet(self.con, self.example_tweets[1], "group_2"))

        tweets, _ = db.get_tweets(self.con)
        self.assertEqual(len(tweets), 2)

    def test_uniqueness(self):
        """ check that integrity constraints are enforced
        """
        self.setup()

        # this one should not be inserted, since it's a duplicate of the previous one
        self.assertTrue(db.insert_tweet(self.con, self.example_tweets[1], "group"))
        self.assertFalse(db.insert_tweet(self.con, self.example_tweets[1], "group"))


class TestTweetGroups(unittest.TestCase):

    def setup(self):
        db.reset("test.db", lambda x: "yes")
        self.con = db.open_db_connection("test.db")

    def test_no_groups(self):
        self.setup()
        # there should be no search groups
        self.assertEqual(len(db.get_tweet_groups(self.con)), 0)

    def test_multiple_groups(self):
        self.setup()
        self.assertTrue(
            db.insert_tweet(self.con, {"id_str": "tweet_id_101",
                                      "user": {"id_str": "usr_id_111"},
                                      "text": "I'm a tweet!",
                                      "created_at": "Mon Sep 24 03:35:21 +0000 2012"},
                            "tweet_group_1")
        )

        self.assertTrue(
            db.insert_tweet(self.con, {"id_str": "tweet_id_101",
                                      "user": {"id_str": "usr_id_111"},
                                      "text": "I'm a tweet!",
                                      "created_at": "Mon Sep 24 03:35:21 +0000 2012"},
                            "tweet_group_2")
        )

        # now there should be 2
        tweet_groups = db.get_tweet_groups(self.con)

        self.assertEqual(len(tweet_groups), 2)
        self.assertTrue("tweet_group_1" in tweet_groups)
        self.assertTrue("tweet_group_2" in tweet_groups)


if __name__ == "__main__":
    unittest.main()