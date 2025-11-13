#include "node.hpp"
#include "edge.hpp"
#include "train.hpp"
#include <iostream>
#include <iomanip>

using namespace fdc;

int main() {
    std::cout << "=== FDC C++ Railway System - Basic Example ===\n\n";
    
    // Create stations
    std::cout << "Creating stations...\n";
    Node milano("MI", "Milano Centrale", NodeType::STATION,
                45.4864, 9.2040, 10, 8);
    Node bologna("BO", "Bologna Centrale", NodeType::STATION,
                 44.5058, 11.3427, 8, 6);
    Node firenze("FI", "Firenze SMN", NodeType::STATION,
                 43.7762, 11.2480, 7, 5);
    Node roma("RO", "Roma Termini", NodeType::STATION,
              41.9009, 12.5023, 12, 10);
    
    std::cout << "  ✓ " << milano.get_name() << " (" << milano.get_platforms() << " platforms)\n";
    std::cout << "  ✓ " << bologna.get_name() << " (" << bologna.get_platforms() << " platforms)\n";
    std::cout << "  ✓ " << firenze.get_name() << " (" << firenze.get_platforms() << " platforms)\n";
    std::cout << "  ✓ " << roma.get_name() << " (" << roma.get_platforms() << " platforms)\n\n";
    
    // Create tracks
    std::cout << "Creating high-speed tracks...\n";
    Edge track_mi_bo("MI", "BO", 218.0, TrackType::HIGH_SPEED, 300.0);
    Edge track_bo_fi("BO", "FI", 80.0, TrackType::HIGH_SPEED, 250.0);
    Edge track_fi_ro("FI", "RO", 275.0, TrackType::HIGH_SPEED, 300.0);
    
    std::cout << "  ✓ Milano - Bologna: " << track_mi_bo.get_distance() << " km "
              << "(max " << track_mi_bo.get_max_speed() << " km/h)\n";
    std::cout << "  ✓ Bologna - Firenze: " << track_bo_fi.get_distance() << " km "
              << "(max " << track_bo_fi.get_max_speed() << " km/h)\n";
    std::cout << "  ✓ Firenze - Roma: " << track_fi_ro.get_distance() << " km "
              << "(max " << track_fi_ro.get_max_speed() << " km/h)\n\n";
    
    // Create trains
    std::cout << "Creating trains...\n";
    Train frecciarossa = Train::create_by_type("FR1000", "Frecciarossa 1000", 
                                               TrainType::HIGH_SPEED);
    Train intercity = Train::create_by_type("IC595", "InterCity 595", 
                                            TrainType::INTERCITY);
    Train regionale = Train::create_by_type("REG2301", "Regionale 2301", 
                                            TrainType::REGIONAL);
    
    std::cout << "  ✓ " << frecciarossa.get_name() 
              << " (max " << frecciarossa.get_max_speed() << " km/h)\n";
    std::cout << "  ✓ " << intercity.get_name() 
              << " (max " << intercity.get_max_speed() << " km/h)\n";
    std::cout << "  ✓ " << regionale.get_name() 
              << " (max " << regionale.get_max_speed() << " km/h)\n\n";
    
    // Calculate travel times
    std::cout << "=== Travel Time Calculations ===\n\n";
    std::cout << std::fixed << std::setprecision(2);
    
    // Milano - Roma route
    double total_distance = track_mi_bo.get_distance() + 
                           track_bo_fi.get_distance() + 
                           track_fi_ro.get_distance();
    
    std::cout << "Route: Milano → Bologna → Firenze → Roma\n";
    std::cout << "Total distance: " << total_distance << " km\n\n";
    
    // Frecciarossa times
    double fr_time_mi_bo = frecciarossa.calculate_travel_time(
        track_mi_bo.get_distance(), track_mi_bo.get_max_speed());
    double fr_time_bo_fi = frecciarossa.calculate_travel_time(
        track_bo_fi.get_distance(), track_bo_fi.get_max_speed());
    double fr_time_fi_ro = frecciarossa.calculate_travel_time(
        track_fi_ro.get_distance(), track_fi_ro.get_max_speed());
    double fr_total = fr_time_mi_bo + fr_time_bo_fi + fr_time_fi_ro;
    
    std::cout << "Frecciarossa 1000:\n";
    std::cout << "  Milano → Bologna:  " << (fr_time_mi_bo * 60) << " min\n";
    std::cout << "  Bologna → Firenze: " << (fr_time_bo_fi * 60) << " min\n";
    std::cout << "  Firenze → Roma:    " << (fr_time_fi_ro * 60) << " min\n";
    std::cout << "  TOTAL: " << (fr_total * 60) << " min "
              << "(" << (int)(fr_total) << "h " 
              << (int)((fr_total - (int)fr_total) * 60) << "m)\n\n";
    
    // InterCity times
    double ic_time_mi_bo = intercity.calculate_travel_time(
        track_mi_bo.get_distance(), track_mi_bo.get_max_speed());
    double ic_time_bo_fi = intercity.calculate_travel_time(
        track_bo_fi.get_distance(), track_bo_fi.get_max_speed());
    double ic_time_fi_ro = intercity.calculate_travel_time(
        track_fi_ro.get_distance(), track_fi_ro.get_max_speed());
    double ic_total = ic_time_mi_bo + ic_time_bo_fi + ic_time_fi_ro;
    
    std::cout << "InterCity 595:\n";
    std::cout << "  Milano → Bologna:  " << (ic_time_mi_bo * 60) << " min\n";
    std::cout << "  Bologna → Firenze: " << (ic_time_bo_fi * 60) << " min\n";
    std::cout << "  Firenze → Roma:    " << (ic_time_fi_ro * 60) << " min\n";
    std::cout << "  TOTAL: " << (ic_total * 60) << " min "
              << "(" << (int)(ic_total) << "h " 
              << (int)((ic_total - (int)ic_total) * 60) << "m)\n\n";
    
    // Regional times
    double reg_time_mi_bo = regionale.calculate_travel_time(
        track_mi_bo.get_distance(), track_mi_bo.get_max_speed());
    double reg_time_bo_fi = regionale.calculate_travel_time(
        track_bo_fi.get_distance(), track_bo_fi.get_max_speed());
    double reg_time_fi_ro = regionale.calculate_travel_time(
        track_fi_ro.get_distance(), track_fi_ro.get_max_speed());
    double reg_total = reg_time_mi_bo + reg_time_bo_fi + reg_time_fi_ro;
    
    std::cout << "Regionale 2301:\n";
    std::cout << "  Milano → Bologna:  " << (reg_time_mi_bo * 60) << " min\n";
    std::cout << "  Bologna → Firenze: " << (reg_time_bo_fi * 60) << " min\n";
    std::cout << "  Firenze → Roma:    " << (reg_time_fi_ro * 60) << " min\n";
    std::cout << "  TOTAL: " << (reg_total * 60) << " min "
              << "(" << (int)(reg_total) << "h " 
              << (int)((reg_total - (int)reg_total) * 60) << "m)\n\n";
    
    // Time savings
    std::cout << "Time saved by Frecciarossa vs Regional: " 
              << ((reg_total - fr_total) * 60) << " minutes\n\n";
    
    std::cout << "✓ Example completed successfully!\n";
    
    return 0;
}
