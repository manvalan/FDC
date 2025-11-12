#!/usr/bin/env python3
"""
Import Ferrovie della Contea network from JSON.
Converts the custom JSON format to FDC railway network format.
"""
import sys
sys.path.insert(0, '../src')

import json
from node import Node, NodeType
from edge import Edge, TrackType
from railway_network import RailwayNetwork


def import_contea_network(json_file_path: str) -> RailwayNetwork:
    """Import network from Ferrovie della Contea JSON format."""
    
    # Load JSON
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Create network
    network = RailwayNetwork(data.get('nome_rete', 'Railway Network'))
    
    print(f"📦 Importing network: {network.name}")
    print()
    
    # Map tipo to NodeType
    tipo_map = {
        'Capolinea': NodeType.STATION,
        'Normale': NodeType.STATION,
        'Interscambio': NodeType.INTERCHANGE,
        'Capolinea/Interscambio': NodeType.INTERCHANGE
    }
    
    # Import nodes
    print("📍 Importing nodes...")
    for node_data in data['nodi']:
        node_id = node_data['id']
        coord = node_data.get('coordinate', [0, 0])
        tipo = node_data.get('tipo', 'Normale')
        
        # Convert coordinates to lat/lon (approximate)
        # Using coordinate system: x=longitude, y=latitude (scaled)
        longitude = coord[0] / 10.0  # Scale down
        latitude = coord[1] / 10.0
        
        node_type = tipo_map.get(tipo, NodeType.STATION)
        
        # Set capacity based on type
        if 'Capolinea' in tipo or 'Interscambio' in tipo:
            capacity = 6
            platforms = 4
        else:
            capacity = 3
            platforms = 2
        
        node = Node(
            node_id=node_id,
            name=node_id,  # Use ID as name
            node_type=node_type,
            latitude=latitude,
            longitude=longitude,
            capacity=capacity,
            platforms=platforms
        )
        
        network.add_node(node)
        print(f"  ✓ {node_id} ({tipo})")
    
    print(f"\n  Total nodes: {len(network.nodes)}")
    print()
    
    # Import edges (connessioni)
    print("🛤️  Importing connections...")
    
    # Map binario type to TrackType
    binario_map = {
        'Singolo': (TrackType.SINGLE, 1),
        'Doppio': (TrackType.DOUBLE, 2)
    }
    
    # Map colore to max_speed
    speed_map = {
        'Giallo': 300,  # Alta velocità
        'Blu': 200,     # Linea principale
        'Rosso': 120,
        'Verde': 120,
        'Arancione': 160,
        'Viola': 120,
        'Marrone': 100,
        'Fucsia': 100
    }
    
    edge_count = 0
    for conn in data['connessioni']:
        from_node = conn['da']
        to_node = conn['a']
        distance = conn['lunghezza']
        colore = conn.get('colore', 'Rosso')
        binario = conn.get('binario', 'Singolo')
        
        # Get track type and capacity
        track_type, capacity = binario_map.get(binario, (TrackType.SINGLE, 1))
        
        # Get max speed based on line color
        max_speed = speed_map.get(colore, 120)
        
        edge = Edge(
            from_node=from_node,
            to_node=to_node,
            distance=distance,
            track_type=track_type,
            max_speed=max_speed,
            capacity=capacity,
            bidirectional=True
        )
        
        if network.add_edge(edge):
            edge_count += 1
            line_type = "🟡" if colore == "Giallo" else "🔵" if colore == "Blu" else "🔴" if colore == "Rosso" else "🟢" if colore == "Verde" else "🟠" if colore == "Arancione" else "🟣" if colore == "Viola" else "🟤" if colore == "Marrone" else "🩷"
            print(f"  {line_type} {from_node} → {to_node} ({distance}km, {binario}, {max_speed}km/h)")
    
    print(f"\n  Total connections: {edge_count}")
    print()
    
    return network


def main():
    print("=" * 80)
    print("FERROVIE DELLA CONTEA - NETWORK IMPORT")
    print("=" * 80)
    print()
    
    # Create JSON file with the network data
    contea_data = {
        "nome_rete": "Ferrovie della Contea",
        "nodi": [
            {"id": "Greenfield", "coordinate": [380, 560], "tipo": "Capolinea"},
            {"id": "Nobottle", "coordinate": [100, 500], "tipo": "Normale"},
            {"id": "Longcleve", "coordinate": [400, 520], "tipo": "Normale"},
            {"id": "Lowcleve", "coordinate": [400, 470], "tipo": "Normale"},
            {"id": "Needhole", "coordinate": [400, 420], "tipo": "Normale"},
            {"id": "Rushock Bag", "coordinate": [400, 370], "tipo": "Normale"},
            {"id": "Bagend", "coordinate": [400, 320], "tipo": "Normale"},
            {"id": "Over The Hill", "coordinate": [400, 270], "tipo": "Normale"},
            {"id": "The Hill", "coordinate": [400, 230], "tipo": "Normale"},
            {"id": "Hobbiton", "coordinate": [400, 190], "tipo": "Normale"},
            {"id": "ByWater Pool", "coordinate": [400, 140], "tipo": "Interscambio"},
            {"id": "Bywater", "coordinate": [400, 110], "tipo": "Interscambio"},
            {"id": "Tuckland", "coordinate": [400, 80], "tipo": "Normale"},
            {"id": "Stockroad", "coordinate": [400, 50], "tipo": "Normale"},
            {"id": "Greenhill Country", "coordinate": [400, 0], "tipo": "Normale"},
            {"id": "Girdlay Island", "coordinate": [600, 530], "tipo": "Normale"},
            {"id": "Quarry", "coordinate": [600, 480], "tipo": "Normale"},
            {"id": "Scary", "coordinate": [600, 430], "tipo": "Normale"},
            {"id": "Dwaling", "coordinate": [600, 380], "tipo": "Normale"},
            {"id": "Brockenborings", "coordinate": [600, 330], "tipo": "Normale"},
            {"id": "Oatbarton", "coordinate": [600, 280], "tipo": "Normale"},
            {"id": "The North Farthing", "coordinate": [600, 240], "tipo": "Normale"},
            {"id": "Frogmorton", "coordinate": [600, 140], "tipo": "Normale"},
            {"id": "Withfurrows", "coordinate": [750, 140], "tipo": "Normale"},
            {"id": "Bridge", "coordinate": [900, 140], "tipo": "Normale"},
            {"id": "Newbury", "coordinate": [900, 100], "tipo": "Normale"},
            {"id": "Brandy Hall", "coordinate": [900, 50], "tipo": "Capolinea/Interscambio"},
            {"id": "Buckelbury Ferry", "coordinate": [900, 0], "tipo": "Normale"},
            {"id": "Rush", "coordinate": [600, 0], "tipo": "Normale"},
            {"id": "Willow Bottom", "coordinate": [700, 0], "tipo": "Normale"},
            {"id": "Deep Hallow", "coordinate": [800, 0], "tipo": "Normale"},
            {"id": "The Stone", "coordinate": [550, 80], "tipo": "Normale"},
            {"id": "The Yale", "coordinate": [550, 50], "tipo": "Normale"},
            {"id": "Stock", "coordinate": [700, 50], "tipo": "Normale"},
            {"id": "Woody End", "coordinate": [500, -50], "tipo": "Normale"},
            {"id": "Whistle Brook", "coordinate": [400, -50], "tipo": "Normale"},
            {"id": "Pincup", "coordinate": [300, -50], "tipo": "Normale"},
            {"id": "Tukborrow", "coordinate": [300, 80], "tipo": "Normale"},
            {"id": "Michel Delving", "coordinate": [200, 140], "tipo": "Normale"},
            {"id": "Westmarch", "coordinate": [300, 140], "tipo": "Normale"},
            {"id": "White Downs", "coordinate": [250, 200], "tipo": "Normale"},
            {"id": "Westbank", "coordinate": [300, 260], "tipo": "Normale"},
            {"id": "Little Delvings", "coordinate": [200, 320], "tipo": "Normale"},
            {"id": "Gamwich", "coordinate": [200, 370], "tipo": "Normale"},
            {"id": "Tightfield", "coordinate": [200, 420], "tipo": "Normale"},
            {"id": "Westmarch Greenholm", "coordinate": [100, 140], "tipo": "Normale"},
            {"id": "Foxdown", "coordinate": [0, 140], "tipo": "Normale"},
            {"id": "Flostirion", "coordinate": [-100, 140], "tipo": "Capolinea"},
            {"id": "White Towers", "coordinate": [-50, 140], "tipo": "Normale"},
            {"id": "Undertower", "coordinate": [0, 110], "tipo": "Interscambio"},
            {"id": "Waymeet", "coordinate": [350, 140], "tipo": "Normale"},
            {"id": "Withwell", "coordinate": [350, 300], "tipo": "Normale"},
            {"id": "Tuck", "coordinate": [400, 10], "tipo": "Normale"},
            {"id": "Greenhill", "coordinate": [300, 0], "tipo": "Normale"}
        ],
        "connessioni": [
            # LINEA ROSSA
            {"da": "Greenfield", "a": "Longcleve", "lunghezza": 20, "colore": "Rosso", "binario": "Singolo"},
            {"da": "Longcleve", "a": "Lowcleve", "lunghezza": 10, "colore": "Rosso", "binario": "Singolo"},
            {"da": "Lowcleve", "a": "Needhole", "lunghezza": 20, "colore": "Rosso", "binario": "Singolo"},
            {"da": "Needhole", "a": "Rushock Bag", "lunghezza": 20, "colore": "Rosso", "binario": "Singolo"},
            {"da": "Rushock Bag", "a": "Bagend", "lunghezza": 20, "colore": "Rosso", "binario": "Singolo"},
            {"da": "Bagend", "a": "Over The Hill", "lunghezza": 9, "colore": "Rosso", "binario": "Singolo"},
            {"da": "Over The Hill", "a": "The Hill", "lunghezza": 8, "colore": "Rosso", "binario": "Singolo"},
            {"da": "The Hill", "a": "Hobbiton", "lunghezza": 4, "colore": "Rosso", "binario": "Singolo"},
            {"da": "Hobbiton", "a": "ByWater Pool", "lunghezza": 10, "colore": "Rosso", "binario": "Singolo"},
            {"da": "ByWater Pool", "a": "Bywater", "lunghezza": 3, "colore": "Rosso", "binario": "Singolo"},
            # LINEA ARANCIONE
            {"da": "Bywater", "a": "ByWater Pool", "lunghezza": 3, "colore": "Arancione", "binario": "Doppio"},
            {"da": "ByWater Pool", "a": "The Stone", "lunghezza": 12, "colore": "Arancione", "binario": "Doppio"},
            {"da": "The Stone", "a": "Stockroad", "lunghezza": 11, "colore": "Arancione", "binario": "Singolo"},
            {"da": "Stockroad", "a": "The Yale", "lunghezza": 12, "colore": "Arancione", "binario": "Singolo"},
            {"da": "The Yale", "a": "Stock", "lunghezza": 14, "colore": "Arancione", "binario": "Singolo"},
            {"da": "Stock", "a": "Buckelbury Ferry", "lunghezza": 12, "colore": "Arancione", "binario": "Singolo"},
            {"da": "Buckelbury Ferry", "a": "Brandy Hall", "lunghezza": 5, "colore": "Arancione", "binario": "Doppio"},
            # LINEA VERDE
            {"da": "Nobottle", "a": "Gamwich", "lunghezza": 24, "colore": "Verde", "binario": "Singolo"},
            {"da": "Gamwich", "a": "Tightfield", "lunghezza": 22, "colore": "Verde", "binario": "Singolo"},
            {"da": "Tightfield", "a": "Little Delvings", "lunghezza": 22, "colore": "Verde", "binario": "Singolo"},
            {"da": "Little Delvings", "a": "Westbank", "lunghezza": 23, "colore": "Verde", "binario": "Singolo"},
            {"da": "Westbank", "a": "Waymeet", "lunghezza": 23, "colore": "Verde", "binario": "Singolo"},
            {"da": "Waymeet", "a": "Withwell", "lunghezza": 14, "colore": "Verde", "binario": "Singolo"},
            {"da": "Withwell", "a": "Tuck", "lunghezza": 10, "colore": "Verde", "binario": "Singolo"},
            {"da": "Tuck", "a": "Tukborrow", "lunghezza": 8, "colore": "Verde", "binario": "Singolo"},
            {"da": "Tukborrow", "a": "Tuckland", "lunghezza": 8, "colore": "Verde", "binario": "Singolo"},
            {"da": "Tuckland", "a": "The Stone", "lunghezza": 16, "colore": "Verde", "binario": "Singolo"},
            {"da": "The Stone", "a": "ByWater Pool", "lunghezza": 12, "colore": "Verde", "binario": "Singolo"},
            {"da": "ByWater Pool", "a": "Bywater", "lunghezza": 3, "colore": "Verde", "binario": "Singolo"},
            # LINEA BLU
            {"da": "Flostirion", "a": "White Towers", "lunghezza": 14, "colore": "Blu", "binario": "Doppio"},
            {"da": "White Towers", "a": "Undertower", "lunghezza": 12, "colore": "Blu", "binario": "Doppio"},
            {"da": "Undertower", "a": "Westmarch", "lunghezza": 21, "colore": "Blu", "binario": "Doppio"},
            {"da": "Westmarch", "a": "Westmarch Greenholm", "lunghezza": 24, "colore": "Blu", "binario": "Doppio"},
            {"da": "Westmarch Greenholm", "a": "Foxdown", "lunghezza": 22, "colore": "Blu", "binario": "Doppio"},
            {"da": "Foxdown", "a": "Michel Delving", "lunghezza": 21, "colore": "Blu", "binario": "Doppio"},
            {"da": "Michel Delving", "a": "White Downs", "lunghezza": 22, "colore": "Blu", "binario": "Doppio"},
            {"da": "White Downs", "a": "Waymeet", "lunghezza": 13, "colore": "Blu", "binario": "Doppio"},
            {"da": "Waymeet", "a": "Bywater", "lunghezza": 15, "colore": "Blu", "binario": "Doppio"},
            {"da": "Bywater", "a": "Frogmorton", "lunghezza": 20, "colore": "Blu", "binario": "Doppio"},
            {"da": "Frogmorton", "a": "Withfurrows", "lunghezza": 16, "colore": "Blu", "binario": "Doppio"},
            {"da": "Withfurrows", "a": "Bridge", "lunghezza": 17, "colore": "Blu", "binario": "Doppio"},
            {"da": "Bridge", "a": "Newbury", "lunghezza": 16, "colore": "Blu", "binario": "Doppio"},
            {"da": "Newbury", "a": "Brandy Hall", "lunghezza": 15, "colore": "Blu", "binario": "Doppio"},
            # LINEA GIALLA (Alta Velocità)
            {"da": "Undertower", "a": "Michel Delving", "lunghezza": 88, "colore": "Giallo", "binario": "Doppio"},
            {"da": "Michel Delving", "a": "Tuck", "lunghezza": 42, "colore": "Giallo", "binario": "Doppio"},
            {"da": "Tuck", "a": "Bywater", "lunghezza": 28, "colore": "Giallo", "binario": "Doppio"},
            {"da": "Bywater", "a": "Brandy Hall", "lunghezza": 84, "colore": "Giallo", "binario": "Doppio"},
            # LINEA VIOLA
            {"da": "Girdlay Island", "a": "Quarry", "lunghezza": 10, "colore": "Viola", "binario": "Singolo"},
            {"da": "Quarry", "a": "Scary", "lunghezza": 12, "colore": "Viola", "binario": "Singolo"},
            {"da": "Scary", "a": "Dwaling", "lunghezza": 12, "colore": "Viola", "binario": "Singolo"},
            {"da": "Dwaling", "a": "Brockenborings", "lunghezza": 6, "colore": "Viola", "binario": "Singolo"},
            {"da": "Brockenborings", "a": "Oatbarton", "lunghezza": 6, "colore": "Viola", "binario": "Singolo"},
            {"da": "Oatbarton", "a": "The North Farthing", "lunghezza": 8, "colore": "Viola", "binario": "Singolo"},
            {"da": "The North Farthing", "a": "ByWater Pool", "lunghezza": 12, "colore": "Viola", "binario": "Singolo"},
            {"da": "ByWater Pool", "a": "Bywater", "lunghezza": 3, "colore": "Viola", "binario": "Singolo"},
            # LINEA MARRONE
            {"da": "The Stone", "a": "Stockroad", "lunghezza": 10, "colore": "Marrone", "binario": "Singolo"},
            {"da": "Stockroad", "a": "Greenhill Country", "lunghezza": 10, "colore": "Marrone", "binario": "Singolo"},
            {"da": "Greenhill Country", "a": "Greenhill", "lunghezza": 10, "colore": "Marrone", "binario": "Singolo"},
            {"da": "Greenhill", "a": "Pincup", "lunghezza": 21, "colore": "Marrone", "binario": "Singolo"},
            {"da": "Pincup", "a": "Whistle Brook", "lunghezza": 12, "colore": "Marrone", "binario": "Singolo"},
            {"da": "Whistle Brook", "a": "Woody End", "lunghezza": 18, "colore": "Marrone", "binario": "Singolo"},
            {"da": "Woody End", "a": "Willow Bottom", "lunghezza": 25, "colore": "Marrone", "binario": "Singolo"},
            {"da": "Willow Bottom", "a": "Deep Hallow", "lunghezza": 14, "colore": "Marrone", "binario": "Singolo"},
            {"da": "Deep Hallow", "a": "Rush", "lunghezza": 12, "colore": "Marrone", "binario": "Singolo"},
            {"da": "Rush", "a": "Buckelbury Ferry", "lunghezza": 12, "colore": "Marrone", "binario": "Singolo"},
            {"da": "Buckelbury Ferry", "a": "Brandy Hall", "lunghezza": 5, "colore": "Marrone", "binario": "Singolo"},
            # LINEA FUCSIA
            {"da": "Nobottle", "a": "Longcleve", "lunghezza": 26, "colore": "Fucsia", "binario": "Singolo"},
            {"da": "Longcleve", "a": "Lowcleve", "lunghezza": 10, "colore": "Fucsia", "binario": "Singolo"},
            {"da": "Lowcleve", "a": "Needhole", "lunghezza": 20, "colore": "Fucsia", "binario": "Singolo"},
            {"da": "Needhole", "a": "Rushock Bag", "lunghezza": 22, "colore": "Fucsia", "binario": "Singolo"},
            {"da": "Rushock Bag", "a": "Dwaling", "lunghezza": 22, "colore": "Fucsia", "binario": "Singolo"},
            {"da": "Dwaling", "a": "Scary", "lunghezza": 12, "colore": "Fucsia", "binario": "Singolo"},
            {"da": "Scary", "a": "Quarry", "lunghezza": 12, "colore": "Fucsia", "binario": "Singolo"},
            {"da": "Quarry", "a": "Girdlay Island", "lunghezza": 10, "colore": "Fucsia", "binario": "Singolo"}
        ]
    }
    
    # Save to temporary file
    with open('ferrovie_contea.json', 'w', encoding='utf-8') as f:
        json.dump(contea_data, f, indent=2, ensure_ascii=False)
    
    # Import network
    network = import_contea_network('ferrovie_contea.json')
    
    # Show statistics
    print("📊 NETWORK STATISTICS:")
    print("=" * 80)
    stats = network.get_network_stats()
    for key, value in stats.items():
        print(f"  • {key.replace('_', ' ').title()}: {value}")
    print()
    
    # Export to FDC format
    print("💾 Exporting to FDC JSON format...")
    network.export_to_json('ferrovie_contea_fdc.json')
    print("  ✓ Saved to: ferrovie_contea_fdc.json")
    print()
    
    # Visualize a sample route
    print("🎨 Generating network visualization...")
    try:
        network.visualize(figsize=(20, 16), save_path='ferrovie_contea_network.png')
        print("  ✓ Saved to: ferrovie_contea_network.png")
    except Exception as e:
        print(f"  ⚠ Could not generate visualization: {e}")
    print()
    
    # Show some example routes
    print("🛤️  EXAMPLE ROUTES:")
    print("=" * 80)
    
    routes_to_test = [
        ("Flostirion", "Brandy Hall", "Linea Blu - Costa a costa"),
        ("Undertower", "Brandy Hall", "Linea Gialla - Alta Velocità"),
        ("Greenfield", "Bywater", "Linea Rossa - Storica"),
        ("Nobottle", "Girdlay Island", "Linea Fucsia - Nord")
    ]
    
    for start, end, description in routes_to_test:
        result = network.find_shortest_path(start, end)
        if result:
            path, distance = result
            print(f"\n{description}:")
            print(f"  Route: {' → '.join(path)}")
            print(f"  Distance: {distance:.1f} km")
            print(f"  Stops: {len(path)}")
    
    print()
    print("=" * 80)
    print("✓ Import completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    main()
