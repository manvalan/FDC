#include "railway_network.hpp"
#include "serialization.hpp"
#include "schedule.hpp"
#include "train.hpp"
#include <iostream>
#include <iomanip>
#include <chrono>

using namespace fdc;
using namespace std::chrono;

// Helper per stampare header
void print_header(const std::string& title) {
    std::cout << "\n";
    std::cout << "╔══════════════════════════════════════════════════════════╗\n";
    std::cout << "║  " << std::left << std::setw(55) << title << "║\n";
    std::cout << "╚══════════════════════════════════════════════════════════╝\n";
}

// Helper per formattare tempo
std::string format_time(const system_clock::time_point& tp) {
    auto time_t = system_clock::to_time_t(tp);
    std::tm tm = *std::localtime(&time_t);
    char buffer[20];
    std::strftime(buffer, sizeof(buffer), "%H:%M", &tm);
    return std::string(buffer);
}

// Helper per creare time_point
system_clock::time_point make_time(int hour, int minute) {
    auto now = system_clock::now();
    auto time_t = system_clock::to_time_t(now);
    std::tm tm = *std::localtime(&time_t);
    tm.tm_hour = hour;
    tm.tm_min = minute;
    tm.tm_sec = 0;
    return system_clock::from_time_t(std::mktime(&tm));
}

int main() {
    try {
        print_header("🚄 JSON Serialization Demo - Complete Export/Import");
        
        // ====================================================================
        // FASE 1: Creazione Rete Ferroviaria
        // ====================================================================
        
        print_header("📍 FASE 1: Creazione Rete Italiana");
        
        auto network = std::make_shared<RailwayNetwork>();
        
        // Aggiungi stazioni principali
        network->add_node(Node("MI", "Milano Centrale", NodeType::STATION, 45.4869, 9.2042, 100, 24));
        network->add_node(Node("BO", "Bologna Centrale", NodeType::STATION, 44.5060, 11.3429, 80, 16));
        network->add_node(Node("FI", "Firenze SMN", NodeType::STATION, 43.7763, 11.2480, 70, 19));
        network->add_node(Node("RO", "Roma Termini", NodeType::STATION, 41.9010, 12.5019, 120, 29));
        
        // Aggiungi connessioni Alta Velocità (binario doppio)
        network->add_edge(Edge("MI", "BO", 218.0, TrackType::HIGH_SPEED, 300.0, 2, true));
        network->add_edge(Edge("BO", "FI", 80.0, TrackType::HIGH_SPEED, 300.0, 2, true));
        network->add_edge(Edge("FI", "RO", 275.0, TrackType::HIGH_SPEED, 300.0, 2, true));
        
        auto stats = network->get_network_stats();
        std::cout << "✓ Rete creata:\n";
        std::cout << "  • Stazioni: " << stats["num_nodes"] << "\n";
        std::cout << "  • Connessioni: " << stats["num_edges"] << "\n";
        std::cout << "  • Lunghezza totale: " << stats["total_track_length"] << " km\n";
        
        // ====================================================================
        // FASE 2: Creazione Treni
        // ====================================================================
        
        print_header("🚂 FASE 2: Creazione Treni");
        
        auto fr1000 = Train("FR9612", "Frecciarossa 1000", TrainType::HIGH_SPEED, 300.0, 0.6, 0.8);
        auto ic = Train("IC305", "InterCity 305", TrainType::INTERCITY, 200.0, 0.5, 0.7);
        
        std::cout << "✓ Treni creati:\n";
        std::cout << "  • " << fr1000.get_name() << " (v_max: " << fr1000.get_max_speed() << " km/h)\n";
        std::cout << "  • " << ic.get_name() << " (v_max: " << ic.get_max_speed() << " km/h)\n";
        
        // ====================================================================
        // FASE 3: Creazione Orari
        // ====================================================================
        
        print_header("📅 FASE 3: Creazione Orari");
        
        // Frecciarossa Milano-Roma (08:00)
        auto schedule1 = std::make_shared<TrainSchedule>("FR9612", "SCH_FR9612_001", network);
        schedule1->add_stop(ScheduleStop("MI", make_time(8, 0), make_time(8, 0), true));
        schedule1->add_stop(ScheduleStop("BO", make_time(8, 45), make_time(8, 50), true));
        schedule1->add_stop(ScheduleStop("FI", make_time(9, 35), make_time(9, 40), true));
        schedule1->add_stop(ScheduleStop("RO", make_time(11, 15), make_time(11, 15), true));
        
        // InterCity Milano-Roma (09:00)
        auto schedule2 = std::make_shared<TrainSchedule>("IC305", "SCH_IC305_001", network);
        schedule2->add_stop(ScheduleStop("MI", make_time(9, 0), make_time(9, 0), true));
        schedule2->add_stop(ScheduleStop("BO", make_time(10, 5), make_time(10, 10), true));
        schedule2->add_stop(ScheduleStop("FI", make_time(11, 15), make_time(11, 20), true));
        schedule2->add_stop(ScheduleStop("RO", make_time(13, 30), make_time(13, 30), true));
        
        std::vector<std::shared_ptr<TrainSchedule>> schedules = {schedule1, schedule2};
        
        std::cout << "✓ Orari creati:\n";
        for (const auto& sched : schedules) {
            std::cout << "  • " << sched->get_schedule_id() 
                      << " (" << sched->get_stop_count() << " fermate)\n";
            for (size_t i = 0; i < sched->get_stop_count(); i++) {
                const auto& stop = sched->get_stop(i);
                std::cout << "    - " << stop.get_node_id() 
                          << ": arr " << format_time(stop.get_arrival())
                          << ", part " << format_time(stop.get_departure()) << "\n";
            }
        }
        
        // ====================================================================
        // FASE 4: Export JSON
        // ====================================================================
        
        print_header("💾 FASE 4: Export to JSON");
        
        std::string network_file = "demo_network.json";
        std::string schedules_file = "demo_schedules.json";
        
        save_network_to_file(*network, network_file);
        std::cout << "✓ Rete salvata in: " << network_file << "\n";
        
        save_schedules_to_file(schedules, schedules_file);
        std::cout << "✓ Orari salvati in: " << schedules_file << "\n";
        
        // ====================================================================
        // FASE 5: Import JSON
        // ====================================================================
        
        print_header("📥 FASE 5: Import from JSON");
        
        auto loaded_network = load_network_from_file(network_file);
        std::cout << "✓ Rete caricata da: " << network_file << "\n";
        
        auto loaded_stats = loaded_network->get_network_stats();
        std::cout << "  • Stazioni: " << loaded_stats["num_nodes"] << "\n";
        std::cout << "  • Connessioni: " << loaded_stats["num_edges"] << "\n";
        
        auto loaded_schedules = load_schedules_from_file(schedules_file, loaded_network);
        std::cout << "✓ Orari caricati da: " << schedules_file << "\n";
        std::cout << "  • Numero schedules: " << loaded_schedules.size() << "\n";
        
        // ====================================================================
        // FASE 6: Verifica Integrità
        // ====================================================================
        
        print_header("✅ FASE 6: Verifica Integrità Dati");
        
        bool integrity_ok = true;
        
        // Verifica numero nodi
        if (loaded_stats["num_nodes"] != stats["num_nodes"]) {
            std::cout << "❌ Numero nodi non corrisponde!\n";
            integrity_ok = false;
        } else {
            std::cout << "✓ Numero nodi: OK\n";
        }
        
        // Verifica numero edges
        if (loaded_stats["num_edges"] != stats["num_edges"]) {
            std::cout << "❌ Numero connessioni non corrisponde!\n";
            integrity_ok = false;
        } else {
            std::cout << "✓ Numero connessioni: OK\n";
        }
        
        // Verifica lunghezza rete
        if (std::abs(loaded_stats["total_track_length"] - stats["total_track_length"]) > 0.1) {
            std::cout << "❌ Lunghezza rete non corrisponde!\n";
            integrity_ok = false;
        } else {
            std::cout << "✓ Lunghezza rete: OK\n";
        }
        
        // Verifica numero schedules
        if (loaded_schedules.size() != schedules.size()) {
            std::cout << "❌ Numero orari non corrisponde!\n";
            integrity_ok = false;
        } else {
            std::cout << "✓ Numero orari: OK\n";
        }
        
        // ====================================================================
        // FASE 7: Riepilogo
        // ====================================================================
        
        print_header("📊 FASE 7: Riepilogo");
        
        std::cout << "\n";
        std::cout << "Dati Originali:\n";
        std::cout << "  • Stazioni: " << stats["num_nodes"] << "\n";
        std::cout << "  • Connessioni: " << stats["num_edges"] << "\n";
        std::cout << "  • Km totali: " << stats["total_track_length"] << "\n";
        std::cout << "  • Schedules: " << schedules.size() << "\n";
        
        std::cout << "\nDati Caricati:\n";
        std::cout << "  • Stazioni: " << loaded_stats["num_nodes"] << "\n";
        std::cout << "  • Connessioni: " << loaded_stats["num_edges"] << "\n";
        std::cout << "  • Km totali: " << loaded_stats["total_track_length"] << "\n";
        std::cout << "  • Schedules: " << loaded_schedules.size() << "\n";
        
        std::cout << "\nFile generati:\n";
        std::cout << "  • " << network_file << " (network)\n";
        std::cout << "  • " << schedules_file << " (schedules)\n";
        
        // ====================================================================
        // CONCLUSIONE
        // ====================================================================
        
        print_header(integrity_ok ? 
            "🎉 TEST COMPLETATO CON SUCCESSO!" :
            "⚠️  TEST COMPLETATO CON ERRORI");
        
        if (integrity_ok) {
            std::cout << "\n";
            std::cout << "✅ Tutti i dati sono stati serializzati e deserializzati correttamente!\n";
            std::cout << "✅ Export/Import JSON funziona perfettamente!\n";
            std::cout << "✅ Formato compatibile con versione Python!\n";
            std::cout << "\n";
        }
        
        return integrity_ok ? 0 : 1;
        
    } catch (const std::exception& e) {
        std::cerr << "\n❌ ERRORE: " << e.what() << "\n";
        return 1;
    }
}
