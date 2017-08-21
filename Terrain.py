import codecs
import string

import nltk
import os.path
from nltk.tokenize import word_tokenize

templates = {}
proper_names = {}
hhgttg = ''
file_path = os.path.join('sources', 'twain')
file_list = [os.path.join(file_path, f) for f in os.listdir(file_path) if f.endswith(".txt") and os.path.isfile(os.path.join(file_path, f))]
# file_list = ['sources/dougadams/dirkgently.txt', 'sources/dougadams/longdarkteatime.txt']
for filename in file_list:
    file_size = min(32, os.path.getsize(filename))
    with open(filename, 'rb') as f_enc:
        raw = f_enc.read(file_size)
        if raw.startswith(codecs.BOM_UTF8):
            encoding = 'utf-8-sig'
        else:
            encoding = 'utf-8'
    with open(filename, "r", encoding=encoding) as my_file:
        try:
            hhgttg = my_file.readlines()
            hhgttg = hhgttg[3:]
            hhgttg = " ".join(hhgttg).strip('\n')
        except UnicodeDecodeError:
            print('Error loading file:', filename, 'Encoding:', encoding)
            hhgttg = ""

    sokin = nltk.sent_tokenize(hhgttg)
    sents = [nltk.word_tokenize(sent) for sent in sokin]
    sentokens = [nltk.pos_tag(sent) for sent in sents]

    # for i in range(10):
        # print(i, ':', sents[i])
    # for i in range(10):
        # print(i, ':', " ".join([elem[1] for elem in sentokens[i]]))

    for st in sentokens:
        if st[0][1] != ':':
            pos_list = [elem[1] for elem in st]
            st_name = " ".join(pos_list)
            if st_name in templates:
                templates[st_name] += 1
            else:
                templates[st_name] = 1
        for pn in [elem for elem in st if elem[1] == 'NNP']:
            if pn[0] in proper_names:
                proper_names[pn[0]] += 1
            elif pn[0] not in proper_names and len(pn[0]) > 3:
                proper_names[pn[0]] = 1

for pn in proper_names:
    if proper_names[pn] > 30:
        print(pn)

# with open('pratchett.structmap', 'w') as f_handle:

    # for tname in sorted([name for name in templates]):
    #     if templates[tname] > 0:
    #         f_handle.write(str(templates[tname]))
    #         f_handle.write(" " + tname + "\n")

print('done')
# for prop_name in proper_names:
    # print(prop_name, proper_names[prop_name], prop_name.endswith("’s"), prop_name.startswith("I’"))
    # if prop_name[0] not in string.punctuation and proper_names[prop_name] > 50 and not prop_name.endswith("’s") and not prop_name.startswith("I’"):
        # print(prop_name)
        # print(prop_name, proper_names[prop_name])
