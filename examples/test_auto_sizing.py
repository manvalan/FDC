#!/usr/bin/env python3
"""
Test automatic window sizing for visualizations.
Demonstrates how network and timetable plots adapt to data size.
"""
import sys
sys.path.insert(0, '../src')

from datetime import datetime, timedelta
from railway_network import RailwayNetwork
from node import Node, NodeType
from edge import Edge, TrackType
from train import Train, TrainType
from schedule import ScheduleBuilder
from visualization import plot_timetable


def test_small_network():
    """Test visualization with a small network (3 stations)."""
    print("=" * 60)
    print("TEST 1: Small Network (3 stations)")
    print("=" * 60)
    
    network = RailwayNetwork("Small Test Network")
    
    # Add 3 stations in a line
    network.add_node(Node("A", "Station A", NodeType.STATION, 45.0, 7.0))
    network.add_node(Node("B", "Station B", NodeType.STATION, 45.0, 7.5))
    network.add_node(Node("C", "Station C", NodeType.STATION, 45.0, 8.0))
    
    network.add_edge(Edge("A", "B", 50, TrackType.DOUBLE, 160))
    network.add_edge(Edge("B", "C", 50, TrackType.DOUBLE, 160))
    
    print("Visualizing small network (should use compact size)...")
    network.visualize(save_path="small_network.png")
    print("✓ Saved to small_network.png\n")


def test_medium_network():
    """Test visualization with the Ferrovie della Contea network."""
    print("=" * 60)
    print("TEST 2: Medium Network (Ferrovie della Contea - 54 stations)")
    print("=" * 60)
    
    # Load the imported network
    network = RailwayNetwork("Ferrovie della Contea")
    network.import_from_json("ferrovie_contea_fdc.json")
    
    print(f"Loaded network: {network.name}")
    print(f"Stations: {len(network.nodes)}")
    print("Visualizing medium network (should adapt to coordinate range)...")
    network.visualize(save_path="medium_network.png")
    print("✓ Saved to medium_network.png\n")


def test_timetable_short_route():
    """Test timetable with a short route (few stations, few hours)."""
    print("=" * 60)
    print("TEST 3: Short Timetable (4 stations, 2 trains, 2 hours)")
    print("=" * 60)
    
    network = RailwayNetwork("Short Route")
    
    # 4 stations
    network.add_node(Node("S1", "Station 1", NodeType.STATION, 45.0, 7.0))
    network.add_node(Node("S2", "Station 2", NodeType.STATION, 45.1, 7.1))
    network.add_node(Node("S3", "Station 3", NodeType.STATION, 45.2, 7.2))
    network.add_node(Node("S4", "Station 4", NodeType.STATION, 45.3, 7.3))
    
    network.add_edge(Edge("S1", "S2", 30, TrackType.DOUBLE, 120))
    network.add_edge(Edge("S2", "S3", 30, TrackType.DOUBLE, 120))
    network.add_edge(Edge("S3", "S4", 30, TrackType.DOUBLE, 120))
    
    # Create 2 trains
    train1 = Train("T1", "Train 1", TrainType.REGIONAL)
    train2 = Train("T2", "Train 2", TrainType.REGIONAL)
    
    # Build schedules
    start_time = datetime(2024, 1, 1, 8, 0)
    
    sched1 = ScheduleBuilder.create_schedule("SCH1", train1, ["S1", "S2", "S3", "S4"], 
                                             network, start_time, stop_duration_minutes=2)
    sched2 = ScheduleBuilder.create_schedule("SCH2", train2, ["S1", "S2", "S3", "S4"], 
                                             network, start_time + timedelta(hours=1), 
                                             stop_duration_minutes=2)
    
    print("Visualizing short timetable (should use compact size)...")
    plot_timetable(
        route=["S1", "S2", "S3", "S4"],
        schedules=[sched1, sched2],
        network=network,
        filename="short_timetable.png"
    )
    print("✓ Saved to short_timetable.png\n")


def test_timetable_long_route():
    """Test timetable with a long route from Ferrovie della Contea."""
    print("=" * 60)
    print("TEST 4: Long Timetable (Linea Blu - 14 stations, 4 trains)")
    print("=" * 60)
    
    # Load network
    network = RailwayNetwork("Ferrovie della Contea")
    network.import_from_json("ferrovie_contea_fdc.json")
    
    # Define Linea Blu route (coast to coast)
    linea_blu = [
        "Flostirion", "White Towers", "Undertower", "Westmarch",
        "Westmarch Greenholm", "Foxdown", "Michel Delving", "White Downs",
        "Waymeet", "Bywater", "Frogmorton", "Withfurrows", "Bridge",
        "Newbury", "Brandy Hall"
    ]
    
    # Create 4 trains (2 each direction)
    trains = [
        Train("BLU1", "Blu Express 1", TrainType.INTERCITY),
        Train("BLU2", "Blu Local 1", TrainType.REGIONAL),
        Train("BLU3", "Blu Express 2", TrainType.INTERCITY),
        Train("BLU4", "Blu Local 2", TrainType.REGIONAL)
    ]
    
    start_time = datetime(2024, 1, 1, 6, 0)
    
    schedules = []
    for i, train in enumerate(trains):
        departure = start_time + timedelta(hours=i * 2)
        sched = ScheduleBuilder.create_schedule(
            f"BLU{i+1}_SCH", train, linea_blu, network, departure, 
            stop_duration_minutes=3
        )
        if sched:
            schedules.append(sched)
    
    print("Visualizing long timetable (should adapt to route length and time span)...")
    plot_timetable(
        route=linea_blu,
        schedules=schedules,
        network=network,
        filename="long_timetable.png",
        show_conflicts=True
    )
    print("✓ Saved to long_timetable.png\n")


def main():
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "AUTO-SIZING VISUALIZATION TEST" + " " * 18 + "║")
    print("╚" + "=" * 58 + "╝")
    print("\n")
    
    # Test 1: Small network
    test_small_network()
    
    # Test 2: Medium network (Ferrovie della Contea)
    test_medium_network()
    
    # Test 3: Short timetable
    test_timetable_short_route()
    
    # Test 4: Long timetable
    test_timetable_long_route()
    
    print("=" * 60)
    print("✓ All tests completed!")
    print("=" * 60)
    print("\nGenerated files:")
    print("  - small_network.png (compact layout)")
    print("  - medium_network.png (adapted to coordinate range)")
    print("  - short_timetable.png (compact time-distance diagram)")
    print("  - long_timetable.png (expanded time-distance diagram)")
    print()


if __name__ == "__main__":
    main()
