import unittest
from lib import database as db


class TestDatabaseInit(unittest.TestCase):
    def test_reset(self):
        """ check that the database has the correct keys after initialisation
        """
        db.reset("test.db", lambda x: "yes")
        db_dict = db.open_db_connection("test.db")

        # test the db has the right keys. The set of keys should be equal to the one below
        keys = {"tweets", "users", "graphs"}
        self.assertTrue(keys.issubset(set(db_dict.keys())))
        self.assertTrue(keys.issuperset(set(db_dict.keys())))

        db.close_db_connection(db_dict)


class TestDatabaseInsert(unittest.TestCase):

    def test_tweet_groups(self):
        db.reset("test.db", lambda x: "yes")
        db_dict = db.open_db_connection("test.db")

        # there should be no search groups
        self.assertEqual(len(db.get_tweet_groups(db_dict)), 0)

        self.assertTrue(
            db.insert_tweet(db_dict, {"id_str": "tweet_id_101",
                                      "user": {"id_str": "usr_id_111"},
                                      "text": "I'm a tweet!",
                                      "created_at": "Mon Sep 24 03:35:21 +0000 2012"},
                            "tweet_group_1")
        )

        self.assertTrue(
            db.insert_tweet(db_dict, {"id_str": "tweet_id_101",
                                      "user": {"id_str": "usr_id_111"},
                                      "text": "I'm a tweet!",
                                      "created_at": "Mon Sep 24 03:35:21 +0000 2012"},
                            "tweet_group_2")
        )

        # now there should be 2
        tweet_groups = db.get_tweet_groups(db_dict)

        self.assertEqual(len(tweet_groups), 2)
        self.assertTrue("tweet_group_1" in tweet_groups)
        self.assertTrue("tweet_group_2" in tweet_groups)

    def test_tweet_insert(self):
        """ check we can create a db and insert then read back a tweet
        """
        db.reset("test.db", lambda x: "yes")

        # check there are no tweets
        db_dict = db.open_db_connection("test.db")
        tweets = db.get_tweets(db_dict)
        self.assertEqual(len(tweets), 0)

        # test with no sentiment
        self.assertTrue(
            db.insert_tweet(db_dict, {"id_str": "tweet_id_101",
                                      "user": {"id_str": "usr_id_111"},
                                      "text": "I'm a tweet!",
                                      "created_at": "Mon Sep 24 03:35:21 +0000 2012"},
                            "tweet_group_1")
        )

        # check we can the tweet back before and after closing the connection
        def _check_tweet(tweets):
            self.assertEqual(tweets[0]["id_str"], "tweet_id_101")
            self.assertEqual(tweets[0]["user"]["id_str"], "usr_id_111")
            self.assertEqual(tweets[0]["text"], "I'm a tweet!")
            self.assertEqual(tweets[0]["created_at"], "Mon Sep 24 03:35:21 +0000 2012")
            self.assertEqual(tweets[0]["tweet_group"], "tweet_group_1")
            self.assertEqual(tweets[0]["sentiment"], "")

        # close and open to check persistence
        tweets = db.get_tweets(db_dict)
        _check_tweet(tweets)
        db.close_db_connection(db_dict)

        db_dict = db.open_db_connection("test.db")
        tweets = db.get_tweets(db_dict)
        _check_tweet(tweets)

        # add another tweet
        self.assertTrue(
            db.insert_tweet(db_dict, {"id_str": "tweet_id_101",
                                      "user": {"id_str": "usr_id_111"},
                                      "text": "I'm a tweet!",
                                      "created_at": "Mon Sep 24 03:35:21 +0000 2012"},
                            "tweet_group_2")
        )

        # test with sentiment
        self.assertTrue(
            db.insert_tweet(db_dict, {"id_str": "tweet_id_101",
                                      "user": {"id_str": "usr_id_111"},
                                      "text": "I'm a tweet!",
                                      "created_at": "Mon Sep 24 03:35:21 +0000 2012"},
                            "tweet_group_3", "neg")
        )
        tweets = db.get_tweets(db_dict)
        self.assertEqual(tweets[2]["sentiment"], "neg")

        db.close_db_connection(db_dict)



if __name__ == "__main__":
    unittest.main()