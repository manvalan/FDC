#!/usr/bin/env python3
"""
Test script to verify Ferrovie della Contea JSON loading.
"""
import json
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from node import Node, NodeType
from edge import Edge, TrackType
from railway_network import RailwayNetwork

def test_load():
    """Test loading Ferrovie della Contea."""
    json_path = os.path.join(os.path.dirname(__file__), 'ferrovie_contea_fdc.json')
    
    print(f"Loading from: {json_path}")
    print(f"File exists: {os.path.exists(json_path)}")
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"\n✅ JSON loaded successfully")
        print(f"Network name: {data.get('name')}")
        print(f"Number of nodes: {len(data.get('nodes', []))}")
        print(f"Number of edges: {len(data.get('edges', []))}")
        
        # Create network
        network = RailwayNetwork(data.get('name', 'Ferrovie della Contea'))
        
        # Import nodes
        for node_data in data.get('nodes', []):
            node_type_str = node_data.get('type', 'station').upper()
            if node_type_str == 'STATION':
                node_type = NodeType.STATION
            elif node_type_str == 'INTERCHANGE':
                node_type = NodeType.INTERCHANGE
            elif node_type_str == 'DEPOT':
                node_type = NodeType.DEPOT
            else:
                node_type = NodeType.STATION
            
            node = Node(
                node_id=node_data['id'],
                name=node_data.get('name', node_data['id']),
                node_type=node_type,
                latitude=node_data.get('latitude', 0.0),
                longitude=node_data.get('longitude', 0.0),
                capacity=node_data.get('capacity', 2),
                platforms=node_data.get('platforms', 2)
            )
            network.add_node(node)
        
        print(f"\n✅ {len(network.nodes)} nodes imported")
        
        # Import edges
        for edge_data in data.get('edges', []):
            from_id = edge_data['from_node']
            to_id = edge_data['to_node']
            
            track_type_str = edge_data.get('track_type', 'single').upper()
            if track_type_str == 'SINGLE':
                track_type = TrackType.SINGLE
            elif track_type_str == 'DOUBLE':
                track_type = TrackType.DOUBLE
            else:
                track_type = TrackType.SINGLE
            
            if from_id in network.nodes and to_id in network.nodes:
                edge = Edge(
                    from_node=from_id,
                    to_node=to_id,
                    distance=edge_data['distance'],
                    track_type=track_type,
                    max_speed=edge_data.get('max_speed', 100.0)
                )
                network.add_edge(edge)
        
        print(f"✅ Edges imported")
        
        # Get statistics
        stats = network.get_network_stats()
        print(f"\n📊 Network Statistics:")
        print(f"   Nodes: {stats['num_nodes']}")
        print(f"   Edges: {stats['num_edges']}")
        print(f"   Total distance: {stats['total_track_length']:.1f} km")
        print(f"   Connected: {stats['is_connected']}")
        
        print(f"\n✅ SUCCESS! Network loaded correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_load()
