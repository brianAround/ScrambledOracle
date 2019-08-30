import random
import time
import schedule
import sys
from WordChain import *
from Oracle import Oracle
from ChainLinker import ChainLinker
from WordChainScribe import Scribe

single_run = False

# ini_stems = ['Oracle']
ini_stems = ['Oracle', 'ScrambledPratchett', 'ScrambledDouglasAdams']

message_buckets = {}
last_messages_filename = "message_buckets.txt"


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
    max_size = 200
    make_response = False
    day_of_week = time.localtime()[6]
    hash_tags = ['']
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
            start_time = time.time()
            r = Repeater()
            random.shuffle(ini_stems)
            for ini_stem in ini_stems:
                prat_config = ini_stem + adjustment + '.ini'
                send_for_config(prat_config, r, iterations, max_length=max_size,
                                add_hashtags=hash_tags, send_response=make_response)

            save_message_buckets()

            Repeater.target = Oracle()

            print("Time taken:", time.time() - start_time)
        else:
            print(time.ctime(int(time.time())), "Tick!")


def send_for_config(config_file, r, iterations=1, max_length=270, add_hashtags=None, send_response=False):
    try:
        if add_hashtags is None:
            add_hashtags = []
        channel = config_file.split('.')[0]
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


def check():
    pass


# cool idea: Set a specific day and/or time that pulls tweets related to a specific
# hashtag, adding them to a fresh (or generic base) word selection matrix, and during
# the course of the day/hour, tweets responses based on this data.

send()
if not single_run:
    schedule.every(120).minutes.do(send)
    while 1:
        schedule.run_pending()
        time.sleep(110)
