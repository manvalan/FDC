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
