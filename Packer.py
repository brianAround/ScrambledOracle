import sys

from WordChain import *
from Oracle import Oracle
from ChainLinker import ChainLinker

map_name = "pratchett.txt.map"
target_depth = 3
build_type = "F"
target_dir = os.path.join("sources", "pratchett")
# text_list = [os.path.join(target_dir, f) for f in text_list]
text_list = ["sources\pratchett\Discworld 23_ Carpe Jugulum - Terry Pratchett.txtPP.txt"]

# handle arguments
# pass either no args or at least 4
# arg 1 - map_name - destination filename
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
    elif build_type == "P":
        source = sys.argv[4]
        if not os.path.isdir(source):
            raise ValueError("This isn't a valid directory.")
        target_dir = source

linker = ChainLinker('Oracle.ini')
# linker.initialize_chain()


o = Oracle()
o.chain = WordChain()



print("Reading files and creating map file:", map_name)
if build_type == "D":
    linker.build_and_save_chain_from_directory(target_dir, depth=target_depth, target_filename=map_name)
elif build_type == "F":
    linker.build_and_save_chain_from_list(text_list, target_depth, map_name)
print("Reading", map_name, "from disk")
o.chain.read_map(map_name)

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

