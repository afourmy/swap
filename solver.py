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
        graph_nodes = {t.name: [] for t in Traffic.query.all()}
        graph_links = []
        nodes = [{
            "id": traffic.name,
            "label": traffic.name
        } for traffic in Traffic.query.all()]
        visited, links = set(), []
        for traffic1 in Traffic.query.all():
            for traffic2 in Traffic.query.all():
                if traffic2 not in visited and traffic1 != traffic2:
                    if set(traffic1.path) & set(traffic2.path):
                        graph_nodes[traffic1.name].append(traffic2.name)
                        graph_nodes[traffic2.name].append(traffic1.name)
                        graph_links.append((traffic1.name, traffic2.name))
                        links.append({"from": traffic1.name, "to": traffic2.name})
            visited.add(traffic1)
        transformed_graph = {'nodes': graph_nodes, 'links': graph_links}
        print(transformed_graph)
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
        uncolored_nodes.sort(key=lambda traffic: len(graph['nodes'][traffic]))
        # and pop nodes one by one
        while uncolored_nodes:
            largest_degree = uncolored_nodes.pop()
            # we compute the set of colors used by neighbors
            colors = set(traffic_color[t] for t in graph['nodes'][largest_degree])
            # we find the minimum indexed color which is available
            min_index = [i in colors for i in range(len(colors) + 1)].index(0)
            # and assign it to the current optical switch
            traffic_color[largest_degree] = min_index
        number_lambda = max(traffic_color.values()) + 1
        return {'lambda': number_lambda, 'colors': traffic_color}

    def linear_programming(self, graph, K=7):
        # we note x_v_wl the variable that defines whether wl is used for 
        # the path v (x_v_wl = 1) or not (x_v_wl = 0)
        # we construct the vector of variable the following way:
        # x = [x_1_0, x_2_0, ..., x_V_0, x_1_1, ... x_V-1_K-1, x_V_K-1]
        # that is, [(x_v_0) for v in V, ..., (x_v_K) for wl in K]
        nodes, links = graph['nodes'], graph['links']
        # V is the total number of path (i.e the total number of nodes
        # in the transformed graph)
        V, T = len(nodes), len(links)

        # for the objective function, which must minimize the sum of y_wl, 
        # that is, the number of wavelength used
        c = np.concatenate([np.zeros(V * K), np.ones(K)])

        # for a given path v, we must have sum(x_v_wl for wl in K) = 1
        # which ensures that each optical path uses only one wavelength
        # for each path v, we must create a vector with all x_v_wl set to 1
        # for the path v, and the rest of it set to 0.
        A = []
        for path in range(V):
            row = [float(K * path <= i < K * (path + 1)) for i in range(V * K)] 
            row += [0.] * K
            A.append(row)
        b = np.ones(V)

        G2 = []
        for i in range(K):
            for link in links:
                # we want to ensure that paths that have at least one 
                # physical link in common are not assigned the same wavelength.
                # this means that x_v_src_i + x_v_dest_i <= y_i
                row = []
                # vector of x_v_wl: we set x_v_src_i and x_v_dest_i to 1
                for traffic in nodes:
                    for j in range(K):
                        row.append(float(traffic in link and i == j))
                # we continue filling the vector with the y_wl
                # we want to have x_v_src_i + x_v_dest_i - y_i <= 0
                # hence the 'minus' sign instead of float
                for j in range(K):
                    row.append(-float(i == j))
                G2.append(row)
        # G2 size should be K * T (rows) x K * (V + 1) (columns)

        # finally, we want to ensure that wavelength are used in 
        # ascending order, meaning that y_wl >= y_(wl + 1) for wl 
        # in [0, K-1]. We can rewrite it y_(wl + 1) - y_wl <= 0
        G3 = []
        for i in range(1, K):
            row_wl = [float((i == wl) or -(i == wl + 1)) for wl in range(K)]
            final_row = np.concatenate([np.zeros(V * K), row_wl])
            G3.append(final_row)
        # G3 size should be K - 1 (rows) x K * (V + 1) (columns)

        # x_v_src_i + x_v_dest_i - y_i <= 0 and y_(wl + 1) - y_wl <= 0
        h = np.concatenate([np.zeros(K * T), np.zeros(K - 1)])
        G = np.concatenate((G2, G3), axis=0).tolist()
        A, G, b, c, h = map(matrix, (A, G, b, c, h))
        binvar = set(range(K * (V + 1)))
        solsta, x = glpk.ilp(c, G.T, h, A.T, b, B=binvar)
        
        for index, traffic in enumerate(nodes):
            for i in range(K):
            
                print(i*V + index, i, index, x[i + index*V], traffic)
                # if x[i*V + index]:
                    # print(i, index, traffic)
                
        print(x, len(x))
        # print('ttt'*100, int(sum(x[-K:])))
        #return int(sum(x[-K:]))