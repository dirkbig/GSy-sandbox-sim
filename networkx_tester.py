import plotly
import plotly.plotly as py
import plotly.graph_objs as go
import logging
import matplotlib.pyplot as plt
import os
import csv
import numpy as np
import networkx as nx

plotly.tools.set_credentials_file(username='dirkGSy', api_key='rJJU93ceA9z7ZtDVEU0Y')
plotly.tools.set_config_file(world_readable=True, sharing='public')

network_graph_log = logging.getLogger('network_visual')


class NetworkPlot(object):
    def __init__(self):
        self.data_array = self.csv_read_file()
        network_graph_log.info('done reading in data in to array')
        self.list_of_agents, self.num_agents = self.count_agents()
        self.list_of_trades, self.dict_of_edges, self.num_edges = self.create_edges()
        self.create_network()

    @staticmethod
    def csv_read_file():

        data_array = []
        with open('grid_trades_big.csv') as csvfile:
            data_file = csv.reader(csvfile, delimiter=',')
            for row in data_file:
                data_array.append(row)
        data_array.remove(data_array[0])

        return data_array

    def count_agents(self):

        list_of_agents = []

        for row in range(np.shape(self.data_array)[0]):
            if self.data_array[row][5] not in list_of_agents:
                list_of_agents.append(self.data_array[row][5])
            if self.data_array[row][6] not in list_of_agents:
                list_of_agents.append(self.data_array[row][6])

        num_agents = len(list_of_agents)

        return list_of_agents, num_agents

    def create_edges(self):

        list_of_trades = []
        dict_of_edges = {}

        for row in range(np.shape(self.data_array)[0]):
            list_of_trades.append((self.data_array[row][5], self.data_array[row][6]))

            if 'self.data_array[row][5], self.data_array[row][6]' in dict_of_edges.keys():
                dict_of_edges[self.data_array[row][5], self.data_array[row][6]] += self.data_array[row][4]
            else:
                dict_of_edges[self.data_array[row][5], self.data_array[row][6]] = self.data_array[row][4]

        num_edges = len(dict_of_edges)

        return list_of_trades, dict_of_edges, num_edges

    def create_network(self):

        graph = nx.DiGraph()
        graph.add_nodes_from(self.list_of_agents)
        graph.add_edges_from(self.list_of_trades)

        pos = nx.circular_layout(graph)

        """ sizes and colors accoding node/edge attributes"""
        node_sizes = [1 for i in range(self.num_agents)]
        edge_colors = [2 for i in range(self.num_edges)]

        v = list(self.dict_of_edges.values())
        k = list(self.dict_of_edges.keys())
        key_max_trade = k[v.index(max(v))]
        max_trade = float(self.dict_of_edges[key_max_trade])
        print(max_trade)

        edge_alphas = []
        for key in self.dict_of_edges:
            edge_alphas.append(float(self.dict_of_edges[key])/max_trade)
        print(self.dict_of_edges)
        print(edge_alphas)

        """ analysis """
        # print(nx.info(graph))
        # print(graph.edges)
        nx.draw_networkx_nodes(graph, pos, node_size=15, node_color='blue')
        edges = nx.draw_networkx_edges(graph, pos, node_sizes=15, arrowstyle='->',
                                       arrowsize=10, edge_color=edge_colors,
                                       width=2)

        for i in range(self.num_edges):
            edges[i].set_alpha(edge_alphas[i])

        labels = {}
        for i in range(self.num_agents):
            labels[i] = self.list_of_agents[i]
        print(labels)
        print(pos)
        # nx.draw_networkx_labels(graph, pos, labels, font_size=16)

        plt.show()


network_graph1 = NetworkPlot()



# from __future__ import division
# import matplotlib.pyplot as plt
# import networkx as nx
#
# G = nx.generators.directed.random_k_out_graph(10, 3, 0.5)
# pos = nx.layout.spring_layout(G)
#
# node_sizes = [3 + 10 * i for i in range(len(G))]
# M = G.number_of_edges()
# edge_colors = range(2, M + 2)
# edge_alphas = [(5 + i) / (M + 4) for i in range(M)]
#
# nodes = nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color='blue')
# edges = nx.draw_networkx_edges(G, pos, node_size=node_sizes, arrowstyle='->',
#                                arrowsize=10, edge_color=edge_colors,
#                                edge_cmap=plt.cm.Blues, width=2)
# # set alpha value for each edge
# for i in range(M):
#     edges[i].set_alpha(edge_alphas[i])
#
# ax = plt.gca()
# ax.set_axis_off()
# plt.show()