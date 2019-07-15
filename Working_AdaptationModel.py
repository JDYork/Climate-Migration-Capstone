from mesa import Agent, Model
from mesa.time import SimultaneousActivation
from mesa.space import NetworkGrid
from mesa.datacollection import DataCollector

import random
import math
import networkx as nx

tick = 0  # counter for current time step

class AdaptationModel(Model):
    def __init__(self, num_agents, num_nodes, init_time=0):
        super().__init__()
        self.num_agents = num_agents  # number of agents in simulation area
        self.schedule = SimultaneousActivation(self)  # agents are updated in a random order at each time step
        self.G = createGraph()  # agents are located on a spatial grid
        self.nodes = self.G.nodes()
        self.grid = NetworkGrid(self.G)
        self.agent_list = []  # list of all agents
        self.county_population_list = [0] * num_nodes
        global tick
        tick = init_time

        # Create Agents -- agents are placed randomly on the grid and added to the model schedule
        list_of_nodes = list(self.G.nodes())
        for i in range(self.num_agents):
            a = Household(i, self)
            self.schedule.add(a)
            # Add the agent to a random node
            self.grid.place_agent(a, random.choice(list_of_nodes))
            self.agent_list.append(a)

        # Store model level attributes using a DataCollector object
        ### WHAT DATA WILL BE COLLECTED AT THE MODEL LEVEL ?? EVERYTHING IS WITHIN THE NODES....
        # provided you can access the node data it Should work .. ?
        # these are based on the attributes of the model.
        self.datacollector = DataCollector(
            model_reporters={"Population": lambda m2: m2.num_agents, "County Population": lambda m1: m1.county_population_list}
        )

    def updateCountyPopulation(self):
        for n in self.nodes:
            self.county_population_list[n] = len(self.G.node[n]['agent'])

    def step(self):
        global tick
        ### WOULD NEED TO DO THIS FOR EVERY NODE - IS IT POSSIBLE
        self.schedule.step()  # update agents
        self.updateCountyPopulation()
        self.datacollector.collect(self)  # collect model level attributes for current time step
        tick += 1


class Household(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.unique_id = unique_id  # unique identification number
        self.connections = []  # list of all agents to which ego is connected
        self.adaptive_capacity = random.normalvariate(0, 1)  # ability to implement adaptation actions
        

    def step(self):
        self.calculate_adaptive_capacity()  # calculate new adaptative capacity

    def advance(self):
        self.make_decision()  # implement adaptation actions

    # Adaptive capacity changes randomly each year
    def calculate_adaptive_capacity(self):
        self.adaptive_capacity += random.normalvariate(0, 0.1)

    # The probability that an agent implements an action depends on flood damage and relative elevation
    # The relative probabilities of each possible type of action depend on community level adaptions and attachment
    # to place. The first resistance or accommodation action effectively reduces inundation by 1 m. The second and
    # third resistance or accommodation actions reduce inundation by 0.5 m each. An agent cannot implement more than 2 m
    # of accommodation or resistance. Agents that retreat are removed from the grid.
    def make_decision(self):
        if self.adaptive_capacity > 0.5:
            possible_steps = [node for node in self.model.grid.get_neighbors(self.pos, include_center=False)]
            if len(possible_steps) > 0:
                new_position = self.random.choice(possible_steps)
                self.model.grid.move_agent(self, new_position)

def createGraph():
    G = nx.Graph()
    G.add_edge(1, 2)
    G.add_edge(0, 1)
    G.add_edge(2, 0)
    G.node[0]['name'] = 'los angeles'
    G.node[1]['name'] = 'anchorage'
    G.node[2]['name'] = 'portland'

    nx.set_node_attributes(G, {0: 300, 1: 90, 2: 60}, 'dry')
    nx.set_edge_attributes(G, {(1,2): 1500, (0, 1): 2300, (0, 2): 900}, 'distance')

    return G