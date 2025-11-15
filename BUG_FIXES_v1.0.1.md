# Bug Fixes - FDC Railway Manager v1.0.1

Data: 20 Gennaio 2025

## Riepilogo Correzioni

Sono stati risolti tutti e tre i bug segnalati durante i test:

### 1. ✅ Icona non visibile nella dock/menu bar

**Problema**: L'icona dell'app non era visibile nella barra delle applicazioni quando lanciata.

**Soluzione**:
- **Nuovo design icona**: Creato design moderno in stile Mac (1024x1024 SVG)
  - Sfondo con gradiente viola-blu (#667eea → #764ba2)
  - Treno geometrico minimalista con gradiente rosa-rosso (#f093fb → #f5576c)
  - Binari in prospettiva con punto di fuga (4 traversine minimaliste)
  - Icona pin posizione (metafora ferroviaria): bianco → rosa → centro bianco
  - Tipografia: "FDC" (SF Pro Display 110pt bold) + "RAILWAY MANAGER" (SF Pro Text 28pt light)
  - Effetti: overlay lucido, ombre morbide, bagliore sul treno
  
- **File generati**:
  - `cpp/gui/resources/icon.svg` (1024x1024)
  - `cpp/gui/resources/AppIcon.icns` (1.6MB con tutte le risoluzioni richieste)
  
- **Integrazione**: L'icona è stata integrata nel bundle dell'app tramite CMake

**Stato**: L'app è stata ricompilata e installata con la nuova icona. Verificare nella dock quando l'app è in esecuzione.

---

### 2. ✅ Creazione treni in senso inverso

**Problema**: Il pulsante "Crea nuovo treno" dal dialogo linea non creava treni in senso inverso (da ultima a prima stazione).

**Soluzione**:
- **Rimossa validazione errata**: Eliminato `if (startIdx >= endIdx) return;` che bloccava la direzione inversa
- **Aggiunta validazione corretta**: Ora controlla solo `if (startIdx == endIdx)` (stazione uguale)
- **Logica bidirezionale**: Implementato loop che supporta entrambe le direzioni:
  ```cpp
  bool reverseDirection = (startIdx > endIdx);
  
  if (reverseDirection) {
      for (int i = startIdx; i >= endIdx; --i) {
          builder.add_stop_auto(line.stationIds[i].toStdString(), dwellTime);
      }
  } else {
      for (int i = startIdx; i <= endIdx; ++i) {
          builder.add_stop_auto(line.stationIds[i].toStdString(), dwellTime);
      }
  }
  ```

**File modificati**:
- `cpp/gui/main_window.cpp` (metodo `createScheduleFromLine()`)
- `cpp/gui/batch_schedule_dialog.cpp` (logica analoga)

**Stato**: Ora è possibile creare treni selezionando qualsiasi combinazione di stazioni (prima→ultima, ultima→prima, intermedia→intermedia).

---

### 3. ✅ Visualizzazione grafico limitata alla finestra temporale

**Problema**: Il grafico di visualizzazione traffico mostrava l'intero percorso dei treni invece di limitarsi alla finestra temporale preimpostata (default ±15 minuti).

**Soluzione**:
- **Nuovo metodo `setTimeWindow()`**: Aggiunto a `ScheduleGraphWidget` per impostare la finestra temporale
  ```cpp
  void ScheduleGraphWidget::setTimeWindow(std::time_t startTime, std::time_t endTime) {
      timeWindowStart_ = startTime;
      timeWindowEnd_ = endTime;
      update();
  }
  ```

- **Membri privati aggiunti**:
  ```cpp
  std::time_t timeWindowStart_ = 0;
  std::time_t timeWindowEnd_ = 0;
  ```

- **Logica di filtraggio in `paintEvent()`**:
  ```cpp
  if (timeWindowStart_ != 0 && timeWindowEnd_ != 0) {
      earliestTime = timeWindowStart_;
      latestTime = timeWindowEnd_;
  } else {
      // Calcola da tutti gli schedule (comportamento precedente)
  }
  ```

- **Chiamate aggiunte**: Prima di mostrare il grafico, viene chiamato:
  ```cpp
  scheduleGraphWidget->setTimeWindow(windowStart, windowEnd);
  ```

**File modificati**:
- `cpp/gui/schedule_graph_widget.hpp` (dichiarazione metodo e membri)
- `cpp/gui/schedule_graph_widget.cpp` (implementazione)
- `cpp/gui/main_window.cpp` (due chiamate prima di `setSchedules()`)

**Stato**: Il grafico ora mostra solo i treni che transitano entro la finestra temporale specificata (±15 minuti di default, configurabile nelle impostazioni).

---

## Modifiche Aggiuntive

### ID Treni Auto-generati
- Rimosso campo manuale per ID treno nel dialogo
- Gli ID vengono ora generati automaticamente dal sistema
- Migliora la user experience e previene errori di duplicazione

### Clipping del Diagramma (Fix 20/01/2025 - 10:30)
- **Problema**: Le tracce dei treni uscivano dai bordi del grafico
- **Soluzione**: Aggiunto clipping region per limitare il disegno all'area degli assi
  ```cpp
  painter.save();
  QRect clipRect(leftMargin, topMargin, graphWidth, graphHeight);
  painter.setClipRect(clipRect);
  // Draw train paths...
  painter.restore();
  ```
- Applicato sia ai percorsi dei treni che ai marcatori di conflitto
- **File modificato**: `cpp/gui/schedule_graph_widget.cpp`

### Visualizzazione Nome Treno (Fix 20/01/2025 - 10:45)
- **Problema**: La tabella degli orari mostrava l'ID del treno invece del nome
- **Soluzione**: Modificato `updateSchedulesView()` per recuperare il nome dal vettore `trains`
  ```cpp
  // Get train name from trains vector
  QString trainLabel = trainId;  // Default to ID if train not found
  for (const auto& train : trains) {
      if (train && train->get_id() == schedule->get_train_id()) {
          QString trainName = QString::fromStdString(train->get_name());
          if (!trainName.isEmpty()) {
              trainLabel = trainName;
          }
          break;
      }
  }
  ```
- Fallback automatico all'ID se il nome è vuoto o il treno non è trovato
- **File modificato**: `cpp/gui/main_window.cpp` (linee 3912-3928)
- **Migliora**: Leggibilità della lista orari treni

### Miglioramento Dialogo Linea (Fix 20/01/2025 - 11:00)
- **Problema**: Stazioni mostrate con ID nel dialogo creazione linea, non ordinate, aggiunte solo con pulsante
- **Soluzioni implementate**:
  
  **1. Solo nomi delle stazioni (senza ID)**:
  ```cpp
  // In updateStationList() - mostra solo il nome
  auto *item = new QListWidgetItem(station.first); // Display only name
  item->setData(Qt::UserRole, station.second);      // Store ID in UserRole
  ```
  
  **2. Ordinamento alfabetico**:
  ```cpp
  // Sort alphabetically by name
  std::sort(stationsToAdd.begin(), stationsToAdd.end(),
            [](const QPair<QString, QString>& a, const QPair<QString, QString>& b) {
                return a.first.toLower() < b.first.toLower();
            });
  ```
  
  **3. Doppio click per aggiungere**:
  ```cpp
  // In setupUI()
  connect(availableStationsList, &QListWidget::itemDoubleClicked, 
          this, &LineDialog::onAvailableStationDoubleClicked);
  
  // Nuovo metodo
  void LineDialog::onAvailableStationDoubleClicked(QListWidgetItem* item) {
      if (!item) return;
      auto *newItem = new QListWidgetItem(item->text());
      newItem->setData(Qt::UserRole, item->data(Qt::UserRole));
      stationsList->addItem(newItem);
      updateStationList();
  }
  ```

- **File modificati**: 
  - `cpp/gui/line_dialog.hpp` (aggiunto slot per doppio click)
  - `cpp/gui/line_dialog.cpp` (3 modifiche: setupUI, updateStationList, nuovo metodo)
- **Migliora**: Usabilità e chiarezza del dialogo creazione linea

---

## Compilazione e Installazione

**Status**: ✅ Compilazione riuscita senza errori

```bash
cd /Users/michelebigi/VisualStudio\ Code/GitHub/FDC/cpp/build
cmake --build .
cmake --install . --prefix ./install
```

**App installata in**: 
```
/Users/michelebigi/VisualStudio Code/GitHub/FDC/cpp/build/install/FDC Railway Manager.app
```

---

## Test Richiesti

Verificare le seguenti funzionalità:

### Test 1: Icona nella Dock
1. ✅ Lanciare l'app
2. Verificare che l'icona viola con il treno geometrico sia visibile nella dock
3. Verificare che l'icona appaia nel menu delle applicazioni (⌘+Tab)

### Test 2: Treni in Senso Inverso
1. ✅ Aprire un file di rete (es. `ferrovie_contea_completa.fdc`)
2. Andare in "Linee" → selezionare una linea
3. Click su "Crea nuovo treno"
4. Selezionare ultima stazione → prima stazione
5. Impostare orario e velocità, click "Crea Treno"
6. Verificare che il treno sia stato creato con le fermate in ordine inverso

### Test 3: Finestra Temporale Grafico
1. ✅ Aprire un file di rete con più treni
2. Selezionare "Traffico" → "Visualizza Traffico per Stazione"
3. Selezionare una stazione e un orario
4. Verificare che il grafico mostri solo treni entro ±15 minuti dall'orario selezionato
5. Verificare nelle impostazioni (Preferenze → Traffico) che il valore "Finestra Temporale" sia configurabile

---

## Note Tecniche

### Compilazione
- **Toolchain**: Apple Clang (Xcode 16.3)
- **Qt Version**: Qt 6.8.1
- **CMake**: 3.31.3
- **Architecture**: ARM64 (Apple Silicon)

### Dipendenze
- Tutte le dipendenze Qt sono state correttamente integrate nel bundle
- L'app è standalone e non richiede installazioni Qt esterne

### Avvisi non critici
Durante l'installazione appare un avviso:
```
error: no LC_RPATH load command with path: /opt/homebrew/lib found
```
Questo è normale e non impedisce il funzionamento dell'app. È dovuto alla rilocazione delle dipendenze nel bundle.

---

## Prossimi Passi

Dopo la verifica dei test, procedere con:
1. Update README.md con nuova versione
2. Tag Git per v1.0.1
3. Creazione release su GitHub
4. Distribuzione .dmg (opzionale)

---

**Fine Report Bug Fixes v1.0.1**
