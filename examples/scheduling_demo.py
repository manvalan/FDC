#!/usr/bin/env python3
"""
Example: Train Scheduling and Traffic Management
Demonstrates automatic schedule generation, conflict detection, and resolution.
"""

import sys
sys.path.insert(0, '../src')

from datetime import datetime, timedelta
from node import Node, NodeType
from edge import Edge, TrackType
from railway_network import RailwayNetwork
from train import Train, TrainType
from schedule import ScheduleBuilder
from traffic_simulator import TrafficSimulator


def create_network():
    """Create a sample network for scheduling demonstration."""
    network = RailwayNetwork("Scheduling Demo Network")
    
    # Create nodes
    nodes = [
        Node("A", "Città A", NodeType.STATION, capacity=3, platforms=3),
        Node("B", "Città B", NodeType.INTERCHANGE, capacity=5, platforms=4),
        Node("C", "Città C", NodeType.STATION, capacity=3, platforms=3),
        Node("D", "Città D", NodeType.STATION, capacity=2, platforms=2),
    ]
    
    for node in nodes:
        network.add_node(node)
    
    # Create edges - note: single track between B and C (capacity=1)
    edges = [
        Edge("A", "B", 80.0, TrackType.DOUBLE, max_speed=200, capacity=2),
        Edge("B", "C", 60.0, TrackType.SINGLE, max_speed=120, capacity=1),  # Single track!
        Edge("C", "D", 50.0, TrackType.DOUBLE, max_speed=180, capacity=2),
    ]
    
    for edge in edges:
        network.add_edge(edge)
    
    return network


def main():
    print("=" * 80)
    print("TRAIN SCHEDULING AND TRAFFIC MANAGEMENT DEMO")
    print("=" * 80)
    print()
    
    # Create network
    network = create_network()
    print(f"✓ Network created: {network}")
    print()
    
    # Create trains with different characteristics
    print("🚂 Creating trains...")
    trains = [
        Train("T1", "Frecciarossa 9600", TrainType.HIGH_SPEED),
        Train("T2", "Intercity 505", TrainType.INTERCITY),
        Train("T3", "Regionale 2341", TrainType.REGIONAL),
        Train("T4", "Frecciarossa 9602", TrainType.HIGH_SPEED),
        Train("T5", "Regionale 2342", TrainType.REGIONAL),
    ]
    
    for train in trains:
        print(f"  • {train.name}: max_speed={train.max_speed}km/h, "
              f"accel={train.acceleration}m/s², brake={train.deceleration}m/s²")
    print()
    
    # Create schedules
    print("📅 Creating schedules...")
    simulator = TrafficSimulator(network)
    
    # Base time for schedules
    base_time = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
    
    # Schedule 1: High-speed train A -> D (priority 10)
    schedule1 = ScheduleBuilder.create_schedule(
        schedule_id="HS9600",
        train=trains[0],
        route=["A", "B", "C", "D"],
        network=network,
        start_time=base_time,
        stop_duration_minutes=2
    )
    schedule1.priority = 10  # High priority
    simulator.add_schedule(schedule1)
    
    # Schedule 2: Intercity train A -> D (priority 7) - 5 minutes after schedule 1
    schedule2 = ScheduleBuilder.create_schedule(
        schedule_id="IC505",
        train=trains[1],
        route=["A", "B", "C", "D"],
        network=network,
        start_time=base_time + timedelta(minutes=5),
        stop_duration_minutes=3
    )
    schedule2.priority = 7
    simulator.add_schedule(schedule2)
    
    # Schedule 3: Regional train D -> A (priority 5) - opposite direction
    schedule3 = ScheduleBuilder.create_schedule(
        schedule_id="REG2341",
        train=trains[2],
        route=["D", "C", "B", "A"],
        network=network,
        start_time=base_time + timedelta(minutes=10),
        stop_duration_minutes=5
    )
    schedule3.priority = 5
    simulator.add_schedule(schedule3)
    
    # Schedule 4: High-speed train A -> D (priority 10) - conflict with schedule 3
    schedule4 = ScheduleBuilder.create_schedule(
        schedule_id="HS9602",
        train=trains[3],
        route=["A", "B", "C", "D"],
        network=network,
        start_time=base_time + timedelta(minutes=15),
        stop_duration_minutes=2
    )
    schedule4.priority = 10
    simulator.add_schedule(schedule4)
    
    # Schedule 5: Regional train A -> C (priority 4)
    schedule5 = ScheduleBuilder.create_schedule(
        schedule_id="REG2342",
        train=trains[4],
        route=["A", "B", "C"],
        network=network,
        start_time=base_time + timedelta(minutes=20),
        stop_duration_minutes=4
    )
    schedule5.priority = 4
    simulator.add_schedule(schedule5)
    
    print(f"✓ Created {len(simulator.schedules)} schedules")
    print()
    
    # Print initial schedules
    print("📋 INITIAL SCHEDULES (before conflict resolution):")
    print()
    for schedule in simulator.schedules:
        ScheduleBuilder.print_schedule(schedule, network)
    
    # Run simulation
    print("\n🔄 Running traffic simulation...")
    print("   (Detecting conflicts on single-track section B-C)")
    print()
    
    results = simulator.simulate()
    
    # Print results
    simulator.print_simulation_results(results)
    
    # Print adjusted schedules if there were delays
    if results['delayed_trains'] > 0:
        print("📋 ADJUSTED SCHEDULES (after conflict resolution):")
        print()
        for schedule, delay in results['delays']:
            print(f"⏰ {schedule.train.name} delayed by {delay} minutes:")
            ScheduleBuilder.print_schedule(schedule, network)
    
    # Print timetable for station B
    print("\n📊 TIMETABLE FOR CITTÀ B (Interchange):")
    print(f"{'='*80}")
    print(f"{'Train':<20} {'From':<15} {'To':<15} {'Arrival':<10} {'Departure':<10} {'Delay'}")
    print(f"{'-'*80}")
    
    timetable = simulator.get_timetable(node_id="B")
    for entry in sorted(timetable, key=lambda x: x['arrival'] or x['departure'] or datetime.min):
        arr = entry['arrival'].strftime("%H:%M") if entry['arrival'] else "---"
        dep = entry['departure'].strftime("%H:%M") if entry['departure'] else "---"
        delay = f"+{entry['delay']}m" if entry['delay'] > 0 else ""
        
        print(f"{entry['train_name']:<20} {entry['origin']:<15} {entry['destination']:<15} "
              f"{arr:<10} {dep:<10} {delay}")
    
    print(f"{'='*80}")
    print()
    
    # Analyze travel times
    print("⏱️  TRAVEL TIME ANALYSIS:")
    print(f"{'='*80}")
    
    for schedule in simulator.schedules:
        if schedule.get_total_duration():
            duration = schedule.get_total_duration()
            hours = duration.seconds // 3600
            minutes = (duration.seconds % 3600) // 60
            
            # Calculate distance
            total_distance = 0
            for i in range(len(schedule.route) - 1):
                for edge in network.edges:
                    if edge.from_node == schedule.route[i] and edge.to_node == schedule.route[i+1]:
                        total_distance += edge.distance
                        break
            
            avg_speed = total_distance / (duration.seconds / 3600) if duration.seconds > 0 else 0
            
            print(f"{schedule.train.name} ({schedule.origin}→{schedule.destination}):")
            print(f"  • Distance: {total_distance:.1f} km")
            print(f"  • Scheduled time: {hours}h {minutes}m")
            print(f"  • Average speed: {avg_speed:.1f} km/h")
            print(f"  • Delay: +{schedule.total_delay}m" if schedule.total_delay > 0 else "  • On time")
            print()
    
    print(f"{'='*80}")
    print()
    
    # Key insights
    print("💡 KEY INSIGHTS:")
    print("─" * 80)
    print("1. Single-track section B-C creates bottleneck")
    print("2. High-priority trains (Frecciarossa) get preference")
    print("3. Lower-priority trains automatically delayed to avoid conflicts")
    print("4. System maintains safety by preventing simultaneous occupancy")
    print("5. Different train types have different acceleration/braking characteristics")
    print("─" * 80)
    print()
    
    # Generate a time-distance plot for the route A->D
    try:
        from visualization import plot_timetable
        print("\n🎨 Generating time-distance diagram (timetable) for route A→D...")
        plot_timetable(route=["A", "B", "C", "D"],
                       schedules=simulator.schedules,
                       network=network,
                       filename="timetable_AD.png",
                       figsize=(14, 6))
        print("  ✓ Saved to: timetable_AD.png")
    except Exception as e:
        print(f"  ⚠ Could not generate timetable plot: {e}")

    print("=" * 80)
    print("Demo completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    main()
