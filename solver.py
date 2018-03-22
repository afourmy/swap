from database import db
import numpy as np
from cvxopt import matrix, glpk
from models import Node, Fiber, Traffic


class Solver:

    def shortest_path(self):
        graph = {node: {} for node in Node.query.all()}
        for node in Node.query.all():
            for neighbor, fiber in node.adjacencies('fiber'):
                graph[node][neighbor] = getattr(fiber, 'cost')

        n = 2*len(Fiber.query.all())

        c = []
        for node in graph:
            for neighbor, cost in graph[node].items():
                c.append(float(cost))

        # for the condition 0 < x_ij < 1
        h = np.concatenate([np.ones(n), np.zeros(n)])
        id = np.eye(n, n)
        G = np.concatenate((id, -1*id), axis=0).tolist()

        for traffic in Traffic.query.all():
            traffic.path.clear()
            A, b = [], []
            for node_r in graph:
                if node_r != traffic.destination:
                    b.append(float(node_r == traffic.source))
                    row = []
                    for node in graph:
                        for neighbor in graph[node]:
                            row.append(
                                -1. if neighbor == node_r
                                else 1. if node == node_r
                                else 0.
                            )
                    A.append(row)

            A, G, b, c, h = map(matrix, (A, G, b, c, h))
            solsta, x = glpk.ilp(c, G.T, h, A.T, b)

            # update the resulting flow for each node
            cpt = 0
            resulting_graph = {node: {} for node in Node.query.all()}
            for node in graph:
                for neighbor in graph[node]:
                    resulting_graph[node][neighbor] = x[cpt]
                    cpt += 1

            # update the network physical links with the new flow value
            for fiber in Fiber.query.all():
                src, dest = fiber.source, fiber.destination
                if resulting_graph[src][dest] or resulting_graph[dest][src]:
                    traffic.path.append(fiber.name)
        db.session.commit()
        return {}

    def graph_transformation(self):
        # in the new graph, each node corresponds to a traffic path
        # we create one node per traffic physical link in the new view
        transformed_graph = {t.name: [] for t in Traffic.query.all()}
        nodes = [{
            "id": traffic.name,
            "label": traffic.name
        } for traffic in Traffic.query.all()]
        visited, links = set(), []
        for traffic1 in Traffic.query.all():
            for traffic2 in Traffic.query.all():
                if traffic2 not in visited and traffic1 != traffic2:
                    if set(traffic1.path) & set(traffic2.path):
                        transformed_graph[traffic1.name].append(traffic2.name)
                        transformed_graph[traffic2.name].append(traffic1.name)
                        links.append({"from": traffic1.name, "to": traffic2.name})
            visited.add(traffic1)
        return transformed_graph, {'nodes': nodes, 'links': links}

    def largest_degree_first(self, graph):
        # we color the transformed graph by allocating colors to largest
        # degree nodes:
        # 1) we select the largest degree uncolored optical switch
        # 2) we look at the adjacent vertices and select the minimum indexed
        # color not yet used by adjacent vertices
        # 3) when everything is colored, we stop
        # we will use a dictionary that binds traffic to the color it uses.
        traffic_color = {traffic.name: None for traffic in Traffic.query.all()}
        # and a list that contains all vertices that we have yet to color
        uncolored_nodes = list(traffic_color)
        # we will use a function that returns the degree of a node to sort
        # the list in ascending order
        uncolored_nodes.sort(key=lambda traffic: len(graph[traffic]))
        # and pop nodes one by one
        while uncolored_nodes:
            largest_degree = uncolored_nodes.pop()
            # we compute the set of colors used by neighbors
            colors = set(traffic_color[t] for t in graph[largest_degree])
            # we find the minimum indexed color which is available
            min_index = [i in colors for i in range(len(colors) + 1)].index(0)
            # and assign it to the current optical switch
            traffic_color[largest_degree] = min_index
        number_lambda = max(traffic_color.values()) + 1
        return {'lambda': number_lambda, 'colors': traffic_color}
