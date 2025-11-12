#!/usr/bin/env python3
"""
Simple JSON Export/Import Demo
Demonstrates saving and loading networks and schedules using JSON.
No database required.
"""
import sys
sys.path.insert(0, '../src')

from datetime import datetime, timedelta
from node import Node, NodeType
from edge import Edge, TrackType
from railway_network import RailwayNetwork
from train import Train, TrainType
from schedule import ScheduleBuilder, TrainSchedule


def main():
    print("=" * 80)
    print("JSON EXPORT/IMPORT DEMONSTRATION")
    print("=" * 80)
    print()
    
    # ========================================================================
    # PART 1: CREATE SAMPLE NETWORK
    # ========================================================================
    print("📊 PART 1: Creating Sample Network")
    print("-" * 80)
    
    network = RailwayNetwork("Demo Railway Network")
    
    # Add nodes (stations)
    print("➕ Adding stations...")
    stations = [
        Node("ROMA", "Roma Termini", NodeType.STATION, 41.9009, 12.5023, 
             capacity=12, platforms=10),
        Node("FLOR", "Firenze SMN", NodeType.INTERCHANGE, 43.7762, 11.2475,
             capacity=8, platforms=6),
        Node("BOLO", "Bologna Centrale", NodeType.INTERCHANGE, 44.5061, 11.3427,
             capacity=10, platforms=8),
        Node("MILA", "Milano Centrale", NodeType.STATION, 45.4864, 9.2040,
             capacity=10, platforms=8),
    ]
    
    for station in stations:
        network.add_node(station)
        print(f"  ✓ {station.name}")
    
    print()
    
    # Add edges (tracks)
    print("➕ Adding track connections...")
    tracks = [
        Edge("ROMA", "FLOR", 264.0, TrackType.HIGH_SPEED, 300, 2),
        Edge("FLOR", "BOLO", 81.0, TrackType.HIGH_SPEED, 300, 2),
        Edge("BOLO", "MILA", 218.0, TrackType.HIGH_SPEED, 300, 2),
    ]
    
    for track in tracks:
        network.add_edge(track)
        print(f"  ✓ {track.from_node} → {track.to_node} ({track.distance} km, {track.max_speed} km/h)")
    
    print()
    print(f"📈 Network Statistics:")
    stats = network.get_network_stats()
    print(f"  • Nodes: {stats['num_nodes']}")
    print(f"  • Edges: {stats['num_edges']}")
    print(f"  • Total track length: {stats['total_track_length']} km")
    print(f"  • Connected: {stats['is_connected']}")
    print()
    
    # ========================================================================
    # PART 2: CREATE TRAIN SCHEDULES
    # ========================================================================
    print("📊 PART 2: Creating Train Schedules")
    print("-" * 80)
    
    print("🚄 Creating trains...")
    trains = [
        Train("FR1000", "Frecciarossa 1000", TrainType.HIGH_SPEED),
        Train("IC505", "Intercity 505", TrainType.INTERCITY),
        Train("REG2301", "Regionale 2301", TrainType.REGIONAL),
    ]
    
    for train in trains:
        print(f"  ✓ {train.name} ({train.train_type.name})")
    
    print()
    
    print("📅 Building schedules...")
    base_time = datetime.now().replace(hour=6, minute=0, second=0, microsecond=0)
    
    schedules = []
    
    # Schedule 1: High-speed north-bound
    sched1 = ScheduleBuilder.create_schedule(
        "SCH001", trains[0], ["ROMA", "FLOR", "BOLO", "MILA"],
        network, base_time, stop_duration_minutes=5
    )
    schedules.append(sched1)
    print(f"  ✓ {sched1.schedule_id}: {sched1.train.name} {sched1.origin}→{sched1.destination}")
    
    # Schedule 2: Intercity south-bound
    sched2 = ScheduleBuilder.create_schedule(
        "SCH002", trains[1], ["MILA", "BOLO", "FLOR", "ROMA"],
        network, base_time + timedelta(hours=1), stop_duration_minutes=8
    )
    schedules.append(sched2)
    print(f"  ✓ {sched2.schedule_id}: {sched2.train.name} {sched2.origin}→{sched2.destination}")
    
    # Schedule 3: Regional north-bound
    sched3 = ScheduleBuilder.create_schedule(
        "SCH003", trains[2], ["ROMA", "FLOR", "BOLO"],
        network, base_time + timedelta(hours=2), stop_duration_minutes=10
    )
    schedules.append(sched3)
    print(f"  ✓ {sched3.schedule_id}: {sched3.train.name} {sched3.origin}→{sched3.destination}")
    
    print()
    
    # ========================================================================
    # PART 3: EXPORT TO JSON
    # ========================================================================
    print("📊 PART 3: Exporting to JSON")
    print("-" * 80)
    
    # Export network
    network_file = "demo_network.json"
    print(f"💾 Exporting network to {network_file}...")
    network.export_to_json(network_file, include_stats=True)
    print(f"  ✓ Network exported successfully")
    print()
    
    # Export schedules
    print("💾 Exporting schedules...")
    schedule_files = []
    for schedule in schedules:
        filename = f"demo_{schedule.schedule_id}.json"
        schedule.export_to_json(filename)
        schedule_files.append(filename)
        print(f"  ✓ {schedule.schedule_id} → {filename}")
    
    print()
    
    # ========================================================================
    # PART 4: IMPORT FROM JSON
    # ========================================================================
    print("📊 PART 4: Importing from JSON")
    print("-" * 80)
    
    # Import network
    print(f"📥 Importing network from {network_file}...")
    imported_network = RailwayNetwork("Imported Network")
    imported_network.import_from_json(network_file)
    print(f"  ✓ Network imported: {imported_network.name}")
    print(f"  • Nodes: {len(imported_network.nodes)}")
    print(f"  • Edges: {len(imported_network.edges)}")
    
    # Verify nodes
    print("\n  📍 Imported stations:")
    for node_id, node in imported_network.nodes.items():
        print(f"    - {node.name} ({node.node_type.name})")
    
    print()
    
    # Import schedules
    print("📥 Importing schedules...")
    imported_schedules = []
    for filename in schedule_files:
        schedule = TrainSchedule.import_from_json(filename)
        imported_schedules.append(schedule)
        print(f"  ✓ {schedule.schedule_id}: {schedule.train.name}")
        print(f"    Route: {schedule.origin} → {schedule.destination}")
        dep_time = schedule.get_departure_time()
        arr_time = schedule.get_arrival_time()
        if dep_time:
            print(f"    Departure: {dep_time.strftime('%H:%M')}")
        if arr_time:
            print(f"    Arrival: {arr_time.strftime('%H:%M')}")
        print(f"    Stops: {len(schedule.stops)}")
        print()
    
    # ========================================================================
    # PART 5: DETAILED SCHEDULE VIEW
    # ========================================================================
    print("📊 PART 5: Detailed Schedule View")
    print("-" * 80)
    
    for schedule in imported_schedules[:1]:  # Show first schedule in detail
        print(f"\n📋 {schedule.schedule_id}: {schedule.train.name}")
        print(f"   {schedule.origin} → {schedule.destination}")
        print(f"   Train Type: {schedule.train.train_type.name}")
        print(f"   Priority: {schedule.priority}")
        print()
        print("   Timetable:")
        print("   " + "-" * 60)
        print(f"   {'Station':<25} {'Arrival':<10} {'Departure':<10} {'Dwell':<6}")
        print("   " + "-" * 60)
        
        for stop in schedule.stops:
            station_name = imported_network.nodes[stop.node_id].name if stop.node_id in imported_network.nodes else stop.node_id
            arrival = stop.arrival_time.strftime('%H:%M') if stop.arrival_time else "---"
            departure = stop.departure_time.strftime('%H:%M') if stop.departure_time else "---"
            dwell = f"{stop.stop_duration}min" if stop.stop_duration else "---"
            
            print(f"   {station_name:<25} {arrival:<10} {departure:<10} {dwell:<6}")
        
        print("   " + "-" * 60)
    
    print()
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("=" * 80)
    print("✅ JSON DEMO COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    print()
    print("📁 Generated files:")
    print(f"   • {network_file}")
    for filename in schedule_files:
        print(f"   • {filename}")
    print()
    print("💡 These files can be:")
    print("   - Shared with other users")
    print("   - Version controlled with Git")
    print("   - Imported into other railway management systems")
    print("   - Used as backup of your network configuration")
    print()


if __name__ == "__main__":
    main()
