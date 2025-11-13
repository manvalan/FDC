#include <iostream>
#include <iomanip>
#include "railway_network.hpp"

using namespace fdc;

void print_separator(const std::string& title = "") {
    std::cout << "\n";
    std::cout << "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n";
    if (!title.empty()) {
        std::cout << "  " << title << "\n";
        std::cout << "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n";
    }
}

void print_path(const Path& path) {
    if (!path.is_valid()) {
        std::cout << "  No valid path found!\n";
        return;
    }
    
    std::cout << "  Route: ";
    for (size_t i = 0; i < path.nodes.size(); ++i) {
        std::cout << path.nodes[i];
        if (i < path.nodes.size() - 1) {
            std::cout << " → ";
        }
    }
    std::cout << "\n";
    
    std::cout << "  Total Distance: " << std::fixed << std::setprecision(1) 
              << path.total_distance << " km\n";
    std::cout << "  Min Travel Time: " << std::fixed << std::setprecision(2) 
              << path.min_travel_time * 60 << " minutes\n";
    std::cout << "  Average Speed: " << std::fixed << std::setprecision(1)
              << (path.total_distance / path.min_travel_time) << " km/h\n";
}

void print_network_stats(const NetworkStats& stats) {
    std::cout << "  Number of Nodes: " << stats.num_nodes << "\n";
    std::cout << "  Number of Edges: " << stats.num_edges << "\n";
    std::cout << "  Total Track Length: " << std::fixed << std::setprecision(1) 
              << stats.total_track_length << " km\n";
    
    if (stats.num_edges > 0) {
        std::cout << "  Average Edge Length: " << std::fixed << std::setprecision(1) 
                  << stats.average_edge_length << " km\n";
        std::cout << "  Min/Max Edge Length: " << std::fixed << std::setprecision(1)
                  << stats.min_edge_length << " / " << stats.max_edge_length << " km\n";
        
        std::cout << "\n  Track Types:\n";
        std::cout << "    - Single Track: " << stats.num_single_track << "\n";
        std::cout << "    - Double Track: " << stats.num_double_track << "\n";
        std::cout << "    - High Speed: " << stats.num_high_speed << "\n";
    }
}

int main() {
    std::cout << "\n";
    std::cout << "╔═══════════════════════════════════════════════════════════════╗\n";
    std::cout << "║                                                               ║\n";
    std::cout << "║         FDC C++ - RAILWAY NETWORK EXAMPLE                     ║\n";
    std::cout << "║         Phase 2: Network Graph & Pathfinding                  ║\n";
    std::cout << "║                                                               ║\n";
    std::cout << "╚═══════════════════════════════════════════════════════════════╝\n";
    
    // Create network
    RailwayNetwork network;
    
    print_separator("STEP 1: Creating Italian Railway Network");
    
    // Create main stations
    Node milano("MI", "Milano Centrale", NodeType::STATION, 45.4864, 9.2041, 10, 10);
    Node bologna("BO", "Bologna Centrale", NodeType::INTERCHANGE, 44.5068, 11.3433, 8, 8);
    Node firenze("FI", "Firenze SMN", NodeType::STATION, 43.7763, 11.2476, 6, 6);
    Node roma("RM", "Roma Termini", NodeType::STATION, 41.9009, 12.5020, 12, 12);
    Node napoli("NA", "Napoli Centrale", NodeType::STATION, 40.8532, 14.2681, 8, 8);
    
    // Add nodes to network
    network.add_node(milano);
    network.add_node(bologna);
    network.add_node(firenze);
    network.add_node(roma);
    network.add_node(napoli);
    
    std::cout << "  ✓ Created 5 major stations\n";
    
    print_separator("STEP 2: Adding Track Connections");
    
    // Add high-speed connections (bidirectional)
    Edge mi_bo("MI", "BO", 218.0, 300.0, TrackType::HIGH_SPEED, 2);
    mi_bo.set_bidirectional(true);
    network.add_edge(mi_bo);
    std::cout << "  ✓ Milano → Bologna (218 km, 300 km/h, High Speed)\n";
    
    Edge bo_fi("BO", "FI", 80.0, 300.0, TrackType::HIGH_SPEED, 2);
    bo_fi.set_bidirectional(true);
    network.add_edge(bo_fi);
    std::cout << "  ✓ Bologna → Firenze (80 km, 300 km/h, High Speed)\n";
    
    Edge fi_rm("FI", "RM", 275.0, 300.0, TrackType::HIGH_SPEED, 2);
    fi_rm.set_bidirectional(true);
    network.add_edge(fi_rm);
    std::cout << "  ✓ Firenze → Roma (275 km, 300 km/h, High Speed)\n";
    
    Edge rm_na("RM", "NA", 225.0, 300.0, TrackType::HIGH_SPEED, 2);
    rm_na.set_bidirectional(true);
    network.add_edge(rm_na);
    std::cout << "  ✓ Roma → Napoli (225 km, 300 km/h, High Speed)\n";
    
    // Add some alternative routes (slower, double track)
    Edge mi_fi_alt("MI", "FI", 320.0, 200.0, TrackType::DOUBLE, 2);
    mi_fi_alt.set_bidirectional(true);
    network.add_edge(mi_fi_alt);
    std::cout << "  ✓ Milano → Firenze (320 km, 200 km/h, Double Track - Alternative)\n";
    
    print_separator("STEP 3: Network Statistics");
    
    auto stats = network.get_network_stats();
    print_network_stats(stats);
    
    std::cout << "\n  Network is connected: " 
              << (network.is_connected() ? "YES ✓" : "NO ✗") << "\n";
    
    print_separator("STEP 4: Pathfinding - Milano to Napoli");
    
    std::cout << "\n  Finding shortest path (by distance)...\n\n";
    auto path = network.find_shortest_path("MI", "NA", true);
    print_path(path);
    
    print_separator("STEP 5: Pathfinding - Milano to Firenze");
    
    std::cout << "\n  Note: Two possible routes exist!\n";
    std::cout << "    1. Direct: Milano → Firenze (320 km, slower)\n";
    std::cout << "    2. Via Bologna: Milano → Bologna → Firenze (298 km, faster)\n\n";
    
    std::cout << "  Finding shortest path...\n\n";
    auto path_mi_fi = network.find_shortest_path("MI", "FI", true);
    print_path(path_mi_fi);
    
    print_separator("STEP 6: Neighbor Analysis");
    
    std::cout << "\n  Neighbors of Bologna Centrale:\n";
    auto neighbors = network.get_neighbors("BO");
    for (const auto& neighbor : neighbors) {
        auto node = network.get_node(neighbor);
        std::cout << "    - " << node->get_name() << " (" << neighbor << ")\n";
    }
    
    print_separator("STEP 7: Distance Calculations");
    
    std::cout << "\n  Direct distances:\n";
    std::cout << "    Milano → Bologna: " << std::fixed << std::setprecision(1)
              << network.calculate_distance("MI", "BO") << " km\n";
    std::cout << "    Bologna → Firenze: " << std::fixed << std::setprecision(1)
              << network.calculate_distance("BO", "FI") << " km\n";
    std::cout << "    Firenze → Roma: " << std::fixed << std::setprecision(1)
              << network.calculate_distance("FI", "RM") << " km\n";
    std::cout << "    Roma → Napoli: " << std::fixed << std::setprecision(1)
              << network.calculate_distance("RM", "NA") << " km\n";
    
    print_separator("STEP 8: All Nodes in Network");
    
    std::cout << "\n";
    auto all_nodes = network.get_all_nodes();
    for (const auto& node : all_nodes) {
        std::cout << "  • " << node->get_name() << " (" << node->get_id() << ")\n";
        std::cout << "    Type: " << node_type_to_string(node->get_type()) << "\n";
        std::cout << "    Capacity: " << node->get_capacity() << " trains\n";
        std::cout << "    Platforms: " << node->get_platforms() << "\n";
        std::cout << "    Location: " << std::fixed << std::setprecision(4) 
                  << node->get_latitude() << "°N, " 
                  << node->get_longitude() << "°E\n\n";
    }
    
    print_separator("STEP 9: All Edges in Network");
    
    std::cout << "\n";
    auto all_edges = network.get_all_edges();
    for (const auto& edge : all_edges) {
        auto from_node = network.get_node(edge->get_from_node());
        auto to_node = network.get_node(edge->get_to_node());
        
        std::cout << "  • " << from_node->get_name() << " → " << to_node->get_name() << "\n";
        std::cout << "    Distance: " << std::fixed << std::setprecision(1) 
                  << edge->get_distance() << " km\n";
        std::cout << "    Max Speed: " << edge->get_max_speed() << " km/h\n";
        std::cout << "    Track Type: " << track_type_to_string(edge->get_track_type()) << "\n";
        std::cout << "    Bidirectional: " << (edge->is_bidirectional() ? "Yes" : "No") << "\n\n";
    }
    
    print_separator("SUMMARY");
    
    std::cout << "\n";
    std::cout << "  ✅ Successfully demonstrated:\n";
    std::cout << "     • Network creation with " << stats.num_nodes << " nodes\n";
    std::cout << "     • Adding " << stats.num_edges << " edges (bidirectional)\n";
    std::cout << "     • Dijkstra shortest path algorithm\n";
    std::cout << "     • Network connectivity analysis\n";
    std::cout << "     • Distance calculations\n";
    std::cout << "     • Neighbor discovery\n";
    std::cout << "     • Network statistics\n";
    std::cout << "\n";
    std::cout << "  🚀 Phase 2 Complete!\n";
    std::cout << "     RailwayNetwork with Boost.Graph is fully functional.\n";
    std::cout << "\n";
    
    std::cout << "╔═══════════════════════════════════════════════════════════════╗\n";
    std::cout << "║                                                               ║\n";
    std::cout << "║  Next Steps:                                                  ║\n";
    std::cout << "║  • Phase 3: Train Scheduling System                           ║\n";
    std::cout << "║  • Phase 4: JSON Serialization                                ║\n";
    std::cout << "║  • Phase 5: Qt GUI Implementation                             ║\n";
    std::cout << "║                                                               ║\n";
    std::cout << "╚═══════════════════════════════════════════════════════════════╝\n";
    std::cout << "\n";
    
    return 0;
}
