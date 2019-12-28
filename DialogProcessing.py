from collections import Counter
import nltk
import os
from People import Person, People
from collections import Iterable

def get_relative_file_list(source_folder, filter_out=[]):
    file_listing = [f for f in os.listdir(source_folder) if f.endswith(".txt") and len([ban_text for ban_text in filter_out if ban_text in f]) == 0]
    file_listing = [os.path.join(source_folder, f) for f in file_listing]
    file_listing = [f for f in file_listing if os.path.isfile(f)]
    return file_listing



para_range_start = 0
para_range_end = 70

recognized_pronouns = Person.recognized_pronouns[:]

# source_folder = os.path.join('sources','various')
# document_file = 'AffairAtStyles.txt'
character_speech = {}

file_stoppers = []

# source_list = ['pratchett', 'dougadams', 'various']
source_list = ['various']
for current_source in source_list:
    print('Processing source', current_source)
    source_folder = os.path.join('sources', current_source)
    document_file = 'EqualRites.txt'

    file_list = get_relative_file_list(source_folder, filter_out=file_stoppers)

    # original_file = os.path.join(source_folder, document_file)
    # file_list = ['sources/dougadams/HitchhikersGuideToTheGalaxy.txt']
    for original_file in file_list:
        # output_file = os.path.join(source_folder, 'talk', os.path.basename(original_file))

        output_file = os.path.join('/Users/brian/Google Drive/IdolBots', current_source, os.path.basename(original_file))

        document = ''
        with open(original_file, 'r') as read_file:
            document = read_file.read()
        read_file.close()


        out_lines = []
        print('Processing file', original_file)
        print('Output file', output_file)
        use_death_speaks_formatting = (current_source == 'pratchett')

        recent_speaker = ''

        recent_person = []
        mentioned_person = []
        speaker = ''
        speaker_pos = ''
        non_quote_preceeding = 0

        paragraphs = [block.strip() for block in document.split('\n\n') if block.strip() != '']
        if len(paragraphs) < 100:
            paragraphs = [block.strip() for block in document.split('\n') if block.strip() != '']
        if para_range_start > 0:
            paragraphs = paragraphs[para_range_start:para_range_end]
        paragraphs = [nltk.sent_tokenize(paragraph) for paragraph in paragraphs]
        clean_para = paragraphs
        paragraphs = [[nltk.word_tokenize(sentence) for sentence in paragraph] for paragraph in paragraphs]
        paragraphs = [nltk.pos_tag_sents(paragraph) for paragraph in paragraphs]

        # build_a_named_character_list
        names = []
        for p in paragraphs:
            for s in p:
                last_pos = ''
                for t in s:
                    if t[1] == 'NNP':
                        if last_pos != 'NNP' and len(mentioned_person) > 0:
                            names.append(' '.join(mentioned_person))
                            mentioned_person = []
                        mentioned_person.append(t[0])
                    last_pos == t[1]
        name_count = dict(Counter([name for name in names]).most_common(50))
        characters = [name for name in name_count]
        print('Proper Nouns:')
        out_lines.append('Proper_Nouns:')

        for n in name_count:
            print(n, ':', name_count[n])
            out_lines.append(str(n) + " : " + str(name_count[n]))

        quote_start = '``'
        quote_end = "''"

        speech_verbs = ['said', 'repeated', 'whispered', 'replied', 'joked']
        noun_pos = ['NN', 'NNS', 'NNP', 'NNPS', 'PRP']
        name_pos = ['NNP', 'NNPS']
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
        people_names = []


        for idx in range(len(paragraphs)):
            print('(', idx, ')', '|'.join([sentence for sentence in clean_para[idx]]))
            out_lines.append('(' + str(idx) + ') ' + '|'.join([sentence for sentence in clean_para[idx]]))
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
                        non_quote_preceeding = 0
                    elif token[0] == quote_end:
                        in_quote = False
                    else:
                        if in_quote or (use_death_speaks_formatting and token[0].isupper() and
                                        ((prev_token is not None and prev_token[0].isupper())
                                         or (next_token is not None and next_token[0].isupper()))):
                            speech.append(token)
                            last_quote_idx = token_idx
                            non_quote_preceeding = 0
                        else:
                            if token[1] in name_pos and not token[0].isupper():
                                if prev_token is None or prev_token[1] not in name_pos:
                                    # if len(mentioned_person) > 0:
                                    # matching_people = full_people.find_phrase_matches(mentioned_person)
                                    # if len(matching_people) == 1:
                                    #    matching_people[0][0].add_names(mentioned_person)
                                    # elif len(matching_people) == 0:
                                    #    new_person = Person()
                                    #    new_person.add_names(mentioned_person)
                                    # names.append(mentioned_person)
                                    recent_person.append(' '.join(mentioned_person))
                                    mentioned_person = []
                                mentioned_person.append(token[0])
                                if ' '.join(mentioned_person) in characters:
                                    last_mentioned_character = ' '.join(mentioned_person)
                                    if recent_person[-1] != last_mentioned_character:
                                        recent_person.append(last_mentioned_character)

                            other.append(token)
                            #if token[0] in all_people or (token[1] in name_pos and token[0] != token[0].upper()):
                            #    if 5 > non_quote_preceeding > 3:
                            #        speaker = token[0]
                            #        speaker_pos = token[1]
                            if token[1].startswith('VB') and (token[0].lower() in speech_verbs or non_quote_preceeding < 3):
                                # decide if the speaker comes before or after
                                if prev_token is not None and non_quote_preceeding == 1 and (prev_token[1] in noun_pos or prev_token[0] in characters):
                                    speaker = prev_token[0]
                                    speaker_pos = prev_token[1]
                                    if speaker_pos in name_pos and token_idx - 2 >= 0:
                                        sp_token = sentence[token_idx -2]
                                        if sp_token[1] in name_pos:
                                            speaker = sp_token[0] + ' ' + speaker
                                elif next_token is not None:
                                    if (next_token[1] in noun_pos or next_token[0] in characters) and not next_token[0].isupper():
                                        speaker = next_token[0]
                                        speaker_pos = next_token[1]
                                        if speaker_pos in name_pos and token_idx + 2 < len(sentence):
                                            sp_token = sentence[token_idx + 2]
                                            if sp_token[1] in name_pos:
                                                speaker = speaker + ' ' + sp_token[0]
                                    elif next_token[1] == 'DT' and token_idx + 2 < len(sentence):
                                        sp_token = sentence[token_idx + 2]
                                        if (sp_token[1] in noun_pos or sp_token[0] in characters) and not sp_token[0].isupper():
                                            speaker = sp_token[0]
                                            speaker_pos = sp_token[1]
                                            if token_idx + 3 < len(sentence) and speaker_pos in name_pos \
                                                    and sentence[token_idx + 3][1] in name_pos:
                                                speaker = speaker + ' ' + sentence[token_idx + 3][0]

                            """if full_people.has_match(token[0]):
                                this_person = full_people.find_word_matches(token[0])[0]
                                if token[1] in name_pos and this_person[1] >= 0.5:
                                    this_person[0].add_name(token[0])
                                elif token[1] in noun_pos and token[1] != 'PRP':
                                    this_person[0].add_noun(token[0])
        
                                people_stack.append(full_people.find_word_matches(token[0])[0][0])"""
                            """possible_speakers = full_people.find_word_matches(speaker)
                            if len(possible_speakers) == 1 and speaker_pos != 'PRP':
                                if possible_speakers[0][1] >= 0.5:
                                    speaker_obj = possible_speakers[0][0]
                                    if speaker_pos in name_pos:
                                        speaker_obj.add_name(speaker)
                                    else:
                                        speaker_obj.add_noun(speaker)"""
                            #do something with this
                            avoid_list = recognized_pronouns[:]
                            if len(speech) > 0 and speaker.lower() in recognized_pronouns:
                                if recent_speaker_paragraph >= idx - 2:
                                    avoid_list.append(recent_speaker.lower())
                                for person_idx in range(-1, len(recent_person) * -1 - 1, -1):
                                    if recent_person[person_idx].lower() not in avoid_list:
                                        was_speaker = speaker
                                        was_speaker_pos = speaker_pos
                                        speaker = recent_person[person_idx]
                                        speaker_pos = 'NNP'
                                        """if full_people.has_match(speaker):
                                            matched_speaker = full_people.find_word_matches(speaker)[0][0]
                                            if was_speaker_pos == 'PRP':
                                                matched_speaker.add_pronoun(was_speaker)
                                            elif was_speaker_pos in name_pos:
                                                matched_speaker.add_name(was_speaker)
                                            elif was_speaker_pos in noun_pos:
                                                matched_speaker.add_noun(was_speaker)"""
                                        break

                            if speaker != '':
                                if speaker not in all_people:
                                    all_people[speaker] = 1
                                    """if speaker_pos in name_pos:
                                        full_people.add_name(speaker)
                                    elif speaker_pos in noun_pos and speaker_pos != 'PRP':
                                        full_people.add_noun(speaker)"""


                            # for person in recent_person:
                            #    all_people[person] = 1

                            non_quote_preceeding += 1
            if len(speaker) > 0 and len(speech) == 0:
                speaker = ''
                speaker_pos = ''
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
                        """if full_people.has_match(speaker):
                            matched_speaker = full_people.find_word_matches(speaker)[0][0]
                            if was_speaker_pos == 'PRP':
                                matched_speaker.add_pronoun(was_speaker)
                            elif was_speaker_pos in name_pos:
                                matched_speaker.add_name(was_speaker)
                                if len(matched_speaker.names) > 10:
                                    print(matched_speaker)
                                    exit(3)
                            elif was_speaker_pos in noun_pos:
                                matched_speaker.add_noun(was_speaker)"""
                        break
            """if len(mentioned_person) > 0:
                mentioned_matches = full_people.find_phrase_matches(mentioned_person)
                if len(mentioned_matches) > 0:
                    for word in mentioned_person:
                        mentioned_matches[0][0].add_name(word)"""
            if len(speech) > 0:
                if speaker not in character_speech:
                    character_speech[speaker] = []
                character_speech[speaker].append([' '.join([token[0] for token in speech]).replace('\n', ' ').replace('\t',' '), os.path.basename(original_file), idx, recent_speaker, recent_speaker_paragraph])
                print(speaker.upper(), ':\t', ' '.join([token[0] for token in speech]))
                out_lines.append(speaker.upper() + ':\t' + ' '.join([token[0] for token in speech]))
                print('mentioned_person', mentioned_person, 'recent_person:', ' '.join(recent_person))
                out_lines.append('mentioned_person:' + str(mentioned_person) + ' recent_person: ' + ' '.join(recent_person))
                out_lines.append('')
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
        with open(output_file, 'w', encoding='utf-16') as talk_file:
            for line in out_lines:
                talk_file.write(line + '\n')
        talk_file.close()
        with open(os.path.join('/Users/brian/Google Drive/IdolBots','character_dialog_' + current_source + '_' + os.path.basename(original_file)), 'w', encoding='utf-16') as od:   # '.txt'
            for char_name in sorted([key for key in character_speech]):
                for items in character_speech[char_name]:
                    od.write(char_name)
                    for value in items:
                        od.write('\t' + str(value))
                    od.write('\n')
        character_speech = {}