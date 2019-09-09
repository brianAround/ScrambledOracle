import re
import codecs
import os
import string


class Preprocess:
    raw_doublequote = r"[“”]"

    # strictly speaking, this where I plan to put code that normalizes punctuation
    # quotes in particular need a better solution


    def replace_doublequotes(self, text):
        text = re.sub(r'(?P<before_it>[\s\S])"(?P<after_it>[\s\S])', self.weird_double_quote_action, text)
        text = re.sub(r'(?P<before_it>"[\s\S])"(?P<after_it>[\s\S])', self.weird_double_quote_action, text)
        text = re.sub(r'"em\b', "'em", text)
        return re.sub(Preprocess.raw_doublequote, '"', text)

    def replace_singlequote(self, text):
        corrected = re.sub(r'(?P<before_it>[\s\S])[’‘`\'](?P<after_it>[\s\S])', self.single_quote_action, text)
        return corrected

    def odd_character_replacements(self, text, enc):
        text = re.sub(r'…', '...', text)
        text = re.sub(r'—', '-', text)
        return text

    def weird_double_quote_action(self, matchobj):
        replacement = '"'
        before = matchobj.group('before_it')
        after = matchobj.group('after_it')
        if before.lower().isalpha() and after.lower().isalpha():
            replacement = "'"
        return before + replacement + after

    def single_quote_action(self, matchobj):
        replacement = '"'
        before = matchobj.group('before_it')
        after = matchobj.group('after_it')
        if before.lower().isalpha() and after.lower().isalpha():
            replacement = "'"
        return before + replacement + after

byline = "by William Shakespeare"
target_folder = os.path.join("sources", "various")
source_filename = os.path.join(target_folder, "AChristmasCarol.txt")
end_marker = "THE END"
license_start = '*** START: FULL LICENSE ***'



sack = []

title = ""

folder_list = os.listdir(target_folder)
folder_list = [f for f in folder_list if f.endswith(".txt") and os.path.isfile(os.path.join(target_folder, f))]
file_list = [os.path.join(target_folder, f) for f in folder_list]
# file_list = [source_filename]
# file_list = file_list[4:5]

p = Preprocess()

for source_filename in file_list:
    file_size = min(32, os.path.getsize(source_filename))
    with open(source_filename, 'rb') as f_enc:
        raw = f_enc.read(file_size)
        if raw.startswith(codecs.BOM_UTF8):
            encoding = 'utf-8-sig'
        else:
            encoding = 'utf-8'
    full_doc = None
    with open(source_filename, 'r', encoding=encoding) as f_handle:
        print('reading doc', source_filename)
        full_doc = f_handle.read()
        print(type(full_doc))
        print(encoding)
    print('replacing text')

    # print(full_doc)
    full_doc = p.replace_singlequote(full_doc)
    full_doc = p.replace_doublequotes(full_doc)
    full_doc = p.odd_character_replacements(full_doc, encoding)

    with open(source_filename, 'w', encoding=encoding) as f_handle:
        f_handle.seek(0)
        print('rewriting doc', source_filename)
        f_handle.write(full_doc)


print('done')
