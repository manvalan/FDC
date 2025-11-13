"""
Node module for Railway Network System.
Represents stations and interchange points in the railway network.
"""

from enum import Enum
from typing import Optional


class NodeType(Enum):
    """Types of nodes in the railway network."""
    STATION = "station"
    INTERCHANGE = "interchange"
    DEPOT = "depot"


class Node:
    """
    Represents a node in the railway network (station or interchange).
    
    Attributes:
        id (str): Unique identifier for the node
        name (str): Human-readable name
        node_type (NodeType): Type of node (station, interchange, depot)
        latitude (float): Latitude coordinate
        longitude (float): Longitude coordinate
        capacity (int): Maximum number of trains that can be at this node
        platforms (int): Number of platforms available
    """
    
    def __init__(
        self,
        node_id: str,
        name: str,
        node_type: NodeType = NodeType.STATION,
        latitude: float = 0.0,
        longitude: float = 0.0,
        capacity: int = 2,
        platforms: int = 2
    ):
        self.id = node_id
        self.name = name
        self.node_type = node_type
        self.latitude = latitude
        self.longitude = longitude
        self.capacity = capacity
        self.platforms = platforms
        self._current_occupancy = 0
        # Track platform occupancy: {platform_num: [(train_id, start_time, end_time), ...]}
        self._platform_schedule = {i: [] for i in range(1, platforms + 1)}
    
    @property
    def current_occupancy(self) -> int:
        """Current number of trains at this node."""
        return self._current_occupancy
    
    def is_available(self) -> bool:
        """Check if the node has available capacity."""
        return self._current_occupancy < self.capacity
    
    def occupy(self) -> bool:
        """
        Occupy a slot at this node.
        
        Returns:
            bool: True if successfully occupied, False if at capacity
        """
        if self.is_available():
            self._current_occupancy += 1
            return True
        return False
    
    def release(self) -> bool:
        """
        Release a slot at this node.
        
        Returns:
            bool: True if successfully released, False if already empty
        """
        if self._current_occupancy > 0:
            self._current_occupancy -= 1
            return True
        return False
    
    def is_platform_available(self, platform: int, start_time, end_time) -> bool:
        """
        Check if a specific platform is available for a given time window.
        
        Args:
            platform: Platform number (1-indexed)
            start_time: Arrival time (datetime)
            end_time: Departure time (datetime)
            
        Returns:
            bool: True if platform is available for the entire time window
        """
        if platform < 1 or platform > self.platforms:
            return False
        
        if platform not in self._platform_schedule:
            return True
        
        # Check for time conflicts with existing reservations
        for train_id, reserved_start, reserved_end in self._platform_schedule[platform]:
            # Check if time windows overlap
            if not (end_time <= reserved_start or start_time >= reserved_end):
                return False  # Conflict detected
        
        return True
    
    def get_available_platform(self, start_time, end_time) -> Optional[int]:
        """
        Find the first available platform for the given time window.
        
        Args:
            start_time: Arrival time (datetime)
            end_time: Departure time (datetime)
            
        Returns:
            Platform number if available, None if all platforms are occupied
        """
        for platform in range(1, self.platforms + 1):
            if self.is_platform_available(platform, start_time, end_time):
                return platform
        return None
    
    def reserve_platform(self, platform: int, train_id: str, start_time, end_time) -> bool:
        """
        Reserve a platform for a train during a specific time window.
        
        Args:
            platform: Platform number (1-indexed)
            train_id: Unique train identifier
            start_time: Arrival time (datetime)
            end_time: Departure time (datetime)
            
        Returns:
            bool: True if reservation successful, False if conflict
        """
        if not self.is_platform_available(platform, start_time, end_time):
            return False
        
        if platform not in self._platform_schedule:
            self._platform_schedule[platform] = []
        
        self._platform_schedule[platform].append((train_id, start_time, end_time))
        return True
    
    def release_platform(self, platform: int, train_id: str):
        """
        Release a platform reservation for a train.
        
        Args:
            platform: Platform number
            train_id: Train identifier
        """
        if platform in self._platform_schedule:
            self._platform_schedule[platform] = [
                (tid, start, end) for tid, start, end in self._platform_schedule[platform]
                if tid != train_id
            ]
    
    def clear_platform_schedule(self):
        """Clear all platform reservations."""
        self._platform_schedule = {i: [] for i in range(1, self.platforms + 1)}
    
    def to_dict(self) -> dict:
        """Convert node to dictionary representation."""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.node_type.value,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'capacity': self.capacity,
            'platforms': self.platforms,
            'current_occupancy': self._current_occupancy
        }
    
    def __str__(self) -> str:
        return f"Node({self.id}: {self.name}, {self.node_type.value})"
    
    def __repr__(self) -> str:
        return self.__str__()
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Node):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id)
