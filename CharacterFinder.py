import random
import time
import schedule
import sys
import nltk
from WordChain import *
from Oracle import Oracle





o = Oracle()
text_list = [
    'dirkgently.txt',
    'longdarkteatime.txt'
]

# shakes_files = ["t8.shakespeare.txt"]

map_name = "hitch.3.map"

# o.build_and_save_chain_from_directory("sources\shakespeare", depth=3, target_filename=map_name)
o.build_and_save_chain_from_list(text_list, 3, map_name)
# o.build_and_save_chain_from_list(shakes_files, 3, "Composite.txt.map")
o.chain = WordChain()
o.chain.depth = 3
o.chain.read_map(map_name)
o.chain.index_terms()
# Repeater.target = o



# Work through the word list and build a score for each word

for word in [item for item in o.chain.words if len(item) > 1 and item[0] in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" and item[1] in "abcdefghijklmnopqrstuvwxyz"]:
    score = 1  # grant 1 for starting with a capital letter
    if not str(word).endswith("'s") and \
            word.lower() not in o.chain.articles and \
            (word.strip(string.punctuation) == word or word.strip(string.punctuation) not in o.chain.words):
        poss_form = word + "'s"
        if poss_form in o.chain.words:
            poss_score = 0
            for prefix in o.chain.words[poss_form]['nodes']:
                node = o.chain.nodes_by_prefix[prefix]
                poss_score += node.quantity
            score += 1
        if 'said' in o.chain.words_lower:
            adj_nodes = o.chain.find_word_adjacent_nodes("said", word, same_case=False, same_order=False)
            score += len(adj_nodes) // 2
    if score > 2:
        print(word, ": ", score)



