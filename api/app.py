from flask import Flask, request
import tweepy
import os
import pymongo
from bson.json_util import dumps
import feedparser

# Authenticate with Twitter API
auth = tweepy.OAuthHandler(os.environ['CONSUMER_KEY'], os.environ['CONSUMER_SECRET'])
auth.set_access_token(os.environ['ACCESS_TOKEN'], os.environ['ACCESS_TOKEN_SECRET'])
api = tweepy.API(auth)

app=Flask(__name__)

# Connect to MongoDB
mongo_client = pymongo.MongoClient(os.environ['MONGODB_URI'])
db = mongo_client[os.environ['MONGODB_DB']]
tweets_collection = db['tweets']

# Define function to get latest tweets with a given keyword
def get_latest_tweet(keyword):
    tweets = api.search(q=keyword, lang='en', result_type='recent', count=1)
    return tweets[0]

# Define function to handle mentions
def handle_mentions():
    mentions = api.mentions_timeline(count=10)
    for mention in mentions:
        if mention.in_reply_to_status_id is not None:
            continue
        if 'keywords' in mention.text.lower():
            keywords = mention.text.lower().split('keywords ')[1]
            latest_tweet = get_latest_tweet(keywords)
            # Save tweet to MongoDB
            tweets_collection.insert_one(latest_tweet._json)
            api.update_status('@' + mention.user.screen_name + ' ' + latest_tweet.text, in_reply_to_status_id=mention.id)

# Define endpoint for periodic news updates
@app.route('/news-update')
def news_update():
    # Get latest news from RSS feed
    rss_feed = 'https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml' # Change this to your RSS feed
    feed = feedparser.parse(rss_feed)
    latest_news_title = feed.entries[0].title
    latest_news_link = feed.entries[0].link
    latest_news = f'{latest_news_title}\n{latest_news_link}\n\n'
    
    # Save news to MongoDB
    news_tweet = api.update_status('Cybersecurity news update:\n' + latest_news)
    tweets_collection.insert_one(news_tweet._json)
    return 'News update posted!'

@app.route('/mentions')
def mentions():
    handle_mentions()
    return 'Mentions handled!'


    