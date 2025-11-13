#include <iostream>
#include <iomanip>
#include <chrono>
#include <memory>
#include <vector>
#include "railway_network.hpp"
#include "schedule.hpp"
#include "train.hpp"
#include "node.hpp"
#include "edge.hpp"

using namespace fdc;
using namespace std::chrono;

// Helper per stampare orari in formato leggibile
std::string format_time(const system_clock::time_point& tp) {
    auto time_t = system_clock::to_time_t(tp);
    auto tm = *std::localtime(&time_t);
    
    std::ostringstream oss;
    oss << std::setfill('0') << std::setw(2) << tm.tm_hour << ":"
        << std::setfill('0') << std::setw(2) << tm.tm_min;
    return oss.str();
}

// Helper per creare time_point da ore e minuti
system_clock::time_point make_time(int hour, int minute) {
    auto now = system_clock::now();
    auto time_t = system_clock::to_time_t(now);
    auto tm = *std::localtime(&time_t);
    
    tm.tm_hour = hour;
    tm.tm_min = minute;
    tm.tm_sec = 0;
    
    return system_clock::from_time_t(std::mktime(&tm));
}

void print_header(const std::string& title) {
    std::cout << "\n╔═══════════════════════════════════════════════════════════════╗\n";
    std::cout << "║ " << std::left << std::setw(61) << title << " ║\n";
    std::cout << "╚═══════════════════════════════════════════════════════════════╝\n\n";
}

void print_separator() {
    std::cout << "───────────────────────────────────────────────────────────────\n";
}

int main() {
    try {
        print_header("🚄 FDC C++ - Scheduling System Demo");
        
        // ====================================================================
        // 1. CREAZIONE RETE FERROVIARIA
        // ====================================================================
        std::cout << "📊 STEP 1: Creazione Rete Ferroviaria\n";
        print_separator();
        
        auto network = std::make_shared<RailwayNetwork>();
        
        // Stazioni principali della Linea Alta Velocità Milano-Napoli
        auto milano = std::make_shared<Node>("MI", "Milano Centrale", NodeType::STATION, 
                                             45.4869, 9.2042, 24, 100);
        auto bologna = std::make_shared<Node>("BO", "Bologna Centrale", NodeType::INTERCHANGE,
                                              44.5057, 11.3426, 16, 80);
        auto firenze = std::make_shared<Node>("FI", "Firenze SMN", NodeType::STATION,
                                              43.7764, 11.2478, 19, 70);
        auto roma = std::make_shared<Node>("RM", "Roma Termini", NodeType::STATION,
                                          41.9009, 12.5028, 29, 120);
        auto napoli = std::make_shared<Node>("NA", "Napoli Centrale", NodeType::STATION,
                                            40.8535, 14.2736, 24, 90);
        
        network->add_node(milano);
        network->add_node(bologna);
        network->add_node(firenze);
        network->add_node(roma);
        network->add_node(napoli);
        
        // Tratte Alta Velocità
        auto mi_bo = std::make_shared<Edge>("MI_BO", milano, bologna, 218.0, 300.0, 
                                           TrackType::HIGH_SPEED, 20, true);
        auto bo_fi = std::make_shared<Edge>("BO_FI", bologna, firenze, 80.0, 300.0,
                                           TrackType::HIGH_SPEED, 20, true);
        auto fi_rm = std::make_shared<Edge>("FI_RM", firenze, roma, 275.0, 300.0,
                                           TrackType::HIGH_SPEED, 20, true);
        auto rm_na = std::make_shared<Edge>("RM_NA", roma, napoli, 225.0, 300.0,
                                           TrackType::HIGH_SPEED, 20, true);
        
        network->add_edge(mi_bo);
        network->add_edge(bo_fi);
        network->add_edge(fi_rm);
        network->add_edge(rm_na);
        
        std::cout << "✓ Rete creata: " << network->node_count() << " stazioni, "
                  << network->edge_count() << " tratte\n";
        std::cout << "✓ Distanza totale: " << std::fixed << std::setprecision(1)
                  << network->calculate_distance({"MI", "BO", "FI", "RM", "NA"}) << " km\n";
        
        // ====================================================================
        // 2. CREAZIONE TRENI
        // ====================================================================
        std::cout << "\n📊 STEP 2: Definizione Treni\n";
        print_separator();
        
        auto frecciarossa_1000 = std::make_shared<Train>("FR9612", "Frecciarossa", 
                                                         TrainType::HIGH_SPEED, 300.0, 600);
        auto frecciarossa_500 = std::make_shared<Train>("FR9654", "Frecciarossa",
                                                        TrainType::HIGH_SPEED, 300.0, 500);
        
        std::cout << "✓ Treno 1: " << frecciarossa_1000->get_name() << " (ID: " 
                  << frecciarossa_1000->get_id() << ")\n";
        std::cout << "  - Velocità max: " << frecciarossa_1000->get_max_speed() << " km/h\n";
        std::cout << "  - Capacità: " << frecciarossa_1000->get_capacity() << " posti\n\n";
        
        std::cout << "✓ Treno 2: " << frecciarossa_500->get_name() << " (ID: " 
                  << frecciarossa_500->get_id() << ")\n";
        std::cout << "  - Velocità max: " << frecciarossa_500->get_max_speed() << " km/h\n";
        std::cout << "  - Capacità: " << frecciarossa_500->get_capacity() << " posti\n";
        
        // ====================================================================
        // 3. COSTRUZIONE ORARI CON SCHEDULEBUILDER
        // ====================================================================
        std::cout << "\n📊 STEP 3: Costruzione Orari Automatica\n";
        print_separator();
        
        // ORARIO 1: FR9612 Milano → Napoli partenza ore 08:00
        auto builder1 = ScheduleBuilder("FR9612", "SCH_FR9612_001", network, frecciarossa_1000);
        
        auto start_time_1 = make_time(8, 0); // 08:00
        
        builder1.set_start_time(start_time_1)
                .enable_auto_platform_assignment(true)
                .add_stop_with_dwell("MI", minutes(0))      // Partenza immediata
                .add_stop_auto("BO", minutes(3))             // Bologna: 3 min sosta
                .add_stop_auto("FI", minutes(2))             // Firenze: 2 min sosta
                .add_stop_auto("RM", minutes(5))             // Roma: 5 min sosta
                .add_stop_auto("NA", minutes(0));            // Napoli: arrivo finale
        
        auto schedule1 = builder1.build();
        
        std::cout << "✓ ORARIO 1 - " << schedule1->get_train_id() << " (Milano → Napoli)\n";
        std::cout << "  Partenza: " << format_time(schedule1->get_stop(0).get_arrival()) << "\n";
        std::cout << "  Fermate:\n";
        
        for (size_t i = 0; i < schedule1->get_stop_count(); ++i) {
            const auto& stop = schedule1->get_stop(i);
            auto node = network->get_node(stop.get_node_id());
            
            std::cout << "    " << (i+1) << ". " << std::setw(20) << std::left << node->get_name()
                      << " | Arr: " << format_time(stop.get_arrival())
                      << " | Dep: " << format_time(stop.get_departure());
            
            if (stop.get_platform().has_value()) {
                std::cout << " | Bin: " << stop.get_platform().value();
            }
            std::cout << "\n";
        }
        
        std::cout << "\n  Durata totale: " << schedule1->get_total_duration().count() / 60 << " minuti\n";
        std::cout << "  Distanza: " << std::fixed << std::setprecision(1) 
                  << schedule1->get_total_distance() << " km\n";
        std::cout << "  Velocità media: " << std::fixed << std::setprecision(1)
                  << schedule1->get_average_speed() << " km/h\n";
        
        // ORARIO 2: FR9654 Milano → Napoli partenza ore 08:15 (POSSIBILE CONFLITTO!)
        std::cout << "\n";
        auto builder2 = ScheduleBuilder("FR9654", "SCH_FR9654_001", network, frecciarossa_500);
        
        auto start_time_2 = make_time(8, 15); // 08:15 (15 minuti dopo il primo)
        
        builder2.set_start_time(start_time_2)
                .enable_auto_platform_assignment(true)
                .add_stop_with_dwell("MI", minutes(0))
                .add_stop_auto("BO", minutes(3))
                .add_stop_auto("FI", minutes(2))
                .add_stop_auto("RM", minutes(5))
                .add_stop_auto("NA", minutes(0));
        
        auto schedule2 = builder2.build();
        
        std::cout << "✓ ORARIO 2 - " << schedule2->get_train_id() << " (Milano → Napoli)\n";
        std::cout << "  Partenza: " << format_time(schedule2->get_stop(0).get_arrival()) << "\n";
        std::cout << "  Fermate:\n";
        
        for (size_t i = 0; i < schedule2->get_stop_count(); ++i) {
            const auto& stop = schedule2->get_stop(i);
            auto node = network->get_node(stop.get_node_id());
            
            std::cout << "    " << (i+1) << ". " << std::setw(20) << std::left << node->get_name()
                      << " | Arr: " << format_time(stop.get_arrival())
                      << " | Dep: " << format_time(stop.get_departure());
            
            if (stop.get_platform().has_value()) {
                std::cout << " | Bin: " << stop.get_platform().value();
            }
            std::cout << "\n";
        }
        
        std::cout << "\n  Durata totale: " << schedule2->get_total_duration().count() / 60 << " minuti\n";
        std::cout << "  Distanza: " << std::fixed << std::setprecision(1)
                  << schedule2->get_total_distance() << " km\n";
        std::cout << "  Velocità media: " << std::fixed << std::setprecision(1)
                  << schedule2->get_average_speed() << " km/h\n";
        
        // ====================================================================
        // 4. RILEVAMENTO CONFLITTI
        // ====================================================================
        std::cout << "\n📊 STEP 4: Rilevamento Conflitti tra Orari\n";
        print_separator();
        
        if (schedule1->has_conflict_with(*schedule2)) {
            std::cout << "⚠️  CONFLITTO RILEVATO!\n";
            std::cout << "   Gli orari " << schedule1->get_schedule_id() << " e "
                      << schedule2->get_schedule_id() << " hanno conflitti.\n\n";
            
            // Trova stazioni con conflitti
            std::vector<std::string> nodes = {"MI", "BO", "FI", "RM", "NA"};
            for (const auto& node_id : nodes) {
                if (schedule1->has_time_overlap_with(*schedule2, node_id)) {
                    auto node = network->get_node(node_id);
                    std::cout << "   - Conflitto a: " << node->get_name() << "\n";
                    
                    auto idx1 = schedule1->find_stop_index(node_id);
                    auto idx2 = schedule2->find_stop_index(node_id);
                    
                    if (idx1.has_value() && idx2.has_value()) {
                        const auto& stop1 = schedule1->get_stop(idx1.value());
                        const auto& stop2 = schedule2->get_stop(idx2.value());
                        
                        if (stop1.get_platform() == stop2.get_platform()) {
                            std::cout << "     * STESSO BINARIO: " << stop1.get_platform().value() << "\n";
                        }
                        
                        std::cout << "     * Treno 1: " << format_time(stop1.get_arrival())
                                  << " - " << format_time(stop1.get_departure()) << "\n";
                        std::cout << "     * Treno 2: " << format_time(stop2.get_arrival())
                                  << " - " << format_time(stop2.get_departure()) << "\n";
                    }
                }
            }
        } else {
            std::cout << "✓ Nessun conflitto rilevato tra gli orari.\n";
        }
        
        // ====================================================================
        // 5. GESTIONE ORARI CON SCHEDULEMANAGER
        // ====================================================================
        std::cout << "\n📊 STEP 5: ScheduleManager - Gestione Collezione Orari\n";
        print_separator();
        
        auto manager = ScheduleManager(network);
        manager.add_schedule(schedule1);
        manager.add_schedule(schedule2);
        
        std::cout << "✓ Orari registrati: " << manager.get_schedule_count() << "\n\n";
        
        // Trova tutti i conflitti
        auto conflicts = manager.find_all_conflicts();
        
        if (!conflicts.empty()) {
            std::cout << "⚠️  Conflitti trovati: " << conflicts.size() << "\n";
            for (const auto& [id1, id2] : conflicts) {
                std::cout << "   - " << id1 << " ↔ " << id2 << "\n";
            }
        } else {
            std::cout << "✓ Nessun conflitto nella collezione di orari.\n";
        }
        
        // Query: orari che passano da Bologna
        std::cout << "\n📍 Orari che passano da Bologna Centrale:\n";
        auto schedules_at_bo = manager.get_schedules_at_node("BO");
        
        for (const auto& sched : schedules_at_bo) {
            auto stop_idx = sched->find_stop_index("BO");
            if (stop_idx.has_value()) {
                const auto& stop = sched->get_stop(stop_idx.value());
                std::cout << "   - " << sched->get_train_id() 
                          << ": arr " << format_time(stop.get_arrival())
                          << ", dep " << format_time(stop.get_departure()) << "\n";
            }
        }
        
        // ====================================================================
        // 6. VALIDAZIONE ORARI
        // ====================================================================
        std::cout << "\n📊 STEP 6: Validazione Orari\n";
        print_separator();
        
        std::cout << "Orario 1 (" << schedule1->get_schedule_id() << "):\n";
        std::cout << "  ✓ Cronologia: " << (schedule1->validate_chronological() ? "OK" : "ERRORE") << "\n";
        std::cout << "  ✓ Rete: " << (schedule1->validate_network() ? "OK" : "ERRORE") << "\n";
        std::cout << "  ✓ Binari: " << (schedule1->validate_platforms() ? "OK" : "ERRORE") << "\n";
        std::cout << "  ✓ Validazione complessiva: " << (schedule1->is_valid() ? "VALIDO" : "NON VALIDO") << "\n\n";
        
        std::cout << "Orario 2 (" << schedule2->get_schedule_id() << "):\n";
        std::cout << "  ✓ Cronologia: " << (schedule2->validate_chronological() ? "OK" : "ERRORE") << "\n";
        std::cout << "  ✓ Rete: " << (schedule2->validate_network() ? "OK" : "ERRORE") << "\n";
        std::cout << "  ✓ Binari: " << (schedule2->validate_platforms() ? "OK" : "ERRORE") << "\n";
        std::cout << "  ✓ Validazione complessiva: " << (schedule2->is_valid() ? "VALIDO" : "NON VALIDO") << "\n";
        
        // ====================================================================
        // RIEPILOGO FINALE
        // ====================================================================
        print_header("✅ Demo Completata!");
        
        std::cout << "📈 RIEPILOGO SISTEMA:\n";
        std::cout << "   • Stazioni: " << network->node_count() << "\n";
        std::cout << "   • Tratte: " << network->edge_count() << "\n";
        std::cout << "   • Treni: 2\n";
        std::cout << "   • Orari: " << manager.get_schedule_count() << "\n";
        std::cout << "   • Conflitti: " << conflicts.size() << "\n\n";
        
        std::cout << "🎯 FUNZIONALITÀ DIMOSTRATE:\n";
        std::cout << "   ✓ ScheduleStop: fermate con orari e binari\n";
        std::cout << "   ✓ TrainSchedule: orari completi con validazione\n";
        std::cout << "   ✓ ScheduleBuilder: costruzione automatica orari\n";
        std::cout << "   ✓ Conflict detection: rilevamento sovrapposizioni\n";
        std::cout << "   ✓ Platform management: assegnazione binari\n";
        std::cout << "   ✓ ScheduleManager: gestione collezioni\n";
        std::cout << "   ✓ Query e statistiche avanzate\n\n";
        
        std::cout << "🚀 FASE 3 COMPLETATA!\n\n";
        
        return 0;
        
    } catch (const std::exception& e) {
        std::cerr << "❌ ERRORE: " << e.what() << std::endl;
        return 1;
    }
}
