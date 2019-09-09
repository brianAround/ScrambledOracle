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
fetch_data_every = 300

ignore_bot_ratio = 0.80


ini_stems = ['Oracle']
# ini_stems = ['Oracle', 'ScrambledPratchett', 'ScrambledDouglasAdams']

message_buckets = {}
last_messages_filename = "message_buckets.txt"

scrambled_accounts = ['ScrambledAdams', 'ScramPratchett', 'SouthernOracle4']

def load_dictionary(file_path):
    result = {}
    file_size = min(32, os.path.getsize(file_path))
    with open(file_path, 'rb') as f_enc:
        raw = f_enc.read(file_size)
        if raw.startswith(codecs.BOM_UTF8):
            encoding = 'utf-8-sig'
        else:
            encoding = 'utf-8'
    with open(file_path, 'r', encoding=encoding) as f_handle:
        for line in f_handle:
            work_line = line.strip()
            if '\t' in work_line:
                bucket_key, bucket_id, bucket_text = work_line.split('\t')
                result[bucket_key] = {'id': int(bucket_id), 'text': bucket_text.replace('<newline />', '/n')}
            else:
                result[line.strip()] = True
    return result


def save_message_buckets():
    with open(last_messages_filename, 'w') as sent_file:
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
            for screen_name in Repeater.target.get_reply_users(as_reply_to_id, posted_user_only=False):
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

    def get_expanded_prompt(self, tweet_id, current_prompt):
        if tweet_id != 0:
            this_tweet = Repeater.target.get_tweet(tweet_id)
            if this_tweet is not None:
                if 'in_reply_to_status_id' in this_tweet:
                    previous_tweet = Repeater.target.get_tweet(this_tweet['in_reply_to_status_id'])
                    if previous_tweet is not None:
                        current_prompt = previous_tweet['full_text'] + ' ' + this_tweet['full_text']
        return current_prompt

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


def send(mode='originate', use_config_stem=None):
    adjustment = ""
    iterations = 1
    day_of_week = time.localtime()[6]
    hash_tags = []
    config_stems = ini_stems
    if use_config_stem is not None:
        config_stems = [use_config_stem]
    start_time = time.time()
    if mode == 'originate':
        max_size = 200
        make_response = False
        if day_of_week == 1:
            iterations = 1
            hash_tags = ['']
        if day_of_week == 2:
            make_response = True
            max_size = 140
        if day_of_week == 3:
            Repeater.max_percent = 1/3
            hash_tags = ['']
        else:
            Repeater.max_percent = 1/2
        if day_of_week == 4:
            adjustment = ".named"
        if day_of_week == 5:
            max_size = random.randint(70, 840)

        if 1 <= time.localtime()[3] <= 23:
            if random.randint(1, 1) == 1:
                r = Repeater()
                random.shuffle(config_stems)
                for config_stem in config_stems:
                    prat_config = config_stem + adjustment + '.ini'
                    send_for_config(prat_config, r, iterations, max_length=max_size,
                                    add_hashtags=hash_tags, send_response=make_response)

                save_message_buckets()

            else:
                print(time.ctime(int(time.time())), "Tick!")
    if mode == 'respond':
        adjustment = ""
        iterations = 1
        max_size = 140

        if 1 <= time.localtime()[3] <= 23:
            if random.randint(1, 1) == 1:
                start_time = time.time()
                r = Repeater()
                random.shuffle(config_stems)
                for config_stem in config_stems:
                    file_config = config_stem + adjustment + '.ini'
                    send_mention_response_for_config(file_config, r, iterations, max_length=max_size,
                                                     add_hashtags=hash_tags, strangers_only=False)
                save_message_buckets()
            else:
                print(time.ctime(int(time.time())), "Tick!")

    Repeater.target = None
    print("Time taken:", time.time() - start_time)


def send_mention_response_for_config(config_file, r: Repeater, iterations=1, max_length=270, add_hashtags=None,
                                     strangers_only=True):
    try:
        # linker = ChainLinker(config_file=config_file)
        if add_hashtags is None:
            add_hashtags = []
        channel = config_file.split('.')[0]
        # linker.data_refresh_time = 10
        # linker.verbose = True
        # linker.initialize_chain()
        configure_repeater_target(add_hashtags, config_file, max_length)
        # Repeater.target.is_new_build = linker.file_rebuilt
        print(time.ctime(int(time.time())), "Handling mentions for", Repeater.target.twitter_handle, "...")

        mentions_file = TwitterTimeline.get_mentions_filename(Repeater.target.twitter_handle.replace('@', ''))

        mentions = {}
        if not os.path.isfile(mentions_file) or os.path.getmtime(mentions_file) < time.time() - fetch_data_every:
            mentions = TwitterTimeline.get_mentions(config_file, Repeater.target.twitter_handle.replace('@', ''),
                                                    mentions_file)
            TwitterTimeline.store_tweets(mentions_file, mentions)
        else:
            mentions = TwitterTimeline.load_mentions(mentions_file, pending_only=False)

        # now that the system can post responses, we're close to being able to process commands.
        # possible valuable commands to use: show build, rebuild, set reply timing 30, set tweet timing 120

        commands = get_commands_pending(mentions)

        run_commands(commands, config_file)

        target_tweets = get_response_candidates(mentions)

        prompt_id = 0
        prompt = ''

        mention_tweet = None
        for idx in range(iterations):
            while len(target_tweets) > 0 and mention_tweet is None:
                mention_tweet = target_tweets.pop(random.randint(0, len(target_tweets) - 1))
                if mention_tweet['posted_by'] in scrambled_accounts:
                    if strangers_only or random.random() < ignore_bot_ratio:
                        mention_tweet['reaction_status'] = 'ignored'
                        mention_tweet = None
            if mention_tweet is not None:
                prompt_id = mention_tweet['id']
                prompt = mention_tweet['text']
                print('Replying to tweet id', prompt_id, ':', prompt, 'from', '@' + mention_tweet['posted_by'])
                message = r.build_message(prompt)
                if len(message) == 0 and mention_tweet['reaction_status'] == 'speechless':
                    print('Digging a little deeper.')
                    prompt = r.get_expanded_prompt(mention_tweet['id'], prompt)
                    print('Building message for exended prompt:', prompt)
                    old_percentage = r.target.max_percent
                    r.target.max_percent = 3/4
                    message = r.build_message(prompt)
                    r.target.max_percent = old_percentage
                if len(message) == 0:
                    print('Unable to generate response from prompt.')
                    mention_tweet['reaction_status'] = 'speechless'
                else:
                    tid = r.send_tweet(message, prompt_id)
                    if tid > 0:
                        mentions[str(prompt_id)]['reaction_status'] = 'replied:' + str(tid)
                    last_message = message
                    message_buckets[channel] = {'id': int(r.target.last_tweet_id), 'text': last_message}
                    prompt = last_message
        TwitterTimeline.store_tweets(mentions_file, mentions)

        linker = None

    except ValueError:
        pass
    else:
        pass


def get_commands_pending(mentions):
    target_tweets = [mentions[tid] for tid in mentions
                     if mentions[tid]['reaction_status'] == 'pending'
                     and ' oracle: ' in mentions[tid]['text'].lower()]
    for tweet in target_tweets:
        clean_words = []
        for word in tweet['text'].split():
            word = word.strip()
            if word[0] != '@':
                clean_words.append(word.lower())
        tweet['command'] = ' '.join(clean_words)
    return target_tweets


def get_response_candidates(mentions):
    target_tweets = [mentions[tid] for tid in mentions
                     if mentions[tid]['reaction_status'] == 'pending']
    if len(target_tweets) == 0:
        target_tweets = [mentions[tid] for tid in mentions
                         if mentions[tid]['reaction_status'] == 'speechless']
    return target_tweets


def run_commands(commands, config_file):
    config_modes = ['originate', 'respond']
    for command in commands:
        command_units = (' ' + command['command']).replace(' o: ', ' oracle: ').split(' oracle: ')
        for command_text in command_units:
            command_text = command_text.strip()
            if len(command_text) > 0:
                options = command_text.split()
                print('Handling command in tweet', command['id'], ':', command_text)

                if options[0] == 'rebuild':
                    linker = configure_linker(config_file=config_file, initialize=False)
                    linker.regenerate_by_config()
                    Repeater.target.initialize_chain()
                    to_user = Repeater.target.get_reply_users(command['id'])
                    Repeater.target.send_build_announcement(to_user)
                if options[0] == 'show':
                    if options[1] == 'build':
                        Repeater.target.initialize_chain()
                        to_user = Repeater.target.get_reply_users(command['id'])
                        Repeater.target.send_build_announcement(to_user)
                if options[0] == 'task' and len(options) >= 3:
                    change_type = ''
                    timing_queue = []
                    config_queue = []
                    tag = options[1]
                    if len([job for job in schedule.jobs if tag in job.tags]) == 0 and tag in config_modes:
                        tag = tag + '_all'
                        change_type = 'global_tasks'
                    minutes = int(options[2])
                    method = send
                    mode = 'originate'
                    config_stem = []
                    if len(options) >= 4:
                        if options[3] in config_modes:
                            mode = options[3]
                        else:
                            config_stem.append(options[3])
                    if len(options) >= 5:
                        config_stem.append(options[4])

                    if len(options) == 3:
                        for job in schedule.jobs:
                            if tag in job.tags:
                                all_tags = job.tags
                                method = job.job_func
                                mode = None
                                timing_queue.append([all_tags, minutes, method])
                    if len(timing_queue) == 0:
                        if len(config_stem) > 0:
                            for stem in config_stem:
                                config_queue.append([tag, minutes, method, mode, stem])
                        else:
                            config_queue.append([tag, minutes, method, mode])

                    schedule.clear(tag)
                    for item in timing_queue:
                        schedule.every(item[1]).minutes.do(item[2]).tags = item[0]
                    for item in config_queue:
                        if len(item) == 4:
                            schedule.every(item[1]).minutes.do(item[2], item[3]).tag(item[0])
                        else:
                            schedule.every(item[1]).minutes.do(item[2], item[3], item[4]).tag(item[0])
        command['reaction_status'] = 'executed'




def configure_repeater_target(add_hashtags, config_file, max_length):
    Repeater.target = Oracle(config_file=config_file)
    Repeater.target.hashtags += add_hashtags
    Repeater.target.max_percent = Repeater.max_percent
    Repeater.target.character_limit = max_length
    Repeater.target.long_tweet_as_image = False


def configure_linker(config_file, initialize=True):
    linker = ChainLinker(config_file=config_file)
    linker.verbose = True
    if initialize:
        linker.initialize_chain()
    return linker


def send_for_config(config_file, r, iterations=1, max_length=270, add_hashtags=None, send_response=False):
    try:
        if add_hashtags is None:
            add_hashtags = []
        channel = config_file.split('.')[0]
        linker = configure_linker(config_file)
        configure_repeater_target(add_hashtags, config_file, max_length)
        Repeater.target.is_new_build = linker.file_rebuilt
        prompt_id = 0
        prompt = ''
        prompt_channel = channel
        queued_items = Repeater.target.get_tweet_queue(use_name='')

        for idx in range(iterations):
            old_values = None
            if len(queued_items) > 0:
                for qidx in range(len(queued_items)):
                    if queued_items[qidx]['bot_name'] == Repeater.target.bot_name:
                        old_values = queued_items.pop(qidx)
                        break
            if old_values is not None:
                Repeater.target.write_tweet_queue(queued_items)
                tid = Repeater.target.send_tweet(old_values['message'], old_values['reply_to_tweet'])
                r.target.last_tweet_id = tid
                last_message = old_values['message']
            else:
                if send_response:
                    all_channels = [key for key in message_buckets.keys()]
                    prompt_channel = random.choice(all_channels)

                if prompt_channel in message_buckets.keys():
                    prompt_id = message_buckets[prompt_channel]['id']
                    prompt = message_buckets[prompt_channel]['text']

                if send_response:
                    last_message = r.send_response(prompt_id, prompt)
                else:
                    last_message = r.send_message(prompt)
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


if not single_run:
    schedule.every(15).minutes.do(send, 'respond').tag('respond_all')
    schedule.every(120).minutes.do(send, 'originate').tag('originate_all')
    # schedule.every(10).minutes.do(send, 'originate', 'oracle').tag('originate_oracle')

    schedule.run_all(1)
    last_hash = str(schedule.jobs)
    print(schedule.jobs)
    while 1:
        schedule.run_pending()
        if last_hash != str(schedule.jobs):
            print(schedule.jobs)
            last_hash = str(schedule.jobs)
        time.sleep(60)
else:
    send('respond', 'oracle')
    # send('originate')
    # send('respond')
