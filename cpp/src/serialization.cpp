#include "serialization.hpp"
#include "node.hpp"
#include "edge.hpp"
#include "train.hpp"
#include <fstream>
#include <stdexcept>

namespace fdc {

nlohmann::json railway_network_to_json(const RailwayNetwork& network) {
    nlohmann::json j;
    
    // Serialize nodes
    nlohmann::json nodes_json = nlohmann::json::array();
    auto all_nodes = network.get_all_nodes();
    for (const auto& node_ptr : all_nodes) {
        nlohmann::json node_json;
        to_json(node_json, *node_ptr);
        nodes_json.push_back(node_json);
    }
    j["nodes"] = nodes_json;
    
    // Serialize edges
    nlohmann::json edges_json = nlohmann::json::array();
    auto all_edges = network.get_all_edges();
    for (const auto& edge_ptr : all_edges) {
        nlohmann::json edge_json;
        to_json(edge_json, *edge_ptr);
        edges_json.push_back(edge_json);
    }
    j["edges"] = edges_json;
    
    // Add metadata
    auto stats = network.get_network_stats();
    j["metadata"] = {
        {"num_nodes", stats.num_nodes},
        {"num_edges", stats.num_edges},
        {"total_track_length", stats.total_track_length}
    };
    
    return j;
}

std::shared_ptr<RailwayNetwork> railway_network_from_json(const nlohmann::json& j) {
    auto network = std::make_shared<RailwayNetwork>();
    
    // Deserialize nodes
    if (j.contains("nodes")) {
        for (const auto& node_json : j["nodes"]) {
            Node node("", "");  // Temporary, will be overwritten by from_json
            from_json(node_json, node);
            network->add_node(node);
        }
    }
    
    // Deserialize edges
    if (j.contains("edges")) {
        for (const auto& edge_json : j["edges"]) {
            Edge edge("", "", 0.0);  // Temporary, will be overwritten by from_json
            from_json(edge_json, edge);
            network->add_edge(edge);
        }
    }
    
    return network;
}

void save_network_to_file(const RailwayNetwork& network, const std::string& filename) {
    try {
        nlohmann::json j = railway_network_to_json(network);
        
        std::ofstream file(filename);
        if (!file.is_open()) {
            throw std::runtime_error("Cannot open file for writing: " + filename);
        }
        
        file << j.dump(2);  // Pretty print with 2-space indentation
        file.close();
        
    } catch (const std::exception& e) {
        throw std::runtime_error("Failed to save network to file: " + std::string(e.what()));
    }
}

std::shared_ptr<RailwayNetwork> load_network_from_file(const std::string& filename) {
    try {
        std::ifstream file(filename);
        if (!file.is_open()) {
            throw std::runtime_error("Cannot open file for reading: " + filename);
        }
        
        nlohmann::json j;
        file >> j;
        file.close();
        
        return railway_network_from_json(j);
        
    } catch (const std::exception& e) {
        throw std::runtime_error("Failed to load network from file: " + std::string(e.what()));
    }
}

void save_schedules_to_file(
    const std::vector<std::shared_ptr<TrainSchedule>>& schedules,
    const std::string& filename) {
    
    try {
        nlohmann::json j = nlohmann::json::array();
        
        for (const auto& schedule : schedules) {
            nlohmann::json schedule_json;
            to_json(schedule_json, *schedule);
            j.push_back(schedule_json);
        }
        
        std::ofstream file(filename);
        if (!file.is_open()) {
            throw std::runtime_error("Cannot open file for writing: " + filename);
        }
        
        file << j.dump(2);
        file.close();
        
    } catch (const std::exception& e) {
        throw std::runtime_error("Failed to save schedules to file: " + std::string(e.what()));
    }
}

std::vector<std::shared_ptr<TrainSchedule>> load_schedules_from_file(
    const std::string& filename,
    std::shared_ptr<RailwayNetwork> network) {
    
    try {
        std::ifstream file(filename);
        if (!file.is_open()) {
            throw std::runtime_error("Cannot open file for reading: " + filename);
        }
        
        nlohmann::json j;
        file >> j;
        file.close();
        
        std::vector<std::shared_ptr<TrainSchedule>> schedules;
        
        if (j.is_array()) {
            for (const auto& schedule_json : j) {
                auto schedule = train_schedule_from_json(schedule_json, network);
                schedules.push_back(schedule);
            }
        }
        
        return schedules;
        
    } catch (const std::exception& e) {
        throw std::runtime_error("Failed to load schedules from file: " + std::string(e.what()));
    }
}

} // namespace fdc
