import codecs
import configparser
import os.path
import smtplib
from email.mime.text import MIMEText
from twython import Twython
from twython.exceptions import TwythonError
from WordChain import *
from WordChainScribe import Scribe


def find_add_item_index(item, item_list):
    item_index = -1
    for i in range(len(item_list)):
        if item_list[i] == item:
            item_index = i
            break
    if item_index == -1:
        item_index = len(item_list)
        item_list.append(item)
    return item_index


class Oracle:

    sent_messages = {}

    def __init__(self, config_file='oracle.ini'):
        self.chain = None
        self.mchain = None
        self.starters = []
        self.data_refresh_time = 43200
        self.depth = 1
        self.word_counts = {}
        self.filename = "Leftovers.txt.map"
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        self.filename = self.config['bot_info']['markov_map']
        self.depth = int(self.config['bot_info']['depth'])
        self.abbreviations = self.load_dictionary('KnownAbbreviations.txt')
        self.articles = self.load_dictionary('SearchIgnoreList.txt')
        self.max_percent = 1/2
        self.regenerate = self.config['bot_info']['regenerate']
        self.source_subdirectory = self.config['bot_info']['source']
        self.prompt_filter = None
        if 'prompt_filter' in self.config['bot_info']:
            self.prompt_filter = self.config['bot_info']['prompt_filter']
        self.hashtags = []
        if 'hashtags' in self.config['bot_info']:
            self.hashtags = self.config['bot_info']['hashtags'].split()
        # self.initialize_chain()
        self.character_limit = 280

    @staticmethod
    def one_word_less(text):
        words = text.split()
        if len(words) == 1:
            return ''
        return ' '.join(words[:len(words) - 1])

    @staticmethod
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
                result[line] = True
        return result

    def get_message(self, prompt="", passages=None, print_passages=True):
        if passages is None:
            passages = []
        if self.chain is None:
            self.initialize_chain()
        attempts = 1
        sources = []
        if self.prompt_filter is not None:
            prompt_items = prompt.split()
            prompt = []
            for word in prompt_items:
                if word in self.prompt_filter:
                    prompt.append(word)
            if len(prompt) == 0:
                prompt.append(self.select_new_prompt())
            prompt = " ".join(prompt)
        response = self.chain.build_message(char_limit=self.character_limit, prompt=prompt, sources=sources)
        # response = self.build_message(char_limit=140, prompt=prompt,sources=sources)
        new_passages = self.chain.identify_passages(sources, 2)
        # new_passages = self.identifyPassages(sources, 2)
        prime_source_len = self.get_primary_source_ratio(new_passages)
        while self.character_limit < len(response) or len(response) < 50 or response[len(response) - 1] not in "?!." \
                or response.lower() == prompt.lower() \
                or self.strip_hash_tags(response) in self.sent_messages \
                or prime_source_len > self.max_percent \
                or 'nigger' in response:
            sources = []
            if response == prompt or response in self.sent_messages or attempts > 1000:
                prompt = self.select_new_prompt()
                attempts = 0
            response = self.chain.build_message(char_limit=self.character_limit, prompt=prompt, sources=sources,
                                                )
            new_passages = self.chain.identify_passages(sources, 2)
            prime_source_len = self.get_primary_source_ratio(new_passages)
            attempts += 1

        if print_passages:
            print("----------")
            for entry in new_passages:
                print(self.chain.render_message_from_path(self.chain.find_passage_nodes(entry)))
                print(entry)
            print("----------")
        passages += new_passages
        return response

    def strip_hash_tags(self, message):
        result = message
        words = message.split()
        for word in words:
            if word[0] == '#':
                result = result.replace(word, '')
        return result.strip()

    def select_new_prompt(self):
        prompt = ""
        if self.prompt_filter is not None and len(self.prompt_filter) > 0:
            prompt = [word for word in self.prompt_filter][random.randint(0, len(self.prompt_filter) - 1)]
        return prompt

    def initialize_chain(self):
        target_file = self.filename
        self.chain = WordChain()
        self.chain.depth = self.depth
        Scribe.read_map(target_file, chain=self.chain)
        if type(self.prompt_filter) is str:
            self.prompt_filter = self.read_filter_list(self.prompt_filter)

    @staticmethod
    def get_primary_source_ratio(passages):
        ps = 0
        tot = 1
        for entry in passages:
            ps = max(entry[2], ps)
            tot = max(entry[1] + entry[2], tot)
        return ps * 10000 // tot / 10000

    @staticmethod
    def get_primary_source(passages):
        if len(passages) > 0:
            biggest = passages[0]
            for entry in passages:
                if entry[2] > biggest[2]:
                    biggest = entry
            return biggest
        else:
            return ["", 0, 0, 0, 0, '']

    def read_filter_list(self, filename):
        prompt_filter = {}
        if os.path.isfile(filename):
            with open(filename, mode='r') as ff:
                for line in ff:
                    word = line.strip()
                    if word in self.chain.words:
                        prompt_filter[word] = True
        return prompt_filter

    def send_message(self, prompt=""):
        twit_config = self.config['twitter']
        app_key = twit_config['app_key']
        app_secret = twit_config['app_secret']
        acct_key = twit_config['acct_key']
        acct_secret = twit_config['acct_secret']

        twitter = Twython(app_key, app_secret, acct_key, acct_secret)
        passages = []
        message = self.get_message(prompt, passages)
        self.sent_messages[message] = True
        message = self.add_hashtag(message)
        seq = self.get_message_sequence(message, 140)
        twit_id = 0
        for message_part in seq:
            try:
                if twit_id == 0:
                    twit_response = twitter.update_status(status=message_part)
                    twit_id = twit_response['id']
                    self.send_passages_email(message, passages, twit_id)
                else:
                    twit_response = twitter.update_status(status=message_part, in_reply_to_status_id=twit_id)
                    twit_id = twit_response['id']
                print(time.ctime(int(time.time())), self.config['bot_info']['name'] + ' Tweeted:', message_part)
            except TwythonError as twy_err:
                print(type(twy_err))
                print(twy_err.args)
                print('Message attempted: "' + message + '"')
        return message

    @staticmethod
    def get_message_sequence(src_text, max_length=140):
        seq = []
        if len(src_text) > max_length:
            # for now just make it split in half, but reserve 6 characters
            # in each sequence for " 11/20"
            allow_length = max_length - 6
            parts = Oracle.split_by_width(src_text, allow_length)
            plen = len(parts)
            for pidx in range(plen):
                seq.append(str(pidx + 1) + '/' + str(plen) + ') ' + parts[pidx])
        else:
            seq.append(src_text)
        return seq

    @staticmethod
    def split_by_width(src_text, allow_length, try_balance=True):
        parts = []
        partsizes = []
        words = src_text.split()
        if try_balance:
            midword = int(len(words) / 2)
            parts.append(words[:midword])
            partsizes.append(sum([len(w) for w in parts[0]]) + len(parts[0]))
            parts.append(words[midword:])
            partsizes.append(sum([len(w) for w in parts[1]]) + len(parts[1]))
        else:
            parts.append(words)
            partsizes.append(sum([len(w) for w in parts[0]]) + len(parts[0]))

        while max(partsizes) > allow_length:
            for widx in range(len(parts)):
                if partsizes[widx] > allow_length:
                    if widx > 0 and partsizes[widx - 1] < allow_length - len(parts[widx][0]):
                        # move to previous part
                        move_text = parts[widx].pop(0)
                        parts[widx - 1].append(move_text)
                        partsizes[widx - 1] += len(move_text) + 1
                        partsizes[widx] -= len(move_text) + 1
                    else:
                        # move to next part
                        if len(parts) == widx + 1:
                            parts.append([])
                            partsizes.append(0)
                        move_text = parts[widx].pop()
                        parts[widx + 1].insert(0, move_text)
                        partsizes[widx + 1] += len(move_text) + 1
                        partsizes[widx] -= len(move_text) + 1
        return [" ".join(p) for p in parts]

    def add_hashtag(self, message):
        if len(self.hashtags) > 0:
            use_hashtag = self.hashtags[0]
            if len(self.hashtags) > 1:
                use_hashtag = self.hashtags[random.randint(0, len(self.hashtags) - 1)]
            if len(message) < self.character_limit - 1 - len(use_hashtag):
                message += ' ' + use_hashtag
        return message

    def send_passages_email(self, message, passages, tweet_id):
        try:
            email_config = self.config['email_account']
            msg = "<h3>" + self.config['bot_info']['name'] + "</h3>\n"
            msg += "<h4>The tweet with ID " + str(tweet_id) + ':</h4>\n\n'
            msg += '<blockquote><h3>' + message
            msg += "</h3></blockquote>\n\nIs composed of the following passages.\n"
            msg += "<ol>\n"
            for passage in passages:
                full_passage = self.chain.render_message_from_path(self.chain.find_passage_nodes(passage))
                msg += "<li><strong>&quot;" + passage[5] + "&quot;</strong> - from source: "
                msg += "<strong><em>" + passage[0] + "</em></strong> at postion " + str(passage[3]) + "<br \>\n"
                msg += "<strong>Full passage:</strong> <em>&quot;" + full_passage + "&quot;</em></li>\n"
            msg += "</ol>\n"

            msg += "<h3>Raw Data:</h3>"
            msg += '<pre>[Source, Position, Size, From Idx, To Idx, Text, Prefix(first)]\n'
            for passage in passages:
                msg += str(passage) + '\n'
            msg += "\n"
            if 'send_email' in email_config and email_config['send_email'] == 'True':
                server = smtplib.SMTP(email_config['smtp_server'], int(email_config['port']))
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(email_config['account_name'], email_config['password'])

                eml = MIMEText(msg)
                if len(message) > 70:
                    subject = self.config['bot_info']['name'] + ' Analysis: ' + message[:70] + '...'
                else:
                    subject = self.config['bot_info']['name'] + ' Analysis: ' + message
                eml['Subject'] = subject
                eml['From'] = email_config['account_name']
                eml['To'] = email_config['send_email_to']
                server.send_message(eml)
            else:
                # open(outfile + '.srcmap', 'w', encoding="utf-8")
                filename = os.path.join('tweets', 'Tweet' + str(tweet_id) + '.htm')
                with open(filename, 'w', encoding='utf-8') as f_handle:
                    f_handle.write(msg)
        except ValueError as err:
            print("Value Error on email send:", err)
            pass

