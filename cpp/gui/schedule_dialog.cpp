#include "schedule_dialog.hpp"
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QFormLayout>
#include <QGroupBox>
#include <QMessageBox>
#include <QHeaderView>
#include <QTimeEdit>
#include <QSpinBox>
#include <QCheckBox>
#include <algorithm>

ScheduleDialog::ScheduleDialog(
    std::shared_ptr<RailwayNetwork> network,
    const std::vector<std::shared_ptr<Train>>& trains,
    QWidget* parent)
    : QDialog(parent), network(network), trains(trains), existingSchedule(nullptr)
{
    setupUI();
    setWindowTitle("Nuovo Orario Treno");
}

ScheduleDialog::ScheduleDialog(
    std::shared_ptr<RailwayNetwork> network,
    const std::vector<std::shared_ptr<Train>>& trains,
    std::shared_ptr<TrainSchedule> schedule,
    QWidget* parent)
    : QDialog(parent), network(network), trains(trains), existingSchedule(schedule)
{
    setupUI();
    setWindowTitle("Modifica Orario Treno");
    
    // Load existing schedule data
    if (schedule) {
        // Find and select train
        for (int i = 0; i < trainCombo->count(); ++i) {
            if (trainCombo->itemData(i).toString().toStdString() == schedule->get_train_id()) {
                trainCombo->setCurrentIndex(i);
                break;
            }
        }
        
        // Load stops
        stops = schedule->get_stops();
        updateStopsTable();
    }
}

void ScheduleDialog::setupUI() {
    auto* mainLayout = new QVBoxLayout(this);
    
    // Train selection group
    auto* trainGroup = new QGroupBox("Selezione Treno");
    auto* trainLayout = new QVBoxLayout(trainGroup);
    
    auto* trainSelectLayout = new QHBoxLayout();
    trainSelectLayout->addWidget(new QLabel("Treno:"));
    trainCombo = new QComboBox();
    populateTrainCombo();
    connect(trainCombo, QOverload<int>::of(&QComboBox::currentIndexChanged), 
            this, &ScheduleDialog::onTrainChanged);
    trainSelectLayout->addWidget(trainCombo, 1);
    trainLayout->addLayout(trainSelectLayout);
    
    trainInfoLabel = new QLabel();
    trainInfoLabel->setStyleSheet("color: #666; font-style: italic;");
    trainLayout->addWidget(trainInfoLabel);
    onTrainChanged(trainCombo->currentIndex());
    
    mainLayout->addWidget(trainGroup);
    
    // Start time group
    auto* timeGroup = new QGroupBox("Orario di Partenza");
    auto* timeLayout = new QHBoxLayout(timeGroup);
    timeLayout->addWidget(new QLabel("Data e Ora:"));
    startTimeEdit = new QDateTimeEdit(QDateTime::currentDateTime());
    startTimeEdit->setDisplayFormat("dd/MM/yyyy HH:mm");
    startTimeEdit->setCalendarPopup(true);
    timeLayout->addWidget(startTimeEdit, 1);
    mainLayout->addWidget(timeGroup);
    
    // Stops table group
    auto* stopsGroup = new QGroupBox("Fermate");
    auto* stopsLayout = new QVBoxLayout(stopsGroup);
    
    stopsTable = new QTableWidget(0, 5);
    stopsTable->setHorizontalHeaderLabels({"Stazione", "Arrivo", "Partenza", "Binario", "Fermata"});
    stopsTable->horizontalHeader()->setStretchLastSection(false);
    stopsTable->horizontalHeader()->setSectionResizeMode(0, QHeaderView::Stretch);
    stopsTable->horizontalHeader()->setSectionResizeMode(1, QHeaderView::ResizeToContents);
    stopsTable->horizontalHeader()->setSectionResizeMode(2, QHeaderView::ResizeToContents);
    stopsTable->horizontalHeader()->setSectionResizeMode(3, QHeaderView::ResizeToContents);
    stopsTable->horizontalHeader()->setSectionResizeMode(4, QHeaderView::ResizeToContents);
    stopsTable->setSelectionBehavior(QTableWidget::SelectRows);
    stopsTable->setSelectionMode(QTableWidget::SingleSelection);
    connect(stopsTable, &QTableWidget::itemSelectionChanged, 
            this, &ScheduleDialog::onStopSelectionChanged);
    stopsLayout->addWidget(stopsTable);
    
    // Buttons for stop management
    auto* stopButtonsLayout = new QHBoxLayout();
    addStopButton = new QPushButton("➕ Aggiungi Fermata");
    removeStopButton = new QPushButton("➖ Rimuovi Fermata");
    moveUpButton = new QPushButton("⬆️ Sposta Su");
    moveDownButton = new QPushButton("⬇️ Sposta Giù");
    
    connect(addStopButton, &QPushButton::clicked, this, &ScheduleDialog::onAddStop);
    connect(removeStopButton, &QPushButton::clicked, this, &ScheduleDialog::onRemoveStop);
    connect(moveUpButton, &QPushButton::clicked, this, &ScheduleDialog::onMoveStopUp);
    connect(moveDownButton, &QPushButton::clicked, this, &ScheduleDialog::onMoveStopDown);
    
    stopButtonsLayout->addWidget(addStopButton);
    stopButtonsLayout->addWidget(removeStopButton);
    stopButtonsLayout->addWidget(moveUpButton);
    stopButtonsLayout->addWidget(moveDownButton);
    stopButtonsLayout->addStretch();
    stopsLayout->addLayout(stopButtonsLayout);
    
    // Auto-calculation buttons
    auto* autoButtonsLayout = new QHBoxLayout();
    calculateTimesButton = new QPushButton("🕒 Calcola Tempi Automaticamente");
    autoAssignButton = new QPushButton("🎯 Assegna Binari Automaticamente");
    
    connect(calculateTimesButton, &QPushButton::clicked, this, &ScheduleDialog::onCalculateTimes);
    connect(autoAssignButton, &QPushButton::clicked, this, &ScheduleDialog::onAutoAssignPlatforms);
    
    autoButtonsLayout->addWidget(calculateTimesButton);
    autoButtonsLayout->addWidget(autoAssignButton);
    stopsLayout->addLayout(autoButtonsLayout);
    
    mainLayout->addWidget(stopsGroup);
    
    // Summary label
    summaryLabel = new QLabel();
    summaryLabel->setStyleSheet("background-color: #f0f0f0; padding: 8px; border-radius: 4px;");
    mainLayout->addWidget(summaryLabel);
    
    // Dialog buttons
    auto* buttonLayout = new QHBoxLayout();
    auto* okButton = new QPushButton("OK");
    auto* cancelButton = new QPushButton("Annulla");
    
    connect(okButton, &QPushButton::clicked, this, &QDialog::accept);
    connect(cancelButton, &QPushButton::clicked, this, &QDialog::reject);
    
    buttonLayout->addStretch();
    buttonLayout->addWidget(okButton);
    buttonLayout->addWidget(cancelButton);
    mainLayout->addLayout(buttonLayout);
    
    updateButtonStates();
    resize(900, 600);
}

void ScheduleDialog::populateTrainCombo() {
    trainCombo->clear();
    
    for (const auto& train : trains) {
        QString label = QString::fromStdString(
            train->get_id() + " - " + train->get_name() + " (" + 
            train_type_to_string(train->get_type()) + ")"
        );
        trainCombo->addItem(label, QString::fromStdString(train->get_id()));
    }
}

void ScheduleDialog::onTrainChanged(int index) {
    if (index < 0) {
        trainInfoLabel->clear();
        return;
    }
    
    auto train = getSelectedTrain();
    if (train) {
        QString info = QString("Velocità Max: %1 km/h | Accelerazione: %2 m/s² | Decelerazione: %3 m/s²")
            .arg(train->get_max_speed(), 0, 'f', 1)
            .arg(train->get_acceleration(), 0, 'f', 2)
            .arg(train->get_deceleration(), 0, 'f', 2);
        trainInfoLabel->setText(info);
    }
}

void ScheduleDialog::onAddStop() {
    // Create dialog to select station
    QDialog dialog(this);
    dialog.setWindowTitle("Aggiungi Fermata");
    
    auto* layout = new QVBoxLayout(&dialog);
    
    auto* formLayout = new QFormLayout();
    
    // Station selection
    auto* stationCombo = new QComboBox();
    auto nodes = network->get_all_nodes();
    for (const auto& node : nodes) {
        stationCombo->addItem(
            QString::fromStdString(node->get_id() + " - " + node->get_name()),
            QString::fromStdString(node->get_id())
        );
    }
    formLayout->addRow("Stazione:", stationCombo);
    
    // Arrival time
    auto* arrivalEdit = new QDateTimeEdit(startTimeEdit->dateTime());
    arrivalEdit->setDisplayFormat("dd/MM/yyyy HH:mm");
    formLayout->addRow("Arrivo:", arrivalEdit);
    
    // Departure time
    auto* departureEdit = new QDateTimeEdit(startTimeEdit->dateTime().addSecs(120)); // +2 min default
    departureEdit->setDisplayFormat("dd/MM/yyyy HH:mm");
    formLayout->addRow("Partenza:", departureEdit);
    
    // Platform
    auto* platformSpin = new QSpinBox();
    platformSpin->setMinimum(0);
    platformSpin->setMaximum(50);
    platformSpin->setSpecialValueText("Auto");
    platformSpin->setValue(0);
    formLayout->addRow("Binario:", platformSpin);
    
    // Is stop checkbox
    auto* isStopCheck = new QCheckBox("È una fermata (non transito)");
    isStopCheck->setChecked(true);
    formLayout->addRow("", isStopCheck);
    
    layout->addLayout(formLayout);
    
    auto* buttonLayout = new QHBoxLayout();
    auto* okButton = new QPushButton("OK");
    auto* cancelButton = new QPushButton("Annulla");
    connect(okButton, &QPushButton::clicked, &dialog, &QDialog::accept);
    connect(cancelButton, &QPushButton::clicked, &dialog, &QDialog::reject);
    buttonLayout->addStretch();
    buttonLayout->addWidget(okButton);
    buttonLayout->addWidget(cancelButton);
    layout->addLayout(buttonLayout);
    
    if (dialog.exec() == QDialog::Accepted) {
        std::string stationId = stationCombo->currentData().toString().toStdString();
        
        // Convert QDateTime to time_point
        auto arrival = std::chrono::system_clock::from_time_t(arrivalEdit->dateTime().toSecsSinceEpoch());
        auto departure = std::chrono::system_clock::from_time_t(departureEdit->dateTime().toSecsSinceEpoch());
        
        ScheduleStop stop(stationId, arrival, departure, isStopCheck->isChecked());
        if (platformSpin->value() > 0) {
            stop.set_platform(platformSpin->value());
        }
        
        stops.push_back(stop);
        updateStopsTable();
        updateButtonStates();
    }
}

void ScheduleDialog::onRemoveStop() {
    int currentRow = stopsTable->currentRow();
    if (currentRow >= 0 && currentRow < static_cast<int>(stops.size())) {
        stops.erase(stops.begin() + currentRow);
        updateStopsTable();
        updateButtonStates();
    }
}

void ScheduleDialog::onMoveStopUp() {
    int currentRow = stopsTable->currentRow();
    if (currentRow > 0) {
        std::swap(stops[currentRow], stops[currentRow - 1]);
        updateStopsTable();
        stopsTable->selectRow(currentRow - 1);
    }
}

void ScheduleDialog::onMoveStopDown() {
    int currentRow = stopsTable->currentRow();
    if (currentRow >= 0 && currentRow < static_cast<int>(stops.size()) - 1) {
        std::swap(stops[currentRow], stops[currentRow + 1]);
        updateStopsTable();
        stopsTable->selectRow(currentRow + 1);
    }
}

void ScheduleDialog::onCalculateTimes() {
    if (stops.empty()) {
        QMessageBox::warning(this, "Attenzione", "Aggiungi almeno una fermata prima di calcolare i tempi.");
        return;
    }
    
    auto train = getSelectedTrain();
    if (!train) {
        QMessageBox::warning(this, "Attenzione", "Seleziona un treno.");
        return;
    }
    
    // Use ScheduleBuilder for automatic time calculation
    ScheduleBuilder builder(train->get_id(), "SCH_TEMP", network, train);
    
    auto startTime = std::chrono::system_clock::from_time_t(startTimeEdit->dateTime().toSecsSinceEpoch());
    builder.set_start_time(startTime);
    
    // Add stops with automatic time calculation
    for (const auto& stop : stops) {
        int dwellSeconds = std::chrono::duration_cast<std::chrono::seconds>(
            stop.get_departure() - stop.get_arrival()
        ).count();
        builder.add_stop_auto(stop.get_node_id(), std::chrono::seconds(dwellSeconds));
    }
    
    try {
        auto schedule = builder.build();
        stops = schedule->get_stops();
        updateStopsTable();
        QMessageBox::information(this, "Successo", "Tempi calcolati automaticamente in base alla rete e alle prestazioni del treno.");
    } catch (const std::exception& e) {
        QMessageBox::critical(this, "Errore", QString("Errore nel calcolo automatico: %1").arg(e.what()));
    }
}

void ScheduleDialog::onAutoAssignPlatforms() {
    if (stops.empty()) {
        QMessageBox::warning(this, "Attenzione", "Aggiungi almeno una fermata prima di assegnare i binari.");
        return;
    }
    
    // Clear existing platform schedules
    for (auto& node : network->get_all_nodes()) {
        node->clear_platform_schedule();
    }
    
    // Try to assign platforms
    bool allAssigned = true;
    for (auto& stop : stops) {
        auto node = network->get_node(stop.get_node_id());
        if (node) {
            auto platform = node->get_available_platform(
                stop.get_arrival(),
                stop.get_departure()
            );
            
            if (platform) {
                stop.set_platform(*platform);
                node->reserve_platform(*platform, "temp", 
                                     stop.get_arrival(),
                                     stop.get_departure());
            } else {
                allAssigned = false;
            }
        }
    }
    
    updateStopsTable();
    
    if (allAssigned) {
        QMessageBox::information(this, "Successo", "Binari assegnati automaticamente per tutte le fermate.");
    } else {
        QMessageBox::warning(this, "Attenzione", "Alcuni binari non sono stati assegnati. Potrebbero non essere disponibili.");
    }
}

void ScheduleDialog::onStopSelectionChanged() {
    updateButtonStates();
}

void ScheduleDialog::updateStopsTable() {
    stopsTable->setRowCount(0);
    
    double totalDistance = 0.0;
    std::chrono::seconds totalDuration(0);
    
    for (size_t i = 0; i < stops.size(); ++i) {
        const auto& stop = stops[i];
        int row = stopsTable->rowCount();
        stopsTable->insertRow(row);
        
        // Station name
        auto node = network->get_node(stop.get_node_id());
        QString stationName = node ? QString::fromStdString(node->get_name()) 
                                   : QString::fromStdString(stop.get_node_id());
        stopsTable->setItem(row, 0, new QTableWidgetItem(stationName));
        
        // Arrival time
        auto arrivalTime = std::chrono::system_clock::to_time_t(stop.get_arrival());
        QDateTime arrivalQt = QDateTime::fromSecsSinceEpoch(arrivalTime);
        stopsTable->setItem(row, 1, new QTableWidgetItem(arrivalQt.toString("dd/MM HH:mm")));
        
        // Departure time
        auto departureTime = std::chrono::system_clock::to_time_t(stop.get_departure());
        QDateTime departureQt = QDateTime::fromSecsSinceEpoch(departureTime);
        stopsTable->setItem(row, 2, new QTableWidgetItem(departureQt.toString("dd/MM HH:mm")));
        
        // Platform
        auto platform = stop.get_platform();
        stopsTable->setItem(row, 3, new QTableWidgetItem(
            platform ? QString::number(*platform) : "Auto"
        ));
        
        // Is stop
        stopsTable->setItem(row, 4, new QTableWidgetItem(stop.is_stop() ? "✓" : ""));
        
        // Calculate distance from previous stop
        if (i > 0) {
            double dist = network->calculate_distance(stops[i-1].get_node_id(), stop.get_node_id());
            if (dist > 0) {
                totalDistance += dist;
            }
        }
        
        if (i == stops.size() - 1) {
            totalDuration = std::chrono::duration_cast<std::chrono::seconds>(
                stop.get_departure() - stops[0].get_arrival()
            );
        }
    }
    
    // Update summary
    if (!stops.empty()) {
        int hours = totalDuration.count() / 3600;
        int minutes = (totalDuration.count() % 3600) / 60;
        double avgSpeed = totalDistance > 0 && totalDuration.count() > 0 
            ? (totalDistance / (totalDuration.count() / 3600.0)) : 0.0;
        
        QString summary = QString("📊 Fermate: %1 | Distanza: %2 km | Durata: %3h %4m | Velocità Media: %5 km/h")
            .arg(stops.size())
            .arg(totalDistance, 0, 'f', 1)
            .arg(hours)
            .arg(minutes)
            .arg(avgSpeed, 0, 'f', 1);
        summaryLabel->setText(summary);
    } else {
        summaryLabel->setText("📊 Nessuna fermata aggiunta");
    }
}

void ScheduleDialog::updateButtonStates() {
    int currentRow = stopsTable->currentRow();
    bool hasSelection = currentRow >= 0;
    bool hasStops = !stops.empty();
    
    removeStopButton->setEnabled(hasSelection);
    moveUpButton->setEnabled(hasSelection && currentRow > 0);
    moveDownButton->setEnabled(hasSelection && currentRow < static_cast<int>(stops.size()) - 1);
    calculateTimesButton->setEnabled(hasStops);
    autoAssignButton->setEnabled(hasStops);
}

std::shared_ptr<Train> ScheduleDialog::getSelectedTrain() const {
    if (trainCombo->currentIndex() < 0) return nullptr;
    
    std::string trainId = trainCombo->currentData().toString().toStdString();
    for (const auto& train : trains) {
        if (train->get_id() == trainId) {
            return train;
        }
    }
    return nullptr;
}

std::shared_ptr<TrainSchedule> ScheduleDialog::getSchedule() const {
    auto train = getSelectedTrain();
    if (!train) return nullptr;
    
    // Generate temporary schedule ID (will be set by MainWindow)
    std::string scheduleId = "SCH_TEMP";
    auto schedule = std::make_shared<TrainSchedule>(train->get_id(), scheduleId, network);
    for (const auto& stop : stops) {
        schedule->add_stop(stop);
    }
    
    return schedule;
}

bool ScheduleDialog::validate() {
    if (!getSelectedTrain()) {
        QMessageBox::warning(const_cast<ScheduleDialog*>(this), "Errore", "Seleziona un treno.");
        return false;
    }
    
    if (stops.size() < 2) {
        QMessageBox::warning(const_cast<ScheduleDialog*>(this), "Errore", 
                           "L'orario deve avere almeno 2 fermate.");
        return false;
    }
    
    // Validate chronological order
    for (size_t i = 1; i < stops.size(); ++i) {
        if (stops[i].get_arrival() <= stops[i-1].get_departure()) {
            QMessageBox::warning(const_cast<ScheduleDialog*>(this), "Errore",
                QString("Le fermate devono essere in ordine cronologico. Problema alla fermata %1.")
                .arg(i + 1));
            return false;
        }
    }
    
    return true;
}
