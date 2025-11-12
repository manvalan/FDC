"""
Rail Network Module

This module provides classes for managing a train timetable system
using a graph-based representation of the rail network.
"""

from typing import Dict, List, Set, Optional, Tuple
from datetime import datetime, timedelta
import heapq


class Station:
    """
    Represents a station or interchange in the rail network.
    
    Attributes:
        name (str): The name of the station
        station_type (str): Type of station ('station' or 'interchange')
    """
    
    def __init__(self, name: str, station_type: str = "station"):
        """
        Initialize a station.
        
        Args:
            name: The name of the station
            station_type: Type of station ('station' or 'interchange')
        """
        self.name = name
        self.station_type = station_type
    
    def __repr__(self):
        return f"Station(name='{self.name}', type='{self.station_type}')"
    
    def __eq__(self, other):
        if not isinstance(other, Station):
            return False
        return self.name == other.name
    
    def __hash__(self):
        return hash(self.name)


class TrackSegment:
    """
    Represents a track segment (edge) connecting two stations.
    
    Attributes:
        from_station (Station): Starting station
        to_station (Station): Ending station
        distance (float): Distance in kilometers
        travel_time (int): Travel time in minutes
        bidirectional (bool): Whether trains can travel both directions
    """
    
    def __init__(self, from_station: Station, to_station: Station, 
                 distance: float, travel_time: int, bidirectional: bool = True):
        """
        Initialize a track segment.
        
        Args:
            from_station: Starting station
            to_station: Ending station
            distance: Distance in kilometers
            travel_time: Travel time in minutes
            bidirectional: Whether trains can travel both directions
        """
        self.from_station = from_station
        self.to_station = to_station
        self.distance = distance
        self.travel_time = travel_time
        self.bidirectional = bidirectional
    
    def __repr__(self):
        direction = "<->" if self.bidirectional else "->"
        return f"TrackSegment({self.from_station.name} {direction} {self.to_station.name}, {self.distance}km, {self.travel_time}min)"


class RailNetwork:
    """
    Represents the rail network as a graph structure.
    
    The network consists of stations (nodes) and track segments (edges).
    """
    
    def __init__(self):
        """Initialize an empty rail network."""
        self.stations: Dict[str, Station] = {}
        self.tracks: List[TrackSegment] = []
        self.adjacency: Dict[Station, List[Tuple[Station, TrackSegment]]] = {}
    
    def add_station(self, station: Station) -> None:
        """
        Add a station to the network.
        
        Args:
            station: The station to add
        """
        if station.name not in self.stations:
            self.stations[station.name] = station
            self.adjacency[station] = []
    
    def add_track_segment(self, track: TrackSegment) -> None:
        """
        Add a track segment to the network.
        
        Args:
            track: The track segment to add
        """
        # Ensure both stations exist
        self.add_station(track.from_station)
        self.add_station(track.to_station)
        
        # Add track to list
        self.tracks.append(track)
        
        # Update adjacency list
        self.adjacency[track.from_station].append((track.to_station, track))
        
        # Add reverse direction if bidirectional
        if track.bidirectional:
            self.adjacency[track.to_station].append((track.from_station, track))
    
    def get_station(self, name: str) -> Optional[Station]:
        """
        Get a station by name.
        
        Args:
            name: The name of the station
            
        Returns:
            The station if found, None otherwise
        """
        return self.stations.get(name)
    
    def get_neighbors(self, station: Station) -> List[Tuple[Station, TrackSegment]]:
        """
        Get all neighboring stations and their connecting tracks.
        
        Args:
            station: The station to get neighbors for
            
        Returns:
            List of tuples (neighbor_station, track_segment)
        """
        return self.adjacency.get(station, [])
    
    def find_shortest_path(self, start_name: str, end_name: str, 
                          by_time: bool = True) -> Optional[Tuple[List[Station], float]]:
        """
        Find the shortest path between two stations using Dijkstra's algorithm.
        
        Args:
            start_name: Name of the starting station
            end_name: Name of the destination station
            by_time: If True, minimize travel time; if False, minimize distance
            
        Returns:
            Tuple of (path as list of stations, total cost) or None if no path exists
        """
        start = self.get_station(start_name)
        end = self.get_station(end_name)
        
        if not start or not end:
            return None
        
        # Priority queue: (cost, counter, station, path)
        # Counter ensures consistent ordering when costs are equal
        counter = 0
        pq = [(0, counter, start, [start])]
        visited: Set[Station] = set()
        
        while pq:
            cost, _, current, path = heapq.heappop(pq)
            
            if current in visited:
                continue
            
            visited.add(current)
            
            if current == end:
                return (path, cost)
            
            for neighbor, track in self.get_neighbors(current):
                if neighbor not in visited:
                    edge_cost = track.travel_time if by_time else track.distance
                    new_cost = cost + edge_cost
                    new_path = path + [neighbor]
                    counter += 1
                    heapq.heappush(pq, (new_cost, counter, neighbor, new_path))
        
        return None
    
    def __repr__(self):
        return f"RailNetwork(stations={len(self.stations)}, tracks={len(self.tracks)})"


class ScheduleEntry:
    """
    Represents a single stop in a train's schedule.
    
    Attributes:
        station (Station): The station
        arrival_time (datetime): When the train arrives
        departure_time (datetime): When the train departs
        platform (str): Platform number/name
    """
    
    def __init__(self, station: Station, arrival_time: datetime, 
                 departure_time: datetime, platform: str = "1"):
        """
        Initialize a schedule entry.
        
        Args:
            station: The station
            arrival_time: When the train arrives
            departure_time: When the train departs
            platform: Platform number/name
        """
        self.station = station
        self.arrival_time = arrival_time
        self.departure_time = departure_time
        self.platform = platform
    
    def __repr__(self):
        return (f"ScheduleEntry(station='{self.station.name}', "
                f"arrival={self.arrival_time.strftime('%H:%M')}, "
                f"departure={self.departure_time.strftime('%H:%M')}, "
                f"platform={self.platform})")


class Train:
    """
    Represents a train with its schedule.
    
    Attributes:
        train_id (str): Unique identifier for the train
        train_name (str): Name of the train
        schedule (List[ScheduleEntry]): List of scheduled stops
    """
    
    def __init__(self, train_id: str, train_name: str):
        """
        Initialize a train.
        
        Args:
            train_id: Unique identifier for the train
            train_name: Name of the train
        """
        self.train_id = train_id
        self.train_name = train_name
        self.schedule: List[ScheduleEntry] = []
    
    def add_stop(self, entry: ScheduleEntry) -> None:
        """
        Add a stop to the train's schedule.
        
        Args:
            entry: The schedule entry to add
        """
        self.schedule.append(entry)
    
    def get_origin(self) -> Optional[Station]:
        """Get the origin station."""
        return self.schedule[0].station if self.schedule else None
    
    def get_destination(self) -> Optional[Station]:
        """Get the destination station."""
        return self.schedule[-1].station if self.schedule else None
    
    def get_departure_time(self) -> Optional[datetime]:
        """Get the departure time from origin."""
        return self.schedule[0].departure_time if self.schedule else None
    
    def get_arrival_time(self) -> Optional[datetime]:
        """Get the arrival time at destination."""
        return self.schedule[-1].arrival_time if self.schedule else None
    
    def __repr__(self):
        return f"Train(id='{self.train_id}', name='{self.train_name}', stops={len(self.schedule)})"


class Timetable:
    """
    Manages the timetable for all trains in the network.
    
    Attributes:
        trains (Dict[str, Train]): Dictionary of trains by train_id
        network (RailNetwork): The rail network
    """
    
    def __init__(self, network: RailNetwork):
        """
        Initialize a timetable.
        
        Args:
            network: The rail network this timetable is for
        """
        self.trains: Dict[str, Train] = {}
        self.network = network
    
    def add_train(self, train: Train) -> None:
        """
        Add a train to the timetable.
        
        Args:
            train: The train to add
        """
        self.trains[train.train_id] = train
    
    def get_train(self, train_id: str) -> Optional[Train]:
        """
        Get a train by ID.
        
        Args:
            train_id: The train ID
            
        Returns:
            The train if found, None otherwise
        """
        return self.trains.get(train_id)
    
    def get_trains_at_station(self, station_name: str, 
                             time: datetime) -> List[Train]:
        """
        Get all trains at a station at a specific time.
        
        Args:
            station_name: Name of the station
            time: The time to check
            
        Returns:
            List of trains at the station at that time
        """
        result = []
        for train in self.trains.values():
            for entry in train.schedule:
                if (entry.station.name == station_name and
                    entry.arrival_time <= time <= entry.departure_time):
                    result.append(train)
                    break
        return result
    
    def get_trains_between(self, origin: str, destination: str) -> List[Train]:
        """
        Get all trains that travel between two stations.
        
        Args:
            origin: Origin station name
            destination: Destination station name
            
        Returns:
            List of trains that serve both stations
        """
        result = []
        for train in self.trains.values():
            station_names = [entry.station.name for entry in train.schedule]
            if origin in station_names and destination in station_names:
                origin_idx = station_names.index(origin)
                dest_idx = station_names.index(destination)
                if origin_idx < dest_idx:
                    result.append(train)
        return result
    
    def __repr__(self):
        return f"Timetable(trains={len(self.trains)})"
