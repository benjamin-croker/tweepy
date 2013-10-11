twerpy
============

twerpy is a Python tool for gathering tweets and performing sentiment and word frequency analysis.

You can provide a list of terms to search for or search for trending terms in a location.

Installation
------------

The Python packages required by twerpy are
```
nltk
oauth2
```
You also need to have a twitter account and [register an app](https://dev.twitter.com/apps/new) to get an Twitter API key.
This is used for authenticating API requests, and is stored in plaintext on your machine, so only use twerpy on
secure machines.

To install twerpy run
```
git clone https://github.com/benjamin-croker/twerpy.git
```

To set up for the first time run
```
python twerpy.py setup
```
which will initialise a default database and auth.py file in the data directory.

Usage
------
### Database setup

All the commands below can use a specific database file with the -d or --database option. To set up a new database,
or reset and existing one
```
python twerpy.py setup -d new_database.db
```
This will set up an SQLite database called `new_database.db` in the `data` directory. All tweets are stored
in these databases.

### Searching for tweets
To gather tweets, you create a file that specifies search terms, as well as the search group.
The search group is used to indicate search terms belong to the same group. Analysis based on
a search group basis. An example file might look like
```
#fun:good_times
#winning:good_times
boring:bad_times
#sad:bad_times
```
You don't just have to search for hashtags, you can search for words as well.

To run a search

usage:
```
python twerpy.py search-terms terms_filename [-d | --database dbfilename][--no_RT]
```
examples:
```
$ python twerpy.py search-terms terms.txt
$ python twerpy.py search-terms terms.txt --database good_bad.db --no_RT
```
The option `--no_RT` will exclude retweets from the search.

### Searching trending tweets
You can search for trending tweets in a specified location, using the [WOEID](http://en.wikipedia.org/wiki/WOEID).
You can [look up WOEIDs here](http://woeid.rosselliot.co.nz/).

This will find all the trending terms for the WOEID, then run a search on each of them.
The search group will be automatically populated as `<WOEID>_<trending_term>`

To run a search for trending terms in San Francisco for example

usage:
```
python twerpy.py search-trends 2487956 [-d | --database dbfilename][--no_RT]
```
example:
```
$ python twerpy.py search-trends 2487956 -d san_fran.db --no_RT
```

### Analysing tweets
To calculate the sentiment (pos, neg or neutral) of all tweets in the database

usage:
```
python twerpy.py calc-sentiment [-d | --database dbfilename]
```
example:
```
$ python twerpy.py calc-sentiment -d good_bad.db
```

twerpy can perform word frequency analysis and sentiment analysis, with summary
statistics broken down by search group.

usage:
```
python twerpy.py report [-d | --database dbfilename]
```
example:
```
$ python twerpy.py report -d good_bad.db
```
This will place reports in CSV and JSON format in the `reports` directory.

Acknowledgements
----------------
Many thanks to the kind people at Cornell who produced the [movie review dataset]
(http://www.cs.cornell.edu/people/pabo/movie-review-data/), used to train the sentiment classifier.
