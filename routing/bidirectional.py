

from heapq import heappush, heappop
from animator import GraphSearchAnimator


class BidirectionalAStarAnimator(GraphSearchAnimator):
    """ Draw a graph search. """

    def __init__(self, graph, vertex_coords, quadtree, landmark_dict):
        GraphSearchAnimator.__init__(self, graph, vertex_coords, quadtree)
        self.landmark_dict = landmark_dict    # for ALT

    def astar_animation(self, source, dest, epsilon=1):
        source = self._find_closest_vertex(source)
        dest = self._find_closest_vertex(dest)
        heuristic = lambda id1, id2: self._dist(id1, id2) * epsilon
        seq, pred_list = self.__astar(source, dest, heuristic)
        return self.__process_search_result(seq, pred_list, dest)

    def dijkstra_animation(self, source, dest):
        source = self._find_closest_vertex(source)
        dest = self._find_closest_vertex(dest)
        # no heurisitic, so just return zero
        heuristic = lambda id1, id2: 0
        seq, pred_list = self.__astar(source, dest, heuristic)
        return self.__process_search_result(seq, pred_list, dest)

    def alt_animation(self, source, dest):
        """ A* Landmark Triangle Inequality: ALT Algorithm """
        source = self._find_closest_vertex(source)
        dest = self._find_closest_vertex(dest)
        # no heurisitic, so just return zero
        heuristic = self.__alt_heuristic
        seq, pred_list = self.__astar(source, dest, heuristic)
        return self.__process_search_result(seq, pred_list, dest)

    def __process_search_result(self, sequence, pred_list, dest):
        sequence_coords = self._sequence_coords(sequence)
        path = self.__construct_shortest_path(pred_list, dest)
        return sequence, sequence_coords, path

    def __astar(self, source, dest, heuristic):
        if not source or not dest:
            return {}, []
        sequence = []
        len_shortest = float("inf")
        midpoint = None
        
        fwd_preds = {source : {'dist' : 0, 'pred' : None}}
        fwd_closed = set()
        fwd_unseen = [(0, source)]

        rev_preds = {dest : {'dist' : 0, 'pred' : None}}
        rev_closed = set()
        rev_unseen = [(0, dest)]
        while rev_unseen and fwd_unseen:
            fwd_scanned = self.__scan(dest, fwd_unseen, fwd_preds, fwd_closed, heuristic)
            fwd_path_len = self.__bidirectional_check(fwd_scanned, fwd_preds, rev_preds, sequence)
            if fwd_path_len > len_shortest:
                return sequence[2:], (fwd_preds, rev_preds, midpoint)
            len_shortest = fwd_path_len
            midpoint = fwd_scanned

            rev_scanned = self.__scan(source, rev_unseen, rev_preds, rev_closed, heuristic)
            rev_path_len = self.__bidirectional_check(rev_scanned, rev_preds, fwd_preds, sequence)
            if rev_path_len > len_shortest:
                return sequence[2:], (fwd_preds, rev_preds, midpoint)
            len_shortest = rev_path_len
            midpoint = rev_scanned
        return {}, []    # no valid path found

    def __bidirectional_check(self, vertex, preds, opp_preds, sequence):
        sequence.append((preds[vertex]['pred'], [vertex]))
        if vertex in opp_preds:
            len_path = (opp_preds[vertex]['dist'] + 
                        preds[vertex]['dist'])
            return len_path
        return float("inf")

    def __scan(self, dest, unseen, pred_list, closed, heuristic):
        _, vert = heappop(unseen)
        closed.add(vert)
        for arc, arc_len in self.graph[vert]:
            if arc in closed: 
                continue    # disgard nodes that already have optimal paths
            new_dist = pred_list[vert]['dist'] + arc_len
            if arc not in pred_list or new_dist < pred_list[arc]['dist']:
                # the shortest path to the arc changed, record this
                # subseq.append(arc)
                pred_list[arc] = {'pred' : vert, 'dist' : new_dist}
                est = new_dist + heuristic(arc, dest)
                heappush(unseen, (est, arc))
        # return the scanned vertex so we can check if the search has finished
        return vert

    def __construct_shortest_path(self, pred_list, dest):
        (fwd_preds, rev_preds, midpoint) = pred_list
        fwd_path = []
        vertex = midpoint
        while fwd_preds[vertex]['pred'] is not None:
            fwd_path.append(vertex)
            vertex = fwd_preds[vertex]['pred']
        fwd_path.reverse()

        rev_path = []
        vertex = midpoint
        while rev_preds[vertex]['pred'] is not None:
            rev_path.append(vertex)
            vertex = rev_preds[vertex]['pred']
        return [self.vertex_coords[v] for v in (fwd_path + rev_path + [dest])]

    def __alt_heuristic(self, id1, id2):
        max_dist = float("-inf")
        lm_dists = self.landmark_dict
        for dist1, dist2 in zip(lm_dists[id1], lm_dists[id2]):
            d = abs(dist1 - dist2)
            if d > max_dist:
                max_dist = d
        return max_dist
