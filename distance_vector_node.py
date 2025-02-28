from simulator.node import Node
import json

class Distance_Vector_Node(Node):
    def __init__(self, id):
        super().__init__(id)
        # Distances between this node and its neighbors
        self.distance_vector = {
            id: (0, id)
        }
        self.paths = {
            id: [id]
        }
        self.neighbor_dvs = {}      # Neighbors' DVs

    # Return a string
    def __str__(self):
        result = "Node " + str(self.id)
        return result

    # Fill in this function
    def link_has_been_updated(self, neighbor, latency):
        # latency = -1 if delete a link
        if(latency == -1 and neighbor):
            self.neighbors.remove(neighbor)
            try:
                del self.distance_vector[neighbor]
                del self.paths[neighbor]

                destinations = list(self.distance_vector.keys())

                for dest in destinations:
                    if(self.distance_vector[dest][1] == neighbor):
                        del self.distance_vector[dest]
                        del self.paths[dest]

            except KeyError:
                print("Neighbor does not exist")
        else:
            # Add neighbor
            if neighbor not in self.neighbors:
                # New node
                self.neighbors.append(neighbor)
            else:
                # Updating existing node
                destinations = list(self.distance_vector.keys())

                print("NODE " + str(self.id) + " DESTINATIONS:", destinations)

                for dest in destinations:
                    path = self.paths[dest]
                    print("PATH FROM NODE " + str(self.id) + " TO " + str(dest) + " :", path)
                    if(neighbor in path):
                        print("NODE " + str(self.id) + " UPDATING PATH TO", dest)
                        self.distance_vector[dest] = (self.distance_vector[dest][0] + (latency - self.distance_vector[neighbor][0]), self.distance_vector[dest][1])
                        print()
            
            # Update distance vector
            self.distance_vector[neighbor] = (latency, neighbor)

            if(self.id == 3):
                print("NODE 3 NEIGHBOR:", neighbor)
                print("NODE 3 NEIGHBOR LATENCY:", latency)
                print("NODE 3 DV:", self.distance_vector)
                print("NODE 3 NEIGHBOR DVs:", self.neighbor_dvs)

            # Update paths
            self.paths[neighbor] = [neighbor]
        
        # Construct message
        message = {
            "sender": self.id,
            "timestamp": self.get_time(),
            "distance_vector": self.distance_vector,
            "paths": self.paths
        }

        self.send_to_neighbors(json.dumps(message))
        
    # Fill in this function
    def process_incoming_routing_message(self, m):
        message = json.loads(m)

        # Get the data in the message
        sender = int(message["sender"])
        timestamp = message["timestamp"]
        dv = message["distance_vector"]
        paths=  message["paths"]
    
        updated = False

        # Check for out-of-order messages
        if(sender not in self.neighbor_dvs or timestamp >= self.neighbor_dvs[sender]["timestamp"]):
            ####################################################################
            # In-order message
            ####################################################################

            print("FROM NODE " + str(sender) + " TO NODE " + str(self.id))
            # if(sender == 2 and self.id == 1):
            #     print(dv)
            if(sender == 3 and self.id == 2):
                print("NODE " + str(self.id) + " DV:", self.distance_vector)
                print("SENT DV:", dv)
                print("NODE " + str(self.id) + " PATHS:", self.paths)
                print("SENT PATHS:", paths)


            for node, (cost, next_hop) in dv.items():   
                node_path = paths.get(int(node), [])
                # print("NODE PATH: ", node_path)
                # if(self.id in node_path):
                #     continue
                if(sender not in self.distance_vector):
                    continue
                
                new_cost = cost + self.distance_vector[sender][0]

                # If new node is discovered or lower cost
                if(int(node) not in self.distance_vector or new_cost < self.distance_vector[int(node)][0]):
                    # New node found or better path found
                    print("NODE " + str(self.id) + " ADDING " + str(node))
                    print("DIST TO " + str(sender) + ":", self.distance_vector[sender][0])
                    print("DIST FROM " + str(sender) + " TO " + str(node) + ":", cost)
                    self.distance_vector[int(node)] = (self.distance_vector[sender][0] + cost, sender)
                    self.paths[int(node)] = [self.id, sender] + node_path
                    print("NODE " + str(self.id) + " PATHS: ", self.paths)
                    updated = True
                elif(int(node) in self.distance_vector and new_cost > self.distance_vector[int(node)][0]):
                    # Latency update (for the worse)
                    print("NODE " + str(self.id) + " PATH TO " + node + " COMPARISON WITH NODE", str(sender))
                    print("CURR PATH:", self.paths[int(node)])
                    print("SENT PATH:", [self.id, sender] + node_path)
                    # Only when it is for the same path:
                    if(self.paths[int(node)] == [self.id, sender] + node_path):
                        # Check neighbors to see if there is a better alternative path
                        next_hop = sender
                        for neighbor in self.neighbors:
                            if(neighbor in self.neighbor_dvs and node in self.neighbor_dvs[neighbor]["distance_vector"]):
                                # Get the neighbor DV
                                dv = self.neighbor_dvs[neighbor]["distance_vector"]
                                # Calculate the cost of using the neighbor's best path to the destination
                                neighbor_cost = dv[node][0] + self.distance_vector[self.neighbor_dvs[neighbor]["sender"]][0]
                                # Neighbor's path to the destination
                                node_path = self.neighbor_dvs[neighbor]["paths"][node]
                                if(new_cost > neighbor_cost):
                                    new_cost = neighbor_cost
                                    next_hop = neighbor
                                    self.paths[int(node)] = [self.id, next_hop] + node_path
                            
                        print("UPDATING LATENCY FOR CURRENT ROUTE TO", new_cost)
                        
                        self.distance_vector[int(node)] = (new_cost, next_hop)
                        updated = True

            if(sender == 3 and self.id == 2):
                print("NODE " + str(self.id) + " DV:", self.distance_vector)
                print("SENT DV:", dv)

            # # Update neighbor distance vector
            self.neighbor_dvs[sender] = message
            
            # Send message if distance vector changed
            if(updated):
                print("NODE " + str(self.id) + " SENDING UPDATED DISTANCE VECTOR")
                # Construct message
                message = {
                    "sender": self.id,
                    "timestamp": self.get_time(),
                    "distance_vector": self.distance_vector,
                    "paths": self.paths
                }

                self.send_to_neighbors(json.dumps(message))

        else:
            ####################################################################
            # Out-of-order message
            ####################################################################
            print("OUT OF ORDER")
            pass


    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):
        # print(self.distance_vector)
        # return self.distance_vector[destination]
        print("DESTINATION:", destination)
        print("NODE " + str(self.id) + " DV:", self.distance_vector)
        print("NODE " + str(self.id) + "PATHS:", self.paths)
        if(destination not in self.distance_vector):
            print("NO PATH FOUND")
            return -1
        print("PATH FOUND: ", self.distance_vector[destination][1])
        return self.distance_vector[destination][1]
