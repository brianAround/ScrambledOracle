import random
import time
import schedule
import sys
from WordChain import *
from Oracle import Oracle
from ChainLinker import ChainLinker
from WordChainScribe import Scribe

single_run = False


class Repeater:

    target = None
    message_buckets = {}
    max_percent = 1/2

    def __init__(self):
        self.awake = True

    def send_message(self, prompt=""):
        if Repeater.target is None:
            Repeater.target = Oracle()
            Repeater.target.chain = WordChain()
            Repeater.target.chain.depth = 3
            Scribe.read_map("current.txt.map", chain=Repeater.target.chain)

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
    iterations = 1
    day_of_week = time.localtime()[6]
    hash_tags = []
    if day_of_week == 1:
        iterations = 2
        hash_tags = ['#TwoForTuesday']
    if day_of_week == 3:
        Repeater.max_percent = 1/3
        hash_tags = ['#Neopolitan']
    else:
        Repeater.max_percent = 1/2
    if day_of_week == 4:
        adjustment = ".named"
    if 1 <= time.localtime()[3] <= 23:
        if random.randint(1, 1) == 1:
            start_time = time.time()
            r = Repeater()
            prat_config = 'ScrambledPratchett' + adjustment + '.ini'

            send_for_config(prat_config, r, iterations, add_hashtags=hash_tags)
            send_for_config('ScrambledDouglasAdams' + adjustment + '.ini', r, iterations, add_hashtags=hash_tags)
            send_for_config('oracle' + adjustment + '.ini', r, iterations, add_hashtags=hash_tags)
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
        linker.initialize_chain()
        Repeater.target = Oracle(config_file=prat_config)
        Repeater.target.hashtags += add_hashtags
        Repeater.target.max_percent = Repeater.max_percent
        prompt = ''
        if channel in Repeater.message_buckets:
            prompt = Repeater.message_buckets[channel]
        for idx in range(iterations):
            Repeater.message_buckets[channel] = r.send_message(prompt)
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
        time.sleep(60)

