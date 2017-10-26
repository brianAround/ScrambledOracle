import os
import os.path
from WordChain import WordChain, ChainNode


class Scribe:

    @staticmethod
    def read_map(filepath, read_srcmap=True, chain:WordChain=None):
        if chain is None:
            chain = WordChain()
        with open(filepath, 'r', encoding='utf-8') as file_in:
            for line in file_in:
                values = line.strip().split('\t')
                key = values[0]
                beats = []
                prefix = chain.convert_key_to_prefix(key, beats)
                word_id = prefix[-1]
                node = chain.get_node_by_prefix(prefix)
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
                    next_word_id = chain.get_word_id(next_word)
                    if len(prefix) < chain.depth:
                        new_prefix = prefix + (next_word_id,)
                    else:
                        new_prefix = prefix[1:] + (next_word_id,)
                    dest_node = chain.get_node_by_prefix(new_prefix)
                    dest_node.inbound.append(node)
                    node.outbound.append([total, dest_node])
        src_filepath = filepath + ".srcmap"
        if read_srcmap and os.path.isfile(src_filepath):
            Scribe.read_sourcemap(src_filepath, chain)
        pos_filepath = filepath + ".posmap"
        if os.path.isfile(pos_filepath):
            Scribe.read_posmap(pos_filepath, chain)
        for prefix in chain.nodes_by_prefix:
            if chain.nodes_by_prefix[prefix].is_starter:
                chain.starters.append(prefix)
        return chain

    @staticmethod
    def read_sourcemap(src_filepath, chain:WordChain):
        with open(src_filepath, 'r', encoding='utf-8') as file_in:
            for line in file_in:
                values = line.strip().split('\t')
                key = values[0]
                prefix = chain.convert_key_to_prefix(key)
                if prefix not in chain.nodes_by_prefix:
                    node = ChainNode(prefix[-1], prefix=prefix)
                    chain.nodes_by_prefix[prefix] = node
                node = chain.nodes_by_prefix[prefix]
                node.is_quote = values[1] == 'True'
                node.is_starter = values[2] == 'True'
                for i in range(3, len(values)):
                    text_file, text_index = values[i].split('|')
                    text_index = int(text_index)
                    entry = (text_file, text_index)
                    node.sources.append(entry)
    #structure of sources: [(file_name, index), ...]


    @staticmethod
    def read_posmap(src_filepath, chain:WordChain):
        with open(src_filepath, 'r', encoding='utf-8') as file_in:
            for line in file_in:
                values = line.strip().split('\t')
                key = values[0]
                prefix = chain.convert_key_to_prefix(key)
                if prefix not in chain.nodes_by_prefix:
                    node = ChainNode(prefix[-1], prefix=prefix)
                    chain.nodes_by_prefix[prefix] = node
                node = chain.nodes_by_prefix[prefix]
                node.parts_of_speech = []
                for i in range(1, len(values)):
                    this_part = values[i]
                    if this_part != "" and this_part not in node.parts_of_speech:
                        node.parts_of_speech.append(this_part)