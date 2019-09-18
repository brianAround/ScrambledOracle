import nltk
import os

source_folder = os.path.join('sources','dougadams')


# source_folder = os.path.join('sources','various')
document_file = 'HitchhikersGuideToTheGalaxy.txt'

original_file = os.path.join(source_folder, document_file)
output_file = os.path.join(source_folder, document_file.split('.')[0] + '.talk')
output_file = None

grammar = r"""

  CV: {<RB.*>*<VB.*><:>*<CC><RB.*>*<VB.*><:>*}
  NP: {<DT|CD|RB.*|JJ.*|NN.*|PRP.*>*<NN.*|PRP>+}          # Chunk sequences of DT, JJ, NN
  NP: {<DT|CD|RB.*|JJ.*><IN><NP>}
  NP: {<NP><NP|CC|,>+<NP>}
  PP: {<IN><NP>}
  NNP: {<NNP|NNPS>*<IN><NNP|NNPS>}
  TON: {<TO><NP|VP>}
  
  VP: {<VB.*><TO><VB><RP><RB>*<WPH>}
  VP: {<VB.*><VBN>+<RB|TON>*}
  VP: {<VB.*><RB>+}
  VP: {<MD><VB>}
  VP: {<VB.*|CV><RB>*<NP|PP|CLAUSE>+} # Chunk verbs and their arguments
  PP: {<IN><CLAUSE>}               # Chunk prepositions followed by NP
  WPH: {<WP><NP><VB.*><VBN><TON>}
  CLAUSE: {<NP|PNP|OWN><VP><,|CC|VP>*}          # Chunk NP, VP

  """
#   VP: {<VB.*|CV><RP|RB|NL|NP|PP|CLAUSE|WPH>*}
#  NP  {<DT>*<JJ><,><JJ><NN.*>}

"""The wood itself was almost black, but the carvings were slightly lighter, and hurt the eyes if you tried to make out precisely what they were supposed to be."""
#  DT   NN   PRP   VBD   RB    JJ  , CC  DT     NNS    VBD    RB      JJR  , CC  VBD  DT  NNS  IN PRP VBD   TO VB   RP    RB       WP  PRP  VBD    VBN    TO VB .
#  <      NP     > <VP            > <


def map_structure(paragraphs, grammar, destination_file=None):
    cp = nltk.RegexpParser(grammar)
    if destination_file is None:
        for idx in range(len(paragraphs)):
            print(idx)
            for line in paragraphs[idx]:
                print(line)
                print(cp.parse(line))
                tree = cp.parse(line)
                tree.draw()
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

map_structure(paragraphs, grammar, destination_file=output_file)

print('Done')

"""
    '',
    '"Are you pleased with yourself?" said the midwife.',
    '"Eh? Oh. Yes. As a matter of fact, yes. Why?"'
"""

# Theory: Sentences that start with a CD - Cardinal and then a RP participle are somewhat inverted, postponing the
# introduction of the subject by starting with a description of its Positioning.  There's not enough evidence in HHGG