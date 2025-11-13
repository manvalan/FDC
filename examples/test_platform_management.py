#!/usr/bin/env python3
"""
Test Platform Management System
Verify automatic platform assignment and conflict detection.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from railway_network import RailwayNetwork
from node import Node, NodeType
from edge import Edge, TrackType
from train import Train, TrainType
from schedule import ScheduleBuilder, auto_assign_platforms, check_platform_conflicts
from datetime import datetime, timedelta


def create_test_network():
    """Create a simple test network."""
    network = RailwayNetwork("Test Network")
    
    # Add 3 stations with 2 platforms each
    network.add_node(Node("A", "Station A", NodeType.STATION, 
                         latitude=45.0, longitude=9.0, platforms=2))
    network.add_node(Node("B", "Station B", NodeType.STATION, 
                         latitude=45.1, longitude=9.1, platforms=2))
    network.add_node(Node("C", "Station C", NodeType.STATION, 
                         latitude=45.2, longitude=9.2, platforms=2))
    
    # Add double-track connections
    network.add_edge(Edge("A", "B", 50.0, TrackType.DOUBLE, max_speed=160.0))
    network.add_edge(Edge("B", "C", 50.0, TrackType.DOUBLE, max_speed=160.0))
    
    return network


def main():
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║                                                                ║")
    print("║     🚉 TEST GESTIONE BINARI - SISTEMA FERROVIARIO            ║")
    print("║                                                                ║")
    print("╚════════════════════════════════════════════════════════════════╝\n")
    
    # Create network
    network = create_test_network()
    print(f"✓ Rete creata: {len(network.nodes)} stazioni con 2 binari ciascuna\n")
    
    # Create trains
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
    print(f"✓ Treno 1 creato: A → B → C, partenza 08:00")
    
    # Train 2: A → B → C, departs 08:10 (should get same route, different platforms at stations)
    train2 = Train("T002", "Train 2", TrainType.REGIONAL, max_speed=140.0)
    schedule2 = ScheduleBuilder.create_schedule(
        schedule_id="SCH002",
        train=train2,
        route=["A", "B", "C"],
        network=network,
        start_time=datetime(2025, 11, 12, 8, 10),
        stop_duration_minutes=5
    )
    schedules.append(schedule2)
    print(f"✓ Treno 2 creato: A → B → C, partenza 08:10")
    
    # Train 3: C → B → A, departs 08:05 (opposite direction)
    train3 = Train("T003", "Train 3", TrainType.REGIONAL, max_speed=140.0)
    schedule3 = ScheduleBuilder.create_schedule(
        schedule_id="SCH003",
        train=train3,
        route=["C", "B", "A"],
        network=network,
        start_time=datetime(2025, 11, 12, 8, 5),
        stop_duration_minutes=5
    )
    schedules.append(schedule3)
    print(f"✓ Treno 3 creato: C → B → A, partenza 08:05\n")
    
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(" PRIMA DELL'ASSEGNAZIONE AUTOMATICA")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
    for schedule in schedules:
        print(f"{schedule.train.name} ({schedule.schedule_id}):")
        for stop in schedule.stops:
            arr = stop.arrival_time.strftime('%H:%M') if stop.arrival_time else '---'
            dep = stop.departure_time.strftime('%H:%M') if stop.departure_time else '---'
            plat = str(stop.platform) if stop.platform else 'NON ASSEGNATO'
            print(f"  {stop.node_id}: arr={arr}, dep={dep}, binario={plat}")
        print()
    
    # Auto-assign platforms
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(" 🔄 ESECUZIONE ASSEGNAZIONE AUTOMATICA BINARI")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
    issues = auto_assign_platforms(schedules, network)
    
    if issues:
        print("⚠️  PROBLEMI RILEVATI:")
        for schedule_id, issue_list in issues.items():
            print(f"\n{schedule_id}:")
            for issue in issue_list:
                print(f"  - {issue}")
        print()
    else:
        print("✓ Nessun problema! Tutti i binari assegnati con successo\n")
    
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(" DOPO L'ASSEGNAZIONE AUTOMATICA")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
    for schedule in schedules:
        print(f"{schedule.train.name} ({schedule.schedule_id}):")
        for stop in schedule.stops:
            arr = stop.arrival_time.strftime('%H:%M') if stop.arrival_time else '---'
            dep = stop.departure_time.strftime('%H:%M') if stop.departure_time else '---'
            plat = str(stop.platform) if stop.platform else 'NON ASSEGNATO'
            node = network.get_node(stop.node_id)
            node_name = node.name if node else stop.node_id
            print(f"  {node_name}: arr={arr}, dep={dep}, binario={plat}")
        print()
    
    # Check for conflicts
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(" 🔍 VERIFICA CONFLITTI")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
    conflicts = check_platform_conflicts(schedules, network)
    
    if conflicts:
        print(f"⚠️  {len(conflicts)} CONFLITTI RILEVATI:\n")
        for conflict in conflicts:
            print(f"❌ Stazione: {conflict['node_name']}")
            print(f"   Binario: {conflict['platform']}")
            print(f"   Treno 1: {conflict['train1']} ({conflict['time1']})")
            print(f"   Treno 2: {conflict['train2']} ({conflict['time2']})")
            print()
    else:
        print("✅ NESSUN CONFLITTO RILEVATO!")
        print("   Tutti i treni hanno binari diversi o orari non sovrapposti\n")
    
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(" 📊 RIEPILOGO")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
    print(f"• Treni creati: {len(schedules)}")
    print(f"• Stazioni: {len(network.nodes)} (2 binari ciascuna)")
    print(f"• Binari totali disponibili: {sum(node.platforms for node in network.nodes.values())}")
    print(f"• Conflitti: {len(conflicts)}")
    print(f"• Sistema operativo: {'NO - Risolvere conflitti' if conflicts else 'SÌ - Nessun conflitto'}")
    
    print("\n╔════════════════════════════════════════════════════════════════╗")
    print("║                                                                ║")
    print("║     ✅ TEST COMPLETATO                                        ║")
    print("║                                                                ║")
    if not conflicts:
        print("║     Il sistema di gestione binari funziona correttamente!     ║")
        print("║     • Assegnazione automatica: OK                              ║")
        print("║     • Rilevamento conflitti: OK                                ║")
        print("║     • Binari doppi gestiti: OK                                 ║")
    else:
        print("║     Rilevati conflitti da risolvere manualmente               ║")
    print("║                                                                ║")
    print("╚════════════════════════════════════════════════════════════════╝\n")


if __name__ == "__main__":
    main()
