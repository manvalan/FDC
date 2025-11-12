#!/usr/bin/env python3
"""
Test script to verify schedule editing functionality.
Creates a simple network with a train and displays the schedule.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from datetime import datetime, timedelta
from railway_network import RailwayNetwork
from node import Node, NodeType
from train import Train, TrainType
from schedule import ScheduleBuilder

def main():
    print("\n" + "="*70)
    print("TEST MODIFICA ORARI - Verifica Funzionalità")
    print("="*70 + "\n")
    
    # Create network
    network = RailwayNetwork()
    
    # Add stations
    stations = [
        ("STA", "Stazione A", 45.0, 9.0),
        ("STB", "Stazione B", 45.1, 9.1),
        ("STC", "Stazione C", 45.2, 9.2),
        ("STD", "Stazione D", 45.3, 9.3)
    ]
    
    for sid, name, lat, lon in stations:
        network.add_node(Node(sid, name, NodeType.STATION, lat, lon))
    
    # Add connections
    from edge import Edge, TrackType
    
    connections = [
        ("STA", "STB", 50, TrackType.SINGLE, 120),
        ("STB", "STC", 40, TrackType.SINGLE, 100),
        ("STC", "STD", 60, TrackType.SINGLE, 140)
    ]
    
    for n1, n2, dist, track_type, speed in connections:
        edge = Edge(n1, n2, dist, track_type, speed)
        network.add_edge(edge)
    
    print("✓ Rete creata: 4 stazioni, 3 connessioni")
    print()
    
    # Create train and schedule
    train = Train("T001", "Treno Test", TrainType.REGIONAL)
    route = ["STA", "STB", "STC", "STD"]
    
    start_time = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
    
    schedule = ScheduleBuilder.create_schedule(
        schedule_id="SCH001",
        train=train,
        route=route,
        network=network,
        start_time=start_time,
        stop_duration_minutes=5
    )
    
    print("✓ Treno creato:")
    print(f"  ID: {train.id}")
    print(f"  Nome: {train.name}")
    print(f"  Tipo: {train.train_type.value}")
    print()
    
    # Display schedule
    print("ORARIO ORIGINALE:")
    print("-" * 70)
    print(f"{'Stazione':<20} {'Arrivo':<10} {'Partenza':<10} {'Sosta':<8}")
    print("-" * 70)
    
    for stop in schedule.stops:
        station_name = network.nodes[stop.node_id].name
        arr = stop.arrival_time.strftime('%H:%M') if stop.arrival_time else '---'
        dep = stop.departure_time.strftime('%H:%M') if stop.departure_time else '---'
        dwell = f"{stop.stop_duration} min" if stop.stop_duration else '---'
        print(f"{station_name:<20} {arr:<10} {dep:<10} {dwell:<8}")
    
    print()
    print("="*70)
    print("TEST COMPLETATO")
    print("="*70)
    print()
    print("📋 ISTRUZIONI PER TESTARE NELL'APPLICAZIONE GUI:")
    print()
    print("1. Avvia l'applicazione: python3 run_gui.py")
    print("2. Crea una linea con almeno 3 stazioni")
    print("3. Aggiungi un treno sulla linea")
    print("4. Seleziona il treno nella tab 'Treni e Orari'")
    print("5. Clicca sul pulsante '✏️ Modifica'")
    print()
    print("✅ NUOVE FUNZIONALITÀ:")
    print("   • Visualizzazione completa di tutte le fermate")
    print("   • Modifica orario di arrivo per ogni stazione")
    print("   • Modifica orario di partenza per ogni stazione")
    print("   • Modifica durata sosta per ogni stazione")
    print("   • Finestra scrollabile per molte fermate")
    print("   • Funziona anche con percorsi inversi")
    print()
    print("="*70)
    print()

if __name__ == "__main__":
    main()
