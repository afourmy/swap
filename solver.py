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
        nodes = [{"id": traffic.name} for traffic in Traffic.query.all()]   
        visited, links = set(), []
        for traffic1 in Traffic.query.all():
            for traffic2 in Traffic.query.all():
                if traffic2 not in visited and traffic1 != traffic2:
                    if set(traffic1.path) & set(traffic2.path):
                        name = '{} - {}'.format(traffic1.name, traffic2.name)
                        links.append({
                            "source": traffic1.name,
                            "target": traffic2.name,
                            "name": name
                        })
            visited.add(traffic1)
        print({'nodes': nodes, 'links': links})
        return {'nodes': nodes, 'links': links}
