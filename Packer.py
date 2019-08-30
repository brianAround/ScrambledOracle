import sys

from WordChain import *
from Oracle import Oracle
from ChainLinker import ChainLinker
from WordChainScribe import Scribe

print('WordChain Packer Utility ver. 2.1')

map_name = "douglasadams.4.txt.map"
target_depth = 4
build_type = "F"
target_dir = os.path.join("sources", "dougadams")
select_count = 7

# target_dir = os.path.join("sources", "pratchett")
#text = os.get
#text_list = [os.path.join(target_dir, f) for f in text_list]

def get_relative_file_list(source_folder):
    file_listing = [f for f in os.listdir(source_folder) if f.endswith(".txt")]
    file_listing = [os.path.join(source_folder, f) for f in file_listing]
    file_listing = [f for f in file_listing if os.path.isfile(f)]
    return file_listing


text_list = get_relative_file_list(target_dir)

#text_list = ['sources/various/alice13a.txt']

#text_list = ['sources\\pratchett\\DW 013 SmallGods.txt','sources\\pratchett\\DW 028 AmazingMaurice.txt','sources\\pratchett\\DW 011 ReaperMan.txt']
# text_list.extend(get_relative_file_list('sources/dougadams'))
# text_list.extend(get_relative_file_list('sources/inaugural'))
# text_list.extend(get_relative_file_list('sources/pratchett'))
# text_list.extend(get_relative_file_list('sources/shakespeare'))
# text_list.extend(get_relative_file_list('sources/twain'))
# text_list.extend(get_relative_file_list('sources/various'))

print('Starting document list has ', len(text_list))
# target_len = len(text_list) / 6
target_len = len(text_list)
while len(text_list) > target_len:
	idx = random.randint(0, len(text_list) - 1)
	text_list.pop(idx)
print('Using list of', len(text_list))
	
# handle arguments
# pass either no args or at least 4
# arg 1 - map_name - destination filename - I expect an extension of .map
# arg 2 - build depth (3 is usual)
# arg 3 - build type (F for list of files, and D to use a directory, S to randomly select files)
if len(sys.argv) > 4:
    map_name = sys.argv[1]
    target_depth = int(sys.argv[2])
    build_type = str(sys.argv[3]).upper()
    if build_type == "F":
        text_list = []
        target_dir = ""
        for arg_idx in range(4, len(sys.argv)):
            source = sys.argv[arg_idx]
            if not os.path.isfile(source) and os.path.isdir(source):
                target_dir = source
            else:
                if not os.path.isfile(source):
                    source = os.path.join(target_dir, source)
                if not os.path.isfile(source):
                    raise ValueError("This isn't a valid source value.")
                text_list.append(source)
    elif build_type == "D":
        source = sys.argv[4]
        if not os.path.isdir(source):
            raise ValueError("This isn't a valid directory.")
        target_dir = source
    elif build_type == "S":
        text_list = []
        source = sys.argv[4]
        if not os.path.isdir(source):
            raise ValueError("This isn't a valid directory.")
        target_dir = source
        if len(sys.argv) > 5:
            select_count = int(sys.argv[5])
        dir_list = get_relative_file_list(target_dir)
        use_file_list = 'N'
        while use_file_list[0].lower() != 'y':
            text_list = random.choices(dir_list, k=select_count)
            print('Files to use:')
            for idx, f in enumerate(text_list):
                print(idx + 1, '.', f)
            use_file_list = input('Use this list? (Y/N)')

print('Build Type:', build_type)
print('Destination file:', map_name)
print('Prefix Length:', target_depth)
if build_type == 'S':
    print('Select', select_count, 'files')
if build_type in ['D','S']:
    print('Source Directory:', target_dir)
if build_type in ['F','S']:
    print('Files:', ','.join([f for f in text_list]))

linker = ChainLinker('Oracle.ini')
# linker.initialize_chain()
linker.verbose = True

o = Oracle()
o.chain = WordChain()

print("Reading files and creating map file:", map_name)
if build_type == "D":
    linker.build_and_save_chain_from_directory(target_dir, depth=target_depth, target_filename=map_name)
elif build_type in ["F", "S"]:
    linker.build_and_save_chain_from_list(text_list, target_depth, map_name)
print("Reading", map_name, "from disk")
Scribe.read_map(map_name, chain=o.chain)


a = ''
b = ""
chain_response = 'y'
if chain_response.lower() in ['y', 'yes']:
    chain_response = True
else:
    chain_response = False

while a.lower() not in ["q", "quit", "stop", "end"]:
    if a[0:5].lower() == "view:":
        for start in [text for text in o.chain.starting if a[5:].lower() in text.lower()]:
            print('"' + start + '"', o.chain.mchain[start])
    else:
        # target.chain.add_expression(a)

        for i in range(0, 50):
            print("Attempt:", i)
            # sources = []
            passages = []
            # this_message_path = o.chain.build_pos_guided_message_path_general(gt, prompt=b + " " + a, sources=sources)
            # this_message = o.chain.render_message_from_path(this_message_path)
            # this_message = o.chain.build_message(char_limit=140, prompt=b + " " + a, sources=sources)
            this_message = o.get_message(a, passages=passages, print_passages=False)
            # passages = o.chain.identify_passages(sources, min_length=1)
            while len(this_message) < 30:
                passages = []
                # sources = []
                # this_message_path = o.chain.build_pos_guided_message_path_general(gt, prompt=b + " " + a, sources=sources)
                # this_message = o.chain.render_message_from_path(this_message_path)
                # this_message = o.chain.build_message(char_limit=140, prompt=b + " " + a, sources=sources)
                this_message = o.get_message(a, passages=passages, print_passages=False)
                # passages = o.chain.identify_passages(sources, min_length=1)
            print(len(this_message), "\t", this_message)
            print("---------------------------------------------")
            quote_size = 0
            # if len(passages) > 0:
            #     quote_size = passages[-1][1] + passages[-1][2]
            # for item in passages:
            #     print(item, item[2] * 1000 // quote_size / 1000)
            # print("---------------------------------------------")
            # print("---------------------------------------------")
            if chain_response:
                b = a
                a = this_message
                if a == b:
                    a = ""
                    b = ""
    a = input("Enter a prompt: ")

