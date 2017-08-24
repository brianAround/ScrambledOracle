import codecs
import os
import os.path
import random
import string
import time
from StructTree import *


full_stop_beats = [".", "!", "?"]


class ChainNode:

    def __init__(self, word_id, prefix=[], is_starter=False, outbound=None, inbound=None):
        self.word_id = word_id
        self.prefix = prefix
        if len(self.prefix) == 0:
            self.prefix = tuple([word_id])
        self.is_starter = is_starter
        self.is_quote = False
        self.quantity = 0
        self.outbound = [] if outbound is None else outbound
        self.inbound = [] if inbound is None else inbound
        self.sources = []
        self.parts_of_speech = []



class WordChain:

    capitals = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def __init__(self):
        self.mchain = {}
        self.starters = []
        self.depth = 1
        self.nodes_by_prefix = {}
        self.nodes_by_id = {}
        self.grammer_templates = []
        self.words = {}
        self.word_list = []
        self.words_lower = {}
        self.abbreviations = {"mr", "mrs", "p.m", "a.m"}
        if os.path.isfile('KnownAbbreviations.txt'):
            self.abbreviations = self.load_dictionary("KnownAbbreviations.txt")
        self.articles = {"a", "but", "not", "one", "that", "the", "to"}
        if os.path.isfile('SearchIgnoreList.txt'):
            self.articles = self.load_dictionary('SearchIgnoreList.txt')

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

    def add_incident(self, prefix, suffix_text, count=1):
        parent = self.get_node_by_prefix(prefix)
        word_id = self.get_word_id(suffix_text)
        if len(prefix) == self.depth:
            new_prefix = prefix[1:] + (word_id, )
        else:
            new_prefix = prefix + (word_id, )
        old_size = parent.quantity
        new_size = old_size + count
        ratio = old_size / new_size
        add_p = count / new_size
        is_new = True
        child_node = self.get_node_by_prefix(new_prefix)
        for entry in parent.outbound:
            if entry[1].prefix == new_prefix:
                is_new = False
            entry[0] *= ratio
            if not is_new:
                entry[0] += add_p
        if is_new:
            new_entry = [1.0, child_node]
            parent.outbound.append(new_entry)
            child_node.inbound.append(parent)
        parent.quantity = new_size
        return child_node

    def add_expression(self, source_text):
        last_prefix = []
        beat_list = []
        lines = source_text.split("\n")
        is_starter = True
        for line in lines:
            if line.strip() == "":
                last_prefix = []
                beat_list = []
            else:
                beat_stream = self.convert_string_to_beats(line)
                for idx in range(len(beat_stream)):
                    current_beat = beat_stream[idx].strip('"')
                    new_node = None
                    if len(last_prefix) > 0:
                        last_node = self.get_node_by_prefix(last_prefix)
                        if not last_node.is_starter and is_starter:
                            last_node.is_starter = True
                            self.starters.append(last_prefix)
                        new_node = self.add_incident(last_prefix, current_beat)
                    if current_beat in full_stop_beats and len(last_prefix) != 0 and \
                            self.word_list[last_prefix[-1]].lower() not in self.abbreviations:
                        is_starter = True
                        last_prefix = []
                    else:
                        if new_node is not None:
                            if len(last_prefix) == self.depth:
                                is_starter = False
                            last_prefix = new_node.prefix
                        else:
                            word_id = self.get_word_id(current_beat)
                            if len(last_prefix) == 0:
                                last_prefix = (word_id, )
                            else:
                                if len(last_prefix) == self.depth:
                                    is_starter = False
                                    last_prefix = last_prefix[1:] + (word_id, )
                                else:
                                    last_prefix = last_prefix + (word_id, )
                                   
    def convert_string_to_beats(self, src):
        beat_stream = []
        for beat in src.strip().split():
            beat_stream.extend(self.splay_beat(beat))
        return beat_stream

    def splay_beat(self, beat_text):
        splayed = []
        first_word_idx = 0
        while beat_text[first_word_idx] in string.punctuation:
            splayed.append(beat_text[first_word_idx])
            first_word_idx += 1
        last_word_idx = len(beat_text) - 1
        while beat_text[last_word_idx] in string.punctuation:
            splayed.insert(first_word_idx, beat_text[last_word_idx])
            last_word_idx -= 1
        splayed.insert(first_word_idx, beat_text[first_word_idx:last_word_idx + 1])
        return splayed

    def convert_key_to_prefix(self, key, beats=[]):
        beats = key.split()
        if self.depth < len(beats):
            self.depth = len(beats)
        prefix = []
        word_id = -1
        for word in beats:
            word_id = self.get_word_id(word)
            prefix.append(word_id)
        return tuple(prefix)

    def convert_prefix_to_text(self, prefix):
        return " ".join([self.word_list[word_id] for word_id in prefix])

    def read_map(self, filepath, read_srcmap=True):
        with open(filepath, 'r', encoding='utf-8') as file_in:
            for line in file_in:
                values = line.strip().split('\t')
                key = values[0]
                beats = []
                prefix = self.convert_key_to_prefix(key, beats)
                word_id = prefix[-1]
                node = self.get_node_by_prefix(prefix)
                if not read_srcmap:
                    if beats[0][0] in WordChain.capitals:
                        node.is_starter = True
                node.quantity = int(values[1])
                total = 0
                for map_item in values[2:]:
                    new_path = map_item.strip().split('|', 1)
                    p = float(new_path[0])
                    total += p
                    next_word = new_path[1].strip('"')
                    next_word_id = self.get_word_id(next_word)
                    if len(prefix) < self.depth:
                        new_prefix = prefix + (next_word_id,)
                    else:
                        new_prefix = prefix[1:] + (next_word_id,)
                    dest_node = self.get_node_by_prefix(new_prefix)
                    dest_node.inbound.append(node)
                    node.outbound.append([total, dest_node])
        src_filepath = filepath + ".srcmap"
        if read_srcmap and os.path.isfile(src_filepath):
            self.read_sourcemap(src_filepath)
        pos_filepath = filepath + ".posmap"
        if os.path.isfile(pos_filepath):
            self.read_posmap(pos_filepath)
        for prefix in self.nodes_by_prefix:
            if self.nodes_by_prefix[prefix].is_starter:
                self.starters.append(prefix)
            
    def read_sourcemap(self, src_filepath):
        with open(src_filepath, 'r', encoding='utf-8') as file_in:
            for line in file_in:
                values = line.strip().split('\t')
                key = values[0]
                prefix = self.convert_key_to_prefix(key)
                if prefix not in self.nodes_by_prefix:
                    node = ChainNode(prefix[-1], prefix=prefix)
                    self.nodes_by_prefix[prefix] = node
                node = self.nodes_by_prefix[prefix]
                node.is_quote = values[1] == 'True'
                node.is_starter = values[2] == 'True'
                for i in range(3, len(values)):
                    text_file, text_index = values[i].split('|')
                    text_index = int(text_index)
                    entry = (text_file, text_index)
                    node.sources.append(entry)

    def read_posmap(self, src_filepath):
        with open(src_filepath, 'r', encoding='utf-8') as file_in:
            for line in file_in:
                values = line.strip().split('\t')
                key = values[0]
                prefix = self.convert_key_to_prefix(key)
                if prefix not in self.nodes_by_prefix:
                    node = ChainNode(prefix[-1], prefix=prefix)
                    self.nodes_by_prefix[prefix] = node
                node = self.nodes_by_prefix[prefix]
                node.parts_of_speech = []
                for i in range(1, len(values)):
                    this_part = values[i]
                    if this_part != "" and this_part not in node.parts_of_speech:
                        node.parts_of_speech.append(this_part)


    def get_word_id(self, word_text):
        if word_text not in self.words:
            self.words[word_text] = {'id': len(self.words), 'nodes': []}
            self.word_list.append(word_text)
            if len(self.words_lower) > 0:
                if word_text.lower() not in self.words_lower:
                    self.words_lower[word_text.lower()] = []
                self.words_lower[word_text.lower()] = word_text
        return self.words[word_text]['id']

    def get_node_by_prefix(self, prefix):
        if prefix not in self.nodes_by_prefix:
            new_node = ChainNode(prefix[-1], prefix)
            self.nodes_by_prefix[prefix] = new_node
        return self.nodes_by_prefix[prefix]

    def index_terms(self):
        if len(self.words_lower) == 0:
            for prefix in self.nodes_by_prefix:
                for word_id in prefix:
                    self.words[self.word_list[word_id]]['nodes'].append(prefix)
                    caseless = self.word_list[word_id].lower()
                    if caseless not in self.words_lower:
                        self.words_lower[caseless] = []
                    self.words_lower[caseless].append(self.word_list[word_id])
    
        
    def select_start_node(self, word_id_set=[], starters_only=False, time_limit=60):
        start_time = time.time()
        start_node = None
        if len(word_id_set) > 0:
            top_score = 0
            candidates = {}
            multiplier = 1
            for word_id in word_id_set:
                for prefix in self.words[self.word_list[word_id]]['nodes']:
                    if not starters_only or self.nodes_by_prefix[prefix].is_starter:
                        if prefix not in candidates:
                            candidates[prefix] = 0
                        candidates[prefix] += multiplier * len(self.word_list[word_id])
                        top_score = max(top_score, candidates[prefix])
                    if time_limit < time.time() - start_time:
                        break
                multiplier += 1
                if time_limit < time.time() - start_time:
                    break
            pick_list = [prefix for prefix in candidates if candidates[prefix] >= top_score // 2]
            if len(pick_list) > 1:
                start_node = pick_list[random.randint(0, len(pick_list) - 1)]
        if start_node is None:
            start_node = self.starters[random.randint(0, len(self.starters) - 1)]
            # print('start node selected randomly:', [self.word_list[widx] for widx in start_node])
        # else:
            # print('start node:', [self.word_list[widx] for widx in start_node])
        if isinstance(start_node, str):
            start_node = self.convert_key_to_prefix(start_node)
        if starters_only and len(start_node) > 1:
            start_node = start_node[:1]
        return self.nodes_by_prefix[start_node]


    def find_starter_paths(self, node: ChainNode, allow_hops=6, max_queue=200, time_limit=60, struct_tree:GrammarTree=None):
        start_time = time.time()
        result = []
        work_queue = [[node]]
        while len(work_queue) > 0:
            current = work_queue.pop(0)
            tail_node = current[-1]
            if tail_node.is_starter and self.word_list[tail_node.prefix[0]][0] in WordChain.capitals:

                grammar_list = []
                for idx in range(len(current) - 1, -1, -1):
                    if len(current[idx].parts_of_speech) > 0:
                        grammar_list.append(current[idx].parts_of_speech[0])
                if struct_tree is not None:
                    if struct_tree.get_size(grammar_list) > 0:
                        result.append(current)
                else:
                    result.append(current)
            elif len(current) <= allow_hops:
                for parent in tail_node.inbound:
                    if len(work_queue) >= max_queue:
                        break
                    new_path = current[:]
                    new_path.append(parent)
                    work_queue.append(new_path)
            if time_limit < time.time() - start_time:
                break
        return result

    def convert_text_to_id_set(self, text, minimum_word_length=4, remove_articles=True):
        raw_words = text.replace(".", "").replace("?", "").replace(",", "").lower().strip().split()
        clean_words = [word.strip(string.punctuation) for word in raw_words]
        long_words = [long_word for long_word in clean_words if len(long_word) >= minimum_word_length]
        if remove_articles:
            long_words = [final_word for final_word in long_words if final_word not in self.articles]
        id_set = []
        for w in long_words:
            if w in self.words_lower:
                for term in self.words_lower[w]:
                    if self.words[term]['id'] not in id_set:
                        id_set.append(self.words[term]['id'])
        return id_set

    def render_message_from_path(self, message_path):
        sentence = []
        add_to_front = ''
        add_to_end = ''
        in_quote = 0
        for node in message_path:
            new_word = self.word_list[node.word_id]
            if len(sentence) == 0:
                for word_id in node.prefix:
                    new_word = self.word_list[word_id]
                    if new_word == "''":
                        if in_quote == 0:
                            add_to_front += '"'
                        else:
                            in_quote -= 1
                    elif new_word == "``":
                        in_quote += 1
                    if len(sentence) > 0 and new_word != "''" and "'" in new_word[:min(len(new_word), 3)]:
                        sentence[-1] += new_word
                    else:
                        sentence.append(self.word_list[word_id])
            else:
                if new_word == "''":
                    if in_quote == 0:
                        add_to_front += '"'
                    else:
                        in_quote -= 1
                elif new_word == "``":
                    in_quote += 1
                if new_word != "''":
                    if "'" in new_word[:min(len(new_word), 3)]:
                        sentence[-1] = sentence[-1] + new_word
                    else:
                        sentence.append(new_word)
                else:
                    sentence.append(new_word)
        for end_idx in range(in_quote):
            add_to_end += '"'
        # regex to fix the ugly?
        message = add_to_front + " ".join(sentence).replace(" .", ".").replace(" ,", ",")\
            .replace(" !", "!").replace(" ?", "?").replace(" :", ":").replace(" ;", ";")\
            .replace(" ''", '"').replace("`` ", '"') + add_to_end

        return message

    def get_pos_list(self, messsage_path):
        prelen = len(messsage_path[0].prefix) - 1
        prenode = messsage_path[0]
        pos_list = []
        for idx in range(prelen):
            prenode = self.nodes_by_prefix[prenode.prefix[:prelen - idx]]
            pos_list.insert(0, prenode.parts_of_speech[0])
        for node in messsage_path:
            pos_list.append(node.parts_of_speech[0])
        return pos_list

    def build_pos_guided_message_path_general(self, struct_tree, char_limit=300, word_count=50, prompt='', sources=[], time_limit=60):
        # use pos_structures to restrict the possible results
        start_time = time.time()
        self.index_terms()
        message_path = []
        down_path = []
        prompt_ids = self.convert_text_to_id_set(prompt)
        while len(message_path) == 0 and time.time() - start_time < time_limit:
            node = self.select_start_node(prompt_ids, starters_only=True, time_limit=(time_limit - (time.time() - start_time)))
            work_queue = []
            score = 0
            top_score = 0
            if node.word_id in prompt_ids:
                score += 1
            for pos in node.parts_of_speech:
                if pos in struct_tree.branches:
                    new_mark = {'current_path': [node], 'struct_path': struct_tree.branches[pos], 'score': 0}
                    work_queue.append(new_mark)
            while len(work_queue) > 0 and time.time() - start_time < time_limit:
                old_mark = work_queue.pop(0)
                current_path = old_mark['current_path']
                struct_path = old_mark['struct_path']
                score = old_mark['score']
                if len(current_path[-1].outbound) == 0:
                    if score >= top_score:
                        message_path = current_path[:]
                        top_score = score
                for entry in current_path[-1].outbound:
                    for pos in entry[1].parts_of_speech:
                        if pos in struct_path.branches:
                            if entry[1].word_id in prompt_ids:
                                score += 1
                            if score >= top_score:
                                new_mark = {'current_path': current_path[:] + [entry[1]],
                                            'struct_path': struct_path.branches[pos],
                                            'score': score}
                                work_queue.append(new_mark)
        for node in message_path:
            self.append_node_sources(node, sources)
        return message_path


    def build_pos_guided_message_path(self, struct_tree, char_limit=300, word_count=50, prompt='', sources=[], time_limit=60):
        # use pos_structures to restrict the possible results
        start_time = time.time()
        self.index_terms()
        message_path = []
        down_path = []
        prompt_ids = self.convert_text_to_id_set(prompt)
        lead_nodes = 3
        node = self.select_start_node(prompt_ids, time_limit=(time_limit - (time.time() - start_time)))
        possible_starts = self.find_starter_paths(node, allow_hops=lead_nodes,
                                                  time_limit=(time_limit - (time.time() - start_time)),
                                                  struct_tree=struct_tree)
        while len(possible_starts) == 0:
            if time.time() - start_time > time_limit:
                break
            lead_nodes += 2
            if lead_nodes > 20:
                prompt_ids = []
            node = self.select_start_node(prompt_ids, time_limit=(time_limit - (time.time() - start_time)))
            possible_starts = self.find_starter_paths(node, allow_hops=lead_nodes,
                                                      time_limit=(time_limit - (time.time() - start_time)),
                                                      struct_tree=struct_tree)
        if len(prompt_ids) == 0:
            down_path = possible_starts[random.randint(0, len(possible_starts) - 1)]
        else:
            top_score = 0
            for p in possible_starts:
                temp_score = sum([len(self.word_list[n.word_id]) for n in p if n.word_id in prompt_ids])
                if temp_score >= top_score:
                    down_path = p
                    top_score = temp_score
        character_count = 0
        node = down_path.pop()
        message_path.append(node)
        pos_list = self.get_pos_list(message_path)
        struct_path = struct_tree.find_branch(pos_list)
        self.append_node_sources(node, sources)
        if struct_path is not None:
            # at some point we will have to consider using a breadth-first search
            # to build a sentence of the right width
            old_word = self.word_list[node.word_id]
            while len(message_path) < word_count and character_count < char_limit \
                    and time.time() - start_time < time_limit and struct_path is not None:
                if len(down_path) > 0:
                    node = down_path.pop()
                elif len(node.outbound) > 0:
                    s = random.random()
                    # print(time.asctime(), "Roll d100 for next node:", s)
                    new_node = None
                    for entry in node.outbound:
                        if s < entry[0] and entry[1].parts_of_speech[0] in struct_path.branches:
                            new_node = entry[1]
                            break
                    if new_node is not None:
                        node = new_node
                    else:
                        break
                else:
                    break

                message_path.append(node)
                if struct_path is not None and len(node.parts_of_speech) > 0 and node.parts_of_speech[0] in struct_path.branches:
                    struct_path = struct_path.branches[node.parts_of_speech[0]]
                    pos_list.append(struct_path.part_of_speech)
                    new_word = self.word_list[node.word_id]  # keep, so we can check abbreviations... further convert?
                    character_count += len(new_word)
                    self.append_node_sources(node, sources)
                    if new_word in full_stop_beats and len(message_path) > 1 and old_word.lower() not in self.abbreviations:
                        if len(down_path) == 0:
                            break
                    old_word = new_word
                else:
                    struct_path = None
        return message_path

    def build_message_path(self, break_at_fullstop=False, char_limit=300, word_count=50, prompt='', sources=[], time_limit=60):
        start_time = time.time()
        self.index_terms()
        # select a node and work your way from there out
        message_path = []
        down_path = []
        prompt_ids = self.convert_text_to_id_set(prompt)
        lead_nodes = 3
        node = self.select_start_node(prompt_ids, time_limit=(time_limit - (time.time() - start_time)))
        possible_starts = self.find_starter_paths(node, allow_hops=lead_nodes,
                                                  time_limit=(time_limit - (time.time() - start_time)))
        while len(possible_starts) == 0:
            if time.time() - start_time > time_limit:
                break
            lead_nodes += 2
            if lead_nodes > 20:
                prompt_ids = []
            node = self.select_start_node(prompt_ids, time_limit=(time_limit - (time.time() - start_time)))
            possible_starts = self.find_starter_paths(node)
        if len(prompt_ids) == 0:
            down_path = possible_starts[random.randint(0, len(possible_starts) - 1)]
        else:
            top_score = 0
            for p in possible_starts:
                temp_score = sum([len(self.word_list[n.word_id]) for n in p if n.word_id in prompt_ids])
                if temp_score >= top_score:
                    down_path = p
                    top_score = temp_score
        character_count = 0
        node = down_path.pop()
        message_path.append(node)
        self.append_node_sources(node, sources)
        # at some point we will have to consider using a breadth-first search
        # to build a sentence of the right width
        old_word = self.word_list[node.word_id]

        while len(message_path) < word_count and character_count < char_limit and time.time() - start_time < time_limit:
            if len(down_path) > 0:
                node = down_path.pop()
            elif len(node.outbound) > 0:
                s = random.random()
                # print(time.asctime(), "Roll d100 for next node:", s)
                for entry in node.outbound:
                    if s < entry[0]:
                        node = entry[1]
                        break
            else:
                break
            message_path.append(node)
            new_word = self.word_list[node.word_id]  # keep, so we can check abbreviations... further convert?
            character_count += len(new_word)
            self.append_node_sources(node, sources)
            # testing whether we even care about full stop beats
            # if new_word in full_stop_beats and len(message_path) > 1 and old_word.lower() not in self.abbreviations:
                # if len(down_path) == 0 and break_at_fullstop:
                    # break
            old_word = new_word
        return message_path

    def append_node_sources(self, node, sources):
        sources.append([node.prefix, self.convert_prefix_to_text(node.prefix), node.sources[:]])

    def find_path_for_message(self, message, allow_partial=False):
        message_path = []
        beat_list = self.convert_string_to_beats(message)
        offset = self.depth - 1
        for i in range(offset, len(beat_list)):
            key = " ".join(beat_list[i - offset:i + 1])
            prefix = self.convert_key_to_prefix(key)
            node = self.nodes_by_prefix[prefix]
            message_path.append(node)
        return message_path

    @staticmethod
    def get_graph_context(path, depth, degree_max=0, size_max=2000):
        result_nodes = {}
        process_queue = []
        for node in path:
            process_queue.append([node, depth])
        while len(process_queue) > 0 and len(result_nodes) < size_max:
            current = process_queue.pop(0)
            add_node = current[0]
            if add_node not in result_nodes:
                result_nodes[current[0].prefix] = current[0]
                if current[1] > 0:
                    new_depth = current[1] - 1
                    items_allowed = degree_max
                    if degree_max == 0:
                        items_allowed = size_max - len(result_nodes)
                    for new_child in add_node.outbound:
                        process_queue.append([new_child[1], new_depth])
                        items_allowed -= 1
                        if items_allowed <= 0:
                            break
                    for new_parent in add_node.inbound:
                        process_queue.append([new_parent, new_depth])
                        items_allowed -= 1
                        if items_allowed <= 0:
                            break
        return result_nodes
    

        # <[^>]*>

    def build_message(self, break_at_fullstop=True, char_limit=300, word_count=50, prompt='', sources=[],
                      time_limit=60):

        message_path = self.build_message_path(break_at_fullstop=break_at_fullstop,
                                               char_limit=char_limit, word_count=word_count,
                                               prompt=prompt, sources=sources, time_limit=time_limit)
        message = self.render_message_from_path(message_path)        
        return message

        # <[^>]*>

    def identify_passages(self, sources, min_length=3, include_internal=False):
        identified = []
        text = []
        current = {}
        resource = []
        for i in range(len(sources)):
            text.append(sources[i][1])
            for source_item in sources[i][2]:
                is_new = True
                if source_item[0] not in current:
                    current[source_item[0]] = []
                for entry in current[source_item[0]]:
                    if entry[3] == source_item[1] - 1:
                        entry[1] = i
                        entry[3] += 1
                        entry[4] += " " + self.word_list[sources[i][0][-1]]
                        is_new = False
                if is_new:
                    new_entry = [i, i, source_item[1], source_item[1], sources[i][1], sources[i][0]]
                    current[source_item[0]].append(new_entry)
            for key in current:
                for cull in current[key]:
                    if cull[1] < i:
                        length = cull[1] - cull[0] + 1
                        if length >= min_length:
                            identified.append([key, cull[0], length, cull[2], cull[3], cull[4], cull[5]])
                        current[key].remove(cull)
        for key in current:
            for item in current[key]:
                length = item[1] - item[0] + 1
                if length >= min_length:
                    identified.append([key, item[0], length, item[2], item[3], item[4], item[5]])
        identified = sorted(identified, key=lambda x: x[1] * 100000 + len(sources) - x[2])
        passages = []
        last_passage = None
        for passage in identified:
            if include_internal or last_passage is None:
                passages.append(passage)
                last_passage = passage
            else:
                if (passage[1] + passage[2]) > (last_passage[1] + last_passage[2]):
                    passages.append(passage)
                    last_passage = passage
        return passages

    def find_passage_nodes(self, passage):
        source_name = passage[0]
        from_idx = passage[3]
        to_idx = passage[4]
        start_prefix = passage[6]
        node = self.nodes_by_prefix[start_prefix]
        node_list = [node]
        # up
        current_idx = from_idx
        previous = self.find_passage_precursor(node, (source_name, current_idx))
        while previous is not None and (previous.is_starter or not node.is_starter):
            node = previous
            current_idx -= 1
            previous = self.find_passage_precursor(node, (source_name, current_idx))
            node_list.insert(0, node)
        # down
        node = node_list[-1]
        current_idx = from_idx
        next_node = self.find_passage_successor(node, (source_name, current_idx))
        full_stop_ids = [self.get_word_id(beat) for beat in full_stop_beats]
        while next_node is not None and current_idx < to_idx + 50:
            node = next_node
            current_idx += 1
            next_node = self.find_passage_successor(node, (source_name, current_idx))
            node_list.append(node)
            if next_node is not None:
                if next_node.word_id in full_stop_ids and self.word_list[node.word_id].lower() not in self.abbreviations:
                    node_list.append(next_node)
                    break
        return node_list

    def find_passage_precursor(self, node, source_entry):
        precursor = None
        source_target = (source_entry[0], source_entry[1] - 1)
        for parent in node.inbound:
            if source_target in parent.sources:
                precursor = parent
                break
        return precursor

    def find_passage_successor(self, node, source_entry):
        successor = None
        source_target = (source_entry[0], source_entry[1] + 1)
        for entry in node.outbound:
            if source_target in entry[1].sources:
                successor = entry[1]
                break
        return successor
