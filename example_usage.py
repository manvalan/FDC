"""
Example usage of the Train Timetable Management System

This demonstrates how to create a rail network, add trains with schedules,
and query the timetable.
"""

from rail_network import Station, TrackSegment, RailNetwork, Train, ScheduleEntry, Timetable
from datetime import datetime, timedelta


def create_sample_network():
    """Create a sample rail network with several stations and track segments."""
    
    # Initialize the network
    network = RailNetwork()
    
    # Create stations
    central = Station("Central Station", "interchange")
    north = Station("North Terminal", "station")
    south = Station("South Terminal", "station")
    east = Station("East Junction", "interchange")
    west = Station("West End", "station")
    airport = Station("Airport", "station")
    
    # Add track segments (connections between stations)
    # Central Station is the main hub
    network.add_track_segment(TrackSegment(central, north, 15.5, 20, bidirectional=True))
    network.add_track_segment(TrackSegment(central, south, 12.0, 18, bidirectional=True))
    network.add_track_segment(TrackSegment(central, east, 10.0, 15, bidirectional=True))
    network.add_track_segment(TrackSegment(central, west, 8.5, 12, bidirectional=True))
    
    # East Junction connects to Airport
    network.add_track_segment(TrackSegment(east, airport, 20.0, 25, bidirectional=True))
    
    # Additional connections
    network.add_track_segment(TrackSegment(north, east, 18.0, 22, bidirectional=True))
    network.add_track_segment(TrackSegment(south, west, 14.0, 17, bidirectional=True))
    
    return network


def create_sample_timetable(network):
    """Create a sample timetable with several trains."""
    
    timetable = Timetable(network)
    
    # Get stations
    central = network.get_station("Central Station")
    north = network.get_station("North Terminal")
    south = network.get_station("South Terminal")
    east = network.get_station("East Junction")
    west = network.get_station("West End")
    airport = network.get_station("Airport")
    
    # Create Train 1: Express from North to Airport
    train1 = Train("T001", "Northern Express")
    base_time = datetime(2024, 1, 15, 8, 0)  # 8:00 AM
    
    train1.add_stop(ScheduleEntry(north, base_time, base_time + timedelta(minutes=5), "1"))
    train1.add_stop(ScheduleEntry(east, base_time + timedelta(minutes=27), 
                                   base_time + timedelta(minutes=30), "2"))
    train1.add_stop(ScheduleEntry(airport, base_time + timedelta(minutes=55), 
                                   base_time + timedelta(minutes=55), "3"))
    timetable.add_train(train1)
    
    # Create Train 2: Central to South route
    train2 = Train("T002", "Southern Link")
    base_time2 = datetime(2024, 1, 15, 9, 0)  # 9:00 AM
    
    train2.add_stop(ScheduleEntry(central, base_time2, base_time2 + timedelta(minutes=5), "4"))
    train2.add_stop(ScheduleEntry(south, base_time2 + timedelta(minutes=23), 
                                   base_time2 + timedelta(minutes=28), "2"))
    train2.add_stop(ScheduleEntry(west, base_time2 + timedelta(minutes=45), 
                                   base_time2 + timedelta(minutes=45), "1"))
    timetable.add_train(train2)
    
    # Create Train 3: Airport to Central route
    train3 = Train("T003", "Airport Shuttle")
    base_time3 = datetime(2024, 1, 15, 10, 0)  # 10:00 AM
    
    train3.add_stop(ScheduleEntry(airport, base_time3, base_time3 + timedelta(minutes=5), "1"))
    train3.add_stop(ScheduleEntry(east, base_time3 + timedelta(minutes=30), 
                                   base_time3 + timedelta(minutes=33), "3"))
    train3.add_stop(ScheduleEntry(central, base_time3 + timedelta(minutes=48), 
                                   base_time3 + timedelta(minutes=48), "5"))
    timetable.add_train(train3)
    
    # Create Train 4: Circular route
    train4 = Train("T004", "Circle Line")
    base_time4 = datetime(2024, 1, 15, 11, 0)  # 11:00 AM
    
    train4.add_stop(ScheduleEntry(central, base_time4, base_time4 + timedelta(minutes=5), "1"))
    train4.add_stop(ScheduleEntry(north, base_time4 + timedelta(minutes=25), 
                                   base_time4 + timedelta(minutes=28), "2"))
    train4.add_stop(ScheduleEntry(east, base_time4 + timedelta(minutes=50), 
                                   base_time4 + timedelta(minutes=53), "1"))
    train4.add_stop(ScheduleEntry(central, base_time4 + timedelta(minutes=68), 
                                   base_time4 + timedelta(minutes=68), "3"))
    timetable.add_train(train4)
    
    return timetable


def demonstrate_network():
    """Demonstrate the rail network features."""
    
    print("=" * 70)
    print("TRAIN TIMETABLE MANAGEMENT SYSTEM - DEMONSTRATION")
    print("=" * 70)
    print()
    
    # Create the network
    network = create_sample_network()
    print(f"Created {network}")
    print(f"Stations: {', '.join(network.stations.keys())}")
    print()
    
    # Display track segments
    print("Track Segments:")
    for track in network.tracks:
        print(f"  {track}")
    print()
    
    # Demonstrate pathfinding
    print("=" * 70)
    print("PATHFINDING EXAMPLES")
    print("=" * 70)
    print()
    
    # Find shortest path by time
    result = network.find_shortest_path("North Terminal", "Airport", by_time=True)
    if result:
        path, cost = result
        print(f"Shortest path (by time) from North Terminal to Airport:")
        print(f"  Route: {' -> '.join([s.name for s in path])}")
        print(f"  Total time: {cost} minutes")
    print()
    
    # Find shortest path by distance
    result = network.find_shortest_path("North Terminal", "Airport", by_time=False)
    if result:
        path, cost = result
        print(f"Shortest path (by distance) from North Terminal to Airport:")
        print(f"  Route: {' -> '.join([s.name for s in path])}")
        print(f"  Total distance: {cost} km")
    print()
    
    # Find path from West End to Airport
    result = network.find_shortest_path("West End", "Airport", by_time=True)
    if result:
        path, cost = result
        print(f"Shortest path from West End to Airport:")
        print(f"  Route: {' -> '.join([s.name for s in path])}")
        print(f"  Total time: {cost} minutes")
    print()
    
    # Create timetable
    print("=" * 70)
    print("TIMETABLE MANAGEMENT")
    print("=" * 70)
    print()
    
    timetable = create_sample_timetable(network)
    print(f"Created {timetable}")
    print()
    
    # Display all trains
    print("All Trains:")
    for train in timetable.trains.values():
        print(f"\n  {train}")
        print(f"    Origin: {train.get_origin().name} at {train.get_departure_time().strftime('%H:%M')}")
        print(f"    Destination: {train.get_destination().name} at {train.get_arrival_time().strftime('%H:%M')}")
        print(f"    Complete Schedule:")
        for entry in train.schedule:
            print(f"      {entry}")
    print()
    
    # Query trains at a station
    print("=" * 70)
    print("STATION QUERIES")
    print("=" * 70)
    print()
    
    query_time = datetime(2024, 1, 15, 9, 0)
    trains_at_central = timetable.get_trains_at_station("Central Station", query_time)
    print(f"Trains at Central Station at {query_time.strftime('%H:%M')}:")
    for train in trains_at_central:
        print(f"  {train.train_name} ({train.train_id})")
    print()
    
    # Query trains between stations
    trains_to_airport = timetable.get_trains_between("East Junction", "Airport")
    print(f"Trains from East Junction to Airport:")
    for train in trains_to_airport:
        print(f"  {train.train_name} ({train.train_id})")
    print()
    
    print("=" * 70)
    print("DEMONSTRATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    demonstrate_network()
