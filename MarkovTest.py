from Oracle import Oracle, WordChain
import os
import os.path

# target_list = ["alice13a.txt", "carroll-hunting-100.txt"]
# target_list = ['Leftovers.txt']
# target_list = ["hhgttg.txt", "rest.txt", "life.txt", "fish.txt", "harmless.txt"]
# target.build_and_save_chain_from_list(target_list, 2, out_file)

# for word_key in target.word_counts:
#    if target.word_counts[word_key] > 500:
#        print(word_key, target.word_counts[word_key])


# target.read_chain(out_file)
target = Oracle()

target.chain = WordChain()
target.chain.depth = 3
target.depth = target.chain.depth
target.mchain = target.chain.mchain
target.starters = target.chain.starters

text_list = [
    "hhgttg.txt",
    "alice13a.txt",
    "rest.txt",
    "sherlock.txt",
    "expectations.txt",
    "life.txt",
    "fish.txt",
    "wuthering.txt",
    "janeeyre.txt",
    "pandp12.txt",
    "princessofmars.txt",
    "stranger.txt"
]

pratchett_dir = os.path.join("sources", "pratchett")
map_name = "pratchett.txt.map"  # "shakespeare.txt.map"

target.build_and_save_chain_from_directory(pratchett_dir, depth=3, target_filename=map_name)
# target.build_and_save_chain_from_list(text_list, 2, "Composite.2.map")
# target.read_chain("Composite.2.map")

# target.build_and_save_chain_from_list(text_list, 3, "pratchett.txt.map")

target.chain.read_chain("pratchett.txt.map")
# target.build_and_save_chain_from_list(["hhgttg.txt", "fish.txt", "harmless.txt", "life.txt", 'rest.txt'], 2, "hitch.2.map")
# target.read_chain("hitch.2.map")

a = input("Enter a prompt: ")
b = ""
chain_response = input("Chain responses (y/n)?: ")
if chain_response.lower() in ['y', 'yes']:
    chain_response = True
else:
    chain_response = False

while a.lower() not in ["q", "quit", "stop", "end"]:
    if a[0:5].lower() == "view:":
        for start in [text for text in target.chain.starting if a[5:].lower() in text.lower()]:
            print('"' + start + '"', target.chain.mchain[start])
    else:
        # target.chain.add_expression(a)
        for i in range(0, 5):
            sources = []
            this_message = target.chain.build_message(char_limit=140, prompt=b + " " + a, sources=sources)
            passages = target.chain.identify_passages(sources, min_length=2)
            while len(this_message) < 50 or this_message[len(this_message) - 1] not in "?!.":
                sources = []
                this_message = target.chain.build_message(char_limit=140, prompt=b + " " + a, sources=sources)
                passages = target.chain.indentify_passages(sources, min_length=2)
            print(len(this_message), "\t", this_message)
            print("---------------------------------------------")
            quote_size = 0
            if len(passages) > 0:
                quote_size = passages[-1][1] + passages[-1][2]
            for item in passages:
                print(item, item[2] * 1000 // quote_size / 1000)
            print("---------------------------------------------")
            print("---------------------------------------------")
            if chain_response:
                b = a
                a = this_message
                if a == b:
                    a = ""
                    b = ""
    a = input("Enter a prompt: ")



