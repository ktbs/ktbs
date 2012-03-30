==================================
Populate the kTBS with your tweets
==================================

The following code uses the kTBS python client to populate the kTBS with your favorite tweets.

You need to install ``python-twitter`` in your kTBS virtual environment.

    $ pip install python-twitter

You need to `get twitter oAuth access tokens <https://dev.twitter.com/docs/auth/tokens-devtwittercom>`_ to be able to use the twitter API.

and then fill the ``credentials.txt`` file with your access tokens.

Then execute the following command.

    $ python getMyFavoritesAndRetweets.py

The model and obsels have to be developped.
