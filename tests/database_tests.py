import unittest
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


if __name__ == "__main__":

    unittest.main()