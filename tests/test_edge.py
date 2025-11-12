"""
Unit tests for Edge class
"""

import unittest
import sys
sys.path.insert(0, '../src')

from edge import Edge, TrackType


class TestEdge(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.edge = Edge(
            from_node="A",
            to_node="B",
            distance=100.0,
            track_type=TrackType.DOUBLE,
            max_speed=200,
            capacity=2,
            bidirectional=True
        )
    
    def test_edge_creation(self):
        """Test edge initialization."""
        self.assertEqual(self.edge.from_node, "A")
        self.assertEqual(self.edge.to_node, "B")
        self.assertEqual(self.edge.distance, 100.0)
        self.assertEqual(self.edge.track_type, TrackType.DOUBLE)
        self.assertEqual(self.edge.max_speed, 200)
        self.assertEqual(self.edge.capacity, 2)
        self.assertTrue(self.edge.bidirectional)
    
    def test_edge_availability(self):
        """Test edge capacity management."""
        self.assertTrue(self.edge.is_available())
        self.assertEqual(self.edge.current_usage, 0)
    
    def test_edge_occupy(self):
        """Test occupying edge slots."""
        self.assertTrue(self.edge.occupy())
        self.assertEqual(self.edge.current_usage, 1)
        self.assertTrue(self.edge.occupy())
        self.assertEqual(self.edge.current_usage, 2)
        
        # Should fail when at capacity
        self.assertFalse(self.edge.occupy())
        self.assertEqual(self.edge.current_usage, 2)
    
    def test_edge_release(self):
        """Test releasing edge slots."""
        self.edge.occupy()
        self.edge.occupy()
        
        self.assertTrue(self.edge.release())
        self.assertEqual(self.edge.current_usage, 1)
        self.assertTrue(self.edge.release())
        self.assertEqual(self.edge.current_usage, 0)
        
        # Should fail when empty
        self.assertFalse(self.edge.release())
    
    def test_travel_time(self):
        """Test travel time calculation."""
        # At max speed (200 km/h)
        time = self.edge.travel_time()
        self.assertEqual(time, 0.5)  # 100km / 200km/h = 0.5h
        
        # At lower speed
        time = self.edge.travel_time(speed=100)
        self.assertEqual(time, 1.0)  # 100km / 100km/h = 1.0h
        
        # Speed higher than max should use max
        time = self.edge.travel_time(speed=300)
        self.assertEqual(time, 0.5)  # Limited to max_speed
    
    def test_edge_weight(self):
        """Test edge weight calculation."""
        weight = self.edge.get_weight()
        self.assertEqual(weight, 100.0)
    
    def test_edge_to_dict(self):
        """Test edge serialization."""
        data = self.edge.to_dict()
        self.assertEqual(data['from_node'], "A")
        self.assertEqual(data['to_node'], "B")
        self.assertEqual(data['distance'], 100.0)
        self.assertEqual(data['track_type'], "double")
        self.assertTrue(data['bidirectional'])


if __name__ == '__main__':
    unittest.main()
