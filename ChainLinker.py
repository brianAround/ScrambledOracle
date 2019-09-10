import codecs
import configparser
import os
import random
import string
import time
import nltk
from WordChain import WordChain, full_stop_beats
from Oracle import Oracle
import TwitterTimeline


class ChainLinker:

    def __init__(self, config_file='oracle.ini'):
        self.config_file = config_file
        self.config = None
        self.chain = None
        self.mchain = None
        self.starters = []
        self.data_refresh_time = 43200
        self.file_rebuilt = False
        self.depth = 1
        self.regenerate = 'None'
        self.word_counts = {}
        self.filename = "Leftovers.txt.map"
        self.source_subdirectory = ''
        self.bot_name = ''
        self.app_key = ''
        self.app_secret = ''
        self.acct_key = ''
        self.acct_secret = ''
        self.twitter_handle = ''

        self.abbreviations = Oracle.load_dictionary('KnownAbbreviations.txt')
        self.articles = Oracle.load_dictionary('SearchIgnoreList.txt')
        self.max_percent = 1/2
        self.prompt_filter_filename = None
        self.prompt_filter = None
        self.learn_from_mentions = False
        self.verbose = False
        self.announce_new_build = False
        self.hashtags = []
        self.sources = []
        self.configure_from_file(self.config_file)

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
            if 'learn_from_mentions' in bot_info:
                self.learn_from_mentions = (bot_info['learn_from_mentions'] == 'True')

    def say(self, message):
        if self.verbose:
            print(message)

    def initialize_chain(self, prevent_timeout=False):
        target_file = self.filename
        self.file_rebuilt = False
        is_timed_out = False
        if not prevent_timeout:
            is_timed_out = (os.path.getmtime(target_file) < time.time() - self.data_refresh_time)
        if not os.path.isfile(target_file) or is_timed_out:
            self.regenerate_by_config(target_file)
        self.chain = WordChain()
        self.chain.depth = self.depth
        # self.chain.read_map(target_file)

    def regenerate_by_config(self, target_file=None):
        if self.regenerate is not None and self.regenerate.startswith('select'):
            if target_file is None:
                target_file = self.filename
            source_count = int(self.regenerate.split()[1])
            source_folder = os.path.join('sources', self.source_subdirectory)
            mention_lines = None
            if self.learn_from_mentions:
                mention_lines = self.get_mentions_text(self.twitter_handle.strip('@'))
            self.regenerate_markov_chain(source_count, source_folder, target_file, mention_lines)
            if self.prompt_filter is not None and type(self.prompt_filter) is str:
                # remove prompt filter file
                if os.path.isfile(self.prompt_filter):
                    os.remove(self.prompt_filter)

    def regenerate_markov_chain(self, source_count, source_folder, target_file, mention_lines=None):
        self.say("Regenerating markov chain with " + str(source_count) + " files from " + source_folder)
        source_files = []
        dir_listing = self.get_relative_file_list(source_folder)
        for idx in range(source_count):
            new_file = dir_listing[random.randint(0, len(dir_listing) - 1)]
            while new_file in source_files and len(source_files) < len(dir_listing):
                new_file = dir_listing[random.randint(0, len(dir_listing) - 1)]
            source_files.append(new_file)
            if len(source_files) >= len(dir_listing):
                break
        self.say("Building markov chain from sources:" + str(source_files))
        self.build_and_save_chain_from_list(source_files, depth=self.depth, target_filename=target_file,
                                            mention_lines=mention_lines)
        self.file_rebuilt = True

    @staticmethod
    def get_relative_file_list(source_folder):
        file_listing = [f for f in os.listdir(source_folder) if f.endswith(".txt")]
        file_listing = [os.path.join(source_folder, f) for f in file_listing]
        file_listing = [f for f in file_listing if os.path.isfile(f)]
        return file_listing

    def build_and_save_chain_from_list(self, file_list, depth=2, target_filename="current.txt.map", mention_lines=None):
        chain = self.build_chain_from_file_list(file_list, depth, mention_lines)
        self.write_chain(chain, target_filename)
        return chain

    def build_and_save_chain_from_directory(self, source_folder, depth=2, target_filename='current.txt.map'):
        file_listing = self.get_relative_file_list(source_folder)
        return self.build_and_save_chain_from_list(file_listing, depth=depth, target_filename=target_filename)

    def build_and_save_chain_from_file(self, file_path, depth=2, target_filename=None):
        if target_filename is None:
            target_filename = file_path + ".map"
        self.filename = target_filename
        chain = self.build_and_save_chain_from_list([file_path], depth=depth, target_filename=target_filename)
        return chain

    def build_chain_from_file_list(self, file_list, depth=2, mention_lines=None):
        word_tally = {}
        for file_path in file_list:
            self.compile_word_tally(file_path, depth, word_tally)
        if mention_lines is not None:
            self.stimulate_word_tally('Twitter', mention_lines, depth, word_tally)

        source_names = WordChain.normalize_text(file_list)
        src_map = {}
        for idx in range(len(file_list)):
            src_map[file_list[idx]] = source_names[idx]
        if len(mention_lines) > 0:
            src_map['Twitter'] = 'Twitter'
        chain = self.convert_tally_to_chain(word_tally, depth, src_map)
        self.set_chain(chain)
        return chain

    def write_chain(self, chain: WordChain, outfile):
        has_source_map = False
        self.filename = outfile

        with open(outfile, 'w', encoding="utf-8") as target:
            for key in chain.mchain:
                if not has_source_map and len(chain.mchain[key]) >= 5:
                    has_source_map = True
                target.write(key + "\t")
                target.write(str(chain.mchain[key][1]) + "\t")
                prev_p = 0
                item_list = []
                for entry in chain.mchain[key][0]:
                    new_item = (entry[0] - prev_p, entry[1])
                    item_list.append(new_item)
                    prev_p = entry[0]
                item_list.sort(key=lambda x: -1 * x[0])
                for entry in item_list:
                    target.write(str(entry[0]) + '|"' + entry[1] + '"\t')
                    # prev_p = entry[0]
                target.write("\n")

        if has_source_map:
            with open(outfile + '.srcmap', 'w', encoding="utf-8") as srcmap:
                # write the header row
                srcmap.write("SRCMAP|Engine:")
                srcmap.write(WordChain.engine_version + "Dev")
                srcmap.write("\n")
                """srcmap.write('{"name":"Sources", ')
                srcmap.write('"documents":[')
                doclist = {}"""
                for key in chain.mchain:
                    entry = chain.mchain[key]
                    if len(entry) >= 5:
                        srcmap.write(key + "\t")
                        srcmap.write(str(entry[2]) + "\t")
                        srcmap.write(str(entry[5]) + "\t")
                        for i in range(len(entry[3])):
                            srcmap.write('"' + entry[3][i] + '"|' + str(entry[4][i]) + "\t")
                        srcmap.write("\n")
            with open(outfile + '.posmap', 'w', encoding="utf-8") as posmap:
                for key in chain.mchain:
                    entry = chain.mchain[key]
                    if len(entry) >= 5:
                        posmap.write(key + "\t")
                        parts_of_speech = entry[6]
                        for pos in parts_of_speech:
                            posmap.write(str(pos) + "\t")
                        posmap.write("\n")

    @staticmethod
    def tag_text(source_text):
        # sentences = nltk.sent_tokenize(source_text)
        sentence = nltk.word_tokenize(source_text)
        return nltk.pos_tag(sentence)

    def get_mentions_text(self, username):
        mentions_filename = TwitterTimeline.get_mentions_filename(username)
        mentions = TwitterTimeline.get_mentions(self.config_file, username, mentions_filename)
        lines = []
        for tweet_id in mentions:
            tweet = mentions[tweet_id]
            if not tweet['is_retweet'] and tweet['reaction_status'] not in ['executed']\
                    and ' oracle: ' not in tweet['text'].lower():
                tweet_text = tweet['text']
                working_text = self.clean_tweet_text(tweet_text)
                lines.append(working_text)

        # print('Retrieved user mentions text:', lines)
        return lines

    def clean_tweet_text(self, tweet_text):
        working_text = []
        for term in tweet_text.split():
            if term[0] not in ('@', '#') and not term.lower().startswith("http"):
                working_text.append(term)
        return ' '.join(working_text)

    def stimulate_word_tally(self, source_name, lines, depth, word_tally, multiplier=10):
        self.say("Stimulating word tally with " + str(len(lines)) + " additional patterns.")
        self.add_lines_to_word_tally(depth, source_name, lines, word_tally, multiplier)

    def compile_word_tally(self, file_path, depth, word_tally, use_pos_tags=True, multiplier=1):
        self.say("Compiling word tally from " + file_path)
        file_size = min(32, os.path.getsize(file_path))
        with open(file_path, 'rb') as f_enc:
            raw = f_enc.read(file_size)
            if raw.startswith(codecs.BOM_UTF8):
                encoding = 'utf-8-sig'
            else:
                encoding = 'utf-8'

        is_spoken = False
        is_starter = True
        current_speech = []
        quotes = []
        source_beat = 0
        with open(file_path, 'r', encoding=encoding) as f_handle:
            self.sources.append(file_path)
            if use_pos_tags:
                source_text = f_handle.readlines()
                source_text = source_text[3:]
                source_text = [line for line in source_text if line[0] != '#']
                self.add_lines_to_word_tally(depth, file_path, source_text, word_tally, multiplier)
            else:
                for line in f_handle:
                    line = line.strip()

                    if len(beat_list) == 0:
                        is_starter = True
                    if line == "" or line[0] == '#':
                        is_spoken = False
                        if len(current_speech) > 0:
                            quotes.append(' '.join(current_speech))
                            current_speech = []

                        last_beat = ""
                        beat_list = []
                    else:
                        beat_stream = line.strip().split()

                        for idx in range(len(beat_stream)):
                            on_deck = []
                            last_of_quote = False
                            if not is_spoken and beat_stream[idx][0] in '"“`\'':
                                is_spoken = True
                                beat_stream[idx] = beat_stream[idx][1:]
                            if is_spoken and len(beat_stream[idx]) > 0:
                                if beat_stream[idx][len(beat_stream[idx]) - 1] in '"”\'':
                                    last_of_quote = True
                                    beat_stream[idx] = beat_stream[idx][:len(beat_stream[idx]) - 1]
                            bbeat = beat_stream[idx].strip('"')
                            if len(bbeat) > 0:
                                if bbeat[0] in string.punctuation:
                                    on_deck.append(bbeat[0])
                                    bbeat = bbeat[1:]
                                if len(bbeat) > 0 and bbeat[len(bbeat) - 1] in string.punctuation:
                                    on_deck.append(bbeat[:len(bbeat) - 1])
                                    on_deck.append(bbeat[len(bbeat) - 1])
                                else:
                                    on_deck.append(bbeat)
                                for current_beat in on_deck:
                                    if is_spoken and len(current_beat) > 0:
                                        if current_beat[len(current_beat) - 1] in '"”\'' and not last_of_quote:
                                            last_of_quote = True
                                            current_beat = current_beat[:len(current_beat) - 1]
                                        current_speech.append(current_beat)
                                    if current_beat != "":
                                        source_beat += 1
                                        if current_beat not in self.word_counts:
                                            self.word_counts[current_beat] = 0
                                        self.word_counts[current_beat] += 1
                                        if last_beat != "":
                                            self.add_sequence_to_tally(last_beat, is_starter, is_spoken, word_tally)
                                            if current_beat not in word_tally[last_beat]:
                                                word_tally[last_beat][current_beat] = 0
                                            word_tally[last_beat][current_beat] += 1
                                            word_tally[last_beat]['_is_spoken'] = is_spoken or word_tally[last_beat][
                                                '_is_spoken']
                                            word_tally[last_beat]['_source_text'].append(file_path)
                                            word_tally[last_beat]['_source_index'].append(source_beat)
                                            word_tally[last_beat]['_is_starter'] = is_starter or word_tally[last_beat][
                                                '_is_starter']
                                            if is_starter:
                                                self.starters.append(last_beat)
                                        while len(beat_list) >= depth:
                                            del beat_list[0]
                                            is_starter = False
                                        beat_list.append(current_beat)
                                        last_beat = " ".join(beat_list)
                                        if len(beat_list) > 1 and current_beat in full_stop_beats and beat_list[
                                                -2].lower() not in self.abbreviations:
                                            self.add_sequence_to_tally(last_beat, False, is_spoken, word_tally)
                                            word_tally[last_beat]['_source_text'].append(file_path)
                                            word_tally[last_beat]['_source_index'].append(source_beat + 1)
                                            beat_list = []
                                            last_beat = ""
                                            is_starter = True
                            if last_of_quote:
                                is_spoken = False
                                quotes.append(' '.join(current_speech))
                                current_speech = []

    def add_lines_to_word_tally(self, depth, source_name, source_text, word_tally, multiplier=1):
        last_beat = ""
        beat_list = []
        if len(word_tally) == 0:
            self.word_counts = {}
            self.sources = []
        is_spoken = False
        current_speech = []
        quotes = []
        source_beat = 0
        source_text = " ".join(source_text).strip('\n')
        sentences = nltk.sent_tokenize(source_text)
        sentences = [nltk.word_tokenize(sentence) for sentence in sentences]
        tagged_sentences = [nltk.pos_tag(sentence) for sentence in sentences]
        for sentence in tagged_sentences:
            is_starter = True
            for idx in range(len(sentence)):
                source_beat += 1
                current_beat = sentence[idx][0]
                current_pos = sentence[idx][1]
                if last_beat != "":
                    self.add_sequence_to_tally(last_beat, is_starter, is_spoken, word_tally)
                    if current_beat not in word_tally[last_beat]:
                        word_tally[last_beat][current_beat] = 0
                    word_tally[last_beat][current_beat] += multiplier
                    word_tally[last_beat]['_is_spoken'] = is_spoken or word_tally[last_beat][
                        '_is_spoken']
                    word_tally[last_beat]['_source_text'].append(source_name)
                    word_tally[last_beat]['_source_index'].append(source_beat)
                    word_tally[last_beat]['_is_starter'] = is_starter or word_tally[last_beat][
                        '_is_starter']
                    if last_pos not in word_tally[last_beat]['_pos']:
                        word_tally[last_beat]['_pos'].append(last_pos)
                    if is_starter:
                        self.starters.append(last_beat)
                while len(beat_list) >= depth:
                    del beat_list[0]
                    is_starter = False
                beat_list.append(current_beat)
                last_beat = " ".join(beat_list)
                last_pos = current_pos
            self.add_sequence_to_tally(last_beat, False, is_spoken, word_tally)
            if last_pos not in word_tally[last_beat]['_pos']:
                word_tally[last_beat]['_pos'].append(last_pos)
            last_beat = ""
            beat_list = []

    @staticmethod
    def add_sequence_to_tally(last_beat, is_starter, is_spoken, word_tally):
        if last_beat not in word_tally:
            word_tally[last_beat] = {}
            word_tally[last_beat]['_is_spoken'] = is_spoken
            word_tally[last_beat]['_source_text'] = []
            word_tally[last_beat]['_source_index'] = []
            word_tally[last_beat]['_is_starter'] = is_starter
            word_tally[last_beat]['_pos'] = []

    @staticmethod
    def convert_tally_to_chain(word_tally, depth=2, src_map: dict=None):
        word_list = [key_word for key_word in word_tally]
        word_list.sort()
        parts_of_speech = []
        chain = WordChain()
        # sources_clean = chain.normalize_text(self.sources)
        chain.depth = depth
        for key in word_list:
            is_spoken = word_tally[key]['_is_spoken']
            is_starter = word_tally[key]['_is_starter']
            if src_map is None:
                source_text = word_tally[key]['_source_text']
            else:
                source_text = [src_map[filename] for filename in word_tally[key]['_source_text']]
            source_index = word_tally[key]['_source_index']
            if '_pos' in word_tally[key]:
                parts_of_speech = word_tally[key]['_pos']
            incidents = 0
            suffixes = []
            for key2 in word_tally[key]:
                if key2[0] != '_':
                    incidents += word_tally[key][key2]
            if is_starter:
                chain.starters.append(key)
            for key2 in word_tally[key]:
                if key2[0] != '_':
                    total = word_tally[key][key2] * 10000 // incidents / 10000    # one day, just store the count
                    entry = [total, key2]
                    suffixes.append(entry)
            # although I want to use int values here, don't upset the apple cart just yet, sort the suffixes
            suffixes.sort(key=lambda x: -1 * x[0])
            # and then make it a cumulative list.
            total = 0
            for entry in suffixes:
                entry[0] += total
                total = entry[0]
            chain.mchain[key] = [suffixes, incidents, is_spoken, source_text, source_index, is_starter, parts_of_speech]
        return chain

    def set_chain(self, chain):
        if len(chain.mchain) > 0:
            self.chain = chain
            self.mchain = chain.mchain
            self.starters = chain.starters
            self.depth = chain.depth


    def reconstruct_tweet_passages(self, source_text):
        sentence = nltk.word_tokenize(self.clean_tweet_text(source_text))
        tagged = self.tag_text(sentence)

        if self.chain is None:
            self.initialize_chain(prevent_timeout=True)

        mpath = self.chain.find_path_for_tagged(tagged)
        sources = []
        for set_node in mpath:
            self.chain.append_node_sources(set_node, sources)

        passages = self.chain.identify_passages(sources)
        return passages

notes = """Ideas for optimizing the file structure:
    Replace the words with numbers:
        Sort the terms in descending order of frequency, then assign numbers sequentially, to minimize space.
        Provide a term map as a separate file.
        Create a header row for all data files that includes a engine version and a date stamp.
    In .srcmap, enumerate sources to keep from repeating source name t1 times.
    In the header for the .srcmap add a listing for each source to enable more rich metadata.
    """

