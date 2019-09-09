import os
import json
from queue import PriorityQueue
from TwitterRepository import TwitterRepository
from twython.exceptions import TwythonError
from twython.exceptions import TwythonRateLimitError
from datetime import datetime
from collections import namedtuple


TweetInfo = namedtuple('TweetInfo', ['id','text','is_retweet','posted_by','posted_date','reaction_status'])


def get_tweet_filename(username):
    return os.path.join('datafile', username + '_tweets.txt')


def get_mentions_filename(username):
    return os.path.join('datafile', username + '_mentions.txt')


def get_mentions(use_config_path=None, target_user='brianAround', mentions_file=None):
    page_size = 200
    min_seen_id = 9148322953504989
    max_avail_id = 0
    repository = TwitterRepository(use_config_path)
    twitter = repository.get_client_instance()
    mentions = {}
    if mentions_file is not None and os.path.isfile(mentions_file):
        mentions = load_mentions(mentions_file)
        if len(mentions) > 0:
            min_seen_id = max([int(tweet_id) for tweet_id in mentions])

    try:
        mention_result = twitter.get_mentions_timeline(count=1)
        max_avail_id = mention_result[0]['id']
        last_count = 0
        if max_avail_id != min_seen_id:
            mention_result = twitter.get_mentions_timeline(count=page_size, since_id=min_seen_id, max_id=max_avail_id, tweet_mode='extended')
            while len(mention_result) > 0 and last_count != len(mentions):
                last_count = len(mentions)
                for result_entry in mention_result:
                    if result_entry['id_str'] not in mentions:
                        item_is_retweet = False
                        final_date = result_entry['created_at']
                        max_avail_id = min(max_avail_id, result_entry['id'])
                        posted_by = result_entry['user']['screen_name']
                        if result_entry['full_text'].startswith('RT '):
                            item_is_retweet = True
                            original_user = result_entry['full_text'].split(' ')[1]
                            full_tweet = result_entry['retweeted_status']
                        elif result_entry['truncated']:
                            print('Calling to look up the full text for', result_entry['id_str'])
                            full_tweet = twitter.lookup_status(id=result_entry['id_str'], tweet_mode='extended')[0]
                        else:
                            full_tweet = result_entry

                        mentions[full_tweet['id_str']] = {'id': full_tweet['id'], 'text': full_tweet['full_text'], 'is_retweet': item_is_retweet, 'posted_by':posted_by, 'posted_date': final_date, 'reaction_status': 'pending'}
                mention_result = twitter.get_mentions_timeline(count=page_size, since_id=str(min_seen_id), max_id=max_avail_id, tweet_mode='extended')
    except TwythonError as twy_err:
        print('Error downloading user mentions for', repository.twitter_handle, 'from Twitter.')
        print(type(twy_err))
        print(twy_err.msg)
    repository.reset_client()
    return mentions

# use the max_id to know what's been handled and what hasn't.
# important attributes: id, text (perhaps full_text, newlines and tabs cloaked for save), truncated, ['entities']['user_mentions']->['screen_name'],


def download_tweets(use_config_path=None, target_user = 'brianAround', tweet_file=None):
    tweets = {}
    page_size = 200
    page_number = 1
    min_seen_id = 10000000000000
    max_avail_id = 0
    current_date = datetime.now()
    max_page = 50

    if tweet_file is not None and os.path.isfile(tweet_file):
        tweets = load_tweets(tweet_file)
        if len(tweets) > 0:
            min_seen_id = max([int(tweet_id) for tweet_id in tweets])

    repository = TwitterRepository(use_config_path)
    twitter = repository.get_client_instance()

    try:
        tweets_result = twitter.get_user_timeline(screen_name=target_user,
                                              count='1',
                                              trim_user='True')
        if len(tweets_result) > 0:
            max_avail_id = int(tweets_result[0]['id'])

        if max_avail_id != min_seen_id:
                tweets_result = twitter.get_user_timeline(screen_name=target_user,
                                                          since_id=min_seen_id,
                                                          max_id=max_avail_id,
                                                          count=page_size,
                                                          trim_user='True', tweet_mode='extended')
                last_count = -1
                while page_number <= max_page and len(tweets_result) > 0 and len(tweets) != last_count:
                    last_count = len(tweets)
                    for item in tweets_result:
                        if item['id_str'] not in tweets:
                            item_is_retweet = False
                            original_user = '@' + target_user
                            final_date = item['created_at']
                            max_avail_id = min(max_avail_id, item['id'])
                            if item['full_text'].startswith('RT '):
                                item_is_retweet = True
                                original_user = item['full_text'].split(' ')[1]
                                full_tweet = item['retweeted_status']
                            elif item['truncated']:
                                print('Calling to look up the full text for', item['id_str'])
                                full_tweet = twitter.lookup_status(id=item['id_str'], tweet_mode='extended')[0]
                            else:
                                full_tweet = item
                            tweets[full_tweet['id_str']] = {'id': full_tweet['id'], 'text': full_tweet['full_text'], 'is_retweet': item_is_retweet, 'posted_by':original_user, 'posted_date': final_date}

                    tweets_result = twitter.get_user_timeline(screen_name=target_user,
                                                              since_id=min_seen_id,
                                                              max_id=max_avail_id,
                                                              count=page_size,
                                                              trim_user='True', tweet_mode='extended')
                    page_number += 1
    except TwythonError as twy_err:
        print('Error downloading timeline for', target_user, 'from Twitter using account', repository.twitter_handle)
        print(type(twy_err))
        print(twy_err.msg)
    repository.reset_client()
    return tweets


def store_tweets(filename, tweets):
    has_reaction = False
    ids_to_store = [tid for tid in tweets]
    if os.path.isfile(filename):
        tweets = load_tweets(filename, tweets)
    if len([tid for tid in ids_to_store if 'is_changed' in tweets[tid]]) > 0:
        with open(filename, 'w', encoding='utf-16') as tweet_file:
            for tweet_id in sorted([int(tid) for tid in tweets], reverse=True):
                tweet = tweets[str(tweet_id)]
                tweet_file.write(str(tweet['id']) + '\t')
                tweet_file.write(tweet['text'].replace('\t',' <tab /> ').replace('\n',' <newline /> ') + '\t')
                tweet_file.write(str(tweet['is_retweet']) + '\t')
                tweet_file.write(tweet['posted_by'] + '\t')
                tweet_file.write(tweet['posted_date'])
                if has_reaction or 'reaction_status' in tweet:
                    has_reaction = True
                    tweet_file.write('\t' + tweet['reaction_status'])
                tweet_file.write('\n')


def load_tweets(filename, existing_tweets:dict = None):
    tweets = {} if existing_tweets is None else existing_tweets
    with open(filename, 'r', encoding='utf-16') as tweet_file:
        for line in tweet_file.readlines():
            values = line.strip('\n').split('\t')
            tweet = {'id': int(values[0]),
                     'text': values[1].replace(' <tab /> ', '\t').replace(' <newline /> ', '\n'),
                     'is_retweet': (values[2] == 'True'),
                     'posted_by': values[3],
                     'posted_date': values[4]}
            if len(values) >= 6:
                tweet['reaction_status'] = values[5]
            if values[0] not in tweets:
                tweets[values[0]] = tweet
            else:
                new_values = tweets[values[0]]
                is_changed = False
                for field_name in ['text', 'posted_by', 'posted_date', 'reaction_status']:
                    if field_name in new_values and new_values[field_name] != tweet[field_name]:
                        is_changed = True
                        break
                if is_changed:
                    new_values['is_changed'] = is_changed
    return tweets


def load_mentions(filename, pending_only=False):
    mentions = {}
    with open(filename, 'r', encoding='utf-16') as tweet_file:
        for line in tweet_file.readlines():
            values = line.strip('\n').split('\t')
            tweet = {'id': int(values[0]),
                     'text': values[1].replace(' <tab /> ', '\t').replace(' <newline /> ', '\n'),
                     'is_retweet': (values[2] == 'True'),
                     'posted_by': values[3],
                     'posted_date': values[4],
                     'reaction_status': 'pending'}
            if len(values) > 5:
                tweet['reaction_status'] = values[5]
            if tweet['reaction_status'] == 'pending' or not pending_only:
                mentions[values[0]] = tweet
    return mentions



# use the max_id to know what's been handled and what hasn't.
# important attributes: id, text (perhaps full_text, newlines and tabs cloaked for save), truncated, ['entities']['user_mentions']->['screen_name'],