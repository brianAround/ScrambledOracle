import codecs
import configparser
import os.path
import smtplib
from email.mime.text import MIMEText
from twython import Twython
from twython.exceptions import TwythonError
from WordChain import *
from WordChainScribe import Scribe
import SequenceAlignment
import TextVisualizer


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

        # other attributes
        self.abbreviations = {}
        self.articles = {}
        self.banned_words = ['nigger']
        self.character_limit = 280
        self.is_new_build = False
        self.is_verbose = False
        self.last_tweet_id = 0
        self.last_tweet_message = ''
        self.long_tweet_as_image = False
        self.max_percent = 1 / 2
        self.max_twitter_char = 280
        self.prompt_reset = False
        self.tweet_queue_path = os.path.join('datafile', 'tweet_queue.txt')
        self.word_counts = {}

        # bot configuration
        self.config = None
        self.announce_new_build = False
        self.bot_name = 'Southern Oracle'
        self.depth = 1
        self.filename = "Leftovers.txt.map"
        self.hashtags = []
        self.prompt_filter_filename = None
        self.prompt_filter = None
        self.regenerate = 'None'
        self.source_subdirectory = ''
        self.use_source_as_hashtag = True

        # twitter configuration
        self.app_key = None
        self.app_secret = None
        self.acct_key = None
        self.acct_secret = None
        self.twitter_handle = '@SouthernOracle4'

        # automated configuration
        self.configure_from_file(config_file)
        self.abbreviations = self.load_dictionary('KnownAbbreviations.txt')
        self.articles = self.load_dictionary('SearchIgnoreList.txt')

    def configure_from_file(self, config_file):
        if os.path.isfile(config_file):
            self.config = configparser.ConfigParser()
            self.config.read(config_file)
            bot_info = self.config['bot_info']
            self.filename = bot_info['markov_map']
            self.depth = int(bot_info['depth'])
            self.regenerate = bot_info['regenerate']
            self.source_subdirectory = bot_info['source']
            self.bot_name = bot_info['name']
            twit_config = self.config['twitter']
            self.app_key = twit_config['app_key']
            self.app_secret = twit_config['app_secret']
            self.acct_key = twit_config['acct_key']
            self.acct_secret = twit_config['acct_secret']
            if 'acct_handle' in twit_config:
                self.twitter_handle = twit_config['acct_handle']

            if 'prompt_filter' in self.config['bot_info']:
                self.prompt_filter_filename = self.config['bot_info']['prompt_filter']
            if 'hashtags' in self.config['bot_info']:
                self.hashtags = self.config['bot_info']['hashtags'].split()
            if 'announce_new_build' in self.config['bot_info']:
                self.announce_new_build = (self.config['bot_info']['announce_new_build'] == 'True')

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
                work_line = line.strip()
                if '\t' in work_line:
                    bucket_key, bucket_value = work_line.split('\t')
                    result[bucket_key] = bucket_value
                else:
                    result[line.strip()] = True
        return result

    def create_name_file(self, filename: str):
        name_list = []

        self.chain.index_terms()
        # identify the possessive 's, use adjacency to that
        pos_s_id = self.chain.words["'s"]['id']

        # identify the "said" adjacency
        said_ids = [self.chain.words[term]['id']
                    for term in self.chain.word_list
                    if term.lower() in ['said', 'asked', 'yelled', 'whispered']]
        for word in [item for item in self.chain.words
                     if len(item) > 1 and item[0].isupper() and item[1].islower()]:
            score = 1  # grant 1 for starting with a capital letter
            word_id = self.chain.words[word]['id']
            for prefix in self.chain.words[word]['nodes']:
                for idx in range(len(prefix)):
                    if prefix[idx] == word_id:
                        if idx < len(prefix) - 1 and prefix[idx + 1] == pos_s_id:
                            score += 1  # add one for being shown as possessive.
                        if idx > 0 and prefix[idx - 1] in said_ids:
                            score += 1
                        if idx < len(prefix) - 1 and prefix[idx + 1] in said_ids:
                            score += 1
            if 'NNP' in self.chain.words[word]['pos']:
                score += 1

                # if 'said' in self.chain.words_lower:
                # adj_nodes = self.chain.find_word_adjacent_nodes("said", word, same_case=False, same_order=False)
                # score += len(adj_nodes) // 2
            if score > 2 * self.chain.depth:
                name_list.append(word)
        with open(filename, 'w') as file_handle:
            for name in name_list:
                file_handle.write(name + '\n')

    def message_is_okay(self, message, passages, prompt, is_verbose=False):
        is_okay = True
        minimum_length = 50
        minimum_passages = 2
        errors = []
        if message[0] not in WordChain.capitals and message[0] not in '"-':
            errors.append('The first character is not capitalized.')
        if message[-1] not in '.!?"\'':
            errors.append("The message doesn't end with a sentence terminator.")
        if len(message) > self.character_limit:
            errors.append('The message exceeds ' + str(self.character_limit) + ' characters.')
        if len(message) < 50:
            errors.append("The message is less than " + str(minimum_length) + " characters long.")
        prime_source_len = self.get_primary_source_ratio(passages)
        if prime_source_len > self.max_percent:
            errors.append("The message consists of " + str(prime_source_len * 100) +
                          "% nodes from a single source, more than " + str(self.max_percent * 100) + "% limit.")
        if len(passages) < minimum_passages:
            errors.append("There are fewer than " + str(minimum_passages) + " passages used in this message.")
        for block_word in self.banned_words:
            if block_word in message.lower():
                errors.append("Message contains banned word: " + block_word)
        if message.lower() == prompt.lower():
            errors.append("The message is the same as the prompt.")
        elif self.strip_hash_tags(message) in self.sent_messages:
            errors.append("The message is identical to a previous message.")
        else:
            if len(prompt) > minimum_length:
                seq_align = SequenceAlignment.get_alignment(message, prompt)
                raw_compare = 'Seq Align Score: ' + str(seq_align['score']) + ' "' + "".join(
                    seq_align['result_1']) + '/' + "".join(seq_align['result_2']) + '"'
                if is_verbose and len(errors) == 0:
                    print("Messg:" + "".join(seq_align['result_1']))
                    print("Prmpt:" + "".join(seq_align['result_2']))
                    print(raw_compare)
                if seq_align['score'] < len(prompt) + len(message):
                    errors.append('Message too similar to prompt. ' + raw_compare)
        if len(errors) > 0:
            is_okay = False
            if is_verbose:
                print("Rejecting completed message:", message)
                print("Reasons:", errors)
        return is_okay

    def get_message(self, prompt="", passages=None, print_passages=True, char_limit=None):
        if self.is_verbose:
            print("running get_message for prompt '" + prompt + "'")
        if passages is None:
            passages = []
        if self.chain is None:
            self.initialize_chain()
        if char_limit is None:
            char_limit = self.character_limit
        print_details = False
        attempts = 1
        sources = []
        prompt = self.apply_prompt_filter(prompt)
        response = self.chain.build_message(char_limit=char_limit, prompt=prompt, sources=sources)
        new_passages = self.chain.identify_passages(sources, 2)
        # prime_source_len = self.get_primary_source_ratio(new_passages)
        is_valid = self.message_is_okay(response, passages=new_passages, prompt=prompt, is_verbose=print_details)
        while not is_valid:
            sources = []
            if attempts > 10000:
                prompt = self.select_new_prompt()
                attempts = 0
            response = self.chain.build_message(char_limit=char_limit, prompt=prompt, sources=sources)
            new_passages = self.chain.identify_passages(sources, 2)
            is_valid = self.message_is_okay(response, passages=new_passages, prompt=prompt, is_verbose=print_details)
            attempts += 1

        response = response.replace('" "', '"\n\n"')

        if print_passages:
            print("----------")
            for entry in new_passages:
                print(self.chain.render_message_from_path(self.chain.find_passage_nodes(entry)))
                print(entry)
            print("----------")
        passages += new_passages
        self.prompt_reset = self.prompt_reset or self.chain.prompt_reset
        return response

    def apply_prompt_filter(self, prompt):
        if self.prompt_filter is not None:
            prompt_items = prompt.split()
            prompt = []
            for word in prompt_items:
                if word in self.prompt_filter:
                    prompt.append(word)
            if len(prompt) == 0:
                prompt.append(self.select_new_prompt())
            prompt = " ".join(prompt)
        return prompt

    @staticmethod
    def skim_hash_tags(message, preserve_inline_hashtags=True):
        result = {'text': [], 'hashtags': []}
        words = message.split()
        tag_run = 0
        for idx in range(len(words)):
            word = words[idx]
            if word[0] == '#':
                result['hashtags'].append(word)
                tag_run += 1
            else:
                if len(result['text']) > 0 and tag_run > 0 and preserve_inline_hashtags:
                    tag_count = len(result['hashtags'])
                    for tag in result['hashtags'][tag_count - tag_run: tag_count]:
                        result['text'].append(tag)
                tag_run = 0
                result['text'].append(word)
        result['text'] = " ".join(result['text'])
        return result

    @staticmethod
    def strip_hash_tags(message):
        result = message
        words = message.split()
        for word in words:
            if word[0] == '#':
                result = result.replace(word, '')
        return result.strip()

    def select_new_prompt(self):
        self.prompt_reset = True
        prompt = ""
        if self.prompt_filter is not None and len(self.prompt_filter) > 0:
            prompt = [word for word in self.prompt_filter][random.randint(0, len(self.prompt_filter) - 1)]
        return prompt

    def initialize_chain(self):
        target_file = self.filename
        self.chain = WordChain()
        self.chain.depth = self.depth
        Scribe.read_map(target_file, chain=self.chain)
        if type(self.prompt_filter_filename) is str and self.prompt_filter_filename != '':
            if not os.path.isfile(self.prompt_filter_filename):
                self.create_name_file(self.prompt_filter_filename)
            self.prompt_filter = self.read_filter_list(self.prompt_filter_filename)

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
        if self.is_verbose:
            print("running send_message for prompt '" + prompt + "'")
        passages = []
        message = self.get_message(prompt, passages)
        self.sent_messages[message] = True
        source_hashtag = []
        source_hashtag = self.get_source_hashtag(passages, source_hashtag)
        message = self.add_hashtag(message, additional_hashtags=source_hashtag)

        while '" "' in message and len(message) < self.max_twitter_char - 1:
            message = message.replace('" "', '"\n\n"', 1)

        if self.announce_new_build and self.is_new_build:
            self.send_build_announcement()
            self.is_new_build = False

        twit_id = self.send_tweet(message)
        if twit_id > 0:
            self.send_passages_email(message, passages, twit_id)
        return message

    def get_source_hashtag(self, passages, source_hashtag):
        if self.use_source_as_hashtag:
            primary_source = self.get_primary_source([passages])
            source_name = primary_source[0][0]
            source_name = ''.join([ch for ch in source_name if ch.isalnum()])
            source_hashtag = ['#' + source_name]
        return source_hashtag

    def send_reply(self, original_tweet_id=0, prompt=""):
        if self.is_verbose:
            print("running send_reply for tweet_id " + str(original_tweet_id) + " with prompt '" + prompt + "'")
        if original_tweet_id == 0:
            return self.send_message(prompt)

        # I have two thoughts here.
        # First: It may be nice that if the prompt is thrown out or fundamentally recreated,
        #           it is not done as a reply, or is aborted.
        # Second: What if instead of selecting ONE message and trying to reply, we selected a list and the first one
        #           to generate a viable message gets the response instead.
        username = self.get_reply_users(original_tweet_id)[0]

        passages = []
        reply_limit = self.character_limit - len(username) - 1
        message = self.get_message(prompt, passages, char_limit=reply_limit)
        self.sent_messages[message] = True
        if self.announce_new_build and self.is_new_build:
            self.send_build_announcement()
            self.is_new_build = False
        if self.prompt_reset:
            message = self.add_hashtag(message)
            twit_id = self.send_tweet(message)
        else:
            message = username + ' ' + message
            message = self.add_hashtag(message)
            twit_id = self.send_tweet(message, respond_to_tweet=original_tweet_id)
        if twit_id > 0:
            self.send_passages_email(message, passages, twit_id)
        return message

    def get_reply_users(self, original_tweet_id, posted_user_only=True):
        target_message = self.get_tweet(original_tweet_id)
        username = []
        if target_message is not None:
            username = ['@' + target_message['user']['screen_name']]
            if not posted_user_only:
                mentioned = ['@' + user_info['screen_name'] for user_info in target_message['entities']['user_mentions']]
                username.extend([screen_name for screen_name in mentioned if screen_name != self.twitter_handle])
        return username



    def send_build_announcement(self):
        build_time = time.time()
        if os.path.isfile(self.filename):
            build_time = os.path.getmtime(self.filename)

        build_message = self.bot_name + " rebuilt " + time.ctime(build_time)
        build_message += '\n' + self.chain.get_chain_description()
        self.send_tweet(build_message)

    def send_tweet(self, message, respond_to_tweet=0):
        twit_id = 0
        last_twit_id = 0
        try:
            twitter = self.get_twitter_client()
            if len(message) > self.max_twitter_char and self.long_tweet_as_image:
                clean_message = self.skim_hash_tags(message)
                image_path = TextVisualizer.image_file_path_from_text(clean_message['text'])
                image = open(image_path, 'rb')
                img_response = twitter.upload_media(media=image)
                caption = " ".join(clean_message['hashtags'])
                if respond_to_tweet == 0:
                    twit_response = twitter.update_status(status=caption, media_ids=[img_response['media_id']])
                else:
                    twit_response = twitter.update_status(status=caption, in_reply_to_status_id=respond_to_tweet,
                                                          media_ids=[img_response['media_id']])
                twit_id = twit_response['id']
                print(time.ctime(int(time.time())), self.bot_name + ' Tweeted as Image:', message)
            else:
                seq = self.get_message_sequence(message, self.max_twitter_char)
                for message_part in seq:
                        if twit_id == 0:
                            if respond_to_tweet == 0:
                                twit_response = twitter.update_status(status=message_part)
                            else:
                                twit_response = twitter.update_status(status=message_part,
                                                                      in_reply_to_status_id=respond_to_tweet)
                            last_twit_id = twit_response['id']
                            twit_id = last_twit_id

                        else:
                            twit_response = twitter.update_status(status=message_part, in_reply_to_status_id=last_twit_id)
                            last_twit_id = twit_response['id']
                        print(time.ctime(int(time.time())), self.bot_name + ' Tweeted:', message_part)
        except TwythonError as twy_err:
            print(type(twy_err))
            print(twy_err.args)
            print('Message attempted: "' + message + '"')
            if 'Status is a duplicate' not in twy_err.msg:
                self.add_tweet_to_queue(message_part, respond_to_tweet)
            twit_id = 0
            last_twit_id = 0
        self.last_tweet_id = twit_id
        self.last_tweet_message = message
        return twit_id

    def get_twitter_client(self):
        twitter = Twython(self.app_key, self.app_secret, self.acct_key, self.acct_secret)
        return twitter

    def add_tweet_to_queue(self, message_part, respond_to_tweet):
        with open(self.tweet_queue_path, mode='a+') as queue_file:
            queue_file.write(self.bot_name + '\t')
            queue_file.write(str(respond_to_tweet) + '\t')
            queue_file.write(message_part.replace('\n', '<newline />') + '\n')

    def get_tweet_queue(self, use_name=None):
        tweet_queue = []
        if use_name is None:
            use_name = self.bot_name
        with open(self.tweet_queue_path, mode='r') as queue_file:
            for line in queue_file.readlines():
                values = line.strip().split('\t')
                if use_name == '' or values[0] == use_name:
                    queue_item = {'bot_name': values[0],
                                  'reply_to_tweet': int(values[1]),
                                  'message': values[2].replace('<newline />', '\n').replace('<tab />', '\t')}
                    tweet_queue.append(queue_item)
        return tweet_queue

    def write_tweet_queue(self, tweet_queue):
        with open(self.tweet_queue_path, mode='w') as queue_file:
            for queue_item in tweet_queue:
                queue_file.write(queue_item['bot_name'] + '\t')
                queue_file.write(str(queue_item['reply_to_tweet']) + '\t')
                queue_file.write(queue_item['message'].replace('\n', '<newline />').replace('\t', '<tab />') + '\n')

    def get_tweet(self, tweet_id):
        raw_tweet = [None]
        try:
            twitter = self.get_twitter_client()
            raw_tweet = twitter.lookup_status(id=tweet_id, tweet_mode='extended')
        except TwythonError as twy_err:
            print(type(twy_err))
            print(twy_err.args)
        return raw_tweet[0]

    @staticmethod
    def get_message_sequence(src_text, max_length=280):
        seq = []
        if len(src_text) > max_length:
            # for now just make it split in half, but reserve 6 characters
            # in each sequence for " 11/20"
            allow_length = max_length - 6
            parts = TextVisualizer.split_by_width(src_text, allow_length)
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

    def add_hashtag(self, message, additional_hashtags=None):
        candidates = self.hashtags[:]
        if additional_hashtags is not None:
            candidates.extend(additional_hashtags)
        if len(candidates) > 0:
            use_hashtag = candidates[0]
            if len(candidates) > 1:
                use_hashtag = candidates[random.randint(0, len(candidates) - 1)]
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
                full_passage = self.wrap_a_substring(full_passage, passage[5],
                                                     '<strong>',
                                                     '</strong>')
                msg += "<li><strong>&quot;" + passage[5] + "&quot;</strong> - from source: "
                msg += "<strong><em>" + self.clean_source(passage[0]) + "</em></strong> "
                msg += "at position " + str(passage[3]) + "<br \>\n"
                msg += "<strong>Full passage:</strong> <blockquote><em>&quot;" + full_passage + \
                       "&quot;</em></blockquote></li>\n"
                # print(full_passage)
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
            # else:
            # open(outfile + '.srcmap', 'w', encoding="utf-8")
            filename = os.path.join('tweets', 'Tweet' + str(tweet_id) + '.htm')
            with open(filename, 'w', encoding='utf-8') as f_handle:
                f_handle.write(msg)
        except ValueError as err:
            print("Value Error on email send:", err)
            pass

    # def write_passages_data(self, message, passages, tweet_id):
        # write tweet_id
        # write message (remove newline characters)

        # for passage in passages:
            # full_passage = self.chain.render_message_from_path(self.chain.find_passage_nodes(passage))
            # write position_id
            # write clean source - self.clean_source(passage[0])
            # write source position. - str(passage[3])
            # write passage text - passage(5)
            # write full_passage text - self.chain.render_message_from_path(self.chain.find_passage_nodes(passage))

    @staticmethod
    def clean_source(source_text):
        working = source_text.replace('.txt', '')
        last_slash = max(working.find("/"), working.find("\\"))
        while last_slash > -1:
            working = working[last_slash + 1:]
            last_slash = max(working.find("/"), working.find("\\"))
        working = working.replace("DW 0", "Discworld #").replace("#0", "#")
        result = []
        for idx in range(len(working)):
            if working[idx].isupper() and idx > 0:
                result.append(" ")
            result.append(working[idx])
        if result[0].islower():
            result[0] = result[0].upper()
        if result[-1] == '"':
            result.pop()
        return "".join(result)

    @staticmethod
    def wrap_a_substring(source_text, subtext, prefix, suffix):
        align = SequenceAlignment.get_alignment(source_text, subtext, penalty_blank=5)
        prefix_idx = align['match_starts_in_1']
        suffix_idx = align['match_ends_in_1'] + 1
        if suffix_idx - prefix_idx > len(subtext) + 5:
            suffix_idx = prefix_idx + len(subtext) + 1

        return source_text[:prefix_idx] + prefix + source_text[prefix_idx:suffix_idx] +\
            suffix + source_text[suffix_idx:]
