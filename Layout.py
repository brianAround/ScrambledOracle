import time

from WordChain import *
from matplotlib import pyplot as mpl
import networkx as nx
import networkx.drawing.layout as lyt

class MessageVisualizer:

    gradient_color_map = 'Accent'

    def __init__(self, chain: WordChain):
        self.chain = chain
        self.base_edge_weight = 10
        self.edge_weight_multiplier = 1.75
        self.depth = 2
        self.font_size = 10
        self.font_size_minor = 6
        self.font_size_legend = 8
        self.max_node_degree = 10
        self.node_size = 200
        self.scale = 5

    @staticmethod
    def select_cmap(size):
        if size > 12:
            return MessageVisualizer.gradient_color_map
        if size > 9:
            return 'Set3'
        return 'Set1'

    def show_graph(self, g,
                   graph_layout,
                   group_list,
                   source_groups,
                   node_size,
                   show_arrows=False,
                   prime_path=None,
                   labels=None,
                   minor_labels=None,
                   legend_graph=None,
                   legend_layout=None,
                   legend_labels=None,
                   save_path=None,
                   save_only=False):
        color_set = MessageVisualizer.select_cmap(len(source_groups))
        mpl.figure(figsize=(15, 15), dpi=100)
        nx.draw_networkx_edges(g, graph_layout, width=0.5, style='dotted', arrows=show_arrows)
        nx.draw_networkx_edges(g, graph_layout, width=2, style='solid', edgelist=prime_path, arrows=show_arrows)
        nx.draw_networkx_nodes(g, graph_layout, node_color=group_list, cmap=color_set, node_size=node_size)
        if labels is not None:
            nx.draw_networkx_labels(g, pos=graph_layout, labels=labels, font_size=self.font_size)
        if minor_labels is not None:
            nx.draw_networkx_labels(g, pos=graph_layout, labels=minor_labels, font_size=self.font_size_minor)
        if legend_graph is not None:
            legend_colors = [col_idx for col_idx in range(len(legend_graph.nodes()))]
            # nx.draw_networkx_edges(legend_graph, legend_layout, width=0.5, style='dashed')
            nx.draw_networkx_nodes(legend_graph, legend_layout, cmap=color_set, node_color=legend_colors)
            if legend_labels is not None:
                nx.draw_networkx_labels(legend_graph, pos=legend_layout, labels=legend_labels, font_size=self.font_size_legend)
        mpl.axis('off')
        if save_path is not None:
            mpl.savefig(save_path, bbox_inches='tight')
        if not save_only:
            mpl.show()

    def build_component_nxgraph(self, start_node, is_directed=True, sub_graph_list=[]):
        use_subgraph = (len(sub_graph_list) > 0)
        wc = self.chain
        if is_directed:
            g = nx.DiGraph()
        else:
            g = nx.Graph()
        g.add_node(start_node.prefix, {'label': wc.convert_prefix_to_text(start_node.prefix), 'group_id': 1})
        to_process = []
        for start_parent in start_node.inbound:
            to_process.append((start_parent, start_node, ))
        for start_out_entry in start_node.outbound:
            to_process.append((start_node, start_out_entry[1]))
        while len(to_process) > 0:
            edge_nodes = to_process.pop(0)
            from_node = edge_nodes[0]
            to_node = edge_nodes[1]
            new_node = None
            if not g.has_node(from_node.prefix):
                new_node = from_node
            elif not g.has_node(to_node.prefix):
                new_node = to_node
            if new_node is not None:
                g.add_node(new_node.prefix, {'label': wc.convert_prefix_to_text(new_node.prefix), 'group_id': 1})
            if not g.has_edge(from_node.prefix, to_node.prefix):
                g.add_edge(from_node.prefix, to_node.prefix, {'weight': self.base_edge_weight})
            if new_node is not None:
                for parent in new_node.inbound:
                    if not use_subgraph or parent.prefix in sub_graph_list:
                        if not g.has_node(parent.prefix) or not g.has_edge(parent.prefix, new_node.prefix):
                            to_process.append((parent, new_node, ))
                for child_entry in new_node.outbound:
                    child = child_entry[1]
                    if not use_subgraph or child.prefix in sub_graph_list:
                        if not g.has_node(child.prefix) or not g.has_edge(new_node.prefix, child.prefix):
                            to_process.append((new_node, child, ))
        return g

    def build_nxgraph(self, chain_nodes, is_directed=True):
        node_list = [prefix for prefix in chain_nodes]
        return self.build_component_nxgraph(chain_nodes[node_list[0]], is_directed=is_directed, sub_graph_list=node_list)

    def set_group_id_by_source_text(self, dg:nx.DiGraph):
        group_names = []
        for prefix in dg.nodes():
            node = self.chain.nodes_by_prefix[prefix]
            if len(node.sources) > 0:
                source_count = {}
                top_source = node.sources[0][0]
                for source_entry in node.sources:
                    source = source_entry[0]
                    if source not in source_count:
                        source_count[source] = 0
                    source_count[source] += 1
                    if source_count[source] > source_count[top_source]:
                        top_source = source
            else:
                top_source = "Unknown"
            if top_source not in group_names:
                group_names.append(top_source)
            dg.node[prefix]['group_id'] = group_names.index(top_source)
        return group_names

    def build_graph_display(self, message_path, layout_type='standard'):
        labels = {}
        minor_labels = {}
        legend_labels = {}

        message_context = WordChain.get_graph_context(message_path, self.depth, degree_max=self.max_node_degree)

        if len(message_context) > 1000:
            show_minor_labels = False
            show_adjacent_labels = False
            self.node_size = 80
        elif len(message_context) > 200:
            show_minor_labels = False
            show_adjacent_labels = True
            self.node_size = 100
        else:
            show_minor_labels = True
            show_adjacent_labels = True
            self.node_size = 200

        dg = self.build_nxgraph(message_context, is_directed=True)

        source_groups = self.set_group_id_by_source_text(dg)
        scale = self.scale
        graph_layout = self.build_spring_layout(dg, scale)
        group_list = [dg.node[node]['group_id'] for node in dg.nodes()]
        path_prefixes = [node.prefix for node in message_path]
        path_edges = [edge for edge in dg.edges() if edge[0] in path_prefixes and edge[1] in path_prefixes]

        for prefix in dg.nodes():
            minor_labels[prefix] = ''
            if prefix in path_prefixes:
                if prefix == message_path[0].prefix:
                    labels[prefix] = dg.node[prefix]['label']
                else:
                    labels[prefix] = self.chain.word_list[prefix[-1]]
            else:
                labels[prefix] = ''
                if show_minor_labels:
                    minor_labels[prefix] = dg.node[prefix]['label']
                elif show_adjacent_labels:
                    for adjacent_item in dg.neighbors(prefix):
                        if adjacent_item not in path_prefixes:
                            minor_labels[adjacent_item] = dg.node[adjacent_item]['label']

        for edge in dg.edges():
            if edge[0] in path_prefixes and edge[1] in path_prefixes:
                dg.edge[edge[0]][edge[1]]['weight'] = 6
            elif edge[0] in path_prefixes:
                dg.edge[edge[0]][edge[1]]['weight'] = 3
            elif edge[1] in path_prefixes:
                dg.edge[edge[0]][edge[1]]['weight'] = 3
            else:
                dg.edge[edge[0]][edge[1]]['weight'] = 2

        legend_graph = nx.Graph()
        last_source = ''
        for src_idx in range(len(source_groups)):
            legend_graph.add_node(source_groups[src_idx])
            if last_source:
                legend_graph.add_edge(last_source, source_groups[src_idx])
            last_source = source_groups[src_idx]
            legend_labels[source_groups[src_idx]] = source_groups[src_idx]
        legend_layout = nx.circular_layout(legend_graph, 2, scale=(scale * 3 / 5), center=(scale * 0.5, scale * 0.5))
        self.show_graph(dg, graph_layout, group_list, source_groups, self.node_size,
                        prime_path=path_edges, save_path='new_output.png', labels=labels, minor_labels=minor_labels,
                        legend_graph=legend_graph, legend_layout=legend_layout, legend_labels=legend_labels)

    def randjust(self, distance):
        return (random.random() - 0.5) * (distance / 4)

    def build_spring_layout(self, g:nx.Graph, scale=1):
        linear_positions = {}
        nl = g.nodes()
        increment = 0.9 / len(nl)
        for i in range(len(nl)):
            value = 0.05 + i * increment
            linear_positions[nl[i]] = (value + self.randjust(increment), value + self.randjust(increment))
        graph_layout = linear_positions
        for i in range(1, scale + 1, max(int(scale/3), 1)):
            graph_layout = nx.spring_layout(g, 2, pos=graph_layout, scale=i, iterations=50, center=(i * 0.5, i * 0.5))
        return graph_layout

