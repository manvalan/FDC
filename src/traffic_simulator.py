"""
Traffic Simulator module for Railway Network System.
Manages train movements, track occupancy, conflicts, and priorities.
"""

from typing import List, Dict, Optional, Set, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import heapq

from train import Train
from schedule import TrainSchedule, ScheduleStop


class TrackOccupancy:
    """
    Tracks which trains are occupying which tracks (edges) at what times.
    """
    
    def __init__(self):
        # Key: (from_node, to_node), Value: list of (train_id, start_time, end_time)
        self.occupancy: Dict[Tuple[str, str], List[Tuple[str, datetime, datetime]]] = defaultdict(list)
    
    def reserve_track(
        self,
        from_node: str,
        to_node: str,
        train_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> bool:
        """
        Try to reserve a track for a train.
        
        Returns:
            bool: True if reservation successful, False if conflict
        """
        track_key = (from_node, to_node)
        
        # Check for conflicts
        for occupied_train, occupied_start, occupied_end in self.occupancy[track_key]:
            # Check if time ranges overlap
            if not (end_time <= occupied_start or start_time >= occupied_end):
                return False  # Conflict detected
        
        # No conflict, reserve the track
        self.occupancy[track_key].append((train_id, start_time, end_time))
        return True
    
    def get_conflicts(
        self,
        from_node: str,
        to_node: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[str]:
        """
        Get list of trains that would conflict with the given time range.
        """
        track_key = (from_node, to_node)
        conflicts = []
        
        for occupied_train, occupied_start, occupied_end in self.occupancy[track_key]:
            if not (end_time <= occupied_start or start_time >= occupied_end):
                conflicts.append(occupied_train)
        
        return conflicts
    
    def clear_reservations(self):
        """Clear all track reservations."""
        self.occupancy.clear()


class NodeOccupancy:
    """
    Tracks which trains are at which stations at what times.
    """
    
    def __init__(self):
        # Key: node_id, Value: list of (train_id, arrival_time, departure_time)
        self.occupancy: Dict[str, List[Tuple[str, datetime, datetime]]] = defaultdict(list)
    
    def reserve_node(
        self,
        node_id: str,
        train_id: str,
        arrival_time: datetime,
        departure_time: datetime,
        capacity: int
    ) -> bool:
        """
        Try to reserve space at a node for a train.
        
        Returns:
            bool: True if reservation successful, False if at capacity
        """
        # Count how many trains are at the node at any point during this time
        max_concurrent = 0
        for _, arr, dep in self.occupancy[node_id]:
            # Check if time ranges overlap
            if not (departure_time <= arr or arrival_time >= dep):
                max_concurrent += 1
        
        if max_concurrent >= capacity:
            return False  # Node at capacity
        
        # Reserve the node
        self.occupancy[node_id].append((train_id, arrival_time, departure_time))
        return True
    
    def get_occupancy_count(self, node_id: str, time: datetime) -> int:
        """Get number of trains at a node at a specific time."""
        count = 0
        for _, arr, dep in self.occupancy[node_id]:
            if arr <= time < dep:
                count += 1
        return count
    
    def clear_reservations(self):
        """Clear all node reservations."""
        self.occupancy.clear()


class Conflict:
    """
    Represents a scheduling conflict.
    """
    
    def __init__(
        self,
        conflict_type: str,  # "track" or "node"
        location: str,  # track ID or node ID
        trains: List[str],  # Conflicting train IDs
        time_range: Tuple[datetime, datetime],
        description: str
    ):
        self.conflict_type = conflict_type
        self.location = location
        self.trains = trains
        self.time_range = time_range
        self.description = description
    
    def __str__(self) -> str:
        start_str = self.time_range[0].strftime("%H:%M")
        end_str = self.time_range[1].strftime("%H:%M")
        return (f"Conflict at {self.location} ({start_str}-{end_str}): "
                f"{', '.join(self.trains)} - {self.description}")


class TrafficSimulator:
    """
    Simulates train traffic on the network, detecting conflicts and managing priorities.
    """
    
    def __init__(self, network):
        self.network = network
        self.schedules: List[TrainSchedule] = []
        self.track_occupancy = TrackOccupancy()
        self.node_occupancy = NodeOccupancy()
        self.conflicts: List[Conflict] = []
    
    def add_schedule(self, schedule: TrainSchedule):
        """Add a train schedule to the simulator."""
        self.schedules.append(schedule)
    
    def clear_schedules(self):
        """Clear all schedules and reservations."""
        self.schedules.clear()
        self.track_occupancy.clear_reservations()
        self.node_occupancy.clear_reservations()
        self.conflicts.clear()
    
    def validate_schedule(self, schedule: TrainSchedule) -> Tuple[bool, List[Conflict]]:
        """
        Validate a single schedule for conflicts with existing schedules.
        
        Returns:
            Tuple of (is_valid, list of conflicts)
        """
        conflicts = []
        
        # Check each segment of the route
        for i in range(len(schedule.stops) - 1):
            current_stop = schedule.stops[i]
            next_stop = schedule.stops[i + 1]
            
            from_node = current_stop.node_id
            to_node = next_stop.node_id
            
            # Find the edge
            edge = None
            for e in self.network.edges:
                if e.from_node == from_node and e.to_node == to_node:
                    edge = e
                    break
                if e.bidirectional and e.to_node == from_node and e.from_node == to_node:
                    edge = e
                    from_node, to_node = to_node, from_node
                    break
            
            if not edge:
                continue
            
            # Check track occupancy
            start_time = current_stop.departure_time
            end_time = next_stop.arrival_time
            
            if start_time and end_time:
                conflicting_trains = self.track_occupancy.get_conflicts(
                    from_node, to_node, start_time, end_time
                )
                
                if conflicting_trains:
                    conflict = Conflict(
                        conflict_type="track",
                        location=f"{from_node}-{to_node}",
                        trains=[schedule.schedule_id] + conflicting_trains,
                        time_range=(start_time, end_time),
                        description=f"Track capacity exceeded (capacity={edge.capacity})"
                    )
                    conflicts.append(conflict)
        
        # Check node occupancy
        for stop in schedule.stops:
            if stop.arrival_time and stop.departure_time:
                node = self.network.get_node(stop.node_id)
                if node and not self.node_occupancy.reserve_node(
                    stop.node_id,
                    schedule.schedule_id,
                    stop.arrival_time,
                    stop.departure_time,
                    node.capacity
                ):
                    conflict = Conflict(
                        conflict_type="node",
                        location=stop.node_id,
                        trains=[schedule.schedule_id],
                        time_range=(stop.arrival_time, stop.departure_time),
                        description=f"Station capacity exceeded"
                    )
                    conflicts.append(conflict)
        
        return (len(conflicts) == 0, conflicts)
    
    def resolve_conflicts_by_priority(self) -> List[Tuple[TrainSchedule, int]]:
        """
        Resolve conflicts by delaying lower-priority trains.
        
        Returns:
            List of (schedule, delay_minutes) tuples for trains that need delays
        """
        # Sort schedules by priority (higher first)
        sorted_schedules = sorted(self.schedules, key=lambda s: s.priority, reverse=True)
        
        # Clear reservations
        self.track_occupancy.clear_reservations()
        self.node_occupancy.clear_reservations()
        self.conflicts.clear()
        
        delays = []
        
        for schedule in sorted_schedules:
            is_valid, conflicts = self.validate_schedule(schedule)
            
            if is_valid:
                # Reserve all tracks and nodes
                self._reserve_schedule_resources(schedule)
            else:
                # Need to delay this train
                delay_needed = self._calculate_minimum_delay(schedule, conflicts)
                if delay_needed > 0:
                    schedule.add_delay(delay_needed)
                    delays.append((schedule, delay_needed))
                    # Try again with delayed schedule
                    is_valid, _ = self.validate_schedule(schedule)
                    if is_valid:
                        self._reserve_schedule_resources(schedule)
                    else:
                        self.conflicts.extend(conflicts)
        
        return delays
    
    def _reserve_schedule_resources(self, schedule: TrainSchedule):
        """Reserve all tracks and nodes for a schedule."""
        # Reserve tracks
        for i in range(len(schedule.stops) - 1):
            current_stop = schedule.stops[i]
            next_stop = schedule.stops[i + 1]
            
            if current_stop.departure_time and next_stop.arrival_time:
                self.track_occupancy.reserve_track(
                    current_stop.node_id,
                    next_stop.node_id,
                    schedule.schedule_id,
                    current_stop.departure_time,
                    next_stop.arrival_time
                )
        
        # Reserve nodes
        for stop in schedule.stops:
            if stop.arrival_time and stop.departure_time:
                node = self.network.get_node(stop.node_id)
                if node:
                    self.node_occupancy.reserve_node(
                        stop.node_id,
                        schedule.schedule_id,
                        stop.arrival_time,
                        stop.departure_time,
                        node.capacity
                    )
    
    def _calculate_minimum_delay(
        self,
        schedule: TrainSchedule,
        conflicts: List[Conflict]
    ) -> int:
        """
        Calculate minimum delay needed to avoid conflicts.
        
        Returns:
            int: Delay in minutes
        """
        if not conflicts:
            return 0
        
        # Find the maximum end time of all conflicting reservations
        max_end_time = schedule.get_departure_time()
        
        for conflict in conflicts:
            if conflict.time_range[1] > max_end_time:
                max_end_time = conflict.time_range[1]
        
        # Add buffer time (5 minutes)
        buffer = timedelta(minutes=5)
        required_start = max_end_time + buffer
        
        current_start = schedule.get_departure_time()
        if current_start and required_start > current_start:
            delay = (required_start - current_start).total_seconds() / 60
            return int(delay) + 1
        
        return 0
    
    def simulate(self) -> Dict:
        """
        Run the simulation and return statistics.
        
        Returns:
            Dictionary with simulation results
        """
        delays = self.resolve_conflicts_by_priority()
        
        total_trains = len(self.schedules)
        delayed_trains = len(delays)
        total_delay_minutes = sum(delay for _, delay in delays)
        
        return {
            'total_trains': total_trains,
            'delayed_trains': delayed_trains,
            'on_time_trains': total_trains - delayed_trains,
            'total_delay_minutes': total_delay_minutes,
            'average_delay': total_delay_minutes / delayed_trains if delayed_trains > 0 else 0,
            'conflicts': len(self.conflicts),
            'delays': delays
        }
    
    def get_timetable(self, node_id: Optional[str] = None) -> List[Dict]:
        """
        Get timetable for all trains or trains stopping at a specific node.
        
        Args:
            node_id: Optional node ID to filter by
            
        Returns:
            List of timetable entries
        """
        timetable = []
        
        for schedule in sorted(self.schedules, key=lambda s: s.get_departure_time() or datetime.min):
            if node_id:
                stop = schedule.get_stop_at_node(node_id)
                if stop:
                    timetable.append({
                        'schedule_id': schedule.schedule_id,
                        'train_name': schedule.train.name,
                        'train_type': schedule.train.train_type.value,
                        'origin': schedule.origin,
                        'destination': schedule.destination,
                        'arrival': stop.arrival_time,
                        'departure': stop.departure_time,
                        'platform': stop.platform,
                        'delay': stop.delay_minutes
                    })
            else:
                timetable.append({
                    'schedule_id': schedule.schedule_id,
                    'train_name': schedule.train.name,
                    'train_type': schedule.train.train_type.value,
                    'origin': schedule.origin,
                    'destination': schedule.destination,
                    'departure_time': schedule.get_departure_time(),
                    'arrival_time': schedule.get_arrival_time(),
                    'total_delay': schedule.total_delay
                })
        
        return timetable
    
    def print_simulation_results(self, results: Dict):
        """Print formatted simulation results."""
        print(f"\n{'='*70}")
        print(f"TRAFFIC SIMULATION RESULTS")
        print(f"{'='*70}")
        print(f"Total trains scheduled: {results['total_trains']}")
        print(f"Trains on time: {results['on_time_trains']}")
        print(f"Trains delayed: {results['delayed_trains']}")
        print(f"Total delay: {results['total_delay_minutes']:.0f} minutes")
        if results['average_delay'] > 0:
            print(f"Average delay: {results['average_delay']:.1f} minutes")
        print(f"Unresolved conflicts: {results['conflicts']}")
        
        if results['delays']:
            print(f"\n{'─'*70}")
            print("DELAYED TRAINS:")
            for schedule, delay in results['delays']:
                print(f"  • {schedule.train.name} ({schedule.schedule_id}): "
                      f"+{delay} minutes delay")
        
        if self.conflicts:
            print(f"\n{'─'*70}")
            print("UNRESOLVED CONFLICTS:")
            for conflict in self.conflicts:
                print(f"  • {conflict}")
        
        print(f"{'='*70}\n")
