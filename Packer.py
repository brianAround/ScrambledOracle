from WordChain import *
from Oracle import Oracle
from ChainLinker import ChainLinker


linker = ChainLinker('Oracle.ini')
# linker.initialize_chain()
text_list = [
    "carroll-hunting-100.txt"
]

o = Oracle()
o.chain = WordChain()

map_name = "snark.txt.map"
target_dir = os.path.join("sources", "various")
text_list = [os.path.join(target_dir, f) for f in text_list]


print("Reading files and creating map file:", map_name)
# o.build_and_save_chain_from_directory(target_dir, depth=3, target_filename=map_name)
linker.build_and_save_chain_from_list(text_list, 3, map_name)
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