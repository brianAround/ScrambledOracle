from ConsecutiveAllChunkTagger import ConsecutiveAllChunker
import nltk
from nltk.corpus import conll2000
import os
import pickle
import time

source_folder = os.path.join('sources','dougadams')

retrain = True
max_sample_size = 100000

# source_folder = os.path.join('sources','various')
document_file = 'HitchhikersGuideToTheGalaxy.txt'

original_file = os.path.join(source_folder, document_file)
output_file = os.path.join(source_folder, document_file.split('.')[0] + '.talk')
# output_file = None

test_sents = conll2000.chunked_sents('test.txt')
train_sents = conll2000.chunked_sents('train.txt')
train_sents = train_sents[:max_sample_size]


# all_chunker = ConsecutiveNPChunker([])
if os.path.isfile('all_chunker.pickle') and not retrain:
    print('loading all chunker from pickle:', time.asctime())
    with open('all_chunker.pickle', 'rb') as load_chunker:
        all_chunker = pickle.load(load_chunker)
    print('all chunker loaded:', time.asctime())
else:
    print('training all chunker with', len(train_sents), 'sentences:', time.asctime())
    all_chunker = ConsecutiveAllChunker(train_sents)
    print('all chunker trained:', time.asctime())
    print('saving np chunker:', time.asctime())
    with open('all_chunker.pickle', 'wb') as save_chunker:
        pickle.dump(all_chunker, save_chunker)
    print('all chunker saved:', time.asctime())

input('hit enter:')
grammar = r"""

  PP: {<IN><NP>}
  CV: {<RB.*>*<VB.*><:|,>*<CC><RB.*>*<VB.*><:|,>*}
  # NP: {<DT|CD|RB.*|JJ.*|NN.*|POS|PRP.*>*<NN.*|PRP>+}          # Chunk sequences of DT, JJ, NN
  # NP: {<DT|CD|RB.*|JJ.*><IN><NP>}
  # NP: {<NP><NP|CC|,>+<NP>}
  NP: {<NP><,><NP>*<VP>}
  NNP: {<NNP|NNPS>*<IN><NNP|NNPS>}
  TON: {<TO><NP|VP>}
  VP: {<RB>*<VB.*><NP><RP|RB>}
  VP: {<RB>*<VB.*><TO><VB><RP><RB>*<WPH>}
  VP: {<RB>*<VB.*><VBN>+<JJ|RB|TON>*}
  VP: {<RB>*<VB.*><RB>+}
  VP: {<MD><VB>}
  VP: {<RB>*<VB.*><,>}
  VP: {<RB>*<VB.*|CV><RB>*<NP|PP|CLAUSE>+} # Chunk verbs and their arguments
  PP: {<IN><CLAUSE>}               # Chunk prepositions followed by NP
  WPH: {<WP><NP><VB.*><VBN><TON>}
  CLAUSE: {<NP|PNP|OWN><VP><,|CC|VP|CV>*}          # Chunk NP, VP

  """
#   VP: {<VB.*|CV><RP|RB|NL|NP|PP|CLAUSE|WPH>*}
#  NP  {<DT>*<JJ><,><JJ><NN.*>}

"""The wood itself was almost black, but the carvings were slightly lighter, and hurt the eyes if you tried to make out precisely what they were supposed to be."""
#  DT   NN   PRP   VBD   RB    JJ  , CC  DT     NNS    VBD    RB      JJR  , CC  VBD  DT  NNS  IN PRP VBD   TO VB   RP    RB       WP  PRP  VBD    VBN    TO VB .
#  <      NP     > <VP            >      <NP        >                                 <NP    >   <NP>                                  <NP>


# Prepositions and what they suggest:
# in - Modified is contained by the object. Not necessarily as "part of" something else, but just "in" it or having that state.
# of - Modified is a member of the object. Though, in some cases it could be another way of saying that the modified
#               is actually part of the "set" of all things of that class that belong to the object or are contained by the object.
# with - Modified is a sibling of the object in some way, possibly described by an additional "in" prepositional phrase.

def map_structure(paragraphs, grammar, destination_file=None):
    cp = nltk.RegexpParser(grammar)
    if destination_file is None:
        for idx in range(len(paragraphs)):
            print(idx)
            for line in paragraphs[idx]:
                print(line)
                print(cp.parse(line))
                s_tree = cp.parse(line)
                if idx >= 84 and len(s_tree) >= 1 and type(s_tree[0]) == type(s_tree) and s_tree[0].label() == 'CLAUSE':
                    print('Identified Subject:', s_tree[0][0])
                    s_tree.draw()
    else:
        with open(destination_file, 'w') as write_doc:
            for idx in range(len(paragraphs)):
                write_doc.write('Paragraph (' + str(idx) + ')\n')
                for line in paragraphs[idx]:
                    write_doc.write(' '.join([token[0] for token in line]) + '\n')
                    write_doc.write(str(cp.parse(line)) + '\n')
        write_doc.close()

def map_structure2(paragraphs, cp:nltk.ChunkParserI, destination_file=None):
    cp_regex = nltk.RegexpParser(grammar)
    if destination_file is None:
        for idx in range(len(paragraphs)):
            print(idx)
            for line in paragraphs[idx]:
                print(line)
                s_tree = cp.parse(line)
                print(s_tree)
                if idx >= 84 and len(s_tree) >= 1 and type(s_tree[0]) == type(s_tree) and s_tree[0].label() == 'CLAUSE':
                    print('Identified Subject:', s_tree[0][0])
                    s_tree.draw()
    else:
        with open(destination_file, 'w') as write_doc:
            for idx in range(len(paragraphs)):
                write_doc.write('Paragraph (' + str(idx) + ')\n')
                for line in paragraphs[idx]:
                    write_doc.write(' '.join([token[0] for token in line]) + '\n')
                    write_doc.write(str(cp.parse(line)) + '\n')
        write_doc.close()



with open(original_file, 'r') as read_doc:
    text = read_doc.read()
read_doc.close()

source_text = text
paragraphs = text.split('\n\n')
paragraphs = [nltk.sent_tokenize(para_text) for para_text in paragraphs]
paragraphs = [[nltk.word_tokenize(sent) for sent in sentences] for sentences in paragraphs]
paragraphs = [nltk.pos_tag_sents(sentences) for sentences in paragraphs]

map_structure2(paragraphs, all_chunker, destination_file=output_file)

print('Done')

"""
    '',
    '"Are you pleased with yourself?" said the midwife.',
    '"Eh? Oh. Yes. As a matter of fact, yes. Why?"'
"""

# Theory: Sentences that start with a CD - Cardinal and then a RP participle are somewhat inverted, postponing the
# introduction of the subject by starting with a description of its Positioning.  There's not enough evidence in HHGG