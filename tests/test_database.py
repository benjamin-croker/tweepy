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
        self.db_dict = db.open_db_connection("test.db")

        self.example_tweets = [{"id_str": "tweet_id_101",
                                      "user": {"id_str": "usr_id_111"},
                                      "text": "I'm a tweet!",
                                      "created_at": "Mon Sep 24 03:35:21 +0000 2012"},
                               {"id_str": "tweet_id_101",
                                      "user": {"id_str": "usr_id_111"},
                                      "text": "I'm a tweet!",
                                      "created_at": "Mon Sep 24 03:35:21 +0000 2012"},
                               {"id_str": "tweet_id_101",
                                      "user": {"id_str": "usr_id_111"},
                                      "text": "I'm a tweet!",
                                      "created_at": "Mon Sep 24 03:35:21 +0000 2012"}]

    def test_no_tweets(self):
        """ tests that there are no tweets immediately after initialisation
        """
        self.setup()
        tweets = db.get_tweets(self.db_dict)
        self.assertEqual(len(tweets), 0)

    def test_tweet_insert(self):
        """ tests that multiple tweets can be written and read back
        """
        self.setup()

        # test with no sentiment
        self.assertTrue(db.insert_tweet(self.db_dict, self.example_tweets[0], "group_1"))

        # read back the tweet, and check it is the same as what was inserted
        # the sentiment and tweet group need to be added
        check_tweet = dict(self.example_tweets[0].items() + {"tweet_group": "group_1", "sentiment": ""}.items())
        tweets = db.get_tweets(self.db_dict)
        self.assertEqual(check_tweet, tweets[0])

    def test_persistence(self):
        """ check that a tweet exists after the database is closed then opened
        """
        self.setup()
        self.test_tweet_insert()

        # close then open
        db.close_db_connection(self.db_dict)
        self.db_dict = db.open_db_connection("test.db")

        check_tweet = dict(self.example_tweets[0].items() + {"tweet_group": "group_1", "sentiment": ""}.items())
        tweets = db.get_tweets(self.db_dict)
        self.assertEqual(check_tweet, tweets[0])

    def test_multiple_insert(self):
        """ test that multiple tweets can be added, including ones with sentiment
        """
        self.setup()

        self.assertTrue(db.insert_tweet(self.db_dict, self.example_tweets[0], "group_1"))
        self.assertTrue(db.insert_tweet(self.db_dict, self.example_tweets[0], "group_2"))
        self.assertTrue(db.insert_tweet(self.db_dict, self.example_tweets[0], "group_2", "neg"))

        tweets = db.get_tweets(self.db_dict)
        self.assertEqual(tweets[2]["sentiment"], "neg")

    def test_uniqueness(self):
        """ check that integrity constraints are enforced
        """
        self.setup()

        # check without enforcing
        self.assertTrue(db.insert_tweet(self.db_dict, self.example_tweets[0], "group"))
        self.assertTrue(db.insert_tweet(self.db_dict, self.example_tweets[0], "group"))

        # enforce uniqueness
        self.assertFalse(db.insert_tweet(self.db_dict, self.example_tweets[0], "group",
                                         id_key="id_str"))


class TestTweetGroups(unittest.TestCase):

    def setup(self):
        db.reset("test.db", lambda x: "yes")
        self.db_dict = db.open_db_connection("test.db")

    def test_no_groups(self):
        self.setup()
        # there should be no search groups
        self.assertEqual(len(db.get_tweet_groups(self.db_dict)), 0)

    def test_multiple_groups(self):
        self.setup()
        self.assertTrue(
            db.insert_tweet(self.db_dict, {"id_str": "tweet_id_101",
                                      "user": {"id_str": "usr_id_111"},
                                      "text": "I'm a tweet!",
                                      "created_at": "Mon Sep 24 03:35:21 +0000 2012"},
                            "tweet_group_1")
        )

        self.assertTrue(
            db.insert_tweet(self.db_dict, {"id_str": "tweet_id_101",
                                      "user": {"id_str": "usr_id_111"},
                                      "text": "I'm a tweet!",
                                      "created_at": "Mon Sep 24 03:35:21 +0000 2012"},
                            "tweet_group_2")
        )

        # now there should be 2
        tweet_groups = db.get_tweet_groups(self.db_dict)

        self.assertEqual(len(tweet_groups), 2)
        self.assertTrue("tweet_group_1" in tweet_groups)
        self.assertTrue("tweet_group_2" in tweet_groups)


if __name__ == "__main__":
    unittest.main()