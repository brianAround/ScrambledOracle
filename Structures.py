import codecs
import configparser
import os
import random
import string
import time
import nltk
from nltk.corpus import conll2000
from WordChain import WordChain, full_stop_beats
from Oracle import Oracle
from ConsecutiveNPChunker import ConsecutiveNPChunker, ConsecutiveNPChunkTagger


class UnigramChunker(nltk.ChunkParserI):
    def __init__(self, train_sents):
        train_data = [[(t, c) for w, t, c in nltk.chunk.tree2conlltags(sent)]
                  for sent in train_sents]
        self.tagger = nltk.UnigramTagger(train_data)

    def parse(self, sentence):
        pos_tags = [pos for (word, pos) in sentence]
        tagged_pos_tags = self.tagger.tag(pos_tags)
        chunktags = [chunktag for (pos, chunktag) in tagged_pos_tags]
        conlltags = [(word, pos, chunktag) for ((word, pos), chunktag)
                     in zip(sentence, chunktags)]
        return nltk.chunk.conlltags2tree(conlltags)


class BigramChunker(nltk.ChunkParserI):
    def __init__(self, train_sents):
        train_data = [[(t, c) for w, t, c in nltk.chunk.tree2conlltags(sent)]
                  for sent in train_sents]
        self.tagger = nltk.BigramTagger(train_data)

    def parse(self, sentence):
        pos_tags = [pos for (word, pos) in sentence]
        tagged_pos_tags = self.tagger.tag(pos_tags)
        chunktags = [chunktag for (pos, chunktag) in tagged_pos_tags]
        conlltags = [(word, pos, chunktag) for ((word, pos), chunktag)
                     in zip(sentence, chunktags)]
        return nltk.chunk.conlltags2tree(conlltags)


def get_uni_chunker():
    train_sents = conll2000.chunked_sents('train.txt', chunk_types=['NP'])
    unigram_nunker = UnigramChunker(train_sents)
    return unigram_nunker


def get_bi_chunker():
    train_sents = conll2000.chunked_sents('train.txt', chunk_types=['NP'])
    bigram_nunker = BigramChunker(train_sents)
    return bigram_nunker


def get_consNPChunker():
    train_sents = conll2000.chunked_sents('train.txt', chunk_types=['NP'])
    train_sents = random.choices(train_sents, k=500)
    cnp_chunker = ConsecutiveNPChunker(train_sents)
    return cnp_chunker


def get_chunker():
    return get_consNPChunker()


def write_pos_file(file_path, ideal_line_length=80):
    last_beat = ""
    beat_list = []
    file_size = min(32, os.path.getsize(file_path))
    quotes = []
    with open(file_path, 'rb') as f_enc:
        raw = f_enc.read(file_size)
        if raw.startswith(codecs.BOM_UTF8):
            encoding = 'utf-8-sig'
        else:
            encoding = 'utf-8'

    is_spoken = False
    is_starter = True
    current_speech = []
    source_beat = 0
    parser = get_chunker()

    pos_filename = file_path + '.pos'
    with open(pos_filename, 'w', encoding='utf-16') as pos_handle:
        pos_handle.write('Parts of Speech Map for ' + file_path + '\n\n')
    with open(file_path, 'r', encoding=encoding) as f_handle:
        source_text = f_handle.readlines()
        source_text = source_text[3:]
        source_text = [line for line in source_text if line[0] != '#']
        source_text = " ".join(source_text).strip('\n')
        sentences = nltk.sent_tokenize(source_text)
        sentences = [nltk.word_tokenize(sentence) for sentence in sentences]
        tagged_sentences = [nltk.pos_tag(sentence) for sentence in sentences]
        sentence_number = 0
        for sentence in tagged_sentences:
            sentence_number += 1
            with open(pos_filename, 'a+', encoding='utf-16') as pos_handle:
                pos_handle.write('\n\nSentence ' + str(sentence_number) + ':\n')
            beat_list = []
            pos_list = []
            is_starter = True
            line_length = 0
            for idx in range(len(sentence)):
                current_beat = sentence[idx][0]
                current_pos = sentence[idx][1]
                beat_length = max(len(current_beat), len(current_pos)) + 1
                if line_length + beat_length > ideal_line_length:
                    with open(pos_filename, 'a+', encoding='utf-16') as pos_handle:
                        pos_handle.write("".join(beat_list) + '\n')
                        pos_handle.write("".join(pos_list) + '\n\n')
                    beat_list = []
                    pos_list = []
                    line_length = 0
                current_beat = current_beat.rjust(beat_length)
                current_pos = current_pos.rjust(beat_length)
                line_length += beat_length
                beat_list.append(current_beat)
                pos_list.append(current_pos)

            result = parser.parse(sentence)

            with open(pos_filename, 'a+', encoding='utf-16') as pos_handle:
                pos_handle.write("".join(beat_list) + '\n')
                pos_handle.write("".join(pos_list) + '\n\n')
                pos_handle.write('Noun Phrases:\n')
                for item in result:
                    if type(item) is nltk.tree.Tree:
                        pos_handle.write(" ".join([word[0] for word in item]) + '\n')
                pos_handle.write('\n')

write_pos_file('sources/dougadams/RestaurantAtTheEndOfTheUniverse.txt')
