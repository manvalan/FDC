"""
Test per verificare il calcolo corretto degli orari dei treni.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from datetime import datetime, timedelta
from railway_network import RailwayNetwork
from node import Node, NodeType
from edge import Edge, TrackType
from train import Train, TrainType
from schedule import TrainSchedule, ScheduleBuilder

def test_schedule_calculation():
    """Test calcolo orari con distanze e velocità note."""
    
    # Crea rete test
    network = RailwayNetwork("test")
    
    # 3 stazioni: A -> B -> C
    # Distanze: A-B = 50 km, B-C = 100 km
    # Velocità massima: 160 km/h (Regional)
    
    nodeA = Node("A", "Stazione A", NodeType.STATION, latitude=45.0, longitude=9.0, platforms=2)
    nodeB = Node("B", "Stazione B", NodeType.STATION, latitude=45.5, longitude=9.5, platforms=2)
    nodeC = Node("C", "Stazione C", NodeType.STATION, latitude=46.0, longitude=10.0, platforms=2)
    
    network.add_node(nodeA)
    network.add_node(nodeB)
    network.add_node(nodeC)
    
    edgeAB = Edge("A", "B", distance=50.0, max_speed=160, track_type=TrackType.DOUBLE, bidirectional=True)
    edgeBC = Edge("B", "C", distance=100.0, max_speed=160, track_type=TrackType.DOUBLE, bidirectional=True)
    
    network.add_edge(edgeAB)
    network.add_edge(edgeBC)
    
    # Crea treno Regional
    train = Train(
        train_id="T001",
        name="Regional Test",
        train_type=TrainType.REGIONAL
    )
    
    print(f"\n{'='*60}")
    print(f"TEST CALCOLO ORARIO TRENO")
    print(f"{'='*60}")
    print(f"\n🚂 Treno: {train.name}")
    print(f"   Tipo: {train.train_type.value}")
    print(f"   Velocità max: {train.max_speed} km/h")
    print(f"   Accelerazione: {train.acceleration} m/s²")
    print(f"   Decelerazione: {train.deceleration} m/s²")
    
    print(f"\n🛤️  PERCORSO:")
    print(f"   A → B: {edgeAB.distance} km @ {edgeAB.max_speed} km/h")
    print(f"   B → C: {edgeBC.distance} km @ {edgeBC.max_speed} km/h")
    
    # Crea schedule con partenza alle 08:00
    start_time = datetime(2024, 1, 1, 8, 0)
    route = ["A", "B", "C"]
    stop_duration = 5  # 5 minuti di sosta
    
    print(f"\n⏰ PARTENZA: {start_time.strftime('%H:%M')}")
    print(f"   Sosta in stazione: {stop_duration} minuti")
    
    schedule = ScheduleBuilder.create_schedule(
        schedule_id="SCH001",
        train=train,
        route=route,
        network=network,
        start_time=start_time,
        stop_duration_minutes=stop_duration
    )
    
    if not schedule:
        print("\n❌ ERRORE: Impossibile creare lo schedule!")
        return False
    
    print(f"\n📋 ORARIO CALCOLATO:")
    print(f"{'─'*60}")
    print(f"{'Stazione':<20} {'Arrivo':>10} {'Partenza':>10} {'Sosta':>8}")
    print(f"{'─'*60}")
    
    total_travel_time = timedelta(0)
    
    for i, stop in enumerate(schedule.stops):
        station_name = network.nodes[stop.node_id].name if stop.node_id in network.nodes else stop.node_id
        arr_str = stop.arrival_time.strftime('%H:%M') if stop.arrival_time else '--:--'
        dep_str = stop.departure_time.strftime('%H:%M') if stop.departure_time else '--:--'
        sosta_str = f"{stop.stop_duration}min" if stop.stop_duration > 0 else '--'
        
        print(f"{station_name:<20} {arr_str:>10} {dep_str:>10} {sosta_str:>8}")
        
        # Calcola tempo di viaggio per questo segmento
        if i > 0:
            prev_stop = schedule.stops[i-1]
            segment_time = (stop.arrival_time - prev_stop.departure_time).total_seconds() / 60
            total_travel_time += (stop.arrival_time - prev_stop.departure_time)
            
            # Trova l'arco
            edge = None
            for e in network.edges:
                if e.from_node == prev_stop.node_id and e.to_node == stop.node_id:
                    edge = e
                    break
            
            if edge:
                avg_speed = (edge.distance / segment_time) * 60  # km/h
                print(f"                     {'└─ Viaggio:':<10} {segment_time:.1f}min → {avg_speed:.1f} km/h")
    
    print(f"{'─'*60}")
    
    # Calcola statistiche
    first_stop = schedule.stops[0]
    last_stop = schedule.stops[-1]
    total_time = (last_stop.arrival_time - first_stop.departure_time).total_seconds() / 60
    total_distance = edgeAB.distance + edgeBC.distance
    avg_speed = (total_distance / total_time) * 60
    
    print(f"\n📊 STATISTICHE:")
    print(f"   Distanza totale: {total_distance} km")
    print(f"   Tempo totale: {total_time:.1f} minuti")
    print(f"   Tempo viaggio: {total_travel_time.total_seconds()/60:.1f} minuti")
    print(f"   Tempo soste: {stop_duration} minuti")
    print(f"   Velocità media: {avg_speed:.1f} km/h")
    
    # Verifica realistica
    print(f"\n✅ VERIFICA:")
    
    # Tempo minimo teorico senza soste a velocità massima
    min_time_no_stops = (total_distance / train.max_speed) * 60
    print(f"   Tempo teorico min (v_max costante): {min_time_no_stops:.1f} min")
    
    # Il tempo reale deve essere maggiore per accelerazione/frenata
    travel_time_only = total_travel_time.total_seconds() / 60
    if travel_time_only > min_time_no_stops:
        print(f"   ✓ Tempo viaggio ({travel_time_only:.1f} min) > Tempo teorico ({min_time_no_stops:.1f} min)")
        print(f"   ✓ Differenza: {travel_time_only - min_time_no_stops:.1f} min per accelerazione/frenata")
    else:
        print(f"   ❌ ERRORE: Tempo viaggio troppo breve!")
        return False
    
    # Verifica velocità media
    if avg_speed < train.max_speed:
        print(f"   ✓ Velocità media ({avg_speed:.1f} km/h) < V_max ({train.max_speed} km/h)")
    else:
        print(f"   ❌ ERRORE: Velocità media impossibile!")
        return False
    
    print(f"\n{'='*60}")
    print(f"✅ TEST COMPLETATO CON SUCCESSO!")
    print(f"{'='*60}\n")
    
    return True

if __name__ == "__main__":
    success = test_schedule_calculation()
    sys.exit(0 if success else 1)
