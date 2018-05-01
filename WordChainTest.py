import time
from WordChain import *
from WordChainScribe import Scribe

print(time.asctime())
wc = WordChain()
wc.depth = 3
print(time.asctime(), "Reading map")

Scribe.read_map('various.txt.map', chain=wc)

last_message = ''


a = input("Prompt: ")
print(time.asctime(), "Building messages")
while len(a) == 0 or a[0] not in ('q', 'Q'):
    for i in range(10):
        attempts = 1
        sources = []
        message = wc.build_message(break_at_fullstop=True, char_limit=280, word_count=25, prompt=a, sources=sources)
        while message[0] not in WordChain.capitals or message[-1] not in '.!?' or len(message) < 50:
            sources = []
            message = wc.build_message(break_at_fullstop=True, char_limit=280, word_count=25, prompt=a, sources=sources)
            attempts += 1
            if attempts > 10:
                a = ""
        print(message)
        print('----------------------------')
        passages = wc.identify_passages(sources, min_length=2)
        for p in passages:
            print(wc.render_message_from_path(wc.find_passage_nodes(p)))
            print(p)
        print('----------------------------')
    a = input("Prompt:")
