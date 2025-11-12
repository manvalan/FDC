"""
Script per creare un'infrastruttura separata ad Alta Velocità (AV)
Identifica la linea principale e la duplica con suffisso _AV
"""

import sys
import json
sys.path.insert(0, '../src')

from railway_network import RailwayNetwork
from node import Node, NodeType
from edge import Edge, TrackType


def identify_main_line(network):
    """
    Identifica la linea principale (presumibilmente quella da convertire in AV).
    Trova il percorso più lungo che attraversa stazioni con maggiore capacità.
    """
    # Trova le stazioni principali (quelle con capacità >= 6)
    main_stations = [node_id for node_id, node in network.nodes.items() 
                     if node.capacity >= 6]
    
    print(f"\n🔍 Stazioni principali identificate (capacità >= 6):")
    for station in main_stations:
        node = network.nodes[station]
        print(f"   • {station} (capacità: {node.capacity}, piattaforme: {node.platforms})")
    
    if len(main_stations) < 2:
        print("\n⚠️  Non abbastanza stazioni principali. Cerco la linea più lunga...")
        # Trova la linea più lunga come alternativa
        return find_longest_line(network)
    
    return main_stations


def find_longest_line(network):
    """Trova il percorso più lungo nella rete."""
    max_length = 0
    longest_path = []
    
    # Prova tutti i percorsi tra tutte le coppie di nodi
    nodes = list(network.nodes.keys())
    for start in nodes:
        for end in nodes:
            if start != end:
                result = network.find_shortest_path(start, end)
                if result:
                    path, distance = result
                    if distance > max_length:
                        max_length = distance
                        longest_path = path
    
    return longest_path[:10] if len(longest_path) > 10 else longest_path


def get_connected_stations(network, start_stations):
    """
    Espande la lista per includere tutte le stazioni connesse in sequenza.
    """
    if not start_stations:
        return []
    
    # Inizia dalle stazioni principali e trova il percorso che le collega
    if len(start_stations) >= 2:
        result = network.find_shortest_path(start_stations[0], start_stations[-1])
        if result:
            path, distance = result
            return path
    
    return start_stations


def create_av_infrastructure(network, av_stations):
    """
    Crea nuove stazioni AV con suffisso _AV e le connette con binari doppi ad alta velocità.
    """
    print(f"\n🚄 Creazione infrastruttura Alta Velocità...")
    print(f"   Stazioni da duplicare: {len(av_stations)}")
    
    # Crea nuove stazioni AV
    av_nodes_created = []
    for station_id in av_stations:
        original_node = network.nodes.get(station_id)
        if not original_node:
            continue
        
        # Crea nuovo ID con suffisso _AV
        av_id = f"{station_id}_AV"
        
        # Crea nuova stazione AV con coordinate leggermente spostate
        av_node = Node(
            node_id=av_id,
            name=f"{original_node.name} AV",
            node_type=NodeType.STATION,
            latitude=original_node.latitude + 0.5,  # Sposta leggermente
            longitude=original_node.longitude + 0.5,
            capacity=original_node.capacity,
            platforms=original_node.platforms
        )
        
        if network.add_node(av_node):
            av_nodes_created.append(av_id)
            print(f"   ✅ Creata: {av_id} ({original_node.name} AV)")
    
    print(f"\n   Totale stazioni AV create: {len(av_nodes_created)}")
    
    # Crea connessioni AV tra le nuove stazioni (linea dedicata)
    av_edges_created = 0
    for i in range(len(av_nodes_created) - 1):
        from_id = av_nodes_created[i]
        to_id = av_nodes_created[i + 1]
        
        # Calcola distanza approssimativa tra le stazioni originali
        from_original = av_stations[i]
        to_original = av_stations[i + 1]
        
        # Cerca l'arco originale per ottenere la distanza
        distance = 50  # Default
        for edge in network.edges:
            if ((edge.from_node == from_original and edge.to_node == to_original) or
                (edge.from_node == to_original and edge.to_node == from_original)):
                distance = edge.distance
                break
        
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
            print(f"   ✅ Connessione AV: {from_id} ↔ {to_id} ({distance} km, 300 km/h)")
    
    print(f"\n   Totale connessioni AV create: {av_edges_created}")
    
    # Crea interconnessioni tra stazioni originali e AV (per interscambio)
    interchange_edges = 0
    for original_id in av_stations:
        av_id = f"{original_id}_AV"
        if av_id in network.nodes:
            # Connessione breve per interscambio
            interchange_edge = Edge(
                from_node=original_id,
                to_node=av_id,
                distance=0.5,  # 500 metri di interscambio
                track_type=TrackType.SINGLE,
                max_speed=30,  # Velocità ridotta per manovra
                capacity=1
            )
            
            if network.add_edge(interchange_edge):
                interchange_edges += 1
                print(f"   🔄 Interscambio: {original_id} ↔ {av_id}")
    
    print(f"\n   Totale interscambi creati: {interchange_edges}")
    
    return av_nodes_created


def main():
    print("=" * 70)
    print("   CREAZIONE INFRASTRUTTURA ALTA VELOCITÀ (AV)")
    print("=" * 70)
    
    # Carica rete esistente
    print("\n📁 Caricamento rete Ferrovie della Contea...")
    network = RailwayNetwork()
    network.import_from_json("ferrovie_contea_fdc.json")
    
    stats_before = network.get_network_stats()
    print(f"   ✅ Rete caricata: {stats_before['num_nodes']} stazioni, "
          f"{stats_before['num_edges']} connessioni")
    
    # Identifica linea principale
    main_stations = identify_main_line(network)
    
    # Espandi per ottenere tutte le stazioni connesse
    av_stations = get_connected_stations(network, main_stations)
    
    print(f"\n📍 Linea AV identificata ({len(av_stations)} stazioni):")
    for i, station in enumerate(av_stations, 1):
        node = network.nodes[station]
        print(f"   {i:2d}. {station} ({node.name})")
    
    # Crea infrastruttura AV
    av_nodes = create_av_infrastructure(network, av_stations)
    
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
    print(f"   • Binari doppi a 300 km/h")
    print(f"   • Infrastruttura separata e dedicata")
    print(f"   • Interscambi con rete tradizionale")
    
    # Salva rete aggiornata
    output_file = "ferrovie_contea_con_av.json"
    network.export_to_json(output_file)
    print(f"\n💾 Rete salvata in: {output_file}")
    
    # Visualizza la rete
    print("\n📊 Generazione visualizzazione...")
    try:
        network.visualize(
            output_file="ferrovie_contea_av_network.png",
            show_labels=True,
            title="Ferrovie della Contea - Con Infrastruttura AV"
        )
        print("   ✅ Visualizzazione salvata: ferrovie_contea_av_network.png")
    except Exception as e:
        print(f"   ⚠️  Visualizzazione non disponibile: {e}")
    
    print("\n" + "=" * 70)
    print("   ✅ INFRASTRUTTURA AV CREATA CON SUCCESSO!")
    print("=" * 70)
    print("\n💡 Nota: Le stazioni AV hanno suffisso '_AV' e sono collegate")
    print("   con binari doppi ad alta velocità (300 km/h).")
    print("   Gli interscambi permettono il trasferimento tra reti.")


if __name__ == "__main__":
    main()
