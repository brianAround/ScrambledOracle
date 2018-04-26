import codecs
import configparser
import os
import random
import string
import time
import nltk
from WordChain import WordChain, full_stop_beats
from Oracle import Oracle


class ChainLinker:

    def __init__(self, config_file='oracle.ini'):
        self.chain = None
        self.mchain = None
        self.starters = []
        self.data_refresh_time = 10 # 43200
        self.depth = 1
        self.word_counts = {}
        self.filename = "Leftovers.txt.map"
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        self.filename = self.config['bot_info']['markov_map']
        self.depth = int(self.config['bot_info']['depth'])
        self.abbreviations = Oracle.load_dictionary('KnownAbbreviations.txt')
        self.articles = Oracle.load_dictionary('SearchIgnoreList.txt')
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

    def initialize_chain(self):
        target_file = self.filename
        if not os.path.isfile(target_file) or os.path.getmtime(target_file) < time.time() - self.data_refresh_time:
            if self.regenerate is not None and self.regenerate.startswith('select'):
                source_count = int(self.regenerate.split()[1])
                source_folder = os.path.join('sources', self.source_subdirectory)
                self.regenerate_markov_chain(source_count, source_folder, target_file)
        self.chain = WordChain()
        self.chain.depth = self.depth
        # self.chain.read_map(target_file)

    def regenerate_markov_chain(self, source_count, source_folder, target_file):
        print("Regenerating markov chain with", source_count, "files from", source_folder)
        source_files = []
        dir_listing = self.get_relative_file_list(source_folder)
        for idx in range(source_count):
            new_file = dir_listing[random.randint(0, len(dir_listing) - 1)]
            while new_file in source_files and len(source_files) < len(dir_listing):
                new_file = dir_listing[random.randint(0, len(dir_listing) - 1)]
            source_files.append(new_file)
            if len(source_files) >= len(dir_listing):
                break
        print("Building markov chain from sources:", source_files)
        self.build_and_save_chain_from_list(source_files, depth=self.depth, target_filename=target_file)

    def get_relative_file_list(self, source_folder):
        file_listing = [f for f in os.listdir(source_folder) if f.endswith(".txt")]
        file_listing = [os.path.join(source_folder, f) for f in file_listing]
        file_listing = [f for f in file_listing if os.path.isfile(f)]
        return file_listing

    def build_and_save_chain_from_list(self, file_list, depth=2, target_filename="current.txt.map"):
        chain = self.build_chain_from_file_list(file_list, depth)
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

    def build_chain_from_file_list(self, file_list, depth=2):
        word_tally = {}
        for file_path in file_list:
            self.compile_word_tally(file_path, depth, word_tally)
        chain = self.convert_tally_to_chain(word_tally, depth)
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
                for entry in chain.mchain[key][0]:
                    target.write(str(entry[0] - prev_p) + '|"' + entry[1] + '"\t')
                    prev_p = entry[0]
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

    def compile_word_tally(self, file_path, depth, word_tally, use_pos_tags=True):
        last_beat = ""
        beat_list = []
        if len(word_tally) == 0:
            self.word_counts = {}
        file_size = min(32, os.path.getsize(file_path))
        quotes = []
        with open(file_path, 'rb') as f_enc:
            raw = f_enc.read(file_size)
            if raw.startswith(codecs.BOM_UTF8):
                encoding = 'utf-8-sig'
            else:
                encoding = 'utf-8'

        is_spoken = False
        is_starter = True
        current_speech = []
        source_beat = 0
        with open(file_path, 'r', encoding=encoding) as f_handle:
            if use_pos_tags:
                source_text = f_handle.readlines()
                source_text = source_text[3:]
                source_text = [line for line in source_text if line[0] != '#']
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
                            word_tally[last_beat][current_beat] += 1
                            word_tally[last_beat]['_is_spoken'] = is_spoken or word_tally[last_beat][
                                '_is_spoken']
                            word_tally[last_beat]['_source_text'].append(file_path)
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
            else:
                for line in f_handle:
                    line = line.strip()

                    if len(beat_list) == 0:
                        is_starter = True
                    if line == "" or line[0] == '#':
                        beat_stream = []
                        last_word = ""
                        is_spoken = False
                        last_of_quote = False
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
                                last_of_quote = False
                                quotes.append(' '.join(current_speech))
                                current_speech = []

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
    def convert_tally_to_chain(word_tally, depth=2):
        word_list = [key_word for key_word in word_tally]
        word_list.sort()
        parts_of_speech = []
        chain = WordChain()
        chain.depth = depth
        for key in word_list:
            is_spoken = word_tally[key]['_is_spoken']
            is_starter = word_tally[key]['_is_starter']
            source_text = word_tally[key]['_source_text']
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
            total = 0
            for key2 in word_tally[key]:
                if key2[0] != '_':
                    total += word_tally[key][key2] * 10000 // incidents / 10000
                    entry = [total, key2]
                    suffixes.append(entry)
            chain.mchain[key] = [suffixes, incidents, is_spoken, source_text, source_index, is_starter, parts_of_speech]
        return chain

    def set_chain(self, chain):
        if len(chain.mchain) > 0:
            self.chain = chain
            self.mchain = chain.mchain
            self.starters = chain.starters
            self.depth = chain.depth


notes = """Ideas for optimizing the file structure:
    Replace the words with numbers:
        Sort the terms in descending order of frequency, then assign numbers sequentially, to minimize space.
        Provide a term map as a separate file.
        Create a header row for all data files that includes a engine version and a date stamp.
    In .srcmap, enumerate sources to keep from repeating source name t1 times.
    In the header for the .srcmap add a listing for each source to enable more rich metadata.
    """