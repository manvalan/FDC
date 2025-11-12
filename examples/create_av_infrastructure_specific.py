"""
Script per creare un'infrastruttura separata ad Alta Velocità (AV)
Solo per le stazioni specifiche: Undertower, Michel Delving, Tuck, ByWater, Brandy Hall
"""

import sys
import json
sys.path.insert(0, '../src')

from railway_network import RailwayNetwork
from node import Node, NodeType
from edge import Edge, TrackType


def create_av_infrastructure_specific(network):
    """
    Crea nuove stazioni AV con suffisso _AV solo per le 5 stazioni specificate.
    Le collega con binari doppi ad alta velocità in sequenza.
    """
    # Stazioni da convertire in AV (ordine geografico)
    av_stations = [
        "Undertower",
        "Michel Delving",
        "Tuck",
        "Bywater",
        "Brandy Hall"
    ]
    
    # Verifica che tutte le stazioni esistano
    print("\n🔍 Verifica stazioni da convertire in AV:")
    valid_stations = []
    for station_id in av_stations:
        if station_id in network.nodes:
            node = network.nodes[station_id]
            print(f"   ✅ {station_id} ({node.name}) - TROVATA")
            valid_stations.append(station_id)
        else:
            print(f"   ❌ {station_id} - NON TROVATA")
            # Prova varianti del nome
            for node_id in network.nodes:
                if station_id.lower() in node_id.lower():
                    node = network.nodes[node_id]
                    print(f"      → Trovata variante: {node_id} ({node.name})")
                    valid_stations.append(node_id)
                    break
    
    if not valid_stations:
        print("\n❌ Nessuna stazione valida trovata!")
        return []
    
    print(f"\n🚄 Creazione infrastruttura Alta Velocità...")
    print(f"   Stazioni da duplicare: {len(valid_stations)}")
    
    # Crea nuove stazioni AV
    av_nodes_created = []
    for station_id in valid_stations:
        original_node = network.nodes[station_id]
        
        # Crea nuovo ID con suffisso _AV
        av_id = f"{station_id}_AV"
        
        # Crea nuova stazione AV con coordinate leggermente spostate
        av_node = Node(
            node_id=av_id,
            name=f"{original_node.name} AV",
            node_type=NodeType.STATION,
            latitude=original_node.latitude + 1.0,  # Sposta più visibilmente
            longitude=original_node.longitude + 1.0,
            capacity=original_node.capacity * 2,  # Capacità doppia per AV
            platforms=original_node.platforms + 2   # Più piattaforme
        )
        
        if network.add_node(av_node):
            av_nodes_created.append(av_id)
            print(f"   ✅ Creata: {av_id}")
            print(f"      Nome: {original_node.name} AV")
            print(f"      Capacità: {av_node.capacity} (originale: {original_node.capacity})")
            print(f"      Piattaforme: {av_node.platforms} (originale: {original_node.platforms})")
    
    print(f"\n   Totale stazioni AV create: {len(av_nodes_created)}")
    
    # Trova il percorso tra le stazioni originali per determinare l'ordine corretto
    print(f"\n🔍 Determinazione ordine stazioni AV...")
    ordered_stations = []
    
    # Trova il percorso ottimale tra tutte le stazioni
    if len(valid_stations) >= 2:
        # Inizia dalla prima stazione e trova il percorso verso le altre
        start = valid_stations[0]
        remaining = valid_stations[1:]
        ordered_stations = [start]
        
        current = start
        while remaining:
            min_dist = float('inf')
            next_station = None
            
            for station in remaining:
                result = network.find_shortest_path(current, station)
                if result:
                    path, distance = result
                    if distance < min_dist:
                        min_dist = distance
                        next_station = station
            
            if next_station:
                ordered_stations.append(next_station)
                remaining.remove(next_station)
                current = next_station
            else:
                # Non trovato percorso, aggiungi comunque
                ordered_stations.extend(remaining)
                break
    else:
        ordered_stations = valid_stations
    
    print(f"   Ordine determinato:")
    for i, station in enumerate(ordered_stations, 1):
        print(f"      {i}. {station}")
    
    # Crea connessioni AV tra le nuove stazioni in ordine
    av_edges_created = 0
    for i in range(len(ordered_stations) - 1):
        from_original = ordered_stations[i]
        to_original = ordered_stations[i + 1]
        from_id = f"{from_original}_AV"
        to_id = f"{to_original}_AV"
        
        # Calcola distanza tra le stazioni originali
        result = network.find_shortest_path(from_original, to_original)
        if result:
            path, distance = result
        else:
            distance = 50  # Default se non c'è percorso
        
        # Crea arco AV con binario doppio e velocità massima 300 km/h
        av_edge = Edge(
            from_node=from_id,
            to_node=to_id,
            distance=distance,
            track_type=TrackType.DOUBLE,
            max_speed=300,  # Alta velocità!
            capacity=2
        )
        
        if network.add_edge(av_edge):
            av_edges_created += 1
            print(f"\n   ✅ Connessione AV creata:")
            print(f"      {from_id} ↔ {to_id}")
            print(f"      Distanza: {distance} km")
            print(f"      Velocità max: 300 km/h")
            print(f"      Binari: DOPPI")
    
    print(f"\n   Totale connessioni AV create: {av_edges_created}")
    
    # Crea interconnessioni tra stazioni originali e AV (per interscambio)
    interchange_edges = 0
    for original_id in valid_stations:
        av_id = f"{original_id}_AV"
        if av_id in network.nodes:
            # Connessione breve per interscambio
            interchange_edge = Edge(
                from_node=original_id,
                to_node=av_id,
                distance=0.3,  # 300 metri di interscambio
                track_type=TrackType.SINGLE,
                max_speed=30,  # Velocità ridotta per manovra
                capacity=1
            )
            
            if network.add_edge(interchange_edge):
                interchange_edges += 1
                print(f"   🔄 Interscambio: {original_id} ↔ {av_id} (300m)")
    
    print(f"\n   Totale interscambi creati: {interchange_edges}")
    
    return av_nodes_created


def main():
    print("=" * 70)
    print("   CREAZIONE INFRASTRUTTURA ALTA VELOCITÀ (AV)")
    print("   Solo stazioni: Undertower, Michel Delving, Tuck,")
    print("                  ByWater, Brandy Hall")
    print("=" * 70)
    
    # Carica rete esistente
    print("\n📁 Caricamento rete Ferrovie della Contea...")
    network = RailwayNetwork()
    network.import_from_json("ferrovie_contea_fdc.json")
    
    stats_before = network.get_network_stats()
    print(f"   ✅ Rete caricata: {stats_before['num_nodes']} stazioni, "
          f"{stats_before['num_edges']} connessioni")
    
    # Lista tutte le stazioni disponibili per debug
    print(f"\n📋 Stazioni disponibili nella rete:")
    all_stations = sorted(network.nodes.keys())
    for i, station in enumerate(all_stations, 1):
        node = network.nodes[station]
        if any(keyword in station.lower() for keyword in ['undertower', 'michel', 'tuck', 'bywater', 'brandy']):
            print(f"   {i:2d}. {station:25s} ({node.name}) ⭐")
        else:
            print(f"   {i:2d}. {station:25s} ({node.name})")
    
    # Crea infrastruttura AV
    av_nodes = create_av_infrastructure_specific(network)
    
    if not av_nodes:
        print("\n❌ Nessuna stazione AV creata!")
        return
    
    # Statistiche finali
    stats_after = network.get_network_stats()
    print("\n" + "=" * 70)
    print("   STATISTICHE FINALI")
    print("=" * 70)
    print(f"\n📊 Rete originale:")
    print(f"   • Stazioni: {stats_before['num_nodes']}")
    print(f"   • Connessioni: {stats_before['num_edges']}")
    print(f"   • Lunghezza totale: {stats_before['total_track_length']:.1f} km")
    
    print(f"\n📊 Rete con infrastruttura AV:")
    print(f"   • Stazioni totali: {stats_after['num_nodes']} "
          f"(+{stats_after['num_nodes'] - stats_before['num_nodes']})")
    print(f"   • Connessioni totali: {stats_after['num_edges']} "
          f"(+{stats_after['num_edges'] - stats_before['num_edges']})")
    print(f"   • Lunghezza totale: {stats_after['total_track_length']:.1f} km")
    
    print(f"\n🚄 Linea AV creata:")
    print(f"   • Stazioni AV: {len(av_nodes)}")
    for av_node_id in av_nodes:
        node = network.nodes[av_node_id]
        print(f"     - {av_node_id:30s} ({node.name})")
    print(f"   • Binari doppi a 300 km/h")
    print(f"   • Infrastruttura separata e dedicata")
    print(f"   • Interscambi con rete tradizionale (300m)")
    
    # Salva rete aggiornata
    output_file = "ferrovie_contea_con_av.json"
    network.export_to_json(output_file)
    print(f"\n💾 Rete salvata in: {output_file}")
    
    print("\n" + "=" * 70)
    print("   ✅ INFRASTRUTTURA AV CREATA CON SUCCESSO!")
    print("=" * 70)
    print("\n💡 Nota: Le stazioni AV hanno suffisso '_AV' e sono collegate")
    print("   con binari doppi ad alta velocità (300 km/h).")
    print("   Gli interscambi (300m) permettono il trasferimento tra reti.")
    print("\n📂 Puoi caricare il file 'ferrovie_contea_con_av.json' nella GUI")
    print("   usando: File → Apri...")


if __name__ == "__main__":
    main()
