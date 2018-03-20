from database import db
import numpy as np
from cvxopt import matrix, glpk, solvers
from models import Node, Fiber, Traffic

class Solver:

    def shortest_path(self):
        

        # Solves the MILP: minimize c'*x
        #         subject to G*x + s = h
        #                     A*x = b
        #                     s >= 0
        #                     xi integer, forall i in I

        # self.reset_flow()
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
                                else  1. if node == node_r 
                                else  0.
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
            print(traffic.path)
        db.session.commit()
        # traceback the shortest path with the flow
        curr_node, path_plink = traffic.source, []
        # while curr_node != traffic.destination:
        #     for neighbor, adj_plink in curr_node.adjacencies('fiber'):
        #         # if the flow leaving the current node is 1, we move
        #         # forward and replace the current node with its neighbor
        #         if adj_plink('flow', curr_node) == 1:
        #             path_plink.append(adj_plink)
        #             curr_node = neighbor
        return {}
        return path_plink