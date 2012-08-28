#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Use twitter-api to retrieve my favorited and retweeted tweets.
"""

import sys
import datetime

import twitter

from ktbs.client import get_ktbs

# Twitter elements
CREDENTIAL = "credentials.txt"

# kTBS elements
KTBS_ROOT = "http://localhost:8001/"
TWITTER_OBSELS = "#TwitterObsels"

def createkTBSForTweets(root=None):
    """
    Creates a kTBS Base for twitter data collection.
    """

    baseTw = root.create_base(id="BaseTw/")

    modelTw = baseTw.create_model(id="twitterModel")

    obselTw = modelTw.create_obsel_type(id=TWITTER_OBSELS)

    traceTw = baseTw.create_stored_trace(id="FavoriteTweets/",
                                         model=modelTw, 
                                         origin=datetime.datetime.now())
    return traceTw

def getTwitterFavorites(trace=None):
    """
    Populates the kTBS Trace with favorite tweets.
    """

    # Get Model Information : should we store it ? 
    model = trace.get_model()

    # Get obsel type URI
    tw_obsel_type = model.get(id=TWITTER_OBSELS)

    with open(CREDENTIAL) as f:
        twitter_credential = dict(line.split() for line in f)

    api = twitter.Api(**twitter_credential)

    nb_favorites_pages = 2
    for i in range(1, nb_favorites_pages):
        print "Fetching page: %s" % i
        favs = api.GetFavorites(page=i)

        if not favs:
            break

        for p in favs:
            user = p.user

            t_date = datetime.datetime.strptime(p.created_at, "%a %b %d %H:%M:%S +0000 %Y")
            #print "t_date: ", t_date.isoformat(), "\n"

            # Insert tweets as obsels
            trace.create_obsel(type=tw_obsel_type.get_uri(),
                               begin=t_date,
                               end=t_date,
                               subject=p.text)

            print p.id, "[", p.created_at, "]\n\t", p.text \
                  ,"\n\tby: ", user.screen_name, "-", user.name, "-", user.id \
                  ,"\n\thastags: ", p.hashtags, "\n"

if __name__ == "__main__":
    root = get_ktbs(KTBS_ROOT)
    trace = createkTBSForTweets(root)
    if trace is not None:
        getTwitterFavorites(trace)
    sys.exit(0)
