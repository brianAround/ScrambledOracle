import codecs
import os
import string

byline = "by William Shakespeare"
target_folder = os.path.join("sources", "pratchett")
source_filename = os.path.join(target_folder, "Discworld 01_ The Colour Of Magic - Terry Pratchett.txt")
end_marker = "THE END"

sack = []

title = ""

folder_list = os.listdir(target_folder)
folder_list = [f for f in folder_list if f.encode(".txt") and os.path.isfile(os.path.join(target_folder, f))]
file_list = [os.path.join(target_folder, f) for f in folder_list]
file_list = [source_filename]


for source_filename in file_list:
    file_size = min(32, os.path.getsize(source_filename))
    with open(source_filename, 'rb') as f_enc:
        raw = f_enc.read(file_size)
        if raw.startswith(codecs.BOM_UTF8):
            encoding = 'utf-8-sig'
        else:
            encoding = None
    with open(source_filename, 'r', encoding=encoding) as f_handle:
        new_filename = ""
        for line in f_handle:
            sack.append(line)
            if byline in line:
                # pull values out of the sack until you get to the year note or "THE END"
                new_sack = []
                new_title = ""
                new_year = ""
                out_line = sack.pop()
                while end_marker not in out_line and not out_line.strip().isdigit() and len(sack) > 0:
                    new_sack.insert(0, out_line)
                    if len(out_line.strip()) > 0:
                        new_title = out_line.strip()
                    out_line = sack.pop()
                if out_line.strip().isdigit():
                    new_sack.append(out_line)
                # write the previous file, if it exists
                if len(title) > 0:
                    new_filename = target_folder + "\\" + title.translate(str.maketrans({a:None for a in string.punctuation})) + ".txt"
                    print("writing file ", new_filename)
                    with open(new_filename, "w", encoding="utf-8") as out_file:
                        for sack_line in sack:
                            out_file.write(sack_line)
                sack = new_sack
                title = new_title
        if len(sack) > 0:
            if len(title.strip()) == 0:
                title = "Unknown"
            new_filename = target_folder + "\\" + title.translate(str.maketrans({a:None for a in string.punctuation})) + ".txt"
            print("writing file ", new_filename)
            with open(new_filename, "w", encoding="utf-8") as out_file:
                for sack_line in sack:
                    out_file.write(sack_line)







