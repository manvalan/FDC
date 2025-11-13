# 🔧 FDC C++ - Installation Guide

Guida completa all'installazione e compilazione del progetto FDC C++.

---

## 📋 Requisiti di Sistema

### Obbligatori
- **C++17 Compiler**: GCC 7+, Clang 5+, MSVC 2017+, Apple Clang 10+
- **CMake**: 3.15 o superiore
- **Boost**: 1.70 o superiore (solo Boost.Graph necessario)

### Opzionali
- **Qt6** o **Qt5** 5.15+ (per interfaccia grafica)
- **MySQL Connector/C++** 8.0+ (per database)
- **Google Test** (per unit testing)
- **Doxygen** (per generazione documentazione)

---

## 🍎 macOS

### Metodo 1: Homebrew (Consigliato)

```bash
# Installa Homebrew (se non già installato)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Installa dipendenze obbligatorie
brew install cmake boost

# Installa dipendenze opzionali
brew install qt6           # Per GUI
brew install mysql         # Per database
brew install googletest    # Per tests
brew install doxygen       # Per docs

# Clona repository e compila
cd "path/to/FDC/cpp"
./build.sh

# Oppure con GUI support
./build.sh --gui
```

### Metodo 2: Build manuale

```bash
# Crea directory build
mkdir build && cd build

# Configura
cmake .. \
    -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_EXAMPLES=ON \
    -DBUILD_TESTS=ON

# Compila (usa tutti i core)
cmake --build . -j$(sysctl -n hw.ncpu)

# Esegui esempio
./bin/basic_example

# Esegui tests
ctest --output-on-failure
```

---

## 🐧 Linux (Ubuntu/Debian)

### Ubuntu 20.04 / 22.04 / Debian 11+

```bash
# Aggiorna package list
sudo apt update

# Installa compiler e build tools
sudo apt install -y build-essential cmake git

# Installa Boost
sudo apt install -y libboost-all-dev

# Installa Qt6 (per GUI)
sudo apt install -y qt6-base-dev qt6-charts-dev

# Installa MySQL (per database)
sudo apt install -y libmysqlclient-dev

# Installa Google Test (per tests)
sudo apt install -y libgtest-dev
cd /usr/src/gtest
sudo cmake CMakeLists.txt
sudo make
sudo cp lib/*.a /usr/lib

# Clona e compila
cd "path/to/FDC/cpp"
./build.sh --gui
```

### Fedora / CentOS / RHEL

```bash
# Installa dipendenze
sudo dnf install -y gcc-c++ cmake boost-devel

# Qt6
sudo dnf install -y qt6-qtbase-devel qt6-qtcharts-devel

# MySQL
sudo dnf install -y mysql-devel

# Compila
./build.sh
```

### Arch Linux

```bash
# Installa dipendenze
sudo pacman -S cmake boost qt6-base qt6-charts mysql++

# Compila
./build.sh --gui
```

---

## 🪟 Windows

### Metodo 1: vcpkg (Consigliato)

```powershell
# Installa Visual Studio 2019 o 2022 (Community Edition)
# Scarica da: https://visualstudio.microsoft.com/

# Clona vcpkg
git clone https://github.com/Microsoft/vcpkg.git
cd vcpkg
.\bootstrap-vcpkg.bat

# Installa dipendenze
.\vcpkg install boost:x64-windows
.\vcpkg install nlohmann-json:x64-windows
.\vcpkg install qt6:x64-windows      # Opzionale, per GUI
.\vcpkg install gtest:x64-windows    # Opzionale, per tests

# Integra con Visual Studio
.\vcpkg integrate install

# Torna al progetto FDC
cd "path\to\FDC\cpp"
mkdir build
cd build

# Configura con vcpkg toolchain
cmake .. -DCMAKE_TOOLCHAIN_FILE="path\to\vcpkg\scripts\buildsystems\vcpkg.cmake"

# Compila
cmake --build . --config Release

# Esegui esempio
.\bin\Release\basic_example.exe
```

### Metodo 2: MSYS2

```bash
# Installa MSYS2 da: https://www.msys2.org/

# Apri MSYS2 MinGW 64-bit terminal

# Aggiorna package database
pacman -Syu

# Installa dipendenze
pacman -S mingw-w64-x86_64-gcc
pacman -S mingw-w64-x86_64-cmake
pacman -S mingw-w64-x86_64-boost
pacman -S mingw-w64-x86_64-qt6      # Opzionale
pacman -S mingw-w64-x86_64-gtest    # Opzionale

# Compila
cd /c/path/to/FDC/cpp
mkdir build && cd build
cmake .. -G "MinGW Makefiles"
cmake --build .
```

---

## 🔧 Opzioni di Build

### Variabili CMake

| Opzione | Default | Descrizione |
|---------|---------|-------------|
| `CMAKE_BUILD_TYPE` | Release | Release, Debug, RelWithDebInfo, MinSizeRel |
| `BUILD_TESTS` | ON | Compila unit tests |
| `BUILD_EXAMPLES` | ON | Compila esempi |
| `BUILD_GUI` | OFF | Compila applicazione GUI con Qt |
| `BUILD_WITH_MYSQL` | OFF | Abilita supporto database MySQL |

### Esempi di configurazione

```bash
# Debug build con GUI
cmake .. -DCMAKE_BUILD_TYPE=Debug -DBUILD_GUI=ON

# Release build minimale (solo libreria core)
cmake .. -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTS=OFF -DBUILD_EXAMPLES=OFF

# Build completo con tutte le features
cmake .. -DBUILD_GUI=ON -DBUILD_WITH_MYSQL=ON -DBUILD_TESTS=ON
```

---

## 🧪 Testing

```bash
# Compila con tests
cmake .. -DBUILD_TESTS=ON
cmake --build .

# Esegui tutti i tests
ctest

# Esegui tests verbose
ctest --output-on-failure

# Esegui tests specifici
ctest -R NodeTest
ctest -R EdgeTest
ctest -R TrainTest
```

---

## 📦 Installazione Sistema

```bash
# Installa in /usr/local (richiede sudo)
cd build
sudo cmake --install .

# Oppure installa in prefix custom
cmake .. -DCMAKE_INSTALL_PREFIX=/opt/fdc
cmake --build .
sudo cmake --install .
```

Dopo l'installazione, puoi usare FDC in altri progetti:

```cmake
# Nel tuo CMakeLists.txt
find_package(FDC REQUIRED)
target_link_libraries(my_app PRIVATE FDC::fdc_core)
```

---

## 🐛 Troubleshooting

### Boost non trovato

```bash
# macOS
brew install boost

# Ubuntu/Debian
sudo apt install libboost-all-dev

# Specifica path manualmente
cmake .. -DBOOST_ROOT=/path/to/boost
```

### Qt non trovato

```bash
# macOS
brew install qt6
export CMAKE_PREFIX_PATH="/opt/homebrew/opt/qt6"

# Ubuntu
sudo apt install qt6-base-dev

# Specifica versione
cmake .. -DQt6_DIR=/path/to/qt6/lib/cmake/Qt6
```

### nlohmann/json non scaricato

```bash
# Disabilita FetchContent e usa system package
sudo apt install nlohmann-json3-dev  # Ubuntu

# Oppure
cmake .. -DFETCHCONTENT_FULLY_DISCONNECTED=OFF
```

### Errori linking Boost.Graph

Boost.Graph è header-only, non serve linking. Se hai errori:

```bash
# Assicurati di avere solo Boost::graph (senza _libs)
target_link_libraries(my_target PRIVATE Boost::graph)
```

### Errori C++17

```bash
# Verifica versione compiler
g++ --version        # GCC 7+
clang++ --version    # Clang 5+

# Forza C++17
cmake .. -DCMAKE_CXX_STANDARD=17
```

---

## 📚 Next Steps

Dopo l'installazione:

1. **Esegui basic_example**
   ```bash
   ./build/bin/basic_example
   ```

2. **Leggi la documentazione**
   ```bash
   cat README.md
   cat PROJECT_STATUS.md
   ```

3. **Esplora gli headers**
   ```bash
   ls include/*.hpp
   ```

4. **Inizia a sviluppare!**
   - Crea tua rete ferroviaria
   - Aggiungi stazioni e binari
   - Calcola percorsi ottimali

---

## 💡 Supporto

- **Issues**: Apri issue su GitHub
- **Documentazione**: Vedi `README.md` e `PROJECT_STATUS.md`
- **Esempi**: Directory `examples/`

---

## ✨ Quick Start Command

```bash
# One-liner per iniziare subito (macOS/Linux)
brew install cmake boost qt6 && \
cd cpp && \
./build.sh --gui --test && \
./build/bin/basic_example
```

Buon coding! 🚂🚄✨
