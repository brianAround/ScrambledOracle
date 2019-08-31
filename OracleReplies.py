import random
import time
import schedule
import sys
from WordChain import *
from Oracle import Oracle
from ChainLinker import ChainLinker
from WordChainScribe import Scribe
import TwitterRepository
import TwitterTimeline

single_run = False
fetch_data_every = 900

# ini_stems = ['ScrambledPratchett']
ini_stems = ['Oracle', 'ScrambledPratchett', 'ScrambledDouglasAdams']

# ini_stems = [random.choice(ini_stems)]

message_buckets = {}
last_messages_filename = "message_buckets.txt"

scrambled_accounts = ['ScrambledAdams','ScramPratchett','SouthernOracle4']


def load_dictionary(file_path):
    result = {}
    with open(file_path, 'r', encoding='utf-16') as f_handle:
        for line in f_handle:
            work_line = line.strip()
            if '\t' in work_line:
                bucket_key, bucket_id, bucket_text = work_line.split('\t')
                result[bucket_key] = {'id': int(bucket_id), 'text': bucket_text.replace('<newline />', '\n')}
            else:
                result[line.strip()] = True
    return result


def save_message_buckets():
    with open(last_messages_filename, 'w', encoding='utf-16') as sent_file:
        for key, message in message_buckets.items():
            sent_file.write(key + '\t' + str(message['id']) + '\t'
                            + message['text'].replace('\n', '<newline />') + '\n')


# if the message_buckets file exists, load it.
if os.path.isfile(last_messages_filename):
    message_buckets = load_dictionary(last_messages_filename)


class Repeater:

    target = None
    # message_buckets = {}
    max_percent = 1/2

    def __init__(self):
        self.awake = True

    def send_message(self, prompt=""):
        self.init_target()
        return Repeater.target.send_message(prompt)

    def send_response(self, message_id, prompt=""):
        if message_id == 0:
            self.send_message(prompt)
        self.init_target()
        return Repeater.target.send_reply(message_id, prompt)

    def send_tweet(self, message_text, as_reply_to_id=0):
        if as_reply_to_id > 0:
            handles = []
            for screen_name in Repeater.target.get_reply_users(as_reply_to_id):
                if screen_name.lower() not in message_text.lower():
                    handles.append(screen_name)
            message_text = " ".join(handles) + ' ' + message_text
        return Repeater.target.send_tweet(message_text, respond_to_tweet=as_reply_to_id)

    def build_message(self, prompt, fail_on_lost_prompt=True):
        self.init_target()
        passage_results = []
        message = Repeater.target.get_message(prompt=prompt, passages=passage_results)
        if fail_on_lost_prompt and Repeater.target.prompt_reset:
            return ''
        else:
            return message

    @staticmethod
    def init_target():
        if Repeater.target is None:
            Repeater.target = Oracle()
            Repeater.target.chain = WordChain()
            Repeater.target.chain.depth = 3
            Scribe.read_map("current.txt.map", chain=Repeater.target.chain)
        Repeater.target.is_verbose = False


if len(sys.argv) > 1:
    Repeater.last_message = sys.argv[1]
    if Repeater.last_message == '-one-time':
        single_run = True
    if len(sys.argv) > 2:
        Repeater.last_message = sys.argv[2]
else:
    Repeater.last_message = ""


def send():
    adjustment = ""
    iterations = 1
    max_size = 140
    make_response = True
    day_of_week = time.localtime()[6]
    hash_tags = []

    if 1 <= time.localtime()[3] <= 23:
        if random.randint(1, 1) == 1:
            start_time = time.time()
            r = Repeater()
            random.shuffle(ini_stems)
            for ini_stem in ini_stems:
                prat_config = ini_stem + adjustment + '.ini'
                send_mention_response_for_config(prat_config, r, iterations, max_length=max_size,
                                add_hashtags=hash_tags)

            save_message_buckets()

            Repeater.target = Oracle()


            print("Time taken:", time.time() - start_time)
        else:
            print(time.ctime(int(time.time())), "Tick!")
    print(schedule.jobs)

def send_mention_response_for_config(config_file, r:Repeater, iterations=1, max_length=270, add_hashtags=None, strangers_only=True):
    try:
        # linker = ChainLinker(config_file=config_file)
        if add_hashtags is None:
            add_hashtags = []
        channel = config_file.split('.')[0]
        # linker.data_refresh_time = 10
        # linker.verbose = True
        # linker.initialize_chain()
        Repeater.target = Oracle(config_file=config_file)
        Repeater.target.hashtags += add_hashtags
        Repeater.target.max_percent = Repeater.max_percent
        Repeater.target.character_limit = max_length
        Repeater.target.long_tweet_as_image = False
        # Repeater.target.is_new_build = linker.file_rebuilt
        print(time.ctime(int(time.time())), "Handling mentions for", Repeater.target.twitter_handle,"...")


        mentions_file = TwitterTimeline.get_mentions_filename(Repeater.target.twitter_handle.replace('@',''))

        mentions = {}
        if not os.path.isfile(mentions_file) or os.path.getmtime(mentions_file) < time.time() - fetch_data_every:
            mentions = TwitterTimeline.get_mentions(config_file, Repeater.target.twitter_handle.replace('@',''), mentions_file)
            TwitterTimeline.store_tweets(mentions_file, mentions)
        else:
            mentions = TwitterTimeline.load_mentions(mentions_file, pending_only=True)

        # now that the system can post responses, we're close to being able to process commands.
        # possible valuable commands to use: show build, rebuild, set reply timing 30, set tweet timing 120
        target_tweets = [mentions[tid] for tid in mentions
                         if mentions[tid]['posted_by'] not in scrambled_accounts and
                         mentions[tid]['reaction_status'] == 'pending']

        if len(target_tweets) == 0 and not strangers_only:
            target_tweets = [mentions[tid] for tid in mentions
                             if mentions[tid]['reaction_status'] == 'pending']

        prompt_id = 0
        prompt = ''


        for idx in range(iterations):
            if len(target_tweets) > 0:
                target = target_tweets.pop(random.randint(0,len(target_tweets) - 1))
                prompt_id = target['id']
                prompt = target['text']
                print('Replying to tweet id', prompt_id, ':', prompt, 'from', '@' + target['posted_by'])
                message = r.build_message(prompt)
                if len(message) == 0:
                    print('Unable to generate response from prompt.')
                else:
                    tid = r.send_tweet(message, prompt_id)
                    if tid > 0:
                        mentions[str(prompt_id)]['reaction_status'] = 'replied:' + str(tid)
                    TwitterTimeline.store_tweets(mentions_file, mentions)
                    last_message = message
                    message_buckets[channel] = {'id': int(r.target.last_tweet_id), 'text': last_message}
                    prompt = last_message
        linker = None

    except ValueError:
        pass
    else:
        pass


def send_random_for_config(config_file, target_user, r, iterations=1, max_length=270, add_hashtags=None, send_response=False):
    try:
        if add_hashtags is None:
            add_hashtags = []
        channel = config_file.split('.')[0]
        print('Preparing to send reply to', target_user, 'for Channel', channel)
        linker = ChainLinker(config_file=config_file)
        # linker.data_refresh_time = 10
        linker.verbose = True
        linker.initialize_chain()
        Repeater.target = Oracle(config_file=config_file)
        Repeater.target.hashtags += add_hashtags
        Repeater.target.max_percent = Repeater.max_percent
        Repeater.target.character_limit = max_length
        Repeater.target.long_tweet_as_image = False
        Repeater.target.is_new_build = linker.file_rebuilt

        tweet_file = TwitterTimeline.get_tweet_filename(target_user)
        tweets = {}
        if not os.path.isfile(tweet_file) or os.path.getmtime(tweet_file) < time.time() - fetch_data_every:
            tweets = TwitterTimeline.download_tweets(config_file, target_user, tweet_file)
            TwitterTimeline.store_tweets(tweet_file, tweets)
        else:
            tweets = TwitterTimeline.load_tweets(tweet_file)

        sample_size = 10
        skip_retweets = True
        top_tweets = get_recent_tweets(tweets, sample_size, skip_retweets)

        prompt_id = 0
        prompt = ''

        for idx in range(iterations):
            if len(top_tweets) > 0:
                target = top_tweets.pop(random.randint(0,len(top_tweets) - 1))
                prompt_id = target['id']
                prompt = target['text']
                print('Replying to tweet id', prompt_id, ':', prompt)

                last_message = r.send_response(prompt_id, prompt)
                message_buckets[channel] = {'id': int(r.target.last_tweet_id), 'text': last_message}
                prompt = last_message

        linker = None

    except ValueError:
        pass
    else:
        pass


def get_recent_tweets(tweets, sample_size=5, skip_retweets=True):
    top_tweets = []
    ordered_ids = sorted([int(tid) for tid in tweets], reverse=True)
    tweet_idx = 0
    while len(top_tweets) < sample_size and tweet_idx < len(tweets):
        tweet = tweets[str(ordered_ids[tweet_idx])]
        if not skip_retweets or not tweet['is_retweet']:
            top_tweets.append(tweet)
        tweet_idx += 1
    return top_tweets


def check():
    pass


# cool idea: Set a specific day and/or time that pulls tweets related to a specific
# hashtag, adding them to a fresh (or generic base) word selection matrix, and during
# the course of the day/hour, tweets responses based on this data.

send()
if not single_run:
    schedule.every(15).minutes.do(send).tag('oracle_replies')
    print(schedule.jobs)

    while 1:
        schedule.run_pending()
        time.sleep(10)
