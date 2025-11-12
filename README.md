# FDC - Railway Manager and Simulator

Sistema di gestione e simulazione dell'infrastruttura ferroviaria basato su grafi.

## 📋 Descrizione

FDC è un sistema per la gestione di reti ferroviarie modellate come grafi, dove:
- **Nodi** rappresentano stazioni e interscambi
- **Archi** rappresentano i binari che collegano i nodi

Il sistema offre funzionalità di:
- Gestione della topologia della rete
- Ricerca del percorso più breve (Dijkstra)
- Calcolo di percorsi alternativi
- Gestione della capacità di stazioni e binari
- Visualizzazione grafica della rete
- Import/Export in formato JSON

## 🚀 Installazione

### Prerequisiti
- Python 3.8 o superiore
- pip

### Setup

1. Clona il repository:
```bash
git clone https://github.com/manvalan/FDC.git
cd FDC
```

2. Installa le dipendenze:
```bash
pip install -r requirements.txt
```

## 📁 Struttura del Progetto

```
FDC/
├── src/
│   ├── __init__.py              # Package principale
│   ├── node.py                  # Classe Node (stazioni/interscambi)
│   ├── edge.py                  # Classe Edge (binari)
│   ├── railway_network.py       # Classe RailwayNetwork (gestione grafo)
│   ├── train.py                 # Classe Train (treni con caratteristiche fisiche)
│   ├── schedule.py              # Classe TrainSchedule (gestione orari)
│   ├── traffic_simulator.py     # Classe TrafficSimulator (simulazione traffico)
│   ├── visualization.py         # Modulo per grafici tempo-distanza
│   ├── plotter.py               # Utilities per plotting (alternativo)
│   ├── database.py              # DatabaseManager per persistenza MySQL
│   └── gui_app.py               # 🆕 Applicazione GUI completa con Tkinter
├── examples/
│   ├── basic_network.py         # Esempio base rete ferroviaria
│   ├── pathfinding.py           # Esempio pathfinding
│   ├── scheduling_demo.py       # Esempio schedulazione e conflitti
│   ├── plot_timetable.py        # Esempio grafico tempo-distanza
│   ├── conflict_visualization.py # Visualizzazione conflitti binario singolo
│   ├── import_contea.py         # Import rete "Ferrovie della Contea" (54 stazioni)
│   ├── test_auto_sizing.py      # Test ridimensionamento automatico visualizzazioni
│   ├── json_demo_simple.py      # Demo completa export/import JSON
│   └── database_json_demo.py    # Demo MySQL database integration (richiede MySQL)
├── tests/                       # Test unitari
├── requirements.txt             # Dipendenze Python
└── README.md                    # Questo file
```

## 🎯 Utilizzo

### Esempio Base

```python
from src.node import Node, NodeType
from src.edge import Edge, TrackType
from src.railway_network import RailwayNetwork

# Crea la rete
network = RailwayNetwork("My Railway Network")

# Aggiungi stazioni
milano = Node("MI", "Milano Centrale", NodeType.STATION, 
              latitude=45.4864, longitude=9.2040, 
              capacity=10, platforms=8)
roma = Node("RO", "Roma Termini", NodeType.STATION,
            latitude=41.9009, longitude=12.5023,
            capacity=12, platforms=10)

network.add_node(milano)
network.add_node(roma)

# Aggiungi binario
track = Edge("MI", "RO", distance=585.0, 
             track_type=TrackType.HIGH_SPEED,
             max_speed=300, capacity=2)
network.add_edge(track)

# Trova percorso più breve
path, distance = network.find_shortest_path("MI", "RO")
print(f"Percorso: {path}")
print(f"Distanza: {distance} km")
```

### 🖥️ Applicazione GUI ⭐ NUOVO

L'applicazione GUI completa permette di gestire reti ferroviarie tramite interfaccia grafica:

```bash
cd examples
python3 run_gui.py
```

**Caratteristiche principali:**
- 📊 **3 Tab principali**: Rete Ferroviaria, Linee, Treni e Orari
- 🎨 **Menu completo**: File, Modifica, Treni, Visualizza, Aiuto
- ⚡ **Toolbar rapido**: Accesso veloce alle funzioni principali
- 🗺️ **Visualizzazioni integrate**: Mappa rete e grafici orario
- 💾 **Gestione progetti**: Nuovo/Apri/Salva con formato .fdc
- 🚉 **Editor stazioni**: Aggiungi/modifica/elimina con form interattivi
- 🔗 **Editor connessioni**: Gestione binari singoli/doppi con velocità
- 🌈 **Gestione linee colorate**: Crea linee con colori personalizzati
- 🚂 **Creazione treni**: Tutti i tipi con selezione percorso da linee
- 📅 **Gestione orari**: Orari di partenza, fermate, durata sosta
- ⚠️ **Simulazione traffico**: Rilevamento e risoluzione automatica conflitti
- 🎯 **Carica rete predefinita**: Menu File → "Carica Ferrovie della Contea" (54 stazioni, 8 linee colorate)

### Eseguire gli Esempi

```bash
cd examples

# Esempio rete ferroviaria italiana
python3 basic_network.py

# Esempio pathfinding
python3 pathfinding.py

# Esempio schedulazione e gestione traffico
python3 scheduling_demo.py

# Visualizzazione grafico tempo-distanza
python3 plot_timetable.py

# Visualizzazione conflitti su binario singolo
python3 conflict_visualization.py

# Import rete personalizzata "Ferrovie della Contea" (54 stazioni, 8 linee)
python3 import_contea.py

# Test ridimensionamento automatico delle visualizzazioni
python3 test_auto_sizing.py

# Demo completa JSON export/import (non richiede database)
python3 json_demo_simple.py

# Demo MySQL database (richiede MySQL server)
python3 database_json_demo.py

# 🆕 Avvia l'applicazione GUI completa
python3 run_gui.py
```

## 🔧 Funzionalità Principali

### 1. Gestione Infrastruttura

#### Classe Node
Rappresenta stazioni e interscambi:
- **Attributi**: ID, nome, tipo, coordinate GPS, capacità, numero di binari
- **Metodi**: gestione occupazione, verifica disponibilità

#### Classe Edge
Rappresenta i binari:
- **Attributi**: nodi collegati, distanza, tipo di binario, velocità massima, capacità
- **Metodi**: calcolo tempo di percorrenza, gestione traffico

#### Classe RailwayNetwork
Gestisce l'intera rete ferroviaria:
- **Aggiunta/rimozione** di nodi e binari
- **Pathfinding**: algoritmo di Dijkstra per percorso più breve
- **Percorsi alternativi**: ricerca di più percorsi tra due stazioni
- **Statistiche**: analisi della rete (numero nodi, lunghezza totale, connettività)
- **Visualizzazione**: rappresentazione grafica con matplotlib
- **Import/Export**: salvataggio e caricamento in formato JSON

### 2. Persistenza Dati ⭐ NUOVO

#### Export/Import JSON
Sistema completo di serializzazione:
- **Network export**: salva topologia completa (nodi, archi, statistiche)
- **Schedule export**: salva orari con tutte le fermate e dettagli
- **Train export**: salva caratteristiche dei treni
- **Import**: ricostruzione completa da file JSON
- **Formato standardizzato**: compatibile con altri sistemi
- **Versionamento**: file JSON facilmente tracciabili con Git

#### Database MySQL (Opzionale)
Persistenza su database relazionale:
- **Schema ottimizzato**: tabelle per networks, trains, schedules, stops
- **CRUD completo**: Create, Read, Update, Delete
- **Query avanzate**: ricerca schedules per network, train, date
- **Transazioni**: operazioni atomiche per consistenza dati
- **Connection pooling**: gestione efficiente connessioni
- **Auto-migration**: creazione automatica schema al primo avvio

```python
# Esempio export/import JSON
network.export_to_json("my_network.json", include_stats=True)
schedule.export_to_json("my_schedule.json")

imported_network = RailwayNetwork()
imported_network.import_from_json("my_network.json")
imported_schedule = TrainSchedule.import_from_json("my_schedule.json")

# Esempio database MySQL
db = DatabaseManager(host="localhost", user="root", password="", database="railway")
db.connect()

network_id = db.save_network(network)
db.save_schedule(schedule, network_id)

loaded_network = db.load_network(network_id)
loaded_schedule = db.load_schedule("SCH001")
```

### 3. Gestione Treni e Orari ⭐ NUOVO

#### Classe Train
Rappresenta treni con caratteristiche fisiche realistiche:
- **Tipi**: Alta velocità, Intercity, Regionale, Merci, Locale
- **Caratteristiche**: velocità massima, accelerazione, frenata, lunghezza
- **Calcoli**: tempo di accelerazione, distanza di frenata, tempo di percorrenza

#### Classe TrainSchedule
Gestisce orari e fermate:
- **Fermate**: arrivo, partenza, binario, durata sosta
- **Calcolo automatico**: orari basati su velocità e caratteristiche del treno
- **Ritardi**: tracciamento e propagazione dei ritardi

#### Classe TrafficSimulator
Simula il traffico e gestisce conflitti:
- **Occupazione binari**: tracciamento utilizzo in tempo reale
- **Rilevamento conflitti**: identifica conflitti su binari singoli
- **Risoluzione automatica**: gestisce precedenze basate su priorità
- **Binari singoli**: gestione corretta di treni in direzioni opposte

### 4. Visualizzazione Grafica ⭐ NUOVO

#### Network Visualization
- **Layout automatico**: posizionamento nodi basato su coordinate GPS
- **Colori per tipo**: stazioni (blu), interscambi (arancio), depositi (verde)
- **Etichette distanze**: km su ogni connessione
- **Ridimensionamento auto**: adattamento a reti di qualsiasi dimensione

#### Time-Distance Diagrams
- **Grafico tempo-distanza**: classico diagramma ferroviario
- **Traiettorie treni**: linee colorate per ogni treno
- **Zone critiche**: evidenziazione binari singoli in rosso
- **Marcatori conflitti**: simboli ⚠️ dove i treni si sovrappongono
- **Tempi di sosta**: visualizzazione fermate come segmenti orizzontali

## 📊 Esempi di Output

### Statistiche di Rete
```
📊 Network Statistics:
  • Num Nodes: 8
  • Num Edges: 8
  • Num Stations: 7
  • Num Interchanges: 1
  • Total Track Length: 1234.0 km
  • Is Connected: True
```

### Ricerca Percorsi
```
🔍 Finding shortest path from Milano to Roma...
  ✓ Path found: Milano Centrale → Bologna Centrale → Firenze SMN → Roma Termini
  • Total distance: 585.0 km
  • Estimated travel time: 2.34 hours (140 minutes)
```

### Schedulazione e Gestione Traffico ⭐ NUOVO
```
📋 SCHEDULE: HS9600
Train: Frecciarossa 9600 (high_speed)
Route: Città A → Città D

Station              Arrival    Departure  Platform Delay   
──────────────────────────────────────────────────────────
Città A              ---        08:00      -        -       
Città B              08:24      08:26      -        -       
Città C              08:47      08:49      -        -       
Città D              08:59      ---        -        -       

🔄 Running traffic simulation...
   (Detecting conflicts on single-track section B-C)

TRAFFIC SIMULATION RESULTS
──────────────────────────────────────────────────────────
Total trains scheduled: 5
Trains on time: 3
Trains delayed: 2
Total delay: 15 minutes
Average delay: 7.5 minutes

DELAYED TRAINS:
  • Regionale 2341 (REG2341): +10 minutes delay
  • Regionale 2342 (REG2342): +5 minutes delay
```

### Grafico Tempo-Distanza ⭐ NUOVO
```
🎨 Generating time-distance diagram...
   - Red shaded area shows single-track section
   - Red X marks show conflicts (trains overlapping on single track)
   - Train labels show which train is which
   
  ✓ Saved to: conflict_visualization.png

💡 In the diagram:
   - Horizontal axis: Time
   - Vertical axis: Distance (km) along the route
   - Each colored line: One train's journey
   - Red shaded area: Single-track bottleneck section
   - Red X markers: Conflicts requiring resolution
```

## ⭐ Caratteristiche Avanzate

### Gestione Conflitti su Binario Singolo
Il sistema gestisce automaticamente situazioni complesse:
- **Binari singoli**: solo un treno alla volta può occupare la tratta
- **Direzioni opposte**: treni in direzioni opposte si attendono nelle stazioni
- **Priorità**: treni ad alta priorità (es. Frecciarossa) hanno precedenza
- **Ritardi automatici**: il sistema calcola il minimo ritardo necessario

### Calcoli Fisici Realistici
- **Accelerazione graduale**: considera il tempo per raggiungere la velocità massima
- **Frenata**: calcola distanza e tempo di frenata necessari
- **Velocità variabile**: rispetta limiti di velocità di ogni tratta
- **Tempi realistici**: orari calcolati con fisica del movimento

### Visualizzazione Grafica Avanzata ⭐ NUOVO
Il modulo `visualization.py` offre:
- **Diagramma tempo-distanza**: grafico classico ferroviario (orario vs km)
- **Etichette treni**: nomi chiaramente visibili lungo le traiettorie
- **Zone binario singolo**: aree rosse evidenziano tratte critiche
- **Marcatori conflitti**: simboli di avviso dove i treni si sovrappongono
- **Indicatori ritardi**: mostra ritardi accumulati per ogni treno
- **Export PNG**: salvataggio alta risoluzione (300 DPI)
- **🆕 Ridimensionamento automatico**: le visualizzazioni si adattano automaticamente ai dati
  - Le dimensioni della figura vengono calcolate in base all'estensione geografica della rete
  - I grafici tempo-distanza si adattano alla lunghezza del percorso e all'arco temporale
  - Layout ottimizzato per finestre visibili con `tight_layout()`
  - Nessun taglio di etichette o elementi fuori schermo

## 🛠️ Sviluppi Futuri

- [x] ~~Simulazione del traffico ferroviario in tempo reale~~
- [x] ~~Gestione orari e scheduling dei treni~~
- [ ] Ottimizzazione multi-obiettivo (tempo, costo, comfort)
- [ ] Interfaccia web interattiva
- [ ] Database per persistenza dati
- [ ] API REST per integrazione con altri sistemi
- [ ] Gestione eventi dinamici e ritardi in tempo reale
- [ ] Analisi predittiva del traffico con ML
- [ ] Visualizzazione animata del movimento dei treni
- [ ] Gestione manutenzioni e chiusure temporanee

## 📝 Note Tecniche

### Algoritmi Utilizzati
- **Dijkstra**: per il calcolo del percorso più breve
- **K-shortest paths**: per percorsi alternativi

### Dipendenze
- `networkx`: gestione grafi e algoritmi
- `matplotlib`: visualizzazione
- `pandas`: manipolazione dati
- `numpy`: calcoli numerici

## 🤝 Contribuire

Contributi, issues e feature requests sono benvenuti!

## 📄 Licenza

Questo progetto è open source.

## 👤 Autore

**FDC Team**
- GitHub: [@manvalan](https://github.com/manvalan)

---

*Creato con ❤️ per la gestione delle infrastrutture ferroviarie*
