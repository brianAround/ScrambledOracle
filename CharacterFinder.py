from WordChain import *
from Oracle import Oracle
from WordChainScribe import Scribe


#text_list = [
#    'dirkgently.txt',
#    'longdarkteatime.txt'
#]

# shakes_files = ["t8.shakespeare.txt"]

target_map = "various.txt.map"

# o.build_and_save_chain_from_directory("sources\shakespeare", depth=3, target_filename=map_name)
# o.build_and_save_chain_from_list(text_list, 3, map_name)
# o.build_and_save_chain_from_list(shakes_files, 3, "Composite.txt.map")
# Repeater.target = o
def create_name_file(filename:str, o:Oracle=None, map_name='various.txt.map'):
    name_list = []
    if o is None:
        o = Oracle()
        o.chain = WordChain()
        o.chain.depth = 3
        Scribe.read_map(map_name, chain=o.chain)

    o.chain.index_terms()
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
                score += poss_score
        if 'NNP' in o.chain.words[word]['pos']:
            score += 1
            # if 'said' in o.chain.words_lower:
                # adj_nodes = o.chain.find_word_adjacent_nodes("said", word, same_case=False, same_order=False)
                # score += len(adj_nodes) // 2
        if score > 2:
            name_list.append(word)
    with open(filename, 'w') as file_handle:
        for name in name_list:
            file_handle.write(name + '\n')




# Work through the word list and build a score for each word




