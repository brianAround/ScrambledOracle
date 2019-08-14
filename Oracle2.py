import random
import time
import schedule
import sys
from WordChain import *
from Oracle import Oracle
from ChainLinker import ChainLinker
from WordChainScribe import Scribe

single_run = True

ini_stems = ['ScrambledPratchett','ScrambledDouglasAdams']
# ini_stems = ['ScrambledPratchett','ScrambledDouglasAdams','Oracle']

message_buckets = {}
last_messages_filename = "message_buckets.txt"

# if the message_buckets file exists, load it.
if os.path.isfile(last_messages_filename):
    message_buckets = Oracle.load_dictionary(last_messages_filename)

class Repeater:

    target = None
    # message_buckets = {}
    max_percent = 1/2

    def __init__(self):
        self.awake = True

    def send_message(self, prompt=""):
        if Repeater.target is None:
            Repeater.target = Oracle()
            Repeater.target.chain = WordChain()
            Repeater.target.chain.depth = 3
            Scribe.read_map("current.txt.map", chain=Repeater.target.chain)
        Repeater.target.is_verbose = True
        return Repeater.target.send_message(prompt)


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
    iterations = 3
    day_of_week = time.localtime()[6]
    hash_tags = ['']
    if day_of_week == 1:
        iterations = 2
        hash_tags = ['']
    if day_of_week == 3:
        Repeater.max_percent = 1/3
        hash_tags = ['']
    else:
        Repeater.max_percent = 1/2
    if day_of_week == 4:
        adjustment = ".named"
    if 1 <= time.localtime()[3] <= 23:
        if random.randint(1, 1) == 1:
            start_time = time.time()
            r = Repeater()
            for ini_stem in ini_stems:
                prat_config = ini_stem + adjustment + '.ini'
                send_for_config(prat_config, r, iterations, add_hashtags=hash_tags)

            #send_for_config('oracle' + adjustment + '.ini', r, iterations, add_hashtags=hash_tags)
            Repeater.target = Oracle()

            print("Time taken:", time.time() - start_time)
        else:
            print(time.ctime(int(time.time())), "Tick!")


def send_for_config(prat_config, r, iterations=1, add_hashtags=[]):
    try:
        channel = prat_config
        if prat_config.startswith('ScrambledPratchett'):
            channel = 'ScrambledPratchett'
        linker = ChainLinker(config_file=prat_config)
        # linker.data_refresh_time = 10
        linker.verbose = True
        linker.initialize_chain()
        Repeater.target = Oracle(config_file=prat_config)
        Repeater.target.hashtags += add_hashtags
        Repeater.target.max_percent = Repeater.max_percent
        Repeater.target.character_limit = 270
        Repeater.target.long_tweet_as_image = True
        prompt = ''
        if channel in message_buckets.keys():
            prompt = message_buckets[channel]
        for idx in range(iterations):
            last_message = r.send_message(prompt)
            message_buckets[channel] = last_message
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
    schedule.every(30).minutes.do(send)
    while 1:
        schedule.run_pending()
        time.sleep(30)

with open(last_messages_filename, 'w') as sent_file:
    for key, message in message_buckets.items():
        sent_file.write(key + '\t' + message + '\n')
