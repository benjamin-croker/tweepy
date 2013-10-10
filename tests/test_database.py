import unittest
import json
from lib import database as db


class TestDatabaseInit(unittest.TestCase):
    def test_reset(self):
        """ check that the database has the correct tables after initialisation
        """
        TWEET_COLUMNS = {"tweet":
                             [(u"id_str", u"TEXT"),
                              (u"user_id", u"TEXT"),
                              (u"tweet_text", u"TEXT"),
                              (u"created_at", u"TEXT"),
                              (u"search_group", u"TEXT"),
                              (u"sentiment", u"TEXT")],
                         "graph":
                             [(u"central_user", u"TEXT"),
                              (u"user_id", u"TEXT"),
                              (u"user_follows_id", u"TEXT")]
        }

        db.reset("test.db", lambda x: "yes")
        con = db.open_db_connection("test.db")

        # test the two tables
        for name in TWEET_COLUMNS.keys():
            cursor = con.execute("PRAGMA table_info({});".format(name))
            table_info = cursor.fetchall()

            # strip extra info off the returned sql
            table_info = [(entry[1], entry[2]) for entry in table_info]
            for info in zip(TWEET_COLUMNS[name], table_info):
                self.assertEquals(info[0], info[1])


class TestDatabaseInsert(unittest.TestCase):

    def test_search_groups(self):
        db.reset("test.db", lambda x: "yes")
        con = db.open_db_connection("test.db")

        # there should be no search groups
        self.assertEqual(len(db.search_groups(con)), 0)

        self.assertTrue(
            db.insert_tweet(con, "tweet_id_101", "usr_id_111", "I'm a tweet!",
                            "2013-10-09 20:44:21", "tweet_group")
        )

        self.assertTrue(
            db.insert_tweet(con, "tweet_id_102", "usr_id_112", "Another tweet!",
                            "2013-10-09 20:44:21", "tweet_group_2", "neg")
        )

        # now there should be 2
        search_groups = db.search_groups(con)

        self.assertEqual(len(search_groups), 2)
        self.assertTrue("tweet_group" in search_groups)
        self.assertTrue("tweet_group_2" in search_groups)

    def test_tweet_insert(self):
        """ check we can create a db and insert then read back a tweet
        """
        db.reset("test.db", lambda x: "yes")

        # check there are no tweets
        con = db.open_db_connection("test.db")
        tweets, header = db.get_tweets(con)
        self.assertEqual(len(tweets), 0)

        # test with no sentiment
        self.assertTrue(
            db.insert_tweet(con, "tweet_id_101", "usr_id_111", "I'm a tweet!",
                            "2013-10-09 20:44:21", "tweet_group")
        )
        # check we can't insert two tweets with same id and search group
        self.assertFalse(
            db.insert_tweet(con, "tweet_id_101", "usr_id_111", "I'm a tweet!",
                            "2013-10-09 20:44:21", "tweet_group")
        )

        # check we can the tweet back before and after closing the connection
        def _check_tweet(tweets):
            self.assertEqual(tweets[0]["id_str"], u"tweet_id_101")
            self.assertEqual(tweets[0]["user_id"], u"usr_id_111")
            self.assertEqual(tweets[0]["tweet_text"], u"I'm a tweet!")
            self.assertEqual(tweets[0]["created_at"], u"2013-10-09 20:44:21")
            self.assertEqual(tweets[0]["search_group"], u"tweet_group")
            self.assertEqual(tweets[0]["sentiment"], u"")
        tweets, header = db.get_tweets(con)
        _check_tweet(tweets)
        db.close_db_connection(con)

        con = db.open_db_connection("test.db")
        tweets, header = db.get_tweets(con)
        _check_tweet(tweets)

        # but we can change the search group
        self.assertTrue(
            db.insert_tweet(con, "tweet_id_101", "usr_id_111", "I'm a tweet!",
                            "2013-10-09 20:44:21", "tweet_group_2")
        )
        # test with sentiment
        self.assertTrue(
            db.insert_tweet(con, "tweet_id_102", "usr_id_112", "Another tweet!",
                            "2013-10-09 20:44:21", "tweet_group", "neg")
        )
        db.close_db_connection(con)

        con = db.open_db_connection("test.db")



if __name__ == "__main__":
    unittest.main()