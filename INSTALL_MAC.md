# 🚂 FDC - Railway Network Management System
## Installazione su macOS

Questo progetto fornisce un sistema completo per la gestione di reti ferroviarie con interfaccia grafica, calcoli fisici realistici, e persistenza dati.

---

## 📋 Requisiti di Sistema

- **macOS** 10.14 (Mojave) o superiore
- **Homebrew** (verrà installato automaticamente se mancante)
- **Python 3.11+** (verrà installato automaticamente se mancante)
- **Connessione Internet** (per download dipendenze)
- **Spazio Disco**: ~500 MB

---

## 🚀 Installazione Rapida

### Metodo 1: Installazione Automatica (Consigliato)

1. **Scarica lo script di installazione**
   ```bash
   curl -O https://raw.githubusercontent.com/manvalan/FDC/main/install_mac.sh
   ```

2. **Rendi eseguibile lo script**
   ```bash
   chmod +x install_mac.sh
   ```

3. **Esegui l'installazione**
   ```bash
   ./install_mac.sh
   ```
   
   Oppure specifica una directory personalizzata:
   ```bash
   ./install_mac.sh /percorso/personalizzato
   ```

4. **Attendi il completamento**
   - Lo script installerà automaticamente tutti i prerequisiti
   - Creerà un ambiente Python virtuale
   - Installerà tutte le dipendenze
   - Creerà shortcuts sul Desktop e alias nel terminale

5. **Avvia l'applicazione**
   - Doppio click su "FDC Railway Manager.command" sul Desktop
   - Oppure digita `fdc` in un terminale

---

### Metodo 2: Installazione Manuale

Se preferisci installare manualmente:

#### 1. Installa Homebrew (se non presente)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### 2. Installa Python 3.11+
```bash
brew install python@3.11
```

#### 3. Clone il repository
```bash
git clone https://github.com/manvalan/FDC.git
cd FDC
```

#### 4. Crea ambiente virtuale
```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### 5. Installa dipendenze
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 6. Avvia l'applicazione
```bash
cd examples
python3 run_gui.py
```

---

## 📦 Cosa Viene Installato

### Software Principale
- **Python 3.11+** - Linguaggio di programmazione
- **NetworkX 3.5** - Gestione grafi e pathfinding
- **NumPy 2.3** - Calcoli numerici
- **Matplotlib 3.10** - Visualizzazioni grafiche
- **Tkinter** - Interfaccia grafica

### Database (Opzionali)
- **SQLite** - Database predefinito (incluso in Python)
- **MySQL** - Database avanzato (opzionale)
  ```bash
  brew install mysql
  ```

---

## 🎯 Utilizzo

### Avvio Rapido

**Dopo l'installazione, hai 4 modi per avviare FDC:**

1. **Shortcut Desktop** (più facile)
   - Doppio click su "FDC Railway Manager.command"

2. **Alias Terminale** (più veloce)
   ```bash
   fdc
   ```

3. **Script Diretto**
   ```bash
   cd ~/FDC  # o la tua directory di installazione
   ./start_fdc.sh
   ```

4. **Manuale Completo**
   ```bash
   cd ~/FDC
   source .venv/bin/activate
   cd examples
   python3 run_gui.py
   ```

---

## 📚 Funzionalità Principali

### 🏗️ Gestione Infrastruttura
- ➕ Aggiungi stazioni con coordinate GPS
- 🔗 Crea connessioni (binari singoli/doppi)
- 🎨 Definisci linee colorate
- 🗺️ Visualizza rete in stile mappa metropolitana
- 📊 Statistiche dettagliate della rete

### 🚂 Gestione Treni
- 🆕 Crea singoli treni
- ➕ Crea serie di treni cadenzati
- ✏️ Modifica orari in tempo reale
- 🎯 Assegna priorità
- 🔄 Ricalcolo automatico tempi

### 📈 Visualizzazioni
- 🗺️ Mappa rete con topologia geografica
- 📊 Grafico tempo-distanza (marcia treni)
- 🗺️ Mappa stile metropolitana (singola/multipla)
- ⚠️ Evidenziazione conflitti binario singolo

### 💾 Persistenza Dati
- 📁 Salvataggio file .fdc (JSON)
- 🗄️ Database SQLite (predefinito)
- 🌐 Database MySQL (opzionale)
- 📤 Export/Import JSON
- 🗑️ Gestione salvataggi database

---

## 🔧 Configurazione

### Database SQLite (Predefinito)
Nessuna configurazione necessaria. I file vengono salvati in:
```
~/FDC/data/railway_network.db
```

### Database MySQL (Opzionale)

1. **Installa MySQL**
   ```bash
   brew install mysql
   brew services start mysql
   ```

2. **Crea database**
   ```bash
   mysql -u root -p
   CREATE DATABASE railway_network;
   EXIT;
   ```

3. **Connetti dall'applicazione**
   - Menu: Database → Connetti a MySQL...
   - Host: localhost
   - Porta: 3306
   - Database: railway_network
   - Utente: root
   - Password: [la tua password]

---

## 📖 Esempi

Il progetto include diversi esempi pronti all'uso:

```bash
cd ~/FDC/examples

# Rete italiana base
python3 basic_network.py

# Algoritmi di pathfinding
python3 pathfinding.py

# Demo schedulazione con conflitti
python3 scheduling_demo.py

# Visualizzazione conflitti
python3 conflict_visualization.py

# Import rete complessa (54 stazioni)
python3 import_contea.py

# Demo JSON export/import
python3 json_demo_simple.py

# Test auto-sizing
python3 test_auto_sizing.py
```

---

## 🆘 Risoluzione Problemi

### Python non trovato
```bash
brew install python@3.11
```

### Tkinter non funziona
```bash
brew install python-tk@3.11
```

### Matplotlib non visualizza finestre
```bash
# Reinstalla matplotlib con backend corretti
pip uninstall matplotlib
pip install matplotlib
```

### Permessi negati su install_mac.sh
```bash
chmod +x install_mac.sh
```

### Alias 'fdc' non funziona
Riavvia il terminale o ricarica il profilo:
```bash
source ~/.zshrc  # o ~/.bash_profile
```

### MySQL non si connette
```bash
# Verifica che MySQL sia in esecuzione
brew services list
brew services start mysql

# Verifica credenziali
mysql -u root -p
```

---

## 🔄 Aggiornamento

### Metodo 1: Git Pull (se installato da repository)
```bash
cd ~/FDC
git pull origin main
source .venv/bin/activate
pip install -r requirements.txt --upgrade
```

### Metodo 2: Reinstallazione
```bash
# Backup dei tuoi dati prima!
cp -r ~/FDC/data ~/FDC_backup
./install_mac.sh ~/FDC
cp -r ~/FDC_backup/data ~/FDC/
```

---

## 🗑️ Disinstallazione

```bash
# Rimuovi directory installazione
rm -rf ~/FDC

# Rimuovi shortcut Desktop
rm ~/Desktop/"FDC Railway Manager.command"

# Rimuovi alias (modifica manualmente)
nano ~/.zshrc  # o ~/.bash_profile
# Rimuovi le righe con "alias fdc="

# Disinstalla MySQL (se non serve più)
brew uninstall mysql
brew services stop mysql
```

---

## 📞 Supporto

- **Issues GitHub**: https://github.com/manvalan/FDC/issues
- **Wiki**: https://github.com/manvalan/FDC/wiki
- **Documentazione**: Vedi README.md nella directory principale

---

## 📄 Licenza

Questo progetto è distribuito sotto licenza MIT. Vedi file LICENSE per dettagli.

---

## 🙏 Crediti

- **NetworkX** - Graph algorithms
- **Matplotlib** - Visualizzazioni
- **NumPy** - Calcoli numerici
- **Python** - Linguaggio base

---

## 🎉 Buon Lavoro!

Ora sei pronto per gestire reti ferroviarie di qualsiasi complessità con FDC!

Per iniziare, digita semplicemente:
```bash
fdc
```

---

**Versione**: 1.0.0  
**Data**: Novembre 2025  
**Compatibilità**: macOS 10.14+
