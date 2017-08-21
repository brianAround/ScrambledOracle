
class GrammarNode:

    def __init__(self, parent_node, pos):
        self.parent = parent_node
        self.part_of_speech = pos
        self.size = 0
        self.branches = {}

class GrammarTree:

    def __init__(self):
        self.branches = {}
        self.size = 0

    def add_structure(self, source_text, size):
        struct = source_text.split()
        current_node = self
        current_node.size += size
        for pos in struct:
            if pos not in current_node.branches:
                current_node.branches[pos] = GrammarNode(current_node, pos)
            current_node = current_node.branches[pos]
            current_node.size += size

    def read_structmap(self, file_path):
        with open(file_path, 'r') as file_handle:
            for line in file_handle:
                idx = 0
                while line[idx] != ' ':
                    idx += 1
                size = int(line[:idx])
                self.add_structure(line[idx + 1:], size)

    def find_branch(self, pos_list):
        current_node = self
        for pos in pos_list:
            if pos in current_node.branches:
                current_node = current_node.branches[pos]
            else:
                return None
        return current_node

    def get_size(self, pos_list):
        current_node = self.find_branch(pos_list)
        if current_node is None:
            return 0
        return current_node.size
