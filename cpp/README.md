# FDC C++ - Railway Network Management System

Riscrittura in C++ del sistema di gestione reti ferroviarie FDC.

## 🎯 Stato del Progetto

**WORK IN PROGRESS** - Riscrittura da Python a C++ in corso

### ✅ Completato
- [x] Struttura progetto CMake
- [x] Classi base: `Node`, `Edge`, `Train`
- [x] Enumerazioni: `NodeType`, `TrackType`, `TrainType`
- [x] Gestione piattaforme e prenotazioni
- [x] Calcoli fisici realistici movimento treni
- [x] Classe `RailwayNetwork` con Boost.Graph
- [x] Algoritmo Dijkstra per shortest path
- [x] Pathfinding e analisi rete
- [x] Sistema Scheduling: `ScheduleStop`, `TrainSchedule`, `ScheduleBuilder`, `ScheduleManager`
- [x] Conflict detection tra orari
- [x] Costruzione automatica orari con calcolo tempi
- [x] **JSON Serialization/Deserialization completo**
- [x] Export/Import Network e Schedules su file
- [x] Formato compatibile con versione Python

### 🚧 In Lavorazione
- [ ] Interfaccia GUI con Qt6
- [ ] Visualizzazioni grafiche (network map, time-distance diagram)
- [ ] Database MySQL (opzionale)

## 📋 Requisiti

### Obbligatori
- **C++17** o superiore
- **CMake** 3.15+
- **Boost** 1.70+ (Boost.Graph)
- **nlohmann/json** (scaricato automaticamente da CMake)

### Opzionali
- **Qt6** o **Qt5** 5.15+ (per GUI)
- **MySQL Connector/C++** (per database)
- **Google Test** (per unit tests)

## 🚀 Compilazione

### macOS

```bash
# Installa dipendenze con Homebrew
brew install cmake boost qt6

# Crea directory di build
mkdir build && cd build

# Configura progetto
cmake .. -DBUILD_GUI=ON -DBUILD_TESTS=ON

# Compila
cmake --build . -j8

# Esegui tests
ctest --output-on-failure
```

### Linux (Ubuntu/Debian)

```bash
# Installa dipendenze
sudo apt update
sudo apt install cmake libboost-all-dev qt6-base-dev

# Crea directory di build
mkdir build && cd build

# Configura progetto
cmake .. -DBUILD_GUI=ON -DBUILD_TESTS=ON

# Compila
cmake --build . -j$(nproc)

# Esegui tests
ctest --output-on-failure
```

### Windows (Visual Studio)

```bash
# Installa vcpkg per dipendenze
vcpkg install boost nlohmann-json qt6

# Crea directory di build
mkdir build && cd build

# Configura progetto
cmake .. -DCMAKE_TOOLCHAIN_FILE=[vcpkg root]/scripts/buildsystems/vcpkg.cmake

# Compila
cmake --build . --config Release
```

## 📁 Struttura

```
cpp/
├── CMakeLists.txt           # Build configuration principale
├── include/                 # Header files (.hpp)
│   ├── node_type.hpp       # ✅
│   ├── track_type.hpp      # ✅
│   ├── train_type.hpp      # ✅
│   ├── node.hpp            # ✅
│   ├── edge.hpp            # ✅
│   ├── train.hpp           # ✅
│   ├── railway_network.hpp # ✅
│   └── ...                  # (altri headers in arrivo)
├── src/                     # Implementation files (.cpp)
│   ├── CMakeLists.txt      # ✅
│   ├── node.cpp            # ✅
│   ├── edge.cpp            # ✅
│   ├── train.cpp           # ✅
│   ├── railway_network.cpp # ✅
│   └── ...                  # (altri sorgenti in arrivo)
├── tests/                   # Unit tests
│   └── ...                  # (tests in arrivo)
├── examples/                # Esempi di utilizzo
│   ├── basic_example.cpp   # ✅
│   ├── network_example.cpp # ✅
│   └── ...                  # (altri esempi in arrivo)
└── README.md               # Questo file
```

## 🎓 Architettura

### Classi Core

#### `Node`
Rappresenta una stazione/nodo nella rete ferroviaria:
- Coordinate GPS (latitudine, longitudine)
- Capacità e numero di binari
- Gestione prenotazioni piattaforme
- Type-safe con `NodeType` enum

#### `Edge`
Rappresenta una connessione ferroviaria tra nodi:
- Distanza in km
- Tipo binario (singolo, doppio, AV)
- Velocità massima
- Capacità simultanea treni

#### `Train`
Rappresenta un treno con caratteristiche fisiche:
- Velocità massima
- Accelerazione e decelerazione
- Calcoli realistici tempi di viaggio
- Type-safe con `TrainType` enum

#### `RailwayNetwork`
Gestisce la rete ferroviaria come grafo:
- Usa **Boost.Graph** (adjacency_list)
- Algoritmo **Dijkstra** per shortest path
- Gestione nodi e archi (add/remove/get)
- Analisi connettività e statistiche
- Pathfinding multi-criterio
- Calcolo vicini e distanze

#### Sistema Scheduling
Gestione completa orari ferroviari:

**`ScheduleStop`**: Singola fermata con orari
- Orari arrivo/partenza (std::chrono)
- Assegnazione binario (std::optional)
- Calcolo tempo di sosta
- Validazione coerenza temporale

**`TrainSchedule`**: Orario completo treno
- Lista ordinata fermate
- Validazione multi-livello (cronologia, rete, binari)
- Calcolo distanze e tempi totali
- Conflict detection tra orari
- Query avanzate (visite nodo, sequenza percorso)

**`ScheduleBuilder`**: Costruzione orari (Builder Pattern)
- Fluent API per costruzione step-by-step
- Calcolo automatico tempi di viaggio
- Assegnazione automatica binari
- 3 modalità: manuale, semi-auto, completamente automatica

**`ScheduleManager`**: Gestione collezioni
- Rilevamento conflitti globale
- Query per nodo/intervallo temporale
- Statistiche aggregate

#### Serializzazione JSON
Export/Import completo per persistenza dati:

**Funzionalità:**
- Serializzazione automatica tutte le classi (Node, Edge, Train, Schedule)
- Formato JSON human-readable
- Orari in formato ISO 8601
- Export/Import network completo
- Export/Import schedules
- File I/O con gestione errori

**Uso:**
```cpp
#include "serialization.hpp"

// Export network
save_network_to_file(network, "my_network.json");

// Export schedules
save_schedules_to_file(schedules, "my_schedules.json");

// Import network
auto loaded_network = load_network_from_file("my_network.json");

// Import schedules
auto loaded_schedules = load_schedules_from_file("my_schedules.json", network);
```

**Formato compatibile con Python**: I file JSON possono essere condivisi tra versione C++ e Python

### Design Patterns

- **RAII**: Gestione automatica risorse (no memory leaks)
- **Smart Pointers**: `std::unique_ptr`, `std::shared_ptr`
- **Type Safety**: Enum class invece di int/string
- **STL Containers**: `std::vector`, `std::map`, `std::optional`
- **Modern C++**: Range-based loops, auto, lambda

## 📖 Esempi Base

```cpp
#include <fdc/node.hpp>
#include <fdc/edge.hpp>
#include <fdc/train.hpp>

using namespace fdc;

int main() {
    // Crea stazioni
    Node milano("MI", "Milano Centrale", NodeType::STATION,
                45.4864, 9.2040, 10, 8);
    Node roma("RO", "Roma Termini", NodeType::STATION,
              41.9009, 12.5023, 12, 10);
    
    // Crea connessione
    Edge track("MI", "RO", 585.0, TrackType::HIGH_SPEED, 300.0);
    
    // Crea treno
    Train frecciarossa = Train::create_by_type(
        "FR1000", "Frecciarossa 1000", TrainType::HIGH_SPEED);
    
    // Calcola tempo di viaggio
    double time = frecciarossa.calculate_travel_time(
        585.0,    // distanza km
        300.0     // velocità massima binario
    );
    
    std::cout << "Tempo di viaggio: " << time << " ore\n";
    
    return 0;
}
```

## 🔄 Differenze con Versione Python

| Aspetto | Python | C++ |
|---------|--------|-----|
| **Memory** | Garbage collected | RAII + Smart pointers |
| **Types** | Dynamic | Static (compile-time) |
| **Speed** | Interpretato | Compilato (10-100x faster) |
| **Graphs** | networkx | Boost.Graph |
| **GUI** | Tkinter | Qt6 |
| **JSON** | built-in | nlohmann/json |
| **DB** | mysql-connector-python | MySQL Connector/C++ |

## 📚 Prossimi Passi

1. **RailwayNetwork** con Boost.Graph
2. **Dijkstra** e algoritmi pathfinding
3. **Schedule** e gestione orari
4. **JSON serialization** completa
5. **GUI Qt** con visualizzazioni
6. **Database layer** (opzionale)
7. **Unit tests** completi
8. **Performance benchmarks**

## 🤝 Contributi

Progetto in fase di riscrittura attiva. Il codice Python originale si trova nella directory `src/` principale.

## 📄 Licenza

Stesso del progetto Python originale.

## ✨ Credits

Riscrittura C++ del progetto FDC Railway Management System.
Versione Python originale: v0.2.0
