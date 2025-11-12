"""
Unit tests for the Train Timetable Management System
"""

import unittest
from datetime import datetime, timedelta
from rail_network import (
    Station, TrackSegment, RailNetwork, 
    Train, ScheduleEntry, Timetable
)


class TestStation(unittest.TestCase):
    """Tests for the Station class."""
    
    def test_station_creation(self):
        """Test creating a station."""
        station = Station("Test Station", "station")
        self.assertEqual(station.name, "Test Station")
        self.assertEqual(station.station_type, "station")
    
    def test_station_equality(self):
        """Test station equality comparison."""
        station1 = Station("Station A")
        station2 = Station("Station A")
        station3 = Station("Station B")
        self.assertEqual(station1, station2)
        self.assertNotEqual(station1, station3)
    
    def test_station_hash(self):
        """Test that stations can be used in sets and dicts."""
        station1 = Station("Station A")
        station2 = Station("Station A")
        station_set = {station1, station2}
        self.assertEqual(len(station_set), 1)


class TestTrackSegment(unittest.TestCase):
    """Tests for the TrackSegment class."""
    
    def test_track_creation(self):
        """Test creating a track segment."""
        station_a = Station("A")
        station_b = Station("B")
        track = TrackSegment(station_a, station_b, 10.0, 15, bidirectional=True)
        self.assertEqual(track.from_station, station_a)
        self.assertEqual(track.to_station, station_b)
        self.assertEqual(track.distance, 10.0)
        self.assertEqual(track.travel_time, 15)
        self.assertTrue(track.bidirectional)


class TestRailNetwork(unittest.TestCase):
    """Tests for the RailNetwork class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.network = RailNetwork()
        self.station_a = Station("Station A")
        self.station_b = Station("Station B")
        self.station_c = Station("Station C")
    
    def test_add_station(self):
        """Test adding stations to the network."""
        self.network.add_station(self.station_a)
        self.assertEqual(len(self.network.stations), 1)
        self.assertIn("Station A", self.network.stations)
    
    def test_add_track_segment(self):
        """Test adding track segments to the network."""
        track = TrackSegment(self.station_a, self.station_b, 10.0, 15)
        self.network.add_track_segment(track)
        self.assertEqual(len(self.network.tracks), 1)
        self.assertEqual(len(self.network.stations), 2)
    
    def test_bidirectional_track(self):
        """Test that bidirectional tracks create connections in both directions."""
        track = TrackSegment(self.station_a, self.station_b, 10.0, 15, bidirectional=True)
        self.network.add_track_segment(track)
        
        neighbors_a = self.network.get_neighbors(self.station_a)
        neighbors_b = self.network.get_neighbors(self.station_b)
        
        self.assertEqual(len(neighbors_a), 1)
        self.assertEqual(len(neighbors_b), 1)
        self.assertEqual(neighbors_a[0][0], self.station_b)
        self.assertEqual(neighbors_b[0][0], self.station_a)
    
    def test_unidirectional_track(self):
        """Test that unidirectional tracks create connection in only one direction."""
        track = TrackSegment(self.station_a, self.station_b, 10.0, 15, bidirectional=False)
        self.network.add_track_segment(track)
        
        neighbors_a = self.network.get_neighbors(self.station_a)
        neighbors_b = self.network.get_neighbors(self.station_b)
        
        self.assertEqual(len(neighbors_a), 1)
        self.assertEqual(len(neighbors_b), 0)
    
    def test_get_station(self):
        """Test retrieving a station by name."""
        self.network.add_station(self.station_a)
        retrieved = self.network.get_station("Station A")
        self.assertEqual(retrieved, self.station_a)
        
        not_found = self.network.get_station("Non-existent")
        self.assertIsNone(not_found)
    
    def test_shortest_path_simple(self):
        """Test finding shortest path in a simple network."""
        # Create a simple path: A -> B -> C
        track1 = TrackSegment(self.station_a, self.station_b, 10.0, 15)
        track2 = TrackSegment(self.station_b, self.station_c, 10.0, 15)
        self.network.add_track_segment(track1)
        self.network.add_track_segment(track2)
        
        result = self.network.find_shortest_path("Station A", "Station C", by_time=True)
        self.assertIsNotNone(result)
        
        path, cost = result
        self.assertEqual(len(path), 3)
        self.assertEqual(path[0].name, "Station A")
        self.assertEqual(path[1].name, "Station B")
        self.assertEqual(path[2].name, "Station C")
        self.assertEqual(cost, 30)  # 15 + 15 minutes
    
    def test_shortest_path_multiple_routes(self):
        """Test finding shortest path when multiple routes exist."""
        # Create a network with two paths from A to C
        # Path 1: A -> B -> C (time: 30)
        # Path 2: A -> C (time: 20)
        station_d = Station("Station D")
        
        track1 = TrackSegment(self.station_a, self.station_b, 10.0, 15)
        track2 = TrackSegment(self.station_b, self.station_c, 10.0, 15)
        track3 = TrackSegment(self.station_a, self.station_c, 15.0, 20)  # Direct but faster
        
        self.network.add_track_segment(track1)
        self.network.add_track_segment(track2)
        self.network.add_track_segment(track3)
        
        result = self.network.find_shortest_path("Station A", "Station C", by_time=True)
        self.assertIsNotNone(result)
        
        path, cost = result
        self.assertEqual(cost, 20)  # Should take the direct route
        self.assertEqual(len(path), 2)  # A -> C directly
    
    def test_shortest_path_by_distance(self):
        """Test finding shortest path by distance."""
        # Two paths with different distance/time tradeoffs
        track1 = TrackSegment(self.station_a, self.station_c, 15.0, 10)  # Longer but faster
        track2 = TrackSegment(self.station_a, self.station_b, 5.0, 15)   # Shorter but slower
        track3 = TrackSegment(self.station_b, self.station_c, 5.0, 15)
        
        self.network.add_track_segment(track1)
        self.network.add_track_segment(track2)
        self.network.add_track_segment(track3)
        
        # By distance, should prefer A -> B -> C (10 km)
        result = self.network.find_shortest_path("Station A", "Station C", by_time=False)
        self.assertIsNotNone(result)
        path, cost = result
        self.assertEqual(cost, 10.0)
        self.assertEqual(len(path), 3)
    
    def test_no_path_exists(self):
        """Test when no path exists between stations."""
        self.network.add_station(self.station_a)
        self.network.add_station(self.station_c)
        # No connection between stations
        
        result = self.network.find_shortest_path("Station A", "Station C")
        self.assertIsNone(result)


class TestScheduleEntry(unittest.TestCase):
    """Tests for the ScheduleEntry class."""
    
    def test_schedule_entry_creation(self):
        """Test creating a schedule entry."""
        station = Station("Test Station")
        arrival = datetime(2024, 1, 15, 10, 0)
        departure = datetime(2024, 1, 15, 10, 5)
        
        entry = ScheduleEntry(station, arrival, departure, "1")
        self.assertEqual(entry.station, station)
        self.assertEqual(entry.arrival_time, arrival)
        self.assertEqual(entry.departure_time, departure)
        self.assertEqual(entry.platform, "1")


class TestTrain(unittest.TestCase):
    """Tests for the Train class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.train = Train("T001", "Test Express")
        self.station_a = Station("Station A")
        self.station_b = Station("Station B")
        self.station_c = Station("Station C")
    
    def test_train_creation(self):
        """Test creating a train."""
        self.assertEqual(self.train.train_id, "T001")
        self.assertEqual(self.train.train_name, "Test Express")
        self.assertEqual(len(self.train.schedule), 0)
    
    def test_add_stop(self):
        """Test adding stops to a train."""
        entry = ScheduleEntry(
            self.station_a,
            datetime(2024, 1, 15, 10, 0),
            datetime(2024, 1, 15, 10, 5),
            "1"
        )
        self.train.add_stop(entry)
        self.assertEqual(len(self.train.schedule), 1)
    
    def test_get_origin_and_destination(self):
        """Test getting origin and destination."""
        entry1 = ScheduleEntry(
            self.station_a,
            datetime(2024, 1, 15, 10, 0),
            datetime(2024, 1, 15, 10, 5),
            "1"
        )
        entry2 = ScheduleEntry(
            self.station_b,
            datetime(2024, 1, 15, 10, 30),
            datetime(2024, 1, 15, 10, 35),
            "2"
        )
        entry3 = ScheduleEntry(
            self.station_c,
            datetime(2024, 1, 15, 11, 0),
            datetime(2024, 1, 15, 11, 0),
            "3"
        )
        
        self.train.add_stop(entry1)
        self.train.add_stop(entry2)
        self.train.add_stop(entry3)
        
        self.assertEqual(self.train.get_origin(), self.station_a)
        self.assertEqual(self.train.get_destination(), self.station_c)
    
    def test_get_times(self):
        """Test getting departure and arrival times."""
        entry1 = ScheduleEntry(
            self.station_a,
            datetime(2024, 1, 15, 10, 0),
            datetime(2024, 1, 15, 10, 5),
            "1"
        )
        entry2 = ScheduleEntry(
            self.station_c,
            datetime(2024, 1, 15, 11, 0),
            datetime(2024, 1, 15, 11, 0),
            "3"
        )
        
        self.train.add_stop(entry1)
        self.train.add_stop(entry2)
        
        self.assertEqual(self.train.get_departure_time(), datetime(2024, 1, 15, 10, 5))
        self.assertEqual(self.train.get_arrival_time(), datetime(2024, 1, 15, 11, 0))


class TestTimetable(unittest.TestCase):
    """Tests for the Timetable class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.network = RailNetwork()
        self.timetable = Timetable(self.network)
        
        self.station_a = Station("Station A")
        self.station_b = Station("Station B")
        self.station_c = Station("Station C")
        
        self.network.add_station(self.station_a)
        self.network.add_station(self.station_b)
        self.network.add_station(self.station_c)
    
    def test_timetable_creation(self):
        """Test creating a timetable."""
        self.assertEqual(len(self.timetable.trains), 0)
        self.assertEqual(self.timetable.network, self.network)
    
    def test_add_train(self):
        """Test adding a train to the timetable."""
        train = Train("T001", "Test Express")
        self.timetable.add_train(train)
        self.assertEqual(len(self.timetable.trains), 1)
    
    def test_get_train(self):
        """Test retrieving a train by ID."""
        train = Train("T001", "Test Express")
        self.timetable.add_train(train)
        
        retrieved = self.timetable.get_train("T001")
        self.assertEqual(retrieved, train)
        
        not_found = self.timetable.get_train("T999")
        self.assertIsNone(not_found)
    
    def test_get_trains_at_station(self):
        """Test getting trains at a station at a specific time."""
        train1 = Train("T001", "Train 1")
        train2 = Train("T002", "Train 2")
        
        # Train 1 stops at Station A from 10:00 to 10:05
        entry1 = ScheduleEntry(
            self.station_a,
            datetime(2024, 1, 15, 10, 0),
            datetime(2024, 1, 15, 10, 5),
            "1"
        )
        train1.add_stop(entry1)
        
        # Train 2 stops at Station A from 10:10 to 10:15
        entry2 = ScheduleEntry(
            self.station_a,
            datetime(2024, 1, 15, 10, 10),
            datetime(2024, 1, 15, 10, 15),
            "2"
        )
        train2.add_stop(entry2)
        
        self.timetable.add_train(train1)
        self.timetable.add_train(train2)
        
        # At 10:03, only Train 1 should be at the station
        trains = self.timetable.get_trains_at_station(
            "Station A", 
            datetime(2024, 1, 15, 10, 3)
        )
        self.assertEqual(len(trains), 1)
        self.assertEqual(trains[0].train_id, "T001")
        
        # At 10:12, only Train 2 should be at the station
        trains = self.timetable.get_trains_at_station(
            "Station A", 
            datetime(2024, 1, 15, 10, 12)
        )
        self.assertEqual(len(trains), 1)
        self.assertEqual(trains[0].train_id, "T002")
    
    def test_get_trains_between_stations(self):
        """Test getting trains that travel between two stations."""
        train1 = Train("T001", "Train 1")
        train2 = Train("T002", "Train 2")
        train3 = Train("T003", "Train 3")
        
        # Train 1: A -> B -> C
        train1.add_stop(ScheduleEntry(
            self.station_a,
            datetime(2024, 1, 15, 10, 0),
            datetime(2024, 1, 15, 10, 5),
            "1"
        ))
        train1.add_stop(ScheduleEntry(
            self.station_b,
            datetime(2024, 1, 15, 10, 30),
            datetime(2024, 1, 15, 10, 35),
            "2"
        ))
        train1.add_stop(ScheduleEntry(
            self.station_c,
            datetime(2024, 1, 15, 11, 0),
            datetime(2024, 1, 15, 11, 0),
            "3"
        ))
        
        # Train 2: A -> C (direct)
        train2.add_stop(ScheduleEntry(
            self.station_a,
            datetime(2024, 1, 15, 11, 0),
            datetime(2024, 1, 15, 11, 5),
            "1"
        ))
        train2.add_stop(ScheduleEntry(
            self.station_c,
            datetime(2024, 1, 15, 12, 0),
            datetime(2024, 1, 15, 12, 0),
            "3"
        ))
        
        # Train 3: B -> C (doesn't include A)
        train3.add_stop(ScheduleEntry(
            self.station_b,
            datetime(2024, 1, 15, 12, 0),
            datetime(2024, 1, 15, 12, 5),
            "2"
        ))
        train3.add_stop(ScheduleEntry(
            self.station_c,
            datetime(2024, 1, 15, 13, 0),
            datetime(2024, 1, 15, 13, 0),
            "3"
        ))
        
        self.timetable.add_train(train1)
        self.timetable.add_train(train2)
        self.timetable.add_train(train3)
        
        # Get trains from A to C
        trains = self.timetable.get_trains_between("Station A", "Station C")
        self.assertEqual(len(trains), 2)
        train_ids = [t.train_id for t in trains]
        self.assertIn("T001", train_ids)
        self.assertIn("T002", train_ids)
        self.assertNotIn("T003", train_ids)


if __name__ == '__main__':
    unittest.main()
