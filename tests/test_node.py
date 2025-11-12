"""
Unit tests for Node class
"""

import unittest
import sys
sys.path.insert(0, '../src')

from node import Node, NodeType


class TestNode(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.node = Node(
            node_id="TEST01",
            name="Test Station",
            node_type=NodeType.STATION,
            latitude=45.0,
            longitude=9.0,
            capacity=3,
            platforms=2
        )
    
    def test_node_creation(self):
        """Test node initialization."""
        self.assertEqual(self.node.id, "TEST01")
        self.assertEqual(self.node.name, "Test Station")
        self.assertEqual(self.node.node_type, NodeType.STATION)
        self.assertEqual(self.node.capacity, 3)
        self.assertEqual(self.node.platforms, 2)
    
    def test_node_availability(self):
        """Test node capacity management."""
        self.assertTrue(self.node.is_available())
        self.assertEqual(self.node.current_occupancy, 0)
    
    def test_node_occupy(self):
        """Test occupying node slots."""
        self.assertTrue(self.node.occupy())
        self.assertEqual(self.node.current_occupancy, 1)
        self.assertTrue(self.node.occupy())
        self.assertEqual(self.node.current_occupancy, 2)
        self.assertTrue(self.node.occupy())
        self.assertEqual(self.node.current_occupancy, 3)
        
        # Should fail when at capacity
        self.assertFalse(self.node.occupy())
        self.assertEqual(self.node.current_occupancy, 3)
    
    def test_node_release(self):
        """Test releasing node slots."""
        self.node.occupy()
        self.node.occupy()
        
        self.assertTrue(self.node.release())
        self.assertEqual(self.node.current_occupancy, 1)
        self.assertTrue(self.node.release())
        self.assertEqual(self.node.current_occupancy, 0)
        
        # Should fail when empty
        self.assertFalse(self.node.release())
        self.assertEqual(self.node.current_occupancy, 0)
    
    def test_node_to_dict(self):
        """Test node serialization."""
        data = self.node.to_dict()
        self.assertEqual(data['id'], "TEST01")
        self.assertEqual(data['name'], "Test Station")
        self.assertEqual(data['type'], "station")
        self.assertEqual(data['capacity'], 3)
    
    def test_node_equality(self):
        """Test node equality comparison."""
        node2 = Node("TEST01", "Another Name")
        node3 = Node("TEST02", "Test Station")
        
        self.assertEqual(self.node, node2)  # Same ID
        self.assertNotEqual(self.node, node3)  # Different ID


if __name__ == '__main__':
    unittest.main()
