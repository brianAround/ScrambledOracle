import codecs
import random
from collections import namedtuple
from math import sqrt

from Subunits import *
import nltk
import os
import statistics

import string

import time

from UnionFind import *
from WordChain import WordChain, full_stop_beats

distances = {}

Centroid = namedtuple("Centroid", ['name','profile','node'])


def calculate_distance(node1, node2):
    diff = node1 ^ node2
    # weight_diff = abs(bin(node1).count("1") - bin(node2).count("1"))
    # dist = bin(diff).count("1") - weight_diff
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
    def __init__(self, preprocessor:WCPreprocess=None):
        self.preprocessor = preprocessor if preprocessor is not None else WCPreprocess()
        self.pos_filter = ['JJ','JJR','JJS','RB','RBR','RBS']
        self.pairings = {}
        self.min_centroid_weight = 3
        self.stopwords = None
        self.stopwords_filepath = 'SearchIgnoreList.txt'

    @staticmethod
    def get_pairing_key(part1, part2):
        part1 = part1.lower()
        part2 = part2.lower()
        if part1 > part2:
            return (part2, part1,)
        else:
            return (part1, part2,)

    def compile_word_tally_for_files(self, file_list, use_pos_tags=None):
        shared_tally = None
        for filename in file_list:
            shared_tally = self.compile_word_tally(filename, use_pos_tags, shared_tally)
        return shared_tally

    def load_ignore_list(self):
        stopwords = {}
        with open(self.stopwords_filepath,'r') as ignore_file:
            lines = ignore_file.readlines()
            for line in lines:
                stopwords[line.strip()] = 1
        return stopwords

    def compile_word_tally(self, file_path, use_pos_tags=None, extend_tally=None):
        if use_pos_tags is None:
            use_pos_tags = self.pos_filter
        if self.stopwords is None:
            self.stopwords = self.load_ignore_list()
        profiles = []
        word_list = []
        word_lookup = {}
        if extend_tally is not None:
            profiles = extend_tally['profiles']
            word_list = extend_tally['word_list']
            word_lookup = extend_tally['word_lookup']
        with open(file_path, 'r') as f_handle:
            source_text = f_handle.readlines()
        source_text = source_text[3:]
        source_text = [line.strip() for line in source_text if line[0] != '#']

        negations = ['not',"n't"]
        subunits = self.divide_into_subunits(source_text)
        subunit_number = 1
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
                    if current_pos in use_pos_tags and current_beat not in self.stopwords:
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
        return self.preprocessor.divide_into_subunits(lines)

    def initialize_centroids(self, opt, count):
        result = []
        selected = {}
        range = len(opt['profiles'])
        nodes = {}
        while len(result) < min(count, range - len(selected)):
            item = random.randint(0, range - 1)
            while item in selected or sum(opt['profiles'][item]) < self.min_centroid_weight:
                item = random.randint(0, range -1)

            selected[item] = 1
            profile = opt['profiles'][item]
            node = opt['nodes'][item]
            if node not in nodes:
                profile_word_list = self.build_profile_word_list(profile, opt['word_list'])
                cent_name = str(profile_word_list)
                centroid = Centroid(cent_name, profile, node)
                result.append(centroid)
        return result

    def build_profile_word_list(self, profile, relevant_word_list):
        profile_word_list = [relevant_word_list[pos_idx] for pos_idx in range(len(profile)) if profile[pos_idx] > 0]
        return profile_word_list

    def calculate_word_penetration(self, word_tally:dict):
        profiles_for_word = []
        for idx in range(len(word_tally['word_list'])):

            occurances = len([p for p in [profile for profile in word_tally['profiles'] if len(profile) > idx] if p[idx] > 0])
            profiles_for_word.append(occurances)
        return profiles_for_word

    def get_optimized_profiles(self, word_tally, min_penetration=1, flatten=True):
        optimized = {}
        word_list = word_tally['word_list']
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
                nodes.append(self.convert_profile_to_node(new_profile))
        optimized = {'word_list': word_list, 'indices': target_indices, 'profiles': clean_profiles}
        if flatten:
            optimized['nodes'] = nodes
        return optimized

    def convert_profile_to_node(self, new_profile):
        return int("".join([str(position) for position in new_profile]), 2)

    def identify_mean(self, profiles):
        mean = []
        if len(profiles) > 0:
            width = max([len(profile) for profile in profiles])
            # mean = [0] * width
            # last_good_score = self.total_profile_distance(mean, profiles)
            # for idx in range(width):
            #     mean[idx] = 1
            #     new_score = self.total_profile_distance(mean, profiles)
            #     if new_score > last_good_score:
            #         mean[idx] = 0
            #     else:
            #         last_good_score = new_score
            word_totals = [sum([p[widx] for p in profiles if len(p) > widx]) for widx in range(width)]
            levels = list(set([value for value in word_totals if value > 0]))
            min_total = statistics.median(levels)
            # min_total = statistics.mean([value for value in word_totals if value > 0])
            mean = [1 if total >= min_total else 0 for total in word_totals]
        return mean

    def total_profile_distance(self, mean, profiles):
        current_total_distance = sum(
            [sum([abs(mean[idx] - (0 if len(profile) <= idx else profile[idx])) for idx in range(len(profile))]) for
             profile in profiles])
        return current_total_distance

    def assign_nodes(self, centroids, opt):
        clusters = {}
        for centroid in centroids:
            clusters[centroid.name] = []
        if 'centroid' in opt:
            opt['last_centroid'] = opt['centroid']
        opt['centroid'] = []
        for idx in range(len(opt['profiles'])):
            node = opt['nodes'][idx]
            profile = opt['profiles'][idx]
            closest_centroid = centroids[0]
            closest_distance = distance(closest_centroid.node, node)
            for centroid in centroids:
                distance_to = distance(centroid.node, node)
                if distance_to < closest_distance:
                    closest_centroid = centroid
                    closest_distance = distance_to
                elif distance_to == closest_distance:
                    if len(clusters[centroid.name]) < len(clusters[closest_centroid.name]):
                        closest_centroid = centroid
                        closest_distance = distance_to
            clusters[closest_centroid.name].append(profile)
            opt['centroid'].append(closest_centroid.name)

        return clusters

    def full_clustering(self, count, opt, max_iterations=20):
        centroids = self.initialize_centroids(opt, count)
        iterations = 0
        changes_made = True
        while iterations < max_iterations and changes_made:
            clusters = self.assign_nodes(centroids, opt)
            new_centroids = []

            if 'last_centroids' in opt and len([pro_idx for pro_idx in range(len(opt['profiles'])) if opt['centroids'][pro_idx] != opt['last_centroids'][pro_idx]]) == 0:
                changes_made = False
            if changes_made:
                for old_centroid in centroids:
                    if old_centroid.name in clusters:
                        new_profile = self.identify_mean(clusters[old_centroid.name])
                        if len(new_profile) > 0:
                            new_node = self.convert_profile_to_node(new_profile)
                            centroid = Centroid(old_centroid.name, new_profile, new_node)
                            new_centroids.append(centroid)
                centroids = new_centroids
            iterations += 1
            if not changes_made:
                print('Achieved stable state!')
            print('Iteration', iterations)
            grouped = [key for key in clusters if len(clusters[key]) > 1]
            print('Groups formed', len(grouped))
        return clusters




def get_relative_file_list(source_folder):
    file_listing = [f for f in os.listdir(source_folder) if f.endswith(".txt")]
    file_listing = [os.path.join(source_folder, f) for f in file_listing]
    file_listing = [f for f in file_listing if os.path.isfile(f)]
    return file_listing

filename = ''
source = 'dougadams'
fileset = []

filename = 'sources/various/expectations.txt'
# fileset = get_relative_file_list(os.path.join('sources','dougadams'))

pos_filter = ['JJ','JJR','JJS','RB','RBR','RBS']
preprocessor = WCTermCount(3, 4, pos_filter)
wc = WordClustering(preprocessor)
wt = {}
if len(fileset) == 0:
    wt = wc.compile_word_tally(filename)
else:
    wt = wc.compile_word_tally_for_files(fileset)

opt = wc.get_optimized_profiles(wt)

write_to_file = True

distance_start = 1000
distance_end = 1000
distance_step = max((distance_end - distance_start) // 3, 1)
if len(fileset) == 0:
    filename_root = filename.split('/')[-1].split('.')[0]
else:
    filename_root = source + '_'

repeat_number = 3
for full_iteration in range(repeat_number):
    for cluster_distance in range(distance_start, distance_end + 1, distance_step):
        range_desc = 'kmeans' + str(cluster_distance)
        file_output = os.path.join('datafile', filename_root + '_' + range_desc + '_Iter' + str(full_iteration) + '.txt')
        if write_to_file:
            with open(file_output, 'w') as outfile:
                outfile.write('K-Means Clustering output: ')
                outfile.write(time.asctime() + '\n\n')
        print('Calculating k-means for k=', cluster_distance)
        result = wc.full_clustering(cluster_distance, opt)
        print(len(result), 'particles')
        grouped = sorted([key for key in result if len(result[key]) > 1], key=lambda x: len(result[x]), reverse=True)
        print(len(grouped), 'grouped sets found')
        if write_to_file:
            with open(file_output, 'a+') as outfile:
                outfile.write('Calculating k-means for k=' + str(cluster_distance) + '\n')
                outfile.write(str(len(result)) + ' particles\n')
                outfile.write(str(len(grouped)) + ' grouped sets found\n')
        if len(grouped) > 1:
            lines = []
            for group_label in grouped:
                if group_label != 0:
                    group_frequency = {}
                    centroid_profile = wc.identify_mean(result[group_label])
                    final_words = str(wc.build_profile_word_list(centroid_profile, opt['word_list']))
                    current_line = str(final_words) + ' : ' + str(len(result[group_label])) + ' items'
                    print(current_line)
                    lines.append(current_line)
                    current_line = 'original profile: ' + str(group_label)
                    print(current_line)
                    lines.append(current_line)
                    for profile in result[group_label]:
                        current_words = wc.build_profile_word_list(profile, opt['word_list'])
                        current_line = '    ' + str(current_words)
                        print(current_line)
                        lines.append(current_line)
                        for word in current_words:
                            if word not in group_frequency:
                                group_frequency[word] = 0
                            group_frequency[word] += 1
                    ordered_terms = sorted([key for key in group_frequency], key=lambda x: group_frequency[x], reverse=True)
                    current_line = 'Term frequency: { ' + ", ".join(["'" + key + "': " + str(group_frequency[key]) for key in ordered_terms]) + ' }'
                    print(current_line + '\n')
                    lines.append(current_line)
                    lines.append('')
            if write_to_file:
                with open(file_output, 'a+') as outfile:
                    outfile.writelines([text + '\n' for text in lines])
                    outfile.write('\n\n')

# I'm starting to see the value of K-Means clustering: once the distance gets to be 2, it's already clumping weird stuff in small paragraphs


# clustering should be based not on the frequency of individual pairs, but on the the frequency of the words appearing near each other.
# like a set of binary flags.