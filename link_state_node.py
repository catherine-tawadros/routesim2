from simulator.node import Node
import math
import heapq
import json


class Link_State_Node(Node):
    def __init__(self, id):
        # has id and list of neighbors
        super().__init__(id)
        # self.direct_links = {}
        self.all_graph_nodes = set([id])
        self.all_graph_links = {}
        self.all_graph_link_seq_nums = {}

    # Return a string
    def __str__(self):
        return f'''
            ID: {self.id}
            Links: {self.get_direct_links()}
            Sequence Numbers: {self.all_graph_link_seq_nums}
        '''

    def get_direct_links(self, id=None):
        if id is None:
            id = self.id
        links = {}
        # print(f"direct links of {id}:")
        # print("whole graph:")
        # print(self.all_graph_links)
        for k in self.all_graph_links:
            if id in k:
                links[k] = self.all_graph_links[k]
                # print(k, links[k])
        return links

    def link_has_been_updated(self, neighbor, latency):
        link_id = frozenset([self.id, neighbor])
        # deleting a link
        if latency == -1 and neighbor in self.neighbors:
            self.neighbors.remove(neighbor)
            # CHOOSE ONE OF THESE TWO
            # self.direct_links.remove(link_id)
            self.all_graph_links.pop(link_id)
        # new link
        elif neighbor not in self.neighbors:
            self.neighbors.append(neighbor)
            # self.all_graph_nodes.add(neighbor)
            # self.direct_links[link_id] = latency
            self.all_graph_links[link_id] = latency
        # updating an old link
        else:
            # self.direct_links[link_id] = latency
            self.all_graph_links[link_id] = latency
        
        if link_id in self.all_graph_link_seq_nums:
            seq_num = self.all_graph_link_seq_nums[link_id] + 1
            self.all_graph_link_seq_nums[link_id] = seq_num
        else:
            self.all_graph_link_seq_nums[link_id] = 0
            seq_num = 0

        if not neighbor in self.all_graph_nodes:
            self.all_graph_nodes.add(neighbor)
            for link in self.all_graph_links:
                message = json.dumps(list(link) + [self.all_graph_links[link], self.all_graph_link_seq_nums[link]])
                self.send_to_neighbor(neighbor, message)

        # send further messages to neighbors
        self.send_to_neighbors(json.dumps([self.id, neighbor, latency, seq_num]))

    # Fill in this function
    def process_incoming_routing_message(self, m):
        # send further routing messages using self.send_to_neighbor(s)
        # print("message", m)
        src, dst, cost, seq_num = json.loads(m)
        if src not in self.all_graph_nodes:
            self.all_graph_nodes.add(src)
        if dst not in self.all_graph_nodes:
            self.all_graph_nodes.add(dst)
        link_id = frozenset([src, dst])
        if not link_id in self.all_graph_link_seq_nums:
            self.all_graph_links[link_id] = cost
            self.all_graph_link_seq_nums[link_id] = seq_num
            self.send_to_neighbors(m)
        elif seq_num > self.all_graph_link_seq_nums[link_id]:
            # update tables
            self.all_graph_links[link_id] = cost
            self.all_graph_link_seq_nums[link_id] = seq_num
            self.send_to_neighbors(m)
        if cost == -1:
            # NOTE: there is a case where there is a seq num for a link but it is not in all_graph_links
            self.all_graph_links.pop(link_id, None)

    def dijkstra(self):
        # print(id, self.get_direct_links())
        # Initialize distance dictionary with infinity for all nodes except self
        distances = {node: math.inf for node in self.all_graph_nodes}
        distances[self.id] = 0
        
        # Priority queue to store (cost, node) tuples
        pq = [(0, self.id)]
        
        # Dictionary to store the next hop towards the destination
        next_hop = {}
        
        # Dictionary to track the shortest path tree
        previous_nodes = {}
        
        while pq:
            current_distance, current_node = heapq.heappop(pq)
            
            # Skip processing if we already have a shorter distance recorded
            if current_distance > distances[current_node]:
                continue
            
            # Get direct links from the current node
            for link, cost in self.get_direct_links(current_node).items():
                neighbor = next(iter(link - {current_node}))  # Get the other node in the link
                new_distance = current_distance + cost
                
                # Update if a shorter path is found
                if new_distance < distances[neighbor]:
                    distances[neighbor] = new_distance
                    heapq.heappush(pq, (new_distance, neighbor))
                    previous_nodes[neighbor] = current_node
        
        # Construct next hop table
        for node in self.all_graph_nodes:
            if node == self.id:
                continue
            
            # Trace back from destination to find the next hop
            next_node = node
            while next_node in previous_nodes and previous_nodes[next_node] != self.id:
                next_node = previous_nodes[next_node]
            
            if next_node in previous_nodes:
                next_hop[node] = next_node
        
        return next_hop

    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):
        # check routing table
        next_hop = self.dijkstra()
        # print(next_hop)
        return next_hop.get(destination, -1)
        # return -1
