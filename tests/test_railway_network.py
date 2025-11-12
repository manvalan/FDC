"""
Unit tests for RailwayNetwork class
"""

import unittest
import sys
import os
sys.path.insert(0, '../src')

from node import Node, NodeType
from edge import Edge, TrackType
from railway_network import RailwayNetwork


class TestRailwayNetwork(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.network = RailwayNetwork("Test Network")
        
        # Create sample nodes
        self.node_a = Node("A", "Station A", latitude=45.0, longitude=9.0)
        self.node_b = Node("B", "Station B", latitude=45.1, longitude=9.1)
        self.node_c = Node("C", "Station C", latitude=45.2, longitude=9.2)
        
        # Create sample edge
        self.edge_ab = Edge("A", "B", 50.0)
        self.edge_bc = Edge("B", "C", 30.0)
    
    def test_network_creation(self):
        """Test network initialization."""
        self.assertEqual(self.network.name, "Test Network")
        self.assertEqual(len(self.network.nodes), 0)
        self.assertEqual(len(self.network.edges), 0)
    
    def test_add_node(self):
        """Test adding nodes to network."""
        self.assertTrue(self.network.add_node(self.node_a))
        self.assertEqual(len(self.network.nodes), 1)
        
        # Adding same node should fail
        self.assertFalse(self.network.add_node(self.node_a))
        self.assertEqual(len(self.network.nodes), 1)
    
    def test_add_edge(self):
        """Test adding edges to network."""
        self.network.add_node(self.node_a)
        self.network.add_node(self.node_b)
        
        self.assertTrue(self.network.add_edge(self.edge_ab))
        self.assertEqual(len(self.network.edges), 1)
        
        # Adding edge with non-existent nodes should fail
        edge_invalid = Edge("A", "Z", 100.0)
        self.assertFalse(self.network.add_edge(edge_invalid))
    
    def test_get_node(self):
        """Test retrieving nodes."""
        self.network.add_node(self.node_a)
        
        node = self.network.get_node("A")
        self.assertIsNotNone(node)
        self.assertEqual(node.name, "Station A")
        
        node = self.network.get_node("Z")
        self.assertIsNone(node)
    
    def test_remove_node(self):
        """Test removing nodes."""
        self.network.add_node(self.node_a)
        self.network.add_node(self.node_b)
        self.network.add_edge(self.edge_ab)
        
        self.assertTrue(self.network.remove_node("A"))
        self.assertEqual(len(self.network.nodes), 1)
        
        # Edge should also be removed
        edges_with_a = [e for e in self.network.edges 
                       if e.from_node == "A" or e.to_node == "A"]
        self.assertEqual(len(edges_with_a), 0)
    
    def test_shortest_path(self):
        """Test shortest path finding."""
        # Create simple path: A -> B -> C
        self.network.add_node(self.node_a)
        self.network.add_node(self.node_b)
        self.network.add_node(self.node_c)
        self.network.add_edge(self.edge_ab)
        self.network.add_edge(self.edge_bc)
        
        result = self.network.find_shortest_path("A", "C")
        self.assertIsNotNone(result)
        
        path, distance = result
        self.assertEqual(path, ["A", "B", "C"])
        self.assertEqual(distance, 80.0)  # 50 + 30
    
    def test_no_path(self):
        """Test when no path exists."""
        self.network.add_node(self.node_a)
        self.network.add_node(self.node_b)
        # No edge added
        
        result = self.network.find_shortest_path("A", "B")
        self.assertIsNone(result)
    
    def test_get_connected_nodes(self):
        """Test getting connected nodes."""
        self.network.add_node(self.node_a)
        self.network.add_node(self.node_b)
        self.network.add_node(self.node_c)
        self.network.add_edge(self.edge_ab)
        self.network.add_edge(self.edge_bc)
        
        connected = self.network.get_connected_nodes("B")
        self.assertEqual(set(connected), {"A", "C"})  # Bidirectional
    
    def test_network_stats(self):
        """Test network statistics."""
        self.network.add_node(self.node_a)
        self.network.add_node(self.node_b)
        self.network.add_edge(self.edge_ab)
        
        stats = self.network.get_network_stats()
        self.assertEqual(stats['num_nodes'], 2)
        self.assertEqual(stats['num_edges'], 1)
        self.assertEqual(stats['total_track_length'], 50.0)
    
    def test_export_import_json(self):
        """Test JSON export and import."""
        # Build network
        self.network.add_node(self.node_a)
        self.network.add_node(self.node_b)
        self.network.add_edge(self.edge_ab)
        
        # Export
        filepath = "test_network.json"
        self.network.export_to_json(filepath)
        self.assertTrue(os.path.exists(filepath))
        
        # Import
        new_network = RailwayNetwork()
        new_network.import_from_json(filepath)
        
        self.assertEqual(len(new_network.nodes), 2)
        self.assertEqual(len(new_network.edges), 1)
        self.assertIn("A", new_network.nodes)
        self.assertIn("B", new_network.nodes)
        
        # Cleanup
        os.remove(filepath)
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove any test files
        test_files = ["test_network.json"]
        for f in test_files:
            if os.path.exists(f):
                os.remove(f)


if __name__ == '__main__':
    unittest.main()
