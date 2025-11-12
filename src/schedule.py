"""
Schedule module for Railway Network System.
Manages train schedules, timetables, and route planning.
"""

from typing import List, Optional, Dict, Tuple
from datetime import datetime, timedelta
from train import Train, TrainType


class ScheduleStop:
    """
    Represents a scheduled stop at a station.
    
    Attributes:
        node_id: Station/node identifier
        arrival_time: Scheduled arrival time (None for first stop)
        departure_time: Scheduled departure time (None for last stop)
        platform: Platform number (optional)
        stop_duration: Duration of stop in minutes
    """
    
    def __init__(
        self,
        node_id: str,
        arrival_time: Optional[datetime] = None,
        departure_time: Optional[datetime] = None,
        platform: Optional[int] = None,
        stop_duration: int = 2
    ):
        self.node_id = node_id
        self.arrival_time = arrival_time
        self.departure_time = departure_time
        self.platform = platform
        self.stop_duration = stop_duration
        
        # Actual times (for simulation/delay tracking)
        self.actual_arrival = None
        self.actual_departure = None
        self.delay_minutes = 0
    
    def to_dict(self) -> dict:
        """Convert stop to dictionary."""
        return {
            'node_id': self.node_id,
            'arrival_time': self.arrival_time.isoformat() if self.arrival_time else None,
            'departure_time': self.departure_time.isoformat() if self.departure_time else None,
            'platform': self.platform,
            'stop_duration': self.stop_duration,
            'actual_arrival': self.actual_arrival.isoformat() if self.actual_arrival else None,
            'actual_departure': self.actual_departure.isoformat() if self.actual_departure else None,
            'delay_minutes': self.delay_minutes
        }
    
    def __str__(self) -> str:
        arr = self.arrival_time.strftime("%H:%M") if self.arrival_time else "---"
        dep = self.departure_time.strftime("%H:%M") if self.departure_time else "---"
        return f"{self.node_id}: arr={arr}, dep={dep}"


class TrainSchedule:
    """
    Represents a complete train schedule/service.
    
    Attributes:
        schedule_id: Unique identifier for this schedule
        train: Train object
        stops: List of scheduled stops
        route: List of node IDs forming the route
        service_date: Date when this service runs
        priority: Priority level (higher = more priority in conflicts)
    """
    
    def __init__(
        self,
        schedule_id: str,
        train: Train,
        stops: List[ScheduleStop],
        service_date: datetime,
        priority: int = 5
    ):
        self.schedule_id = schedule_id
        self.train = train
        self.stops = stops
        self.service_date = service_date
        self.priority = priority
        
        # Derived from stops
        self.route = [stop.node_id for stop in stops]
        self.origin = stops[0].node_id if stops else None
        self.destination = stops[-1].node_id if stops else None
        
        # Status tracking
        self.status = "scheduled"  # scheduled, running, completed, cancelled
        self.current_stop_index = 0
        self.total_delay = 0
    
    @property
    def departure_time(self) -> Optional[datetime]:
        """Get the initial departure time (property for compatibility)."""
        return self.stops[0].departure_time if self.stops else None
    
    @departure_time.setter
    def departure_time(self, value: datetime):
        """Set the initial departure time."""
        if self.stops:
            self.stops[0].departure_time = value
    
    def get_departure_time(self) -> Optional[datetime]:
        """Get the initial departure time."""
        return self.stops[0].departure_time if self.stops else None
    
    def get_arrival_time(self) -> Optional[datetime]:
        """Get the final arrival time."""
        return self.stops[-1].arrival_time if self.stops else None
    
    def get_total_duration(self) -> Optional[timedelta]:
        """Get total scheduled duration."""
        if not self.stops or len(self.stops) < 2:
            return None
        dep = self.get_departure_time()
        arr = self.get_arrival_time()
        if dep and arr:
            return arr - dep
        return None
    
    def get_stop_at_node(self, node_id: str) -> Optional[ScheduleStop]:
        """Get the scheduled stop at a specific node."""
        for stop in self.stops:
            if stop.node_id == node_id:
                return stop
        return None
    
    def get_current_stop(self) -> Optional[ScheduleStop]:
        """Get the current stop based on status."""
        if 0 <= self.current_stop_index < len(self.stops):
            return self.stops[self.current_stop_index]
        return None
    
    def advance_to_next_stop(self):
        """Advance to the next stop."""
        if self.current_stop_index < len(self.stops) - 1:
            self.current_stop_index += 1
        else:
            self.status = "completed"
    
    def add_delay(self, minutes: int):
        """Add delay to the schedule."""
        self.total_delay += minutes
        # Propagate delay to all remaining stops
        for i in range(self.current_stop_index, len(self.stops)):
            stop = self.stops[i]
            if stop.arrival_time:
                stop.arrival_time += timedelta(minutes=minutes)
            if stop.departure_time:
                stop.departure_time += timedelta(minutes=minutes)
            stop.delay_minutes += minutes
    
    def to_dict(self) -> dict:
        """Convert schedule to dictionary."""
        return {
            'schedule_id': self.schedule_id,
            'train': self.train.to_dict(),
            'stops': [stop.to_dict() for stop in self.stops],
            'route': self.route,
            'origin': self.origin,
            'destination': self.destination,
            'service_date': self.service_date.isoformat() if hasattr(self.service_date, 'isoformat') else str(self.service_date),
            'priority': self.priority,
            'status': self.status,
            'total_delay': self.total_delay
        }
    
    @staticmethod
    def from_dict(data: dict):
        """Create TrainSchedule from dictionary."""
        from train import Train, TrainType
        from datetime import datetime
        
        # Reconstruct train
        train_data = data['train']
        train = Train(
            train_id=train_data['id'],
            name=train_data['name'],
            train_type=TrainType(train_data['type']),
            max_speed=train_data.get('max_speed'),
            acceleration=train_data.get('acceleration'),
            deceleration=train_data.get('deceleration'),
            length=train_data.get('length'),
            capacity=train_data.get('capacity')
        )
        
        # Reconstruct stops
        stops = []
        for stop_data in data['stops']:
            stop = ScheduleStop(
                node_id=stop_data['node_id'],
                arrival_time=datetime.fromisoformat(stop_data['arrival_time']) if stop_data['arrival_time'] else None,
                departure_time=datetime.fromisoformat(stop_data['departure_time']) if stop_data['departure_time'] else None,
                platform=stop_data.get('platform'),
                stop_duration=stop_data.get('stop_duration', 2)
            )
            stop.delay_minutes = stop_data.get('delay_minutes', 0)
            stops.append(stop)
        
        # Create schedule
        service_date = datetime.fromisoformat(data['service_date']) if isinstance(data['service_date'], str) else data['service_date']
        schedule = TrainSchedule(
            schedule_id=data['schedule_id'],
            train=train,
            stops=stops,
            service_date=service_date,
            priority=data.get('priority', 5)
        )
        schedule.status = data.get('status', 'scheduled')
        schedule.total_delay = data.get('total_delay', 0)
        
        return schedule
    
    def export_to_json(self, filepath: str):
        """Export this schedule to a JSON file."""
        import json
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def import_from_json(filepath: str):
        """Import a schedule from a JSON file."""
        import json
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return TrainSchedule.from_dict(data)
    
    def __str__(self) -> str:
        dep = self.get_departure_time().strftime("%H:%M") if self.get_departure_time() else "?"
        arr = self.get_arrival_time().strftime("%H:%M") if self.get_arrival_time() else "?"
        return (f"Schedule({self.schedule_id}: {self.train.name} "
                f"{self.origin}→{self.destination}, {dep}-{arr})")
    
    def __repr__(self) -> str:
        return self.__str__()


class ScheduleBuilder:
    """
    Helper class to build train schedules with automatic time calculation.
    """
    
    @staticmethod
    def create_schedule(
        schedule_id: str,
        train: Train,
        route: List[str],
        network,  # RailwayNetwork instance
        start_time: datetime,
        stop_duration_minutes: int = 2,
        platform_assignments: Optional[Dict[str, int]] = None,
        target_arrival_time: Optional[datetime] = None
    ) -> Optional[TrainSchedule]:
        """
        Create a train schedule with automatic time calculation.
        
        Args:
            schedule_id: Schedule identifier
            train: Train object
            route: List of node IDs to visit
            network: RailwayNetwork instance
            start_time: Departure time from first station
            stop_duration_minutes: Duration of stops in minutes
            platform_assignments: Optional dict mapping node_id to platform number
            target_arrival_time: Optional target arrival time at final station (will adjust dwell times)
            
        Returns:
            TrainSchedule or None if route is invalid
        """
        if len(route) < 2:
            return None
        
        stops = []
        current_time = start_time
        
        for i, node_id in enumerate(route):
            if i == 0:
                # First stop - departure only
                stop = ScheduleStop(
                    node_id=node_id,
                    arrival_time=None,
                    departure_time=current_time,
                    platform=platform_assignments.get(node_id) if platform_assignments else None,
                    stop_duration=0
                )
                stops.append(stop)
                train.current_speed = 0  # Start from stop
            else:
                # Get edge between previous and current node
                prev_node = route[i-1]
                
                # Find the edge
                edge = None
                for e in network.edges:
                    if e.from_node == prev_node and e.to_node == node_id:
                        edge = e
                        break
                
                if not edge:
                    # Try reverse direction if bidirectional
                    for e in network.edges:
                        if e.to_node == prev_node and e.from_node == node_id and e.bidirectional:
                            edge = e
                            break
                
                if not edge:
                    return None  # Invalid route
                
                # Calculate travel time
                is_last_stop = (i == len(route) - 1)
                travel_info = train.calculate_travel_time(
                    distance=edge.distance,
                    max_allowed_speed=edge.max_speed,
                    stop_at_end=True  # Always stop at stations
                )
                
                # Add travel time
                travel_minutes = travel_info['total_time_minutes']
                current_time += timedelta(minutes=travel_minutes)
                arrival_time = current_time
                
                # Add stop duration (except for last stop)
                if not is_last_stop:
                    current_time += timedelta(minutes=stop_duration_minutes)
                    departure_time = current_time
                else:
                    departure_time = None
                
                stop = ScheduleStop(
                    node_id=node_id,
                    arrival_time=arrival_time,
                    departure_time=departure_time,
                    platform=platform_assignments.get(node_id) if platform_assignments else None,
                    stop_duration=stop_duration_minutes
                )
                stops.append(stop)
                
                # Reset speed for next segment
                train.current_speed = 0
        
        # If target arrival time is specified, adjust dwell times proportionally
        if target_arrival_time and len(stops) > 1:
            # Calculate current total time
            calculated_arrival = stops[-1].arrival_time
            time_diff = (target_arrival_time - calculated_arrival).total_seconds() / 60  # minutes
            
            # Only adjust if we need to slow down (add time)
            if time_diff > 0:
                # Number of intermediate stops (excluding first and last)
                intermediate_stops = len(stops) - 2
                if intermediate_stops > 0:
                    # Distribute extra time equally among intermediate stops
                    extra_dwell_per_stop = time_diff / intermediate_stops
                    
                    # Update stops with new dwell times
                    cumulative_added = 0
                    for i in range(1, len(stops) - 1):  # Skip first and last
                        additional_dwell = extra_dwell_per_stop
                        cumulative_added += additional_dwell
                        
                        # Update this stop's departure time
                        if stops[i].departure_time:
                            stops[i].departure_time += timedelta(minutes=cumulative_added)
                        
                        # Update all subsequent stops' times
                        for j in range(i + 1, len(stops)):
                            if stops[j].arrival_time:
                                stops[j].arrival_time += timedelta(minutes=cumulative_added)
                            if stops[j].departure_time:
                                stops[j].departure_time += timedelta(minutes=cumulative_added)
        
        return TrainSchedule(
            schedule_id=schedule_id,
            train=train,
            stops=stops,
            service_date=start_time.date(),
            priority=5
        )
    
    @staticmethod
    def print_schedule(schedule: TrainSchedule, network=None):
        """Print a formatted schedule."""
        print(f"\n{'='*70}")
        print(f"SCHEDULE: {schedule.schedule_id}")
        print(f"Train: {schedule.train.name} ({schedule.train.train_type.value})")
        print(f"Route: {schedule.origin} → {schedule.destination}")
        
        if schedule.get_total_duration():
            duration = schedule.get_total_duration()
            hours = duration.seconds // 3600
            minutes = (duration.seconds % 3600) // 60
            print(f"Duration: {hours}h {minutes}m")
        
        print(f"{'='*70}")
        print(f"{'Station':<20} {'Arrival':<10} {'Departure':<10} {'Platform':<8} {'Delay':<8}")
        print(f"{'-'*70}")
        
        for stop in schedule.stops:
            node_name = stop.node_id
            if network:
                node = network.get_node(stop.node_id)
                if node:
                    node_name = node.name
            
            arr = stop.arrival_time.strftime("%H:%M") if stop.arrival_time else "---"
            dep = stop.departure_time.strftime("%H:%M") if stop.departure_time else "---"
            plat = str(stop.platform) if stop.platform else "-"
            delay = f"+{stop.delay_minutes}m" if stop.delay_minutes > 0 else "-"
            
            print(f"{node_name:<20} {arr:<10} {dep:<10} {plat:<8} {delay:<8}")
        
        print(f"{'='*70}\n")
