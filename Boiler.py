import codecs
import os
import nltk

term_file = 'data/classification/thankful.txt'
source_file = 'sources/HorrorShow/Poe.txt'
output_file = 'sources/HorrorShow/Poe_GoodParts.txt'

source_folder = "sources/dougadams"
destination_folder = "sources/thankful/dougadams"
file_listing = [f for f in os.listdir(source_folder) if f.endswith(".txt")]
file_listing = [os.path.join(source_folder, f) for f in file_listing]
file_listing = [f for f in file_listing if os.path.isfile(f)]
preferred_terms = {}

# read preferred terms
if os.path.isfile(term_file):
    with open(term_file, mode='r') as ff:
        for line in ff:
            parts = line.strip().split('\t')
            word = parts.pop(0)
            if word in preferred_terms:
                preferred_terms[word].extend(parts)
            else:
                preferred_terms[word] = parts
else:
    print("Can't open '", term_file, "' because it isn't a file name.")

for source_file in file_listing:
    output_file = os.path.split(source_file)[1].replace('.txt', '_GoodParts.txt')
    output_file = os.path.join(destination_folder, output_file)
    file_size = min(32, os.path.getsize(source_file))
    encoding = 'utf-8'
    quotes = []
    with open(source_file, 'rb') as f_enc:
        raw = f_enc.read(file_size)
        if raw.startswith(codecs.BOM_UTF8):
            encoding = 'utf-8-sig'
        else:
            encoding = 'utf-8'

    source_text = []
    with open(source_file, 'r', encoding=encoding) as f_handle:
        source_text = f_handle.readlines()

    source_text = source_text[3:]
    source_text = [line for line in source_text if line[0] != '#']
    source_text = " ".join(source_text).strip('\n')
    sentences = nltk.sent_tokenize(source_text)
    sentences = [nltk.word_tokenize(sentence) for sentence in sentences]

    with open(output_file, mode='w', encoding=encoding) as out_handle:
        for sentence in sentences:
            if [w for w in sentence if w in preferred_terms]:
                message = " ".join(sentence).replace(" .", ".").replace(" ,", ",") \
                    .replace(" !", "!").replace(" ?", "?").replace(" :", ":").replace(" ;", ";") \
                    .replace(" ''", '"').replace("`` ", '"')
                out_handle.write(message)
                out_handle.write('\n')


