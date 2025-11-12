#!/usr/bin/env python3
"""
Example: Generate time-distance diagram for all trains on a route.
"""
import sys
sys.path.insert(0, '../src')

from datetime import datetime, timedelta
from node import Node, NodeType
from edge import Edge, TrackType
from railway_network import RailwayNetwork
from train import Train, TrainType
from schedule import ScheduleBuilder
from traffic_simulator import TrafficSimulator
from plotter import plot_time_distance


def create_network():
    network = RailwayNetwork("Plot Demo Network")
    nodes = [
        Node("A", "Città A", NodeType.STATION, capacity=3, platforms=2),
        Node("B", "Città B", NodeType.INTERCHANGE, capacity=3, platforms=2),
        Node("C", "Città C", NodeType.STATION, capacity=3, platforms=2),
        Node("D", "Città D", NodeType.STATION, capacity=2, platforms=1),
    ]
    for n in nodes:
        network.add_node(n)

    edges = [
        Edge("A", "B", 80.0, TrackType.DOUBLE, max_speed=200, capacity=2),
        Edge("B", "C", 60.0, TrackType.SINGLE, max_speed=120, capacity=1),
        Edge("C", "D", 50.0, TrackType.DOUBLE, max_speed=180, capacity=2),
    ]
    for e in edges:
        network.add_edge(e)
    return network


def create_schedules(network):
    base_time = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
    trains = [
        Train("T1", "FR9600", TrainType.HIGH_SPEED),
        Train("T2", "IC505", TrainType.INTERCITY),
        Train("T3", "REG2341", TrainType.REGIONAL),
    ]

    s1 = ScheduleBuilder.create_schedule("FR9600", trains[0], ["A","B","C","D"], network, base_time)
    s1.priority = 10
    s2 = ScheduleBuilder.create_schedule("IC505", trains[1], ["A","B","C","D"], network, base_time + timedelta(minutes=6))
    s2.priority = 7
    s3 = ScheduleBuilder.create_schedule("REG2341", trains[2], ["D","C","B","A"], network, base_time + timedelta(minutes=15))
    s3.priority = 5

    return [s1, s2, s3]


def main():
    network = create_network()
    schedules = create_schedules(network)

    # Optionally run the simulator to resolve conflicts (so plotting shows adjusted times)
    sim = TrafficSimulator(network)
    for s in schedules:
        sim.add_schedule(s)
    results = sim.simulate()
    print(f"Simulation results: total_trains={results['total_trains']}, delayed_trains={results['delayed_trains']}")

    # Plot time-distance diagram for route A->D
    route = ["A","B","C","D"]
    plot_time_distance(schedules, network, route=route, save_path="time_distance.png")
    print("Saved time-distance diagram to time_distance.png")

if __name__ == '__main__':
    main()
