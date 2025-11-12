#!/usr/bin/env python3
"""
Example: Visualize train conflicts on single-track sections.
Creates a clear scenario showing how trains must wait for each other.
"""
import sys
sys.path.insert(0, '../src')

from datetime import datetime, timedelta
from node import Node, NodeType
from edge import Edge, TrackType
from railway_network import RailwayNetwork
from train import Train, TrainType
from schedule import ScheduleBuilder, ScheduleBuilder
from visualization import plot_timetable


def main():
    print("=" * 80)
    print("TRAIN CONFLICT VISUALIZATION - Single Track Example")
    print("=" * 80)
    print()
    
    # Create simple linear network: A --- B === C --- D
    # Where B-C is single track (===)
    network = RailwayNetwork("Single Track Conflict Demo")
    
    nodes = [
        Node("A", "Station Alpha", NodeType.STATION, capacity=2, platforms=2),
        Node("B", "Station Beta", NodeType.STATION, capacity=3, platforms=2),
        Node("C", "Station Gamma", NodeType.STATION, capacity=3, platforms=2),
        Node("D", "Station Delta", NodeType.STATION, capacity=2, platforms=2),
    ]
    for n in nodes:
        network.add_node(n)
    
    edges = [
        Edge("A", "B", 50.0, TrackType.DOUBLE, max_speed=160, capacity=2),
        Edge("B", "C", 40.0, TrackType.SINGLE, max_speed=100, capacity=1),  # SINGLE TRACK!
        Edge("C", "D", 60.0, TrackType.DOUBLE, max_speed=160, capacity=2),
    ]
    for e in edges:
        network.add_edge(e)
    
    print("Network created:")
    print("  A ---(50km)--- B ===(40km SINGLE)=== C ---(60km)--- D")
    print()
    
    # Create trains going in opposite directions
    base_time = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
    
    train1 = Train("T1", "Express 101", TrainType.INTERCITY)
    train2 = Train("T2", "Regional 202", TrainType.REGIONAL)
    train3 = Train("T3", "Express 103", TrainType.INTERCITY)
    
    # Schedule 1: A -> D (10:00 departure)
    sched1 = ScheduleBuilder.create_schedule(
        "EX101", train1, ["A", "B", "C", "D"], 
        network, base_time, stop_duration_minutes=3
    )
    
    # Schedule 2: D -> A (10:05 departure) - OPPOSITE DIRECTION
    sched2 = ScheduleBuilder.create_schedule(
        "REG202", train2, ["D", "C", "B", "A"],
        network, base_time + timedelta(minutes=5), stop_duration_minutes=4
    )
    
    # Schedule 3: A -> D (10:20 departure)
    sched3 = ScheduleBuilder.create_schedule(
        "EX103", train3, ["A", "B", "C", "D"],
        network, base_time + timedelta(minutes=20), stop_duration_minutes=3
    )
    
    schedules = [sched1, sched2, sched3]
    
    print("📋 Train Schedules:")
    print()
    for s in schedules:
        dep = s.get_departure_time().strftime("%H:%M") if s.get_departure_time() else "?"
        arr = s.get_arrival_time().strftime("%H:%M") if s.get_arrival_time() else "?"
        print(f"  • {s.train.name}: {s.origin} → {s.destination} ({dep} - {arr})")
    print()
    
    # Analyze conflicts
    print("⚠️  CONFLICT ANALYSIS:")
    print("-" * 80)
    print("Single-track section B-C can only accommodate ONE train at a time.")
    print()
    
    # Check who uses B-C and when
    for s in schedules:
        for i in range(len(s.stops) - 1):
            if ((s.stops[i].node_id == "B" and s.stops[i+1].node_id == "C") or
                (s.stops[i].node_id == "C" and s.stops[i+1].node_id == "B")):
                dep = s.stops[i].departure_time.strftime("%H:%M") if s.stops[i].departure_time else "?"
                arr = s.stops[i+1].arrival_time.strftime("%H:%M") if s.stops[i+1].arrival_time else "?"
                direction = f"{s.stops[i].node_id}→{s.stops[i+1].node_id}"
                print(f"  {s.train.name}: uses {direction} from {dep} to {arr}")
    print()
    
    # Generate visualization
    print("🎨 Generating time-distance diagram...")
    print("   - Red shaded area shows single-track section")
    print("   - Red X marks show conflicts (trains overlapping on single track)")
    print("   - Train labels show which train is which")
    print()
    
    plot_timetable(
        route=["A", "B", "C", "D"],
        schedules=schedules,
        network=network,
        filename="conflict_visualization.png",
        figsize=(16, 8),
        show_conflicts=True
    )
    
    print("  ✓ Saved to: conflict_visualization.png")
    print()
    print("=" * 80)
    print("💡 In the diagram:")
    print("   - Horizontal axis: Time")
    print("   - Vertical axis: Distance (km) along the route")
    print("   - Each colored line: One train's journey")
    print("   - Red shaded area: Single-track bottleneck section (B-C)")
    print("   - Red X markers: Conflicts requiring resolution")
    print("=" * 80)


if __name__ == "__main__":
    main()
