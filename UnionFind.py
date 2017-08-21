
class UnionFind:

    def __init__(self, size):
        self.nodes = []
        for i in range(size):
            self.nodes.append(i)

    def union(self, n1, n2):
        p1 = self.find(n1)
        p2 = self.find(n2)
        if p1 != p2:
            self.nodes[p2] = p1

    def find(self, n):
        nodes = self.nodes
        while nodes[n] != n:
            nodes[n] = nodes[nodes[n]]
            n = nodes[n]
        return n


class UTUnionFind:

    def __init__(self, items):
        self.lookup = {}
        self.item_list = [item for item in items]
        for i in range(len(self.item_list)):
            self.lookup[self.item_list[i]] = i
        self.uf = UnionFind(len(self.item_list))

    def union(self, item1, item2):
        n1 = self.lookup[item1]
        n2 = self.lookup[item2]
        self.uf.union(n1, n2)

    def find(self, item):
        n = self.lookup[item]
        return self.item_list[self.uf.find(n)]

