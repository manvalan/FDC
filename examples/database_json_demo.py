#!/usr/bin/env python3
"""
Example: Database and JSON integration
Demonstrates saving/loading networks and schedules to MySQL and JSON files.
"""
import sys
sys.path.insert(0, '../src')

from datetime import datetime, timedelta
from node import Node, NodeType
from edge import Edge, TrackType
from railway_network import RailwayNetwork
from train import Train, TrainType
from schedule import ScheduleBuilder, TrainSchedule
from database import DatabaseManager


def create_sample_data():
    """Create sample network and schedules."""
    # Create network
    network = RailwayNetwork("Test Railway Network")
    
    nodes = [
        Node("STN1", "Central Station", NodeType.STATION, 45.0, 9.0, capacity=10, platforms=8),
        Node("STN2", "North Junction", NodeType.INTERCHANGE, 45.5, 9.2, capacity=6, platforms=4),
        Node("STN3", "South Terminal", NodeType.STATION, 44.8, 8.9, capacity=8, platforms=6),
    ]
    for node in nodes:
        network.add_node(node)
    
    edges = [
        Edge("STN1", "STN2", 50.0, TrackType.DOUBLE, max_speed=200, capacity=2),
        Edge("STN2", "STN3", 60.0, TrackType.SINGLE, max_speed=120, capacity=1),
    ]
    for edge in edges:
        network.add_edge(edge)
    
    # Create trains and schedules
    train1 = Train("TR001", "Express 100", TrainType.HIGH_SPEED)
    train2 = Train("TR002", "Local 200", TrainType.REGIONAL)
    
    base_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
    
    schedule1 = ScheduleBuilder.create_schedule(
        "SCH001", train1, ["STN1", "STN2", "STN3"],
        network, base_time, stop_duration_minutes=3
    )
    
    schedule2 = ScheduleBuilder.create_schedule(
        "SCH002", train2, ["STN3", "STN2", "STN1"],
        network, base_time + timedelta(minutes=10), stop_duration_minutes=5
    )
    
    return network, [schedule1, schedule2]


def demo_json_export_import():
    """Demonstrate JSON export/import."""
    print("=" * 80)
    print("JSON EXPORT/IMPORT DEMO")
    print("=" * 80)
    print()
    
    network, schedules = create_sample_data()
    
    # Export network to JSON
    print("📤 Exporting network to JSON...")
    network.export_to_json("network_export.json", include_stats=True)
    print("  ✓ Saved to: network_export.json")
    print()
    
    # Export schedules to JSON
    print("📤 Exporting schedules to JSON...")
    for schedule in schedules:
        filename = f"schedule_{schedule.schedule_id}.json"
        schedule.export_to_json(filename)
        print(f"  ✓ Saved to: {filename}")
    print()
    
    # Import network from JSON
    print("📥 Importing network from JSON...")
    imported_network = RailwayNetwork()
    imported_network.import_from_json("network_export.json")
    print(f"  ✓ Loaded: {imported_network}")
    print(f"  • Nodes: {len(imported_network.nodes)}")
    print(f"  • Edges: {len(imported_network.edges)}")
    print()
    
    # Import schedule from JSON
    print("📥 Importing schedule from JSON...")
    imported_schedule = TrainSchedule.import_from_json("schedule_SCH001.json")
    print(f"  ✓ Loaded: {imported_schedule}")
    print(f"  • Stops: {len(imported_schedule.stops)}")
    print()


def demo_database_operations():
    """Demonstrate MySQL database operations."""
    print("=" * 80)
    print("DATABASE OPERATIONS DEMO")
    print("=" * 80)
    print()
    
    # Note: Requires MySQL server running
    print("⚠️  This demo requires a MySQL server running on localhost.")
    print("   Default connection: root@localhost (no password)")
    print("   Database: railway_network (will be created if not exists)")
    print()
    
    response = input("Continue with database demo? (y/n): ")
    if response.lower() != 'y':
        print("Skipping database demo.")
        return
    
    print()
    
    # Connect to database
    print("🔌 Connecting to database...")
    db = DatabaseManager(host="localhost", user="root", password="", database="railway_network")
    
    if not db.connect():
        print("  ✗ Failed to connect to database.")
        print("  Make sure MySQL is running and credentials are correct.")
        return
    
    print("  ✓ Connected successfully!")
    print()
    
    try:
        network, schedules = create_sample_data()
        
        # Save network
        print("💾 Saving network to database...")
        network_id = db.save_network(network)
        if network_id:
            print(f"  ✓ Network saved with ID: {network_id}")
        else:
            print("  ✗ Failed to save network")
            return
        print()
        
        # Save trains and schedules
        print("💾 Saving schedules to database...")
        for schedule in schedules:
            if db.save_schedule(schedule, network_id):
                print(f"  ✓ Schedule {schedule.schedule_id} saved")
            else:
                print(f"  ✗ Failed to save schedule {schedule.schedule_id}")
        print()
        
        # List networks
        print("📋 Listing all networks in database...")
        networks = db.list_networks()
        for net in networks:
            print(f"  • ID: {net['id']}, Name: {net['name']}, Created: {net['created_at']}")
        print()
        
        # Load network
        print(f"📥 Loading network ID {network_id} from database...")
        loaded_network = db.load_network(network_id)
        if loaded_network:
            print(f"  ✓ Loaded: {loaded_network}")
            print(f"  • Nodes: {len(loaded_network.nodes)}")
            print(f"  • Edges: {len(loaded_network.edges)}")
        else:
            print("  ✗ Failed to load network")
        print()
        
        # List schedules
        print(f"📋 Listing schedules for network {network_id}...")
        schedules_list = db.list_schedules(network_id=network_id)
        for sched in schedules_list:
            print(f"  • {sched['id']}: {sched['train_name']} "
                  f"(Priority: {sched['priority']}, Status: {sched['status']})")
        print()
        
        # Load schedule
        print("📥 Loading schedule SCH001 from database...")
        loaded_schedule = db.load_schedule("SCH001")
        if loaded_schedule:
            print(f"  ✓ Loaded: {loaded_schedule}")
            print(f"  • Train: {loaded_schedule.train.name}")
            print(f"  • Stops: {len(loaded_schedule.stops)}")
            for stop in loaded_schedule.stops:
                arr = stop.arrival_time.strftime("%H:%M") if stop.arrival_time else "---"
                dep = stop.departure_time.strftime("%H:%M") if stop.departure_time else "---"
                print(f"    - {stop.node_id}: {arr} → {dep} (Duration: {stop.stop_duration}min)")
        else:
            print("  ✗ Failed to load schedule")
        print()
        
        print("=" * 80)
        print("✅ Database demo completed successfully!")
        print("=" * 80)
        
    finally:
        db.disconnect()
        print("\n🔌 Database connection closed.")


def main():
    print("=" * 80)
    print("RAILWAY NETWORK - DATABASE & JSON INTEGRATION")
    print("=" * 80)
    print()
    
    # JSON demo
    demo_json_export_import()
    print()
    
    # Database demo
    demo_database_operations()


if __name__ == "__main__":
    main()
