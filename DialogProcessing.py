import nltk
import os




source_folder = os.path.join('sources','pratchett')
document_file = 'EqualRites.txt'

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

paragraphs = [block.strip() for block in ''.join(lines).split('\n\n') if block.strip() != '']
paragraphs = [nltk.sent_tokenize(paragraph) for paragraph in paragraphs]
paragraphs = [[nltk.word_tokenize(sentence) for sentence in paragraph] for paragraph in paragraphs]
paragraphs = [nltk.pos_tag_sents(paragraph) for paragraph in paragraphs]

quote_start = '``'
quote_end = "''"

speech_verbs = ['said']
noun_pos = ['NN','NNS','NNP','NNPS','PRP']
name_pos = ['NNP','NNPS']
names = {}
all_people = {}
people_verbs = ['said', 'considered', 'pretended', 'smiled', 'shrugged', 'nodded', 'thought']
people_verb_pos = ['VBD']
vbd_verbs = {}
last_quote_idx = -1
in_quote = False
recent_speaker = ''
recent_speaker_paragraph = -1

for idx in range(20, 50):
    print('(', idx, ') Number of sentences:', len(paragraphs[idx]))
    speech = []
    other = []
    if speaker != '':
        recent_speaker_paragraph = idx - 1
        recent_speaker = speaker
    speaker = ''
    print(' '.join([' '.join([token[0] for token in sentence]) for sentence in paragraphs[idx]]))
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
                        if prev_token is not None and prev_token[1] not in name_pos:
                            mentioned_person = []
                        mentioned_person.append(token[0])
                else:
                    other.append(token)
                    if token[1] == 'POS':
                        recent_person.append(prev_token[0])
                    elif token[1] in name_pos and token[0] != token[0].upper():
                        if token[0] in all_people:
                            recent_person.append(token[0])
                    elif token[1] == 'VBD' and token[0].lower() in speech_verbs:
                        # decide if the speaker comes before or after
                        if prev_token is not None:
                            if prev_token[1] in noun_pos or prev_token[0] in all_people:
                                speaker = prev_token[0]
                        elif next_token is not None:
                            if next_token[1] in noun_pos:
                                speaker = next_token[0]
                            if next_token[1] == 'DT' and token_idx + 2 < len(sentence):
                                if sentence[token_idx + 2][1] in noun_pos or sentence[token_idx + 2][0] in all_people:
                                    speaker = sentence[token_idx + 2][0]

                    all_people[speaker] = 1

                    for person in recent_person:
                        all_people[person] = 1

                    if token[1] in people_verb_pos and token[0] in people_verbs:
                        if prev_token is not None and prev_token[1] in noun_pos:
                            recent_person.append(prev_token[0])
                        elif next_token is not None and next_token[1] in noun_pos:
                            recent_person.append(next_token[0])
    recent_person = recent_person[-5:]
    if len(speech) > 0 and speaker == '':
        if recent_speaker_paragraph == idx - 1:
            for person_idx in range(-1,len(recent_person)*-1 - 1,-1):
                if recent_person[person_idx] != recent_speaker:
                    speaker = recent_person[person_idx]
                    break
    if len(speech) > 0 and speaker == '':
        # this rule is dubious
        speaker = ' '.join(mentioned_person)
    if speaker != '' and recent_person[-1] != speaker:
        recent_person.append(speaker)
    print('speech:', speech)
    print('speaker:', speaker)
    print('recent_person:', recent_person)
    print('mentioned_person', mentioned_person)
    print('other:', other)
print('vbd_verbs:', [verb for verb in vbd_verbs])
print('people_verbs:', [verb for verb in people_verbs])
print('all_people:', [person for person in all_people])