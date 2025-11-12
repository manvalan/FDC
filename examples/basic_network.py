#!/usr/bin/env python3
"""
Example: Basic Railway Network
Demonstrates how to create a simple railway network and perform basic operations.
"""

import sys
sys.path.insert(0, '../src')

from node import Node, NodeType
from edge import Edge, TrackType
from railway_network import RailwayNetwork


def create_sample_network():
    """Create a sample railway network for demonstration."""
    
    # Create the network
    network = RailwayNetwork("Italian Regional Network - Sample")
    
    # Add stations
    stations = [
        Node("MI", "Milano Centrale", NodeType.STATION, 45.4864, 9.2040, capacity=10, platforms=8),
        Node("BO", "Bologna Centrale", NodeType.STATION, 44.5065, 11.3427, capacity=8, platforms=6),
        Node("FI", "Firenze SMN", NodeType.STATION, 43.7769, 11.2477, capacity=6, platforms=5),
        Node("RO", "Roma Termini", NodeType.STATION, 41.9009, 12.5023, capacity=12, platforms=10),
        Node("NA", "Napoli Centrale", NodeType.STATION, 40.8532, 14.2739, capacity=8, platforms=7),
        Node("VE", "Venezia Mestre", NodeType.STATION, 45.4800, 12.2325, capacity=6, platforms=5),
        Node("TO", "Torino Porta Nuova", NodeType.STATION, 45.0623, 7.6756, capacity=7, platforms=6),
        Node("PR", "Parma", NodeType.INTERCHANGE, 44.8015, 10.3279, capacity=4, platforms=4),
    ]
    
    for station in stations:
        network.add_node(station)
    
    # Add railway tracks (edges)
    tracks = [
        Edge("MI", "BO", 215.0, TrackType.HIGH_SPEED, max_speed=250, capacity=2),
        Edge("BO", "FI", 95.0, TrackType.HIGH_SPEED, max_speed=250, capacity=2),
        Edge("FI", "RO", 275.0, TrackType.HIGH_SPEED, max_speed=300, capacity=2),
        Edge("RO", "NA", 225.0, TrackType.HIGH_SPEED, max_speed=300, capacity=2),
        Edge("MI", "VE", 267.0, TrackType.DOUBLE, max_speed=200, capacity=2),
        Edge("TO", "MI", 142.0, TrackType.HIGH_SPEED, max_speed=250, capacity=2),
        Edge("MI", "PR", 120.0, TrackType.DOUBLE, max_speed=180, capacity=1),
        Edge("PR", "BO", 95.0, TrackType.DOUBLE, max_speed=180, capacity=1),
    ]
    
    for track in tracks:
        network.add_edge(track)
    
    return network


def main():
    """Main function demonstrating railway network features."""
    
    print("=" * 60)
    print("RAILWAY NETWORK MANAGEMENT SYSTEM - DEMO")
    print("=" * 60)
    print()
    
    # Create network
    print("📍 Creating railway network...")
    network = create_sample_network()
    print(f"✓ Network created: {network}")
    print()
    
    # Display network statistics
    print("📊 Network Statistics:")
    stats = network.get_network_stats()
    for key, value in stats.items():
        print(f"  • {key.replace('_', ' ').title()}: {value}")
    print()
    
    # List all stations
    print("🚉 Stations in the network:")
    for node_id, node in network.nodes.items():
        print(f"  • [{node_id}] {node.name} - {node.node_type.value} "
              f"({node.platforms} platforms, capacity: {node.capacity})")
    print()
    
    # Find shortest path
    print("🔍 Finding shortest path from Milano to Roma...")
    result = network.find_shortest_path("MI", "RO")
    if result:
        path, distance = result
        print(f"  ✓ Path found: {' → '.join([network.get_node(n).name for n in path])}")
        print(f"  • Total distance: {distance:.1f} km")
        
        # Calculate estimated travel time
        total_time = 0
        for i in range(len(path) - 1):
            for edge in network.edges:
                if edge.from_node == path[i] and edge.to_node == path[i+1]:
                    time = edge.travel_time()
                    total_time += time
                    break
        print(f"  • Estimated travel time: {total_time:.2f} hours ({total_time * 60:.0f} minutes)")
    else:
        print("  ✗ No path found")
    print()
    
    # Find alternative paths
    print("🔍 Finding alternative routes from Milano to Napoli...")
    paths = network.find_all_paths("MI", "NA", max_paths=3)
    if paths:
        for i, path in enumerate(paths, 1):
            path_names = ' → '.join([network.get_node(n).name for n in path])
            
            # Calculate distance for this path
            distance = 0
            for j in range(len(path) - 1):
                edge_data = network.graph.get_edge_data(path[j], path[j+1])
                if edge_data:
                    distance += edge_data.get('distance', 0)
            
            print(f"  Route {i}: {path_names}")
            print(f"    Distance: {distance:.1f} km")
    else:
        print("  ✗ No paths found")
    print()
    
    # Find connections from a specific station
    print("🔗 Connections from Bologna:")
    connected = network.get_connected_nodes("BO")
    for node_id in connected:
        node = network.get_node(node_id)
        edge_data = network.graph.get_edge_data("BO", node_id)
        print(f"  • {node.name} - {edge_data['distance']:.1f} km "
              f"(max speed: {edge_data['max_speed']} km/h)")
    print()
    
    # Export network
    print("💾 Exporting network to JSON...")
    network.export_to_json("railway_network.json")
    print("  ✓ Exported to: railway_network.json")
    print()
    
    # Visualize network
    print("🎨 Generating network visualization...")
    try:
        network.visualize(figsize=(14, 10), save_path="railway_network.png")
        print("  ✓ Visualization saved to: railway_network.png")
    except Exception as e:
        print(f"  ⚠ Could not generate visualization: {e}")
        print("  (Make sure matplotlib is installed and display is available)")
    print()
    
    print("=" * 60)
    print("Demo completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
