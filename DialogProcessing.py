import nltk
import os
from People import Person, People
from collections import Iterable

source_folder = os.path.join('sources','pratchett')
document_file = 'EqualRites.txt'

para_range_start = 0
para_range_end = 70

recognized_pronouns = Person.recognized_pronouns[:]

# source_folder = os.path.join('sources','various')
# document_file = 'AffairAtStyles.txt'

original_file = os.path.join(source_folder, document_file)
output_file = os.path.join(source_folder, document_file.split('.')[0] + '.talk')

lines = []
with open(original_file, 'r') as read_file:
    lines = read_file.readlines()

use_death_speaks_formatting = False

recent_speaker = ''

recent_person = []
mentioned_person = []
speaker = ''
speaker_pos = ''

paragraphs = [block.strip() for block in ''.join(lines).split('\n\n') if block.strip() != '']
if para_range_start > 0:
    paragraphs = paragraphs[para_range_start:para_range_end]
paragraphs = [nltk.sent_tokenize(paragraph) for paragraph in paragraphs]
clean_para = paragraphs
paragraphs = [[nltk.word_tokenize(sentence) for sentence in paragraph] for paragraph in paragraphs]
paragraphs = [nltk.pos_tag_sents(paragraph) for paragraph in paragraphs]

quote_start = '``'
quote_end = "''"

speech_verbs = ['said', 'repeated', 'whispered', 'replied', 'joked']
noun_pos = ['NN', 'NNS', 'NNP', 'NNPS', 'PRP']
name_pos = ['NNP', 'NNPS']
names = {}
all_people = {}
full_people = People()
people_stack = People()
people_verbs = ['said', 'considered', 'pretended', 'smiled', 'shrugged', 'nodded', 'thought']
people_verb_pos = ['VBD']
vbd_verbs = {}
last_quote_idx = -1
in_quote = False
recent_speaker = ''
recent_speaker_pos = ''
people_recently_speaking = People()
recent_speaker_paragraph = -1


for idx in range(len(paragraphs)):
    print('(', idx, ')', '|'.join([sentence for sentence in clean_para[idx]]))
    speech = []
    other = []
    antecedent = ''
    if speaker != '':
        recent_speaker_paragraph = idx - 1
        recent_speaker = speaker
        recent_speaker_pos = speaker_pos
    speaker = ''
    speaker_pos = ''
    speaker_obj = None
    for sentence_idx in range(len(paragraphs[idx])):
        sentence = paragraphs[idx][sentence_idx]
        # print('sentence:', ' '.join([token[0] for token in sentence]))
        prev_token = None
        token = None
        next_token = None
        for token_idx in range(len(sentence)):
            prev_token = token
            token = sentence[token_idx]
            if token_idx + 1 < len(sentence):
                next_token = sentence[token_idx + 1]
            else:
                next_token = None
            if token[0] == quote_start:
                in_quote = True
            elif token[0] == quote_end:
                in_quote = False
            else:
                if in_quote or (use_death_speaks_formatting and token[0].isupper()):
                    speech.append(token)
                    last_quote_idx = token_idx
                    if token[1] in name_pos:
                        if prev_token is None or prev_token[1] not in name_pos:
                            mentioned_person = []
                        mentioned_person.append(token[0])
                else:
                    other.append(token)
                    if token[0] in all_people or (token[1] in name_pos and token[0] != token[0].upper()):
                        if last_quote_idx > token_idx - 4 > 0:
                            speaker = token[0]
                            speaker_pos = token[1]

                    if token[0] in all_people and token[0] not in recent_person[-2:]:
                        recent_person.append(token[0])
                    elif token[1] in name_pos and token[0] != token[0].upper():
                        recent_person.append(token[0])
                    elif token[1] == 'VBD' and token[0].lower() in speech_verbs:
                        # decide if the speaker comes before or after
                        if prev_token is not None and (prev_token[1] in noun_pos or prev_token[0] in all_people):
                            speaker = prev_token[0]
                            speaker_pos = prev_token[1]
                        elif next_token is not None:
                            if next_token[1] in noun_pos:
                                speaker = next_token[0]
                                speaker_pos = next_token[1]
                            if next_token[1] == 'DT' and token_idx + 2 < len(sentence):
                                sp_token = sentence[token_idx + 2]
                                if sp_token[1] in noun_pos or sp_token[0] in all_people:
                                    speaker = sp_token[0]
                                    speaker_pos = sp_token[1]

                    if full_people.has_match(token[0]):
                        this_person = full_people.find_word_matches(token[0])[0]
                        if token[1] in name_pos and this_person[1] >= 0.5:
                            this_person[0].add_name(token[0])
                        elif token[1] in noun_pos and token[1] != 'PRP':
                            this_person[0].add_noun(token[0])

                        people_stack.append(full_people.find_word_matches(token[0])[0][0])
                    possible_speakers = full_people.find_word_matches(speaker)
                    if len(possible_speakers) == 1 and speaker_pos != 'PRP':
                        if possible_speakers[0][1] >= 0.5:
                            speaker_obj = possible_speakers[0][0]
                            if speaker_pos in name_pos:
                                speaker_obj.add_name(speaker)
                            else:
                                speaker_obj.add_noun(speaker)
                    #do something with this
                    avoid_list = recognized_pronouns[:]
                    if len(speech) > 0 and speaker.lower() in recognized_pronouns:
                        avoid_list.append(recent_speaker.lower())
                        for person_idx in range(-1, len(recent_person) * -1 - 1, -1):
                            if recent_person[person_idx].lower() not in avoid_list:
                                was_speaker = speaker
                                was_speaker_pos = speaker_pos
                                speaker = recent_person[person_idx]
                                if full_people.has_match(speaker):
                                    matched_speaker = full_people.find_word_matches(speaker)[0][0]
                                    if was_speaker_pos == 'PRP':
                                        matched_speaker.add_pronoun(was_speaker)
                                    elif was_speaker_pos in name_pos:
                                        matched_speaker.add_name(was_speaker)
                                    elif was_speaker_pos in noun_pos:
                                        matched_speaker.add_noun(was_speaker)
                                break

                    if speaker != '':
                        if speaker not in all_people:
                            all_people[speaker] = 1
                            if speaker_pos in name_pos:
                                full_people.add_name(speaker)
                            elif speaker_pos in noun_pos and speaker_pos != 'PRP':
                                full_people.add_noun(speaker)


                    # for person in recent_person:
                    #    all_people[person] = 1

                    if token[1] in people_verb_pos and token[0] in people_verbs:
                        if prev_token is not None and prev_token[1] in noun_pos:
                            recent_person.append(prev_token[0])
                            if not full_people.has_match(prev_token[0]):
                                if prev_token[1] in name_pos:
                                    full_people.add_name(prev_token[0])
                                elif prev_token[1] != 'PRP':
                                    full_people.add_noun(prev_token[0])
                        elif next_token is not None and next_token[1] in noun_pos:
                            recent_person.append(next_token[0])
                            if not full_people.has_match(next_token[0]):
                                if next_token[1] in name_pos:
                                    full_people.add_name(next_token[0])
                                elif next_token[1] != 'PRP':
                                    full_people.add_noun(next_token[0])
    recent_person = recent_person[-5:]
    avoid_list = Person.recognized_pronouns[:]
    if len(speech) > 0 and (speaker == '' or speaker.lower() in avoid_list):
        if recent_speaker_paragraph == idx - 1:
            avoid_list.append(recent_speaker.lower())
        for person_idx in range(-1, len(recent_person)*-1 - 1, -1):
            if recent_person[person_idx].lower() not in avoid_list:
                was_speaker = speaker
                was_speaker_pos = speaker_pos
                speaker = recent_person[person_idx]
                if full_people.has_match(speaker):
                    matched_speaker = full_people.find_word_matches(speaker)[0][0]
                    if was_speaker_pos == 'PRP':
                        matched_speaker.add_pronoun(was_speaker)
                    elif was_speaker_pos in name_pos:
                        matched_speaker.add_name(was_speaker)
                    elif was_speaker_pos in noun_pos:
                        matched_speaker.add_noun(was_speaker)
                break
    if len(mentioned_person) > 0:
        mentioned_matches = full_people.find_phrase_matches(mentioned_person)
        if len(mentioned_matches) > 0:
            for word in mentioned_person:
                mentioned_matches[0][0].add_name(word)
    if speaker != '' and speaker not in recent_person:
        recent_person.append(speaker)
    if len(speech) > 0:
        if speaker_obj is not None:
            speaker = speaker_obj.say_person()
        print(speaker.upper(), ':\t', ' '.join([token[0] for token in speech]))
        print('mentioned_person', mentioned_person, 'recent_person:', ' '.join(recent_person))
        print()
        #print('full_people:')
        #for p in full_people:
        #    print(p)
        # print('other:', ' '.join(other))
print('vbd_verbs:', [verb for verb in vbd_verbs])
print('people_verbs:', [verb for verb in people_verbs])
print('all_people:', [person for person in all_people])
print('full_people:')
for p in full_people:
    print(p)