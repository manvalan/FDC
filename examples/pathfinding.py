#!/usr/bin/env python3
"""
Example: Path Finding and Route Optimization
Demonstrates advanced pathfinding features.
"""

import sys
sys.path.insert(0, '../src')

from node import Node, NodeType
from edge import Edge, TrackType
from railway_network import RailwayNetwork


def create_complex_network():
    """Create a more complex network for pathfinding demonstration."""
    
    network = RailwayNetwork("Complex Railway Network")
    
    # Create a grid-like network
    nodes_data = [
        ("A", "Station A", 0, 0),
        ("B", "Station B", 1, 0),
        ("C", "Station C", 2, 0),
        ("D", "Station D", 0, 1),
        ("E", "Interchange E", 1, 1),
        ("F", "Station F", 2, 1),
        ("G", "Station G", 0, 2),
        ("H", "Station H", 1, 2),
        ("I", "Station I", 2, 2),
    ]
    
    for node_id, name, lon, lat in nodes_data:
        node_type = NodeType.INTERCHANGE if "Interchange" in name else NodeType.STATION
        node = Node(node_id, name, node_type, latitude=lat, longitude=lon)
        network.add_node(node)
    
    # Create edges with different distances
    edges_data = [
        ("A", "B", 10), ("B", "C", 15),
        ("A", "D", 12), ("B", "E", 8), ("C", "F", 10),
        ("D", "E", 9), ("E", "F", 11),
        ("D", "G", 14), ("E", "H", 7), ("F", "I", 13),
        ("G", "H", 16), ("H", "I", 9),
        ("A", "E", 20),  # Direct diagonal route
        ("E", "I", 18),  # Another diagonal
    ]
    
    for from_node, to_node, distance in edges_data:
        edge = Edge(from_node, to_node, distance)
        network.add_edge(edge)
    
    return network


def main():
    print("=" * 60)
    print("PATH FINDING AND ROUTE OPTIMIZATION - DEMO")
    print("=" * 60)
    print()
    
    network = create_complex_network()
    
    print(f"Network created with {len(network.nodes)} stations")
    print()
    
    # Test multiple routes
    start, end = "A", "I"
    
    print(f"🔍 Finding routes from {start} to {end}...")
    print()
    
    # Shortest path
    result = network.find_shortest_path(start, end)
    if result:
        path, distance = result
        print(f"✓ Shortest path: {' → '.join(path)}")
        print(f"  Distance: {distance:.1f} km")
    print()
    
    # All alternative paths
    print("📋 All possible routes (top 5):")
    paths = network.find_all_paths(start, end, max_paths=5)
    for i, path in enumerate(paths, 1):
        # Calculate distance
        distance = 0
        for j in range(len(path) - 1):
            edge_data = network.graph.get_edge_data(path[j], path[j+1])
            if edge_data:
                distance += edge_data['distance']
        
        print(f"  {i}. {' → '.join(path)} ({distance:.1f} km)")
    print()
    
    # Visualize
    print("🎨 Generating visualization...")
    try:
        network.visualize(figsize=(10, 10), save_path="pathfinding_network.png")
        print("  ✓ Saved to: pathfinding_network.png")
    except Exception as e:
        print(f"  ⚠ Visualization not available: {e}")
    
    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
