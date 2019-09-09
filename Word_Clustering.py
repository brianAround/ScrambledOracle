import codecs
import nltk
import os
from statistics import median
import string

import time

from UnionFind import *
from WordChain import WordChain, full_stop_beats

distances = {}


def calculate_distance(node1, node2):
    diff = node1 ^ node2
    # weight = max(bin(node1).count("1"), bin(node2).count("1"))
    # dist = bin(diff).count("1") - weight
    dist = bin(diff).count("1")
    return dist


def lookup_distance(node1, node2):
    if node1 in distances:
        if node2 in distances[node1]:
            return distances[node1][node2]
    return None


def store_distance(node1, node2, dist):
    if node1 not in distances:
        distances[node1] = {}
    distances[node1][node2] = dist


def distance(node1, node2):
    dist = lookup_distance(node1, node2)
    if dist is None:
        dist = calculate_distance(node1, node2)
        store_distance(node1, node2, dist)
    return dist


class WordClustering:
    def __init__(self):
        self.pairings = {}

    @staticmethod
    def get_pairing_key(part1, part2):
        part1 = part1.lower()
        part2 = part2.lower()
        if part1 > part2:
            return (part2, part1,)
        else:
            return (part1, part2,)

    def compile_word_tally(self, file_path, use_pos_tags=['JJ','JJR','JJS','RB','RBR','RBS']):
        pairings = {}
        source_text = []
        word_list = []
        word_lookup = {}
        with open(file_path, 'r') as f_handle:
            source_text = f_handle.readlines()
        source_text = source_text[3:]
        source_text = [line.strip() for line in source_text if line[0] != '#']

        negations = ['not',"n't"]
        subunits = self.divide_into_subunits(source_text)
        subunit_number = 1
        profiles = []
        for paragraph in subunits:
            source_text = " ".join(paragraph)
            sentences = nltk.sent_tokenize(source_text)
            sentences = [nltk.word_tokenize(sentence) for sentence in sentences]
            tagged_sentences = [nltk.pos_tag(sentence) for sentence in sentences]
            current_profile = [0] * len(word_list)
            for sentence in tagged_sentences:
                apply_not = -1
                for idx in range(len(sentence)):
                    current_beat = sentence[idx][0].lower()
                    current_pos = sentence[idx][1]
                    if apply_not == idx:
                        current_beat = '!' + current_beat
                    if current_pos in use_pos_tags:
                        if current_beat in negations:
                            apply_not = idx + 1
                        else:
                            if current_beat not in word_lookup:
                                word_lookup[current_beat] = len(word_list)
                                word_list.append(current_beat)
                            while word_lookup[current_beat] >= len(current_profile):
                                current_profile.append(0)
                            current_profile[word_lookup[current_beat]] += 1
            profiles.append(current_profile)
            # print('Subunit', subunit_number, current_profile)
            # print('Words:',[word_list[idx] for idx in range(len(word_list)) if current_profile[idx] > 0])
            subunit_number += 1
        word_tally = {'word_list': word_list,
                      'word_lookup': word_lookup,
                      'profiles': profiles}
        print('Unique words found:', len(word_list))
        return word_tally

    def divide_into_subunits(self, lines):
        return self.divide_by_profile_weight(lines)

    def divide_by_line_count(self, lines, block_size=20):
        subunits = []
        current_subunit = []
        for idx in range(len(lines)):
            if len(lines[idx]) > 0:
                current_subunit.append(lines[idx])
            if len(current_subunit) >= block_size:
                subunits.append(current_subunit)
                current_subunit = []
        if len(current_subunit) > 0:
            subunits.append(current_subunit)
        return subunits

    @staticmethod
    def divide_by_paragraphs(lines):
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

    def divide_by_profile_weight(self, lines, min_weight=8, use_pos_tags=['JJ','JJR','JJS','RB','RBR','RBS']):
        subunits = []
        source_text = " ".join(lines)
        sentences = nltk.sent_tokenize(source_text)
        worded_sentences = [nltk.word_tokenize(sentence) for sentence in sentences]
        tagged_sentences = [nltk.pos_tag(sentence) for sentence in worded_sentences]
        current_subunit = []
        current_words = {}
        for idx in range(len(tagged_sentences)):
            for beat in tagged_sentences[idx]:
                if beat[1] in use_pos_tags and beat[0] not in current_words:
                    current_words[beat[0]] = 1
            current_subunit.append(sentences[idx])
            if len(current_words) >= min_weight:
                subunits.append(current_subunit)
                current_subunit = []
                current_words = {}
        if len(current_subunit) > 0 and len(current_words) > 0:
            subunits.append(current_subunit)
        return subunits



    def calculate_word_penetration(self, word_tally:dict):
        profiles_for_word = []
        for idx in range(len(word_tally['word_list'])):

            occurances = len([p for p in [profile for profile in word_tally['profiles'] if len(profile) > idx] if p[idx] > 0])
            profiles_for_word.append(occurances)
        return profiles_for_word

    def get_optimized_profiles(self, word_tally, min_penetration=3, flatten=True):
        optimized = {}
        word_list = sorted(word_tally['word_list'])
        word_lookup = word_tally['word_lookup']
        if 'penetration' not in word_tally:
            word_tally['penetration']= self.calculate_word_penetration(word_tally)
        penetration = word_tally['penetration']
        target_indices = []
        clean_profiles = []
        nodes = []
        for idx in range(len(word_list)):
            col_idx = word_lookup[word_list[idx]]
            if penetration[col_idx] >= min_penetration:
                target_indices.append(col_idx)
        for profile in word_tally['profiles']:
            new_profile = []
            for col_idx in target_indices:
                if len(profile) > col_idx and profile[col_idx] > 0:
                    new_profile.append(1 if flatten else profile[col_idx])
                else:
                    new_profile.append(0)
            clean_profiles.append(new_profile)
            if flatten:
                nodes.append(int("".join([str(position) for position in new_profile]),2))
        optimized = {'indices': target_indices, 'profiles': clean_profiles}
        if flatten:
            optimized['nodes'] = nodes
        return optimized

    def full_clustering(self, cluster_distance, nodes):
        node_list = sorted([node for node in nodes], key=lambda x: bin(x).count("1"))
        node_weight = [bin(node).count("1") for node in node_list]
        uf = UTUnionFind(node_list)
        clusters = len(node_list)
        for i in range(len(node_list) - 1):
            if node_weight[i] > 7:
                for j in range(i + 1, len(node_list)):
                    if node_weight[j] > 7:
                        # if node_weight[j] - node_weight[i] > cluster_distance:
                            # print('i:', i, ' wgt:', node_weight[i], 'j:', j, node_weight[j])
                            # break
                        if uf.find(node_list[i]) != uf.find(node_list[j]) and distance(node_list[i], node_list[j]) <= cluster_distance:
                            uf.union(node_list[i], node_list[j])
                            clusters -= 1
            if i % 100 == 0:
                print(i, ':', clusters, 'time:', time.asctime())
        return uf.get_clusters()







filename = 'sources/dougadams/RestaurantAtTheEndOfTheUniverse.txt'

wc = WordClustering()
wt = wc.compile_word_tally(filename)
opt = wc.get_optimized_profiles(wt)

write_to_file = True




distance_start = 8
distance_end = 12
filename_root = filename.split('/')[-1].split('.')[0]
range_desc = str(distance_start) + 'to' + str(distance_end)
file_output = os.path.join('datafile', filename_root + '_' + range_desc + '.txt')
if write_to_file:
    with open(file_output, 'w') as outfile:
        outfile.write('Clustering output: ')
        outfile.write(time.asctime() + '\n\n')
for cluster_distance in range(distance_start, distance_end + 1):
    print('Calculating for cluster distance', cluster_distance)
    result = wc.full_clustering(cluster_distance, opt['nodes'])
    print(len(result), 'particles')
    grouped = [key for key in result if len(result[key]) > 1]
    print(len(grouped), 'grouped sets found')
    if write_to_file:
        with open(file_output, 'a+') as outfile:
            outfile.write('Calculating for cluster distance ' + str(cluster_distance) + '\n')
            outfile.write(str(len(result)) + ' particles\n')
            outfile.write(str(len(grouped)) + ' grouped sets found\n')
    if len(grouped) > 1:
        lines = []
        for group_label in grouped:
            if group_label != 0:
                group_frequency = {}
                current_line = str(group_label) + ' : ' + str(len(result[group_label])) + ' items'
                print(current_line)
                lines.append(current_line)
                for opt_idx in range(len(opt['nodes'])):
                    if opt['nodes'][opt_idx] in result[group_label]:
                        opt_profile = opt['profiles'][opt_idx]
                        current_words = [wt['word_list'][opt['indices'][pos_idx]] for pos_idx in range(len(opt_profile)) if opt_profile[pos_idx] > 0]
                        current_line = str(current_words)
                        print(current_line)
                        lines.append(current_line)
                        for word in current_words:
                            if word not in group_frequency:
                                group_frequency[word] = 0
                            group_frequency[word] += 1
                current_line = str(group_frequency)
                print(current_line)
                lines.append(current_line)
        if write_to_file:
            with open(file_output, 'a+') as outfile:
                outfile.writelines([text + '\n' for text in lines])
                outfile.write('\n\n')

# I'm starting to see the value of K-Means clustering: once the distance gets to be 2, it's already clumping weird stuff in small paragraphs


# clustering should be based not on the frequency of individual pairs, but on the the frequency of the words appearing near each other.
# like a set of binary flags.