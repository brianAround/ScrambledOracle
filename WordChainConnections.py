import time
from UnionFind import UTUnionFind
from WordChain import *
from WordChainScribe import Scribe

# To help analyze a generated WordChain by identifying
# connected components, etc.

list_all_components = True
list_nodes_in_components = False
list_source_texts_in_components = True
show_word_disconnects = False
find_paths = False

print(time.asctime())
wc = WordChain()
wc.depth = 3
print(time.asctime(), "Reading map")

wc = Scribe.read_map('douglasadams.txt.map', chain=wc)
print(time.asctime(), "Indexing terms")
wc.index_terms()

last_message = ''

prefix_list = [prefix for prefix in wc.nodes_by_prefix]
uf = UTUnionFind(prefix_list)

print('Word count:', len(wc.word_list))
print('Node count:', len(prefix_list))

for prefix in prefix_list:
    node = wc.nodes_by_prefix[prefix]
    for entry in node.outbound:
        second = entry[1].prefix
        if uf.find(prefix) != uf.find(second):
            uf.union(prefix, second)

comps = {}
for prefix in prefix_list:
    component = uf.find(prefix)
    if component not in comps:
        comps[component] = []
    comps[component].append(prefix)

word_lists = {}
print("There are", len(comps), "distinct components.")
for cname in comps:
    text_name = " ".join([wc.word_list[id] for id in cname])
    if list_all_components or len(comps[cname]) < 100:
        print(text_name, cname, ":", len(comps[cname]), 'nodes')
        words = {}
        source_texts = {}
        for prefix in comps[cname]:
            if list_nodes_in_components:
                print("[", " ".join([wc.word_list[id] for id in prefix]), "]",)
            if list_source_texts_in_components:
                node = wc.nodes_by_prefix[prefix]
                for src in node.sources:
                    if src[0] not in source_texts:
                        source_texts[src[0]] = 0
                    source_texts[src[0]] += 1
            for id in prefix:
                if wc.word_list[id] not in words:
                    words[wc.word_list[id]] = 0
                words[wc.word_list[id]] += 1
        print(len(words), " words")
        print("Sources:", [(src_text, src_count) for src_text, src_count in source_texts.items()])
        word_lists[text_name] = words

if show_word_disconnects:
    word_lists = {}
    for text_name in word_lists:
        other_lists = [other_name for other_name in word_lists if other_name != text_name]
        not_in_all = [word for word in word_lists[text_name]]
        for other_name in other_lists:
            not_in_this = []
            check_list = word_lists[other_name]
            for word in word_lists[text_name]:
                if word in check_list and word in not_in_all:
                    not_in_all.remove(word)
                else:
                    not_in_this.append(word)
            print("Words in", text_name, "but not in", other_name, ":")
            print(not_in_this)
        print("Words only in", text_name)
        print(not_in_all)



# you now have a directory of words... you could figure out which words are unique to what components
if find_paths:
    a = input("Prompt A: ")
    while len(a.strip()) == 0 or a not in wc.words:
        print("You must enter a term that is in the map.")
        a = input("Prompt A: ")

    b = input("Prompt B: ")
    while len(b.strip()) == 0 or b not in wc.words:
        print("You must enter a term that is in the map.")
        b = input("Prompt B: ")

    print(time.asctime(), "Identifying Paths from", a, "to", b)
    while len(a) == 0 or a[0] not in ('q', 'Q'):
        prefix_set_a = wc.words[a]['nodes']
        prefix_set_b = wc.words[b]['nodes']

        print(a, 'node count:', len(prefix_set_a))
        print(b, 'node count:', len(prefix_set_b))

        # how do we find our way from one node in the list to another?
        # follow everything downstream from a, in order.  Stop a chain when b is found, or there are no more paths.
        spangle = []
        viewed = {}
        connections = []
        for prefix in prefix_set_a:
            spangle.append([prefix])
        while len(spangle) > 0:
            target = spangle.pop(0)
            if target[-1] in prefix_set_b:
                connections.append(target)
                print("Added connection #", len(connections), "Queue size:", len(spangle), "Nodes in connection:", len(target))
            else:
                parent = wc.nodes_by_prefix[target[-1]]
                for entry in parent.outbound:
                    child = entry[1]
                    if child.prefix not in target and len(target) < 9:
                        new_path = target[:]
                        new_path.append(child.prefix)
                        spangle.append(new_path)

        idx = 1
        for path in connections:
            print("Path", idx, ":")
            print(path)
            words = []
            for i in range(len(path[0])):
                words.append(wc.word_list[path[0][i]])

            words += [wc.word_list[item[-1]] for item in path]
            print(" ".join(words))
            print()
            idx += 1

        a = input("Prompt A: ")
        while len(a.strip()) == 0 or a not in wc.words:
            print("You must enter a term that is in the map.")
            a = input("Prompt A: ")

        b = input("Prompt B: ")
        while len(b.strip()) == 0 or b not in wc.words:
            print("You must enter a term that is in the map.")
            b = input("Prompt B: ")




