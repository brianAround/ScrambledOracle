import time
from WordChain import *
from WordChainScribe import Scribe
import SequenceAlignment

print(time.asctime())
wc = WordChain()
wc.depth = 3
print(time.asctime(), "Reading map")


repetitions = 4
is_verbose = False
max_characters = 840
single_sentence = True

Scribe.read_map('pratchett.4.alt.txt.map', chain=wc)

# print(wc.get_chain_description())

last_message = ''

def message_is_okay(message, passages, prompt, is_verbose=False):
    is_okay = True
    minimum_length = 50
    minimum_passages = 2
    errors = []
    if message[0] not in WordChain.capitals and message[0] not in '"-':
        errors.append('The first character is not capitalized.')
    if message[-1] not in '.!?"\'':
        errors.append("The message doesn't end with a sentence terminator.")
    if len(message) < 50:
        errors.append("The message is less than " + str(minimum_length) + " characters long.")
    if len(passages) < 3:
        errors.append("There are fewer than " + str(minimum_passages) + " passages used in this message.")
    if message == prompt:
        errors.append("The message is the same as the prompt.")
    else:
        if len(prompt) > minimum_length:
            seq_align = SequenceAlignment.get_alignment(message, prompt)
            raw_compare = 'Seq Align Score: ' + str(seq_align['score']) + ' "' + "".join(seq_align['result_1']) + '/' + "".join(seq_align['result_2']) + '"'
            if len(errors) == 0:
                print("Messg:" + "".join(seq_align['result_1']))
                print("Prmpt:" + "".join(seq_align['result_2']))
                print(raw_compare)
            if seq_align['score'] < len(message) + len(prompt):
                errors.append('Message too similar to prompt. ' + raw_compare)
    if len(errors) > 0:
        is_okay = False
        if is_verbose:
            print("Rejecting completed message:", message)
            print("Reasons:", errors)
    return is_okay


a = input("Prompt: ")
print(time.asctime(), "Building messages")
while len(a) == 0 or a[0] not in ('q', 'Q'):
    for i in range(repetitions):
        attempts = 1
        sources = []
        message = wc.build_message(break_at_fullstop=single_sentence, char_limit=max_characters, word_count=150, prompt=a, sources=sources, time_limit=6000)
        prompt_list = [wc.word_list[wid] for wid in wc.convert_text_to_id_set(a)]
        print("Initial filtered prompt:", " ".join(prompt_list))
        passages = wc.identify_passages(sources, min_length=2)
        while not message_is_okay(message, passages, prompt=a, is_verbose=is_verbose):
            if attempts > 30:
                a = ""
            sources = []
            message = wc.build_message(break_at_fullstop=single_sentence, char_limit=max_characters, word_count=150, prompt=a, sources=sources, time_limit=6000)
            passages = wc.identify_passages(sources, min_length=2)
            attempts += 1
        print(message)
        print('----------------------------')
        print('finished prompt:', a, ' attempts:', attempts)
        print('----------------------------')

        for p in passages:
            print(wc.render_message_from_path(wc.find_passage_nodes(p)))
            print(p)
        print('----------------------------')
        a = message
    a = input("Prompt:")
