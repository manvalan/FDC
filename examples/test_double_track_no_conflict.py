#!/usr/bin/env python3
"""
Test Double Track - No Conflicts
Verify that trains on double-track sections do NOT show conflicts.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from railway_network import RailwayNetwork
from node import Node, NodeType
from edge import Edge, TrackType
from train import Train, TrainType
from schedule import ScheduleBuilder
from visualization import _detect_track_conflicts
from datetime import datetime
import matplotlib.dates as mdates


def main():
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║                                                                ║")
    print("║     🔍 TEST BINARIO DOPPIO - NESSUN CONFLITTO                 ║")
    print("║                                                                ║")
    print("╚════════════════════════════════════════════════════════════════╝\n")
    
    # Create network with DOUBLE track
    network = RailwayNetwork("Test Network")
    
    network.add_node(Node("A", "Station A", NodeType.STATION, platforms=2))
    network.add_node(Node("B", "Station B", NodeType.STATION, platforms=2))
    network.add_node(Node("C", "Station C", NodeType.STATION, platforms=2))
    
    # Add DOUBLE track connections
    print("🛤️  Creazione binari DOPPI:")
    network.add_edge(Edge("A", "B", 50.0, TrackType.DOUBLE, max_speed=160.0, capacity=2))
    print(f"   ✓ A → B: TrackType.DOUBLE (capacity=2)")
    
    network.add_edge(Edge("B", "C", 50.0, TrackType.DOUBLE, max_speed=160.0, capacity=2))
    print(f"   ✓ B → C: TrackType.DOUBLE (capacity=2)\n")
    
    # Verify track types
    print("🔍 Verifica configurazione binari:")
    for edge in network.edges:
        print(f"   {edge.from_node} → {edge.to_node}:")
        print(f"      track_type: {edge.track_type}")
        print(f"      track_type.value: '{edge.track_type.value}'")
        print(f"      capacity: {edge.capacity}")
        print(f"      Is single? {edge.track_type.value == 'single'}")
        print()
    
    # Create schedules
    schedules = []
    
    # Train 1: A → B → C, departs 08:00
    train1 = Train("T001", "Train 1", TrainType.REGIONAL, max_speed=140.0)
    schedule1 = ScheduleBuilder.create_schedule(
        schedule_id="SCH001",
        train=train1,
        route=["A", "B", "C"],
        network=network,
        start_time=datetime(2025, 11, 12, 8, 0),
        stop_duration_minutes=5
    )
    schedules.append(schedule1)
    print(f"✓ Train 1: A → B → C, partenza 08:00")
    
    # Train 2: A → B → C, departs 08:05 (overlaps with Train 1)
    train2 = Train("T002", "Train 2", TrainType.REGIONAL, max_speed=140.0)
    schedule2 = ScheduleBuilder.create_schedule(
        schedule_id="SCH002",
        train=train2,
        route=["A", "B", "C"],
        network=network,
        start_time=datetime(2025, 11, 12, 8, 5),
        stop_duration_minutes=5
    )
    schedules.append(schedule2)
    print(f"✓ Train 2: A → B → C, partenza 08:05 (sovrapposto)")
    
    # Train 3: C → B → A, departs 08:00 (opposite direction, overlaps)
    train3 = Train("T003", "Train 3", TrainType.REGIONAL, max_speed=140.0)
    schedule3 = ScheduleBuilder.create_schedule(
        schedule_id="SCH003",
        train=train3,
        route=["C", "B", "A"],
        network=network,
        start_time=datetime(2025, 11, 12, 8, 0),
        stop_duration_minutes=5
    )
    schedules.append(schedule3)
    print(f"✓ Train 3: C → B → A, partenza 08:00 (direzione opposta)\n")
    
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(" 📊 ORARI TRENI")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
    for schedule in schedules:
        print(f"{schedule.train.name}:")
        for stop in schedule.stops:
            arr = stop.arrival_time.strftime('%H:%M') if stop.arrival_time else '---'
            dep = stop.departure_time.strftime('%H:%M') if stop.departure_time else '---'
            print(f"  {stop.node_id}: arr={arr}, dep={dep}")
        print()
    
    # Build km_map for conflict detection
    route = ["A", "B", "C"]
    km_map = {"A": 0.0, "B": 50.0, "C": 100.0}
    
    # Check for conflicts
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(" 🔍 RILEVAMENTO CONFLITTI")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
    conflicts = _detect_track_conflicts(schedules, route, km_map, network)
    
    if conflicts:
        print(f"❌ ERRORE: {len(conflicts)} conflitti rilevati su binario DOPPIO!\n")
        for conflict in conflicts:
            print(f"   Conflitto: {conflict['trains']}")
            print(f"   Posizione: {conflict['km']} km")
            print(f"   Ora: {mdates.num2date(conflict['time']).strftime('%H:%M')}")
            print()
        print("\n⚠️  IL TEST È FALLITO!")
        print("   I binari doppi NON dovrebbero generare conflitti!\n")
        return False
    else:
        print("✅ NESSUN CONFLITTO RILEVATO!")
        print("   I treni su binario doppio possono sovrapporsi senza problemi\n")
        
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(" ✅ RIEPILOGO")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
        
        print(f"• Tipo binario: DOUBLE (2 binari paralleli)")
        print(f"• Treni testati: {len(schedules)}")
        print(f"  - Train 1: direzione A→C, ore 08:00")
        print(f"  - Train 2: direzione A→C, ore 08:05 (sovrapposto)")
        print(f"  - Train 3: direzione C→A, ore 08:00 (opposta)")
        print(f"• Sovrapposizioni temporali: SÌ")
        print(f"• Conflitti rilevati: NO ✅")
        print(f"• Risultato: CORRETTO - binario doppio permette sovrapposizioni\n")
        
        print("╔════════════════════════════════════════════════════════════════╗")
        print("║                                                                ║")
        print("║     ✅ TEST SUPERATO!                                         ║")
        print("║                                                                ║")
        print("║     I binari doppi NON generano falsi conflitti               ║")
        print("║                                                                ║")
        print("╚════════════════════════════════════════════════════════════════╝\n")
        return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
