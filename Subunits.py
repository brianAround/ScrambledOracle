from enum import Enum
from statistics import median

import nltk


class WCPreprocess:

     def divide_into_subunits(self, lines):
        return [[line] for line in lines]


class WCLineCounts(WCPreprocess):

    def __init__(self, block_size=20):
        self.lines_per_subunit = block_size

    def divide_into_subunits(self, lines):
        subunits = []
        current_subunit = []
        for idx in range(len(lines)):
            if len(lines[idx]) > 0:
                current_subunit.append(lines[idx])
            if len(current_subunit) >= self.lines_per_subunit:
                subunits.append(current_subunit)
                current_subunit = []
        if len(current_subunit) > 0:
            subunits.append(current_subunit)
        return subunits

class WCParagraphs(WCPreprocess):

    def divide_into_subunits(self, lines):
        subunits = []
        widths = [len(line) for line in lines]
        midpoint = median(widths)
        current_subunit = []
        for line_idx in range(len(widths)):
            if widths[line_idx] > 0:
                current_subunit.append(lines[line_idx])
            if widths[line_idx] < midpoint:
                if len(current_subunit) > 0:
                    subunits.append(current_subunit)
                    current_subunit = []
        if len(current_subunit) > 0:
            subunits.append(current_subunit)
        return subunits


class WCSentences(WCPreprocess):

    def divide_into_subunits(self, lines):
        source_text = " ".join(lines)
        sentences = nltk.sent_tokenize(source_text)
        subunits = [[sentence] for sentence in sentences if len(sentence) > 0]
        return subunits


class WCTermCount(WCPreprocess):

    def __init__(self, min_weight:int, max_weight=None, use_pos_tags=None, stopwords:dict=None):
        self.min_terms = min_weight
        self.max_terms = max_weight if max_weight is not None else min_weight * 2
        self.pos_filter = use_pos_tags if use_pos_tags is not None else ['JJ','JJR','JJS','RB','RBR','RBS']
        self.exceptions = {"max_terms": [], 'min_terms': [], 'other': []}
        self.stopwords = stopwords
        self.stopwords_filepath = 'SearchIgnoreList.txt'

    def load_ignore_list(self):
        stopwords = {}
        with open(self.stopwords_filepath,'r') as ignore_file:
            lines = ignore_file.readlines()
            for line in lines:
                stopwords[line.strip()] = 1
        return stopwords

    def divide_into_subunits(self, lines):
        if self.stopwords is None:
            self.stopwords = self.load_ignore_list()
        subunits = []
        source_text = " ".join(lines)
        sentences = nltk.sent_tokenize(source_text)
        worded_sentences = [nltk.word_tokenize(sentence) for sentence in sentences]
        tagged_sentences = [nltk.pos_tag(sentence) for sentence in worded_sentences]
        current_subunit = []
        current_words = {}
        for idx in range(len(tagged_sentences)):
            for beat in tagged_sentences[idx]:
                if beat[1] in self.pos_filter and beat[0] not in current_words and beat[0] not in self.stopwords:
                    current_words[beat[0]] = 1
            current_subunit.append(sentences[idx])
            if len(current_words) >= self.min_terms:
                if len(current_words) <= self.max_terms:
                    subunits.append(current_subunit)
                else:
                    self.exceptions['max_terms'].append(current_subunit)
                current_subunit = []
                current_words = {}

        if len(current_words) < self.min_terms:
            self.exceptions['min_terms'].append(current_subunit)
        else:
            self.exceptions['other'].append(current_subunit)

        return subunits
