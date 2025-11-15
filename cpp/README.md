# 🚆 FDC Railway Manager - C++ Edition

Professional railway network management system with advanced scheduling, conflict detection, and multi-train visualization.

## 🎯 Project Status

**✨ VERSION 1.0.1 - BUG FIXES** - Fully functional with Qt6 GUI

### 🐛 Latest Updates (v1.0.1 - 2025-01-20)
- ✅ **New modern icon**: Purple gradient design with geometric train
- ✅ **Reverse direction trains**: Fixed "Create from Line" for any direction
- ✅ **Time window filtering**: Graph now respects ±15 minute window

### ✅ Core Features Complete
- [x] Complete C++ core library with Boost.Graph
- [x] Realistic train physics (acceleration, cruising, braking)
- [x] Dijkstra pathfinding algorithm
- [x] Advanced scheduling system with automatic time calculation
- [x] JSON serialization/deserialization
- [x] Network and schedule import/export

### ✅ GUI Application Complete
- [x] Full Qt6 interface with 7 specialized dialogs
- [x] Interactive network map with zoom/pan
- [x] Multi-train time-distance visualization
- [x] **Bidirectional batch train creation** (any station to any station)
- [x] **Advanced conflict detection** with track-type rules
- [x] **Configurable settings system** (4-tab dialog)
- [x] **Custom macOS-style app icon**

### 🚀 Next Steps
- [ ] AI-powered scheduling optimization (Phase 7 - Q1 2026)
- [ ] Advanced analytics dashboard (Phase 8 - Q2 2026)
- [ ] Real-time simulation (Phase 9 - Q3 2026)
- [ ] Multi-user collaboration (Phase 10 - Q4 2026)

## 🎨 Key Features

### � Network Management
- Visual network editor with interactive map
- Stations with GPS coordinates, capacity, platform management
- Connections with track type (single/double), distance, max speed
- Import/export network data in JSON format

### 🚄 Train Scheduling
- **Bidirectional batch creation**: Create multiple trains from any station to any station
- Automatic time calculation based on realistic physics
- **Multi-train visualization** with color-coded time-distance charts
- **Smart conflict detection**:
  - Single track: 1 train max per section (opposite = conflict)
  - Same direction: configurable minimum separation (default 5km)
  - Double track: separate tracks, configurable separation
  - Station conflicts: time tolerance (default ±2 minutes)

### ⚙️ Configuration System
- **4-tab settings dialog**:
  1. **Traffic Visualization**: time window (±20 min), common stations filter
  2. **Conflict Detection**: enable/disable, track separations, tolerances
  3. **Batch Creation**: default train count, interval, naming
  4. **Schedule Calculation**: dwell time, auto-calculate
- Settings persist via QSettings (macOS: `~/Library/Preferences`)

### 📊 Visualization
- **Network Map Widget**: Zoom, pan, node/edge highlighting
- **Schedule Graph Widget**: 
  - Time-distance diagrams with multiple trains
  - Red conflict markers with warnings
  - Focused traffic view (±20 min window)
  - Color-coded train identification

### 🎯 User Experience
- Professional Qt6 interface
- macOS-style custom icon
- Keyboard shortcuts (⌘, for Preferences)
- Intuitive dialogs with validation
- Real-time conflict feedback

## 📋 Requirements

### Required
- **C++17** or higher
- **CMake** 3.15+
- **Boost** 1.70+ (Boost.Graph)
- **Qt6** 6.2+ (Core, Widgets, GUI)
- **nlohmann/json** (auto-downloaded by CMake)

### Optional
- **Google Test** (for unit tests)
- **Doxygen** (for API documentation)

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

## � Quick Start

### Running the GUI Application

```bash
cd build
./bin/fdc_gui  # or open "FDC Railway Manager.app" on macOS
```

### Basic Workflow

1. **Create Network**:
   - Add stations (View → Stazioni)
   - Create connections (View → Connessioni)
   - View network map (View → Mappa Rete)

2. **Define Trains**:
   - Add train types (View → Treni)
   - Set speed, capacity, acceleration

3. **Create Lines**:
   - Define routes (View → Linee)
   - Drag & drop stations to order

4. **Schedule Trains**:
   - Create single schedule (View → Orari)
   - Or batch create multiple trains (Orari → Crea Batch)
   - **Select any start/end station for bidirectional routes**
   - Automatic time calculation with physics

5. **Visualize Traffic**:
   - Click "Visualizza Treni" button
   - See all trains with time-distance chart
   - **Red triangles = conflicts detected**

6. **Configure Settings**:
   - Menu → Impostazioni → Preferenze (⌘,)
   - Adjust conflict rules, time windows, defaults

### Example Files

Load the demo network to get started:

```bash
# Load Contea railway network
File → Apri Rete → examples/ferrovie_contea.json
```

## 📁 Structure

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

## � Documentation

For comprehensive project documentation, see:

- **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - Complete feature list, roadmap, and AI integration plans
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and release notes
- **[SUMMARY.md](SUMMARY.md)** - Technical architecture and design decisions

### Future Development

See [PROJECT_STATUS.md](PROJECT_STATUS.md) for detailed roadmap including:
- 🤖 **Phase 7**: AI-powered scheduling with LLM integration
- 📈 **Phase 8**: Advanced analytics and reporting dashboard
- 🌐 **Phase 9**: Real-time simulation with digital twin
- 👥 **Phase 10**: Multi-user collaboration with cloud sync
- 🎨 **Phase 11**: Advanced UI/UX with mobile companion apps
- 🧪 **Phase 12**: Comprehensive testing and quality assurance

## 🔄 Differences with Python Version

| Aspect | Python | C++ |
|--------|--------|-----|
| **Memory** | Garbage collected | RAII + Smart pointers |
| **Types** | Dynamic | Static (compile-time) |
| **Speed** | Interpreted | Compiled (10-100x faster) |
| **Graphs** | networkx | Boost.Graph |
| **GUI** | Tkinter | Qt6 (professional) |
| **JSON** | built-in | nlohmann/json |
| **Status** | Prototype | Production-ready |

## 🤝 Contributing

The project is **open source** and welcomes contributions!

**How to contribute:**
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

**Areas needing help:**
- 💻 C++ development (algorithms, optimization)
- 🎨 UI/UX design and improvements
- 📝 Documentation and tutorials
- 🧪 Testing and quality assurance
- 🤖 AI/ML integration
- 🌍 Internationalization (i18n)

## 📄 License

**MIT License** - Free for commercial and non-commercial use.

See [LICENSE](../LICENSE) file for details.

## 👨‍💻 Author

**Michele Bigi** & Contributors

## 🙏 Acknowledgments

- Original Python version foundation
- Boost.Graph library for network algorithms
- Qt6 for professional cross-platform GUI
- nlohmann/json for modern C++ JSON handling
- Railway engineering community for domain knowledge

---

**Version:** 1.0.0 | **Status:** ✅ Production Ready | **Last Updated:** November 15, 2025

🚆 **All aboard for the future of railway management!** 🚆
