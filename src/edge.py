"""
Edge module for Railway Network System.
Represents railway tracks connecting nodes.
"""

from enum import Enum
from typing import Optional


class TrackType(Enum):
    """Types of railway tracks."""
    SINGLE = "single"  # Single track (bidirectional)
    DOUBLE = "double"  # Double track (one per direction)
    HIGH_SPEED = "high_speed"
    FREIGHT = "freight"


class Edge:
    """
    Represents an edge in the railway network (railway track).
    
    Attributes:
        from_node (str): ID of the source node
        to_node (str): ID of the destination node
        distance (float): Distance in kilometers
        track_type (TrackType): Type of track
        max_speed (int): Maximum speed in km/h
        capacity (int): Maximum number of trains that can use this track simultaneously
        bidirectional (bool): Whether trains can travel in both directions
    """
    
    def __init__(
        self,
        from_node: str,
        to_node: str,
        distance: float,
        track_type: TrackType = TrackType.SINGLE,
        max_speed: int = 120,
        capacity: int = 1,
        bidirectional: bool = True
    ):
        self.from_node = from_node
        self.to_node = to_node
        self.distance = distance
        self.track_type = track_type
        self.max_speed = max_speed
        self.capacity = capacity
        self.bidirectional = bidirectional
        self._current_usage = 0
    
    @property
    def current_usage(self) -> int:
        """Current number of trains using this track."""
        return self._current_usage
    
    def is_available(self) -> bool:
        """Check if the track has available capacity."""
        return self._current_usage < self.capacity
    
    def occupy(self) -> bool:
        """
        Occupy a slot on this track.
        
        Returns:
            bool: True if successfully occupied, False if at capacity
        """
        if self.is_available():
            self._current_usage += 1
            return True
        return False
    
    def release(self) -> bool:
        """
        Release a slot on this track.
        
        Returns:
            bool: True if successfully released, False if already empty
        """
        if self._current_usage > 0:
            self._current_usage -= 1
            return True
        return False
    
    def travel_time(self, speed: Optional[int] = None) -> float:
        """
        Calculate travel time in hours.
        
        Args:
            speed: Speed in km/h. If None, uses max_speed
            
        Returns:
            float: Travel time in hours
        """
        effective_speed = min(speed or self.max_speed, self.max_speed)
        return self.distance / effective_speed
    
    def get_weight(self) -> float:
        """
        Get edge weight for pathfinding (using distance).
        
        Returns:
            float: Weight value (distance in km)
        """
        return self.distance
    
    def to_dict(self) -> dict:
        """Convert edge to dictionary representation."""
        return {
            'from_node': self.from_node,
            'to_node': self.to_node,
            'distance': self.distance,
            'track_type': self.track_type.value,
            'max_speed': self.max_speed,
            'capacity': self.capacity,
            'bidirectional': self.bidirectional,
            'current_usage': self._current_usage
        }
    
    def __str__(self) -> str:
        direction = "<->" if self.bidirectional else "->"
        return f"Edge({self.from_node} {direction} {self.to_node}, {self.distance}km)"
    
    def __repr__(self) -> str:
        return self.__str__()
