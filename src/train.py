"""
Train module for Railway Network System.
Represents trains with their physical characteristics and movement capabilities.
"""

from enum import Enum
from typing import Optional
from datetime import datetime, timedelta


class TrainType(Enum):
    """Types of trains with different characteristics."""
    HIGH_SPEED = "high_speed"      # Alta velocità (Frecciarossa, Italo)
    INTERCITY = "intercity"        # Intercity
    REGIONAL = "regional"          # Regionale
    FREIGHT = "freight"            # Merci
    LOCAL = "local"                # Locale/Suburbano


class Train:
    """
    Represents a train with its physical and operational characteristics.
    
    Attributes:
        id (str): Unique identifier for the train
        name (str): Train name/number
        train_type (TrainType): Type of train
        max_speed (int): Maximum speed in km/h
        acceleration (float): Acceleration in m/s²
        deceleration (float): Braking deceleration in m/s²
        length (float): Train length in meters
        capacity (int): Passenger/cargo capacity
    """
    
    # Default characteristics for each train type
    DEFAULT_CHARACTERISTICS = {
        TrainType.HIGH_SPEED: {
            'max_speed': 300,
            'acceleration': 0.5,
            'deceleration': 0.7,
            'length': 200,
            'capacity': 500
        },
        TrainType.INTERCITY: {
            'max_speed': 200,
            'acceleration': 0.4,
            'deceleration': 0.6,
            'length': 150,
            'capacity': 400
        },
        TrainType.REGIONAL: {
            'max_speed': 160,
            'acceleration': 0.6,
            'deceleration': 0.8,
            'length': 100,
            'capacity': 300
        },
        TrainType.FREIGHT: {
            'max_speed': 100,
            'acceleration': 0.15,
            'deceleration': 0.3,
            'length': 500,
            'capacity': 1000
        },
        TrainType.LOCAL: {
            'max_speed': 120,
            'acceleration': 0.7,
            'deceleration': 0.9,
            'length': 80,
            'capacity': 200
        }
    }
    
    def __init__(
        self,
        train_id: str,
        name: str,
        train_type: TrainType,
        max_speed: Optional[int] = None,
        acceleration: Optional[float] = None,
        deceleration: Optional[float] = None,
        length: Optional[float] = None,
        capacity: Optional[int] = None
    ):
        self.id = train_id
        self.name = name
        self.train_type = train_type
        
        # Use defaults if not specified
        defaults = self.DEFAULT_CHARACTERISTICS[train_type]
        self.max_speed = max_speed if max_speed is not None else defaults['max_speed']
        self.acceleration = acceleration if acceleration is not None else defaults['acceleration']
        self.deceleration = deceleration if deceleration is not None else defaults['deceleration']
        self.length = length if length is not None else defaults['length']
        self.capacity = capacity if capacity is not None else defaults['capacity']
        
        # Current state
        self.current_speed = 0.0
        self.current_position = None  # Current node or edge
        self.status = "idle"  # idle, running, stopped, delayed
    
    def update_characteristics_from_type(self, train_type: TrainType):
        """
        Update train characteristics based on a new train type.
        
        Args:
            train_type: The new train type to apply
        """
        self.train_type = train_type
        defaults = self.DEFAULT_CHARACTERISTICS[train_type]
        self.max_speed = defaults['max_speed']
        self.acceleration = defaults['acceleration']
        self.deceleration = defaults['deceleration']
        self.length = defaults['length']
        self.capacity = defaults['capacity']
    
    def calculate_acceleration_time(self, target_speed: float) -> float:
        """
        Calculate time needed to accelerate from current speed to target speed.
        
        Args:
            target_speed: Target speed in km/h
            
        Returns:
            float: Time in seconds
        """
        # Convert km/h to m/s
        v0 = self.current_speed * (1000 / 3600)
        v1 = min(target_speed, self.max_speed) * (1000 / 3600)
        
        if v1 <= v0:
            return 0.0
        
        # t = (v1 - v0) / a
        return (v1 - v0) / self.acceleration
    
    def calculate_braking_time(self, target_speed: float = 0.0) -> float:
        """
        Calculate time needed to brake from current speed to target speed.
        
        Args:
            target_speed: Target speed in km/h (default: 0 = full stop)
            
        Returns:
            float: Time in seconds
        """
        # Convert km/h to m/s
        v0 = self.current_speed * (1000 / 3600)
        v1 = target_speed * (1000 / 3600)
        
        if v0 <= v1:
            return 0.0
        
        # t = (v0 - v1) / d
        return (v0 - v1) / self.deceleration
    
    def calculate_braking_distance(self, target_speed: float = 0.0) -> float:
        """
        Calculate distance needed to brake from current speed to target speed.
        
        Args:
            target_speed: Target speed in km/h (default: 0 = full stop)
            
        Returns:
            float: Distance in meters
        """
        # Convert km/h to m/s
        v0 = self.current_speed * (1000 / 3600)
        v1 = target_speed * (1000 / 3600)
        
        if v0 <= v1:
            return 0.0
        
        # s = (v0² - v1²) / (2 * d)
        return (v0 * v0 - v1 * v1) / (2 * self.deceleration)
    
    def calculate_travel_time(
        self,
        distance: float,
        max_allowed_speed: float,
        stop_at_end: bool = True
    ) -> dict:
        """
        Calculate detailed travel time for a segment including acceleration and braking.
        
        Args:
            distance: Distance in kilometers
            max_allowed_speed: Maximum allowed speed on this segment (km/h)
            stop_at_end: Whether the train stops at the end of the segment
            
        Returns:
            dict: Dictionary with time breakdown (acceleration, cruise, braking, total)
        """
        distance_m = distance * 1000  # Convert to meters
        effective_max_speed = min(self.max_speed, max_allowed_speed)
        
        # Convert to m/s
        v_max_ms = effective_max_speed * (1000 / 3600)
        v_start_ms = self.current_speed * (1000 / 3600)
        v_end_ms = 0.0 if stop_at_end else v_start_ms
        
        # Distance to accelerate to max speed
        if v_start_ms < v_max_ms:
            t_accel = (v_max_ms - v_start_ms) / self.acceleration
            s_accel = v_start_ms * t_accel + 0.5 * self.acceleration * t_accel * t_accel
        else:
            t_accel = 0
            s_accel = 0
            v_max_ms = v_start_ms
        
        # Distance to brake to end speed
        if v_max_ms > v_end_ms:
            t_brake = (v_max_ms - v_end_ms) / self.deceleration
            s_brake = v_max_ms * t_brake - 0.5 * self.deceleration * t_brake * t_brake
        else:
            t_brake = 0
            s_brake = 0
        
        # Distance at cruise speed
        s_cruise = distance_m - s_accel - s_brake
        
        if s_cruise < 0:
            # Not enough distance to reach max speed
            # Calculate peak speed reached
            # s_total = (v_peak² - v_start²)/(2*a) + (v_peak² - v_end²)/(2*d)
            # Solving for v_peak:
            # v_peak² = (s_total + v_start²/(2*a) + v_end²/(2*d)) / (1/(2*a) + 1/(2*d))
            
            numerator = (distance_m + 
                        (v_start_ms * v_start_ms) / (2 * self.acceleration) + 
                        (v_end_ms * v_end_ms) / (2 * self.deceleration))
            denominator = (1.0 / (2 * self.acceleration) + 1.0 / (2 * self.deceleration))
            
            v_peak_squared = numerator / denominator
            
            # Check if solution is valid
            if v_peak_squared > 0:
                v_peak_ms = v_peak_squared ** 0.5
                # Limit to max speed
                v_peak_ms = min(v_peak_ms, v_max_ms)
            else:
                # Fallback: use simple average
                v_peak_ms = (v_start_ms + v_end_ms) / 2
            
            t_accel = (v_peak_ms - v_start_ms) / self.acceleration if v_peak_ms > v_start_ms else 0
            t_brake = (v_peak_ms - v_end_ms) / self.deceleration if v_peak_ms > v_end_ms else 0
            t_cruise = 0
            s_cruise = 0
        else:
            # Time at cruise speed
            t_cruise = s_cruise / v_max_ms if v_max_ms > 0 else 0
        
        total_time = t_accel + t_cruise + t_brake
        
        return {
            'acceleration_time': t_accel,
            'cruise_time': t_cruise,
            'braking_time': t_brake,
            'total_time': total_time,
            'total_time_minutes': total_time / 60,
            'effective_max_speed': effective_max_speed,
            'average_speed': (distance_m / total_time * 3.6) if total_time > 0 else 0  # km/h
        }
    
    def to_dict(self) -> dict:
        """Convert train to dictionary representation."""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.train_type.value,
            'max_speed': self.max_speed,
            'acceleration': self.acceleration,
            'deceleration': self.deceleration,
            'length': self.length,
            'capacity': self.capacity,
            'current_speed': self.current_speed,
            'current_position': self.current_position,
            'status': self.status
        }
    
    def __str__(self) -> str:
        return f"Train({self.id}: {self.name}, {self.train_type.value}, max_speed={self.max_speed}km/h)"
    
    def __repr__(self) -> str:
        return self.__str__()
