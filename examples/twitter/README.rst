==================================
Populate the kTBS with your tweets
==================================

The following code uses the kTBS python client to populate the kTBS with your favorite tweets.

You need to install ``python-twitter`` in your kTBS virtual environment.

.. code-block:: bash

    $ pip install python-twitter

You need to get twitter oAuth access tokens to be able to use the twitter API.

 - https://dev.twitter.com/docs/auth/tokens-devtwittercom

and then fill the ``credentials.txt`` file with your access tokens.

Then execute the following command.

.. code-block:: bash

    $ python getMyFavoritesAndRetweets.py

The model and obsels have to be developped.
