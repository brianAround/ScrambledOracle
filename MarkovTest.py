import random

from Oracle import Oracle, WordChain
from WordChainScribe import Scribe
import os
import os.path


map_name = 'InauguralHorror.txt.map'
# map_name = 'AdamsPoe.txt.map'

# target_list = ["alice13a.txt", "carroll-hunting-100.txt"]
# target_list = ['Leftovers.txt']
# target_list = ["hhgttg.txt", "rest.txt", "life.txt", "fish.txt", "harmless.txt"]
# target.build_and_save_chain_from_list(target_list, 2, out_file)

# for word_key in target.word_counts:
#    if target.word_counts[word_key] > 500:
#        print(word_key, target.word_counts[word_key])




target = Oracle()

target.chain = WordChain()
target.chain.depth = 3

print("Reading", map_name, "from disk")
Scribe.read_map(map_name, chain=target.chain)


target.depth = target.chain.depth
target.max_percent = 1/3


a = input("Enter a prompt: ")
b = ""
chain_response = input("Chain responses (y/n)?: ")
if chain_response.lower() in ['y', 'yes']:
    chain_response = True
else:
    chain_response = False

while a.lower() not in ["q", "quit", "stop", "end"]:
    paragraph = []
    if a[0:5].lower() == "view:":
        for start in [text for text in target.chain.starting if a[5:].lower() in text.lower()]:
            print('"' + start + '"', target.chain.mchain[start])
    else:
        # target.chain.add_expression(a)
        for i in range(0, random.randint(1, 5)):
            sources = []
            passages = []
            target.max_percent = 1/(random.randint(2,5))
            this_message = target.get_message(prompt=b + " " + a,passages=passages)
            while len(this_message) < 5:
                passages = []
                this_message = target.get_message(prompt=b + " " + a, passages=passages)

            print(this_message)
            if chain_response:
                b = a
                a = this_message
                if a == b:
                    a = ""
                    b = ""
            paragraph.append(this_message)
    print(' '.join(paragraph).replace('. "','".\n"'))
    a = input("Enter a prompt: ")



