#include "main_window.hpp"
#include <QApplication>
#include <QScreen>
#include <QMenuBar>
#include <QToolBar>
#include <QStatusBar>
#include <QTabWidget>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QGroupBox>
#include <algorithm>
#include <QSplitter>
#include <QPushButton>
#include <QLabel>
#include <QComboBox>
#include <QHeaderView>
#include <QFileDialog>
#include <QMessageBox>
#include <QCloseEvent>
#include <QInputDialog>
#include <QColorDialog>
#include <QDateTimeEdit>
#include <QSpinBox>
#include <QFormLayout>
#include <QDialog>
#include <QDialogButtonBox>
#include <fstream>

namespace fdc {

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
    , tabWidget(nullptr)
    , stationsTable(nullptr)
    , stationsModel(nullptr)
    , connectionsTable(nullptr)
    , connectionsModel(nullptr)
    , linesListView(nullptr)
    , linesModel(nullptr)
    , lineDetailsText(nullptr)
    , schedulesTreeView(nullptr)
    , schedulesModel(nullptr)
    , scheduleDetailsText(nullptr)
    , lineFilterCombo(nullptr)
    , network(std::make_shared<RailwayNetwork>())
    , isModified(false)
{
    setupUI();
    setupMenuBar();
    setupToolBar();
    setupStatusBar();
    createConnections();
    
    updateWindowTitle();
    resize(DEFAULT_WIDTH, DEFAULT_HEIGHT);
    
    // Centro la finestra sullo schermo (stile macOS) - Qt6
    QScreen *screen = QApplication::primaryScreen();
    if (screen) {
        QRect screenGeometry = screen->geometry();
        int x = (screenGeometry.width() - DEFAULT_WIDTH) / 2;
        int y = (screenGeometry.height() - DEFAULT_HEIGHT) / 2;
        move(x, y);
    }
}

MainWindow::~MainWindow() = default;

void MainWindow::setupUI() {
    // Central widget con tab
    tabWidget = new QTabWidget(this);
    setCentralWidget(tabWidget);
    
    // Stile macOS: tabs in alto, bordi arrotondati
    tabWidget->setDocumentMode(true);
    tabWidget->setTabPosition(QTabWidget::North);
    
    // Setup dei tre tab principali
    setupNetworkTab();
    setupLinesTab();
    setupSchedulesTab();
}

void MainWindow::setupMenuBar() {
    // File Menu
    QMenu *fileMenu = menuBar()->addMenu(tr("&File"));
    
    QAction *newAction = fileMenu->addAction(tr("&Nuovo Progetto"));
    newAction->setShortcut(QKeySequence::New); // Cmd+N su macOS
    connect(newAction, &QAction::triggered, this, &MainWindow::newProject);
    
    QAction *openAction = fileMenu->addAction(tr("&Apri Progetto..."));
    openAction->setShortcut(QKeySequence::Open); // Cmd+O
    connect(openAction, &QAction::triggered, this, &MainWindow::openProject);
    
    fileMenu->addSeparator();
    
    QAction *saveAction = fileMenu->addAction(tr("&Salva"));
    saveAction->setShortcut(QKeySequence::Save); // Cmd+S
    connect(saveAction, &QAction::triggered, this, &MainWindow::saveProject);
    
    QAction *saveAsAction = fileMenu->addAction(tr("Salva &con Nome..."));
    saveAsAction->setShortcut(QKeySequence::SaveAs); // Cmd+Shift+S
    connect(saveAsAction, &QAction::triggered, this, &MainWindow::saveProjectAs);
    
    fileMenu->addSeparator();
    
    QAction *quitAction = fileMenu->addAction(tr("&Esci"));
    quitAction->setShortcut(QKeySequence::Quit); // Cmd+Q
    connect(quitAction, &QAction::triggered, this, &QWidget::close);
    
    // View Menu
    QMenu *viewMenu = menuBar()->addMenu(tr("&Visualizza"));
    
    QAction *networkMapAction = viewMenu->addAction(tr("Mappa &Rete"));
    networkMapAction->setShortcut(QKeySequence(tr("Cmd+1")));
    connect(networkMapAction, &QAction::triggered, this, &MainWindow::showNetworkMap);
    
    QAction *timetableAction = viewMenu->addAction(tr("&Grafico Orario"));
    timetableAction->setShortcut(QKeySequence(tr("Cmd+2")));
    connect(timetableAction, &QAction::triggered, this, &MainWindow::showTimetableGraph);
    
    viewMenu->addSeparator();
    
    QAction *refreshAction = viewMenu->addAction(tr("&Aggiorna"));
    refreshAction->setShortcut(QKeySequence::Refresh); // Cmd+R o F5
    connect(refreshAction, &QAction::triggered, this, &MainWindow::refreshViews);
    
    // Database Menu (placeholder per fase 7)
    QMenu *dbMenu = menuBar()->addMenu(tr("&Database"));
    
    QAction *connectDbAction = dbMenu->addAction(tr("&Connetti a MySQL..."));
    connect(connectDbAction, &QAction::triggered, this, &MainWindow::connectToDatabase);
    
    QAction *saveDbAction = dbMenu->addAction(tr("&Salva nel Database"));
    connect(saveDbAction, &QAction::triggered, this, &MainWindow::saveToDatabase);
    
    QAction *loadDbAction = dbMenu->addAction(tr("&Carica dal Database..."));
    connect(loadDbAction, &QAction::triggered, this, &MainWindow::loadFromDatabase);
    
    dbMenu->addSeparator();
    
    QAction *dbStatusAction = dbMenu->addAction(tr("Stato &Connessione"));
    connect(dbStatusAction, &QAction::triggered, this, &MainWindow::showDatabaseStatus);
    
    // Help Menu
    QMenu *helpMenu = menuBar()->addMenu(tr("&Aiuto"));
    
    QAction *docsAction = helpMenu->addAction(tr("&Documentazione"));
    docsAction->setShortcut(QKeySequence::HelpContents); // Cmd+?
    connect(docsAction, &QAction::triggered, this, &MainWindow::showDocumentation);
    
    helpMenu->addSeparator();
    
    QAction *aboutAction = helpMenu->addAction(tr("&Informazioni su FDC"));
    connect(aboutAction, &QAction::triggered, this, &MainWindow::showAboutDialog);
}

void MainWindow::setupToolBar() {
    QToolBar *toolbar = addToolBar(tr("Strumenti"));
    
    // Stile macOS: icone grandi, unified toolbar
    toolbar->setToolButtonStyle(Qt::ToolButtonTextUnderIcon);
    toolbar->setIconSize(QSize(32, 32));
    toolbar->setMovable(false);
    
    // Su macOS, usa stile unificato con title bar
    #ifdef Q_OS_MAC
    setUnifiedTitleAndToolBarOnMac(true);
    #endif
    
    // Nuova Stazione
    actionNewStation = toolbar->addAction(tr("🏢\nStazione"));
    actionNewStation->setToolTip(tr("Aggiungi nuova stazione (Cmd+Shift+S)"));
    connect(actionNewStation, &QAction::triggered, this, &MainWindow::addStation);
    
    // Nuova Connessione
    actionNewConnection = toolbar->addAction(tr("🛤️\nConnessione"));
    actionNewConnection->setToolTip(tr("Aggiungi nuova connessione (Cmd+Shift+C)"));
    connect(actionNewConnection, &QAction::triggered, this, &MainWindow::addConnection);
    
    toolbar->addSeparator();
    
    // Nuova Linea
    actionNewLine = toolbar->addAction(tr("📍\nLinea"));
    actionNewLine->setToolTip(tr("Aggiungi nuova linea (Cmd+Shift+L)"));
    connect(actionNewLine, &QAction::triggered, this, &MainWindow::addLine);
    
    // Nuovo Treno
    actionNewTrain = toolbar->addAction(tr("🚂\nTreno"));
    actionNewTrain->setToolTip(tr("Aggiungi nuovo treno (Cmd+Shift+T)"));
    connect(actionNewTrain, &QAction::triggered, this, &MainWindow::addSchedule);
}

void MainWindow::setupStatusBar() {
    statusBar()->showMessage(tr("Pronto"));
}

void MainWindow::setupNetworkTab() {
    QWidget *networkWidget = new QWidget();
    QVBoxLayout *mainLayout = new QVBoxLayout(networkWidget);
    
    // Splitter orizzontale per stazioni e connessioni
    QSplitter *splitter = new QSplitter(Qt::Vertical);
    
    // === SEZIONE STAZIONI ===
    QGroupBox *stationsGroup = new QGroupBox(tr("Stazioni"));
    QVBoxLayout *stationsLayout = new QVBoxLayout();
    
    // Tabella stazioni
    stationsTable = new QTableView();
    stationsModel = new QStandardItemModel(0, 6, this);
    stationsModel->setHorizontalHeaderLabels({
        tr("ID"), tr("Nome"), tr("Tipo"), 
        tr("Latitudine"), tr("Longitudine"), tr("Binari")
    });
    stationsTable->setModel(stationsModel);
    stationsTable->setSelectionBehavior(QAbstractItemView::SelectRows);
    stationsTable->setSelectionMode(QAbstractItemView::SingleSelection);
    stationsTable->horizontalHeader()->setStretchLastSection(true);
    stationsTable->setAlternatingRowColors(true);
    stationsLayout->addWidget(stationsTable);
    
    // Pulsanti stazioni
    QHBoxLayout *stationButtonsLayout = new QHBoxLayout();
    QPushButton *addStationBtn = new QPushButton(tr("Aggiungi"));
    QPushButton *editStationBtn = new QPushButton(tr("Modifica"));
    QPushButton *deleteStationBtn = new QPushButton(tr("Elimina"));
    connect(addStationBtn, &QPushButton::clicked, this, &MainWindow::addStation);
    connect(editStationBtn, &QPushButton::clicked, this, &MainWindow::editStation);
    connect(deleteStationBtn, &QPushButton::clicked, this, &MainWindow::deleteStation);
    stationButtonsLayout->addWidget(addStationBtn);
    stationButtonsLayout->addWidget(editStationBtn);
    stationButtonsLayout->addWidget(deleteStationBtn);
    stationButtonsLayout->addStretch();
    stationsLayout->addLayout(stationButtonsLayout);
    
    stationsGroup->setLayout(stationsLayout);
    splitter->addWidget(stationsGroup);
    
    // === SEZIONE CONNESSIONI ===
    QGroupBox *connectionsGroup = new QGroupBox(tr("Connessioni"));
    QVBoxLayout *connectionsLayout = new QVBoxLayout();
    
    // Tabella connessioni
    connectionsTable = new QTableView();
    connectionsModel = new QStandardItemModel(0, 6, this);
    connectionsModel->setHorizontalHeaderLabels({
        tr("Da"), tr("A"), tr("Distanza (km)"), 
        tr("Tipo Binario"), tr("Vel. Max (km/h)"), tr("Bidirezionale")
    });
    connectionsTable->setModel(connectionsModel);
    connectionsTable->setSelectionBehavior(QAbstractItemView::SelectRows);
    connectionsTable->setSelectionMode(QAbstractItemView::SingleSelection);
    connectionsTable->horizontalHeader()->setStretchLastSection(true);
    connectionsTable->setAlternatingRowColors(true);
    connectionsLayout->addWidget(connectionsTable);
    
    // Pulsanti connessioni
    QHBoxLayout *connectionButtonsLayout = new QHBoxLayout();
    QPushButton *addConnectionBtn = new QPushButton(tr("Aggiungi"));
    QPushButton *editConnectionBtn = new QPushButton(tr("Modifica"));
    QPushButton *deleteConnectionBtn = new QPushButton(tr("Elimina"));
    connect(addConnectionBtn, &QPushButton::clicked, this, &MainWindow::addConnection);
    connect(editConnectionBtn, &QPushButton::clicked, this, &MainWindow::editConnection);
    connect(deleteConnectionBtn, &QPushButton::clicked, this, &MainWindow::deleteConnection);
    connectionButtonsLayout->addWidget(addConnectionBtn);
    connectionButtonsLayout->addWidget(editConnectionBtn);
    connectionButtonsLayout->addWidget(deleteConnectionBtn);
    connectionButtonsLayout->addStretch();
    connectionsLayout->addLayout(connectionButtonsLayout);
    
    connectionsGroup->setLayout(connectionsLayout);
    splitter->addWidget(connectionsGroup);
    
    mainLayout->addWidget(splitter);
    tabWidget->addTab(networkWidget, tr("Rete Ferroviaria"));
}

void MainWindow::setupLinesTab() {
    QWidget *linesWidget = new QWidget();
    QHBoxLayout *mainLayout = new QHBoxLayout(linesWidget);
    
    // Splitter per lista linee e dettagli
    QSplitter *splitter = new QSplitter(Qt::Horizontal);
    
    // Lista linee a sinistra
    QGroupBox *linesListGroup = new QGroupBox(tr("Linee"));
    QVBoxLayout *linesListLayout = new QVBoxLayout();
    
    linesListView = new QListView();
    linesModel = new QStandardItemModel(this);
    linesListView->setModel(linesModel);
    linesListLayout->addWidget(linesListView);
    
    // Pulsanti linee
    QHBoxLayout *lineButtonsLayout = new QHBoxLayout();
    QPushButton *addLineBtn = new QPushButton(tr("Aggiungi"));
    QPushButton *editLineBtn = new QPushButton(tr("Modifica"));
    QPushButton *deleteLineBtn = new QPushButton(tr("Elimina"));
    connect(addLineBtn, &QPushButton::clicked, this, &MainWindow::addLine);
    connect(editLineBtn, &QPushButton::clicked, this, &MainWindow::editLine);
    connect(deleteLineBtn, &QPushButton::clicked, this, &MainWindow::deleteLine);
    lineButtonsLayout->addWidget(addLineBtn);
    lineButtonsLayout->addWidget(editLineBtn);
    lineButtonsLayout->addWidget(deleteLineBtn);
    linesListLayout->addLayout(lineButtonsLayout);
    
    linesListGroup->setLayout(linesListLayout);
    splitter->addWidget(linesListGroup);
    
    // Dettagli linea a destra
    QGroupBox *lineDetailsGroup = new QGroupBox(tr("Dettagli Linea"));
    QVBoxLayout *lineDetailsLayout = new QVBoxLayout();
    
    lineDetailsText = new QTextEdit();
    lineDetailsText->setReadOnly(true);
    lineDetailsLayout->addWidget(lineDetailsText);
    
    lineDetailsGroup->setLayout(lineDetailsLayout);
    splitter->addWidget(lineDetailsGroup);
    
    splitter->setStretchFactor(0, 1);
    splitter->setStretchFactor(1, 2);
    
    mainLayout->addWidget(splitter);
    tabWidget->addTab(linesWidget, tr("Linee"));
}

void MainWindow::setupSchedulesTab() {
    QWidget *schedulesWidget = new QWidget();
    QVBoxLayout *mainLayout = new QVBoxLayout(schedulesWidget);
    
    // ===== SEZIONE TRENI =====
    QGroupBox *trainsGroup = new QGroupBox(tr("📋 Parco Treni"));
    QVBoxLayout *trainsGroupLayout = new QVBoxLayout();
    
    // Tabella treni
    trainsTable = new QTableView();
    trainsModel = new QStandardItemModel(this);
    trainsModel->setHorizontalHeaderLabels({
        tr("ID"), tr("Nome"), tr("Tipo"), tr("Vel. Max"), tr("Accel."), tr("Decel.")
    });
    trainsTable->setModel(trainsModel);
    trainsTable->setAlternatingRowColors(true);
    trainsTable->setSelectionBehavior(QAbstractItemView::SelectRows);
    trainsTable->setSelectionMode(QAbstractItemView::SingleSelection);
    trainsTable->horizontalHeader()->setStretchLastSection(true);
    trainsGroupLayout->addWidget(trainsTable);
    
    // Pulsanti treni
    QHBoxLayout *trainButtonsLayout = new QHBoxLayout();
    QPushButton *addTrainBtn = new QPushButton(tr("➕ Aggiungi"));
    QPushButton *editTrainBtn = new QPushButton(tr("✏️ Modifica"));
    QPushButton *deleteTrainBtn = new QPushButton(tr("🗑️ Elimina"));
    connect(addTrainBtn, &QPushButton::clicked, this, &MainWindow::addTrain);
    connect(editTrainBtn, &QPushButton::clicked, this, &MainWindow::editTrain);
    connect(deleteTrainBtn, &QPushButton::clicked, this, &MainWindow::deleteTrain);
    trainButtonsLayout->addWidget(addTrainBtn);
    trainButtonsLayout->addWidget(editTrainBtn);
    trainButtonsLayout->addWidget(deleteTrainBtn);
    trainButtonsLayout->addStretch();
    trainsGroupLayout->addLayout(trainButtonsLayout);
    
    trainsGroup->setLayout(trainsGroupLayout);
    mainLayout->addWidget(trainsGroup);
    
    // ===== SEZIONE ORARI =====
    // Filtro per linea
    QHBoxLayout *filterLayout = new QHBoxLayout();
    filterLayout->addWidget(new QLabel(tr("Filtra per linea:")));
    lineFilterCombo = new QComboBox();
    lineFilterCombo->addItem(tr("Tutte le linee"), -1);
    connect(lineFilterCombo, QOverload<int>::of(&QComboBox::currentIndexChanged),
            this, &MainWindow::filterSchedulesByLine);
    filterLayout->addWidget(lineFilterCombo);
    filterLayout->addStretch();
    mainLayout->addLayout(filterLayout);
    
    // Splitter per tree view e dettagli
    QSplitter *splitter = new QSplitter(Qt::Horizontal);
    
    // TreeView schedules a sinistra
    QGroupBox *schedulesListGroup = new QGroupBox(tr("Treni e Orari"));
    QVBoxLayout *schedulesListLayout = new QVBoxLayout();
    
    schedulesTreeView = new QTreeView();
    schedulesModel = new QStandardItemModel(this);
    schedulesModel->setHorizontalHeaderLabels({
        tr("Treno"), tr("Tipo"), tr("Partenza"), tr("Arrivo")
    });
    schedulesTreeView->setModel(schedulesModel);
    schedulesTreeView->setAlternatingRowColors(true);
    schedulesListLayout->addWidget(schedulesTreeView);
    
    // Pulsanti schedules
    QHBoxLayout *scheduleButtonsLayout = new QHBoxLayout();
    QPushButton *addScheduleBtn = new QPushButton(tr("Aggiungi"));
    QPushButton *editScheduleBtn = new QPushButton(tr("Modifica"));
    QPushButton *deleteScheduleBtn = new QPushButton(tr("Elimina"));
    connect(addScheduleBtn, &QPushButton::clicked, this, &MainWindow::addSchedule);
    connect(editScheduleBtn, &QPushButton::clicked, this, &MainWindow::editSchedule);
    connect(deleteScheduleBtn, &QPushButton::clicked, this, &MainWindow::deleteSchedule);
    scheduleButtonsLayout->addWidget(addScheduleBtn);
    scheduleButtonsLayout->addWidget(editScheduleBtn);
    scheduleButtonsLayout->addWidget(deleteScheduleBtn);
    schedulesListLayout->addLayout(scheduleButtonsLayout);
    
    schedulesListGroup->setLayout(schedulesListLayout);
    splitter->addWidget(schedulesListGroup);
    
    // Dettagli schedule a destra
    QGroupBox *scheduleDetailsGroup = new QGroupBox(tr("Dettagli Orario"));
    QVBoxLayout *scheduleDetailsLayout = new QVBoxLayout();
    
    scheduleDetailsText = new QTextEdit();
    scheduleDetailsText->setReadOnly(true);
    scheduleDetailsLayout->addWidget(scheduleDetailsText);
    
    scheduleDetailsGroup->setLayout(scheduleDetailsLayout);
    splitter->addWidget(scheduleDetailsGroup);
    
    splitter->setStretchFactor(0, 2);
    splitter->setStretchFactor(1, 1);
    
    mainLayout->addWidget(splitter);
    tabWidget->addTab(schedulesWidget, tr("Treni e Orari"));
}

void MainWindow::createConnections() {
    // Connessioni per selezione elementi
    connect(stationsTable->selectionModel(), &QItemSelectionModel::selectionChanged,
            this, &MainWindow::onStationSelectionChanged);
    connect(connectionsTable->selectionModel(), &QItemSelectionModel::selectionChanged,
            this, &MainWindow::onConnectionSelectionChanged);
    connect(linesListView->selectionModel(), &QItemSelectionModel::selectionChanged,
            this, &MainWindow::onLineSelectionChanged);
    connect(schedulesTreeView->selectionModel(), &QItemSelectionModel::selectionChanged,
            this, &MainWindow::onScheduleSelectionChanged);
}

// ============================================================================
// PLACEHOLDER IMPLEMENTATIONS - Da completare nelle prossime iterazioni
// ============================================================================

void MainWindow::newProject() {
    if (!maybeSave()) return;
    
    network = std::make_shared<RailwayNetwork>();
    schedules.clear();
    currentFilePath.clear();
    
    updateStationsView();
    updateConnectionsView();
    updateLinesView();
    updateSchedulesView();
    setModified(false);
    
    statusBar()->showMessage(tr("Nuovo progetto creato"), 3000);
}

void MainWindow::openProject() {
    if (!maybeSave()) return;
    
    QString fileName = QFileDialog::getOpenFileName(this,
        tr("Apri Progetto"), QString(), tr("File FDC (*.fdc *.json)"));
    
    if (fileName.isEmpty()) return;
    
    try {
        // Usa la funzione di serialization.hpp
        network = load_network_from_file(fileName.toStdString());
        schedules = load_schedules_from_file(fileName.toStdString(), network);
        
        currentFilePath = fileName;
        updateStationsView();
        updateConnectionsView();
        updateLinesView();
        updateSchedulesView();
        setModified(false);
        
        statusBar()->showMessage(tr("Progetto caricato: %1").arg(fileName), 3000);
    } catch (const std::exception& e) {
        QMessageBox::critical(this, tr("Errore"),
            tr("Impossibile aprire il file:\n%1").arg(e.what()));
    }
}

void MainWindow::saveProject() {
    if (currentFilePath.isEmpty()) {
        saveProjectAs();
        return;
    }
    
    try {
        save_network_to_file(*network, currentFilePath.toStdString());
        save_schedules_to_file(schedules, currentFilePath.toStdString());
        
        setModified(false);
        statusBar()->showMessage(tr("Progetto salvato: %1").arg(currentFilePath), 3000);
    } catch (const std::exception& e) {
        QMessageBox::critical(this, tr("Errore"),
            tr("Impossibile salvare il file:\n%1").arg(e.what()));
    }
}

void MainWindow::saveProjectAs() {
    QString fileName = QFileDialog::getSaveFileName(this,
        tr("Salva Progetto"), QString(), tr("File FDC (*.fdc);;File JSON (*.json)"));
    
    if (fileName.isEmpty()) return;
    
    currentFilePath = fileName;
    saveProject();
}

void MainWindow::showNetworkMap() {
    QMessageBox::information(this, tr("Mappa Rete"),
        tr("Visualizzazione mappa rete in fase 6 (Visualizations)"));
}

void MainWindow::showTimetableGraph() {
    QMessageBox::information(this, tr("Grafico Orario"),
        tr("Visualizzazione grafico orario in fase 6 (Visualizations)"));
}

void MainWindow::refreshViews() {
    updateStationsView();
    updateConnectionsView();
    updateLinesView();
    updateSchedulesView();
    statusBar()->showMessage(tr("Viste aggiornate"), 2000);
}

void MainWindow::connectToDatabase() {
    QMessageBox::information(this, tr("Database"),
        tr("Connessione MySQL disponibile in fase 7"));
}

void MainWindow::saveToDatabase() {
    QMessageBox::information(this, tr("Database"),
        tr("Salvataggio su MySQL disponibile in fase 7"));
}

void MainWindow::loadFromDatabase() {
    QMessageBox::information(this, tr("Database"),
        tr("Caricamento da MySQL disponibile in fase 7"));
}

void MainWindow::showDatabaseStatus() {
    QMessageBox::information(this, tr("Stato Database"),
        tr("Database non connesso"));
}

void MainWindow::showAboutDialog() {
    QMessageBox::about(this, tr("Informazioni su FDC"),
        tr("<h2>FDC Railway Manager</h2>"
           "<p>Versione 0.2.0</p>"
           "<p>Sistema di gestione reti ferroviarie con:<br>"
           "• Pathfinding intelligente<br>"
           "• Schedulazione realistica<br>"
           "• Rilevamento conflitti<br>"
           "• Visualizzazioni avanzate</p>"
           "<p>© 2025 FDC Project</p>"));
}

void MainWindow::showDocumentation() {
    QMessageBox::information(this, tr("Documentazione"),
        tr("La documentazione è disponibile nella cartella docs/"));
}

void MainWindow::addStation() {
    StationDialog dialog(this);
    
    if (dialog.exec() == QDialog::Accepted) {
        auto station = dialog.getStation();
        
        // Check if station ID already exists
        if (network->has_node(station->get_id())) {
            QMessageBox::warning(this, tr("ID Duplicato"),
                tr("Esiste già una stazione con ID: %1")
                    .arg(QString::fromStdString(station->get_id())));
            return;
        }
        
        // Add station to network
        network->add_node(*station);
        
        // Update view
        updateStationsView();
        
        // Mark as modified
        isModified = true;
        updateWindowTitle();
        
        statusBar()->showMessage(
            tr("Stazione '%1' aggiunta con successo")
                .arg(QString::fromStdString(station->get_name())), 
            3000);
    }
}

void MainWindow::editStation() {
    // Get selected station
    QModelIndexList selection = stationsTable->selectionModel()->selectedRows();
    if (selection.isEmpty()) {
        QMessageBox::information(this, tr("Nessuna Selezione"),
            tr("Seleziona una stazione da modificare."));
        return;
    }
    
    // Get station ID from first column
    QModelIndex index = selection.first();
    QString stationId = stationsModel->data(
        stationsModel->index(index.row(), 0)).toString();
    
    auto station = network->get_node(stationId.toStdString());
    if (!station) {
        QMessageBox::warning(this, tr("Errore"),
            tr("Stazione non trovata."));
        return;
    }
    
    // Open dialog in edit mode
    StationDialog dialog(station, this);
    
    if (dialog.exec() == QDialog::Accepted) {
        auto updatedStation = dialog.getStation();
        
        // Remove old station and add updated one
        network->remove_node(station->get_id());
        network->add_node(*updatedStation);
        
        // Update view
        updateStationsView();
        updateConnectionsView(); // Connections might reference this station
        
        // Mark as modified
        isModified = true;
        updateWindowTitle();
        
        statusBar()->showMessage(
            tr("Stazione '%1' modificata con successo")
                .arg(QString::fromStdString(updatedStation->get_name())), 
            3000);
    }
}

void MainWindow::deleteStation() {
    // Get selected station
    QModelIndexList selection = stationsTable->selectionModel()->selectedRows();
    if (selection.isEmpty()) {
        QMessageBox::information(this, tr("Nessuna Selezione"),
            tr("Seleziona una stazione da eliminare."));
        return;
    }
    
    // Get station info
    QModelIndex index = selection.first();
    QString stationId = stationsModel->data(
        stationsModel->index(index.row(), 0)).toString();
    QString stationName = stationsModel->data(
        stationsModel->index(index.row(), 1)).toString();
    
    // Confirm deletion
    QMessageBox::StandardButton reply = QMessageBox::question(this,
        tr("Conferma Eliminazione"),
        tr("Sei sicuro di voler eliminare la stazione '%1'?\n\n"
           "Verranno eliminate anche tutte le connessioni associate.")
            .arg(stationName),
        QMessageBox::Yes | QMessageBox::No);
    
    if (reply == QMessageBox::Yes) {
        // Remove station (this will also remove connected edges)
        network->remove_node(stationId.toStdString());
        
        // Update views
        updateStationsView();
        updateConnectionsView();
        
        // Mark as modified
        isModified = true;
        updateWindowTitle();
        
        statusBar()->showMessage(
            tr("Stazione '%1' eliminata con successo").arg(stationName), 
            3000);
    }
}

void MainWindow::addConnection() {
    // Check if we have at least 2 stations
    if (network->get_all_nodes().size() < 2) {
        QMessageBox::information(this, tr("Stazioni Insufficienti"),
            tr("Aggiungi almeno due stazioni prima di creare una connessione."));
        return;
    }
    
    ConnectionDialog dialog(network, this);
    
    if (dialog.exec() == QDialog::Accepted) {
        auto connection = dialog.getConnection();
        
        // Add connection to network (bidirectional)
        network->add_edge(*connection);
        
        // Update view
        updateConnectionsView();
        
        // Mark as modified
        isModified = true;
        updateWindowTitle();
        
        statusBar()->showMessage(
            tr("Connessione aggiunta con successo"), 
            3000);
    }
}

void MainWindow::editConnection() {
    // Get selected connection
    QModelIndexList selection = connectionsTable->selectionModel()->selectedRows();
    if (selection.isEmpty()) {
        QMessageBox::information(this, tr("Nessuna Selezione"),
            tr("Seleziona una connessione da modificare."));
        return;
    }
    
    // Get connection info from table
    QModelIndex index = selection.first();
    QString fromId = connectionsModel->data(
        connectionsModel->index(index.row(), 0)).toString();
    QString toId = connectionsModel->data(
        connectionsModel->index(index.row(), 1)).toString();
    
    // Find the edge in the network
    std::shared_ptr<Edge> connection = nullptr;
    for (const auto& edge : network->get_all_edges()) {
        if ((edge->get_from_node() == fromId.toStdString() && 
             edge->get_to_node() == toId.toStdString()) ||
            (edge->get_from_node() == toId.toStdString() && 
             edge->get_to_node() == fromId.toStdString())) {
            connection = edge;
            break;
        }
    }
    
    if (!connection) {
        QMessageBox::warning(this, tr("Errore"),
            tr("Connessione non trovata."));
        return;
    }
    
    // Open dialog in edit mode
    ConnectionDialog dialog(network, connection, this);
    
    if (dialog.exec() == QDialog::Accepted) {
        auto updatedConnection = dialog.getConnection();
        
        // Remove old connection
        network->remove_edge(connection->get_from_node(), 
                            connection->get_to_node());
        
        // Add updated connection
        network->add_edge(*updatedConnection);
        
        // Update view
        updateConnectionsView();
        
        // Mark as modified
        isModified = true;
        updateWindowTitle();
        
        statusBar()->showMessage(
            tr("Connessione modificata con successo"), 
            3000);
    }
}

void MainWindow::deleteConnection() {
    // Get selected connection
    QModelIndexList selection = connectionsTable->selectionModel()->selectedRows();
    if (selection.isEmpty()) {
        QMessageBox::information(this, tr("Nessuna Selezione"),
            tr("Seleziona una connessione da eliminare."));
        return;
    }
    
    // Get connection info
    QModelIndex index = selection.first();
    QString fromName = connectionsModel->data(
        connectionsModel->index(index.row(), 0)).toString();
    QString toName = connectionsModel->data(
        connectionsModel->index(index.row(), 1)).toString();
    QString fromId = connectionsModel->data(
        connectionsModel->index(index.row(), 0)).toString();
    QString toId = connectionsModel->data(
        connectionsModel->index(index.row(), 1)).toString();
    
    // Confirm deletion
    QMessageBox::StandardButton reply = QMessageBox::question(this,
        tr("Conferma Eliminazione"),
        tr("Sei sicuro di voler eliminare la connessione tra '%1' e '%2'?")
            .arg(fromName, toName),
        QMessageBox::Yes | QMessageBox::No);
    
    if (reply == QMessageBox::Yes) {
        // Remove connection
        network->remove_edge(fromId.toStdString(), toId.toStdString());
        
        // Update view
        updateConnectionsView();
        
        // Mark as modified
        isModified = true;
        updateWindowTitle();
        
        statusBar()->showMessage(
            tr("Connessione eliminata con successo"), 
            3000);
    }
}

void MainWindow::addLine() {
    // Check if we have at least 2 stations
    if (network->get_all_nodes().size() < 2) {
        QMessageBox::information(this, tr("Stazioni Insufficienti"),
            tr("Aggiungi almeno due stazioni prima di creare una linea."));
        return;
    }
    
    LineDialog dialog(network, this);
    
    if (dialog.exec() == QDialog::Accepted) {
        Line line = dialog.getLine();
        
        // Check if line name already exists
        for (const Line& l : lines) {
            if (l.name == line.name) {
                QMessageBox::warning(this, tr("Nome Duplicato"),
                    tr("Esiste già una linea con nome: %1").arg(line.name));
                return;
            }
        }
        
        // Add line
        lines.append(line);
        
        // Update view
        updateLinesView();
        
        // Mark as modified
        isModified = true;
        updateWindowTitle();
        
        statusBar()->showMessage(
            tr("Linea '%1' aggiunta con successo").arg(line.name), 
            3000);
    }
}

void MainWindow::editLine() {
    // Get selected line
    QModelIndexList selection = linesListView->selectionModel()->selectedIndexes();
    if (selection.isEmpty()) {
        QMessageBox::information(this, tr("Nessuna Selezione"),
            tr("Seleziona una linea da modificare."));
        return;
    }
    
    int lineIndex = selection.first().row();
    if (lineIndex < 0 || lineIndex >= lines.size()) {
        return;
    }
    
    Line existingLine = lines[lineIndex];
    
    // Open dialog in edit mode
    LineDialog dialog(network, existingLine, this);
    
    if (dialog.exec() == QDialog::Accepted) {
        Line updatedLine = dialog.getLine();
        
        // Replace line
        lines[lineIndex] = updatedLine;
        
        // Update view
        updateLinesView();
        
        // Mark as modified
        isModified = true;
        updateWindowTitle();
        
        statusBar()->showMessage(
            tr("Linea '%1' modificata con successo").arg(updatedLine.name), 
            3000);
    }
}

void MainWindow::deleteLine() {
    // Get selected line
    QModelIndexList selection = linesListView->selectionModel()->selectedIndexes();
    if (selection.isEmpty()) {
        QMessageBox::information(this, tr("Nessuna Selezione"),
            tr("Seleziona una linea da eliminare."));
        return;
    }
    
    int lineIndex = selection.first().row();
    if (lineIndex < 0 || lineIndex >= lines.size()) {
        return;
    }
    
    QString lineName = lines[lineIndex].name;
    
    // Confirm deletion
    QMessageBox::StandardButton reply = QMessageBox::question(this,
        tr("Conferma Eliminazione"),
        tr("Sei sicuro di voler eliminare la linea '%1'?").arg(lineName),
        QMessageBox::Yes | QMessageBox::No);
    
    if (reply == QMessageBox::Yes) {
        // Remove line
        lines.removeAt(lineIndex);
        
        // Update view
        updateLinesView();
        
        // Mark as modified
        isModified = true;
        updateWindowTitle();
        
        statusBar()->showMessage(
            tr("Linea '%1' eliminata con successo").arg(lineName), 
            3000);
    }
}

void MainWindow::addTrain() {
    TrainDialog dialog(this);
    
    if (dialog.exec() == QDialog::Accepted) {
        auto train = dialog.getTrain();
        
        // Check if train ID already exists
        for (const auto& t : trains) {
            if (t->get_id() == train->get_id()) {
                QMessageBox::warning(this, tr("ID Duplicato"),
                    tr("Esiste già un treno con ID: %1")
                        .arg(QString::fromStdString(train->get_id())));
                return;
            }
        }
        
        // Add train
        trains.push_back(train);
        
        // Update view
        updateTrainsView();
        
        // Mark as modified
        isModified = true;
        updateWindowTitle();
        
        statusBar()->showMessage(
            tr("Treno '%1' aggiunto con successo")
                .arg(QString::fromStdString(train->get_name())), 
            3000);
    }
}

void MainWindow::editTrain() {
    // Get selected train
    QModelIndexList selection = trainsTable->selectionModel()->selectedRows();
    if (selection.isEmpty()) {
        QMessageBox::information(this, tr("Nessuna Selezione"),
            tr("Seleziona un treno da modificare."));
        return;
    }
    
    // Get train ID from first column
    QModelIndex index = selection.first();
    QString trainId = trainsModel->data(
        trainsModel->index(index.row(), 0)).toString();
    
    // Find train
    std::shared_ptr<Train> train;
    for (const auto& t : trains) {
        if (t->get_id() == trainId.toStdString()) {
            train = t;
            break;
        }
    }
    
    if (!train) {
        QMessageBox::warning(this, tr("Errore"),
            tr("Treno non trovato."));
        return;
    }
    
    // Open dialog in edit mode
    TrainDialog dialog(train, this);
    
    if (dialog.exec() == QDialog::Accepted) {
        auto updatedTrain = dialog.getTrain();
        
        // Replace train
        for (size_t i = 0; i < trains.size(); ++i) {
            if (trains[i]->get_id() == train->get_id()) {
                trains[i] = updatedTrain;
                break;
            }
        }
        
        // Update view
        updateTrainsView();
        
        // Mark as modified
        isModified = true;
        updateWindowTitle();
        
        statusBar()->showMessage(
            tr("Treno '%1' modificato con successo")
                .arg(QString::fromStdString(updatedTrain->get_name())), 
            3000);
    }
}

void MainWindow::deleteTrain() {
    // Get selected train
    QModelIndexList selection = trainsTable->selectionModel()->selectedRows();
    if (selection.isEmpty()) {
        QMessageBox::information(this, tr("Nessuna Selezione"),
            tr("Seleziona un treno da eliminare."));
        return;
    }
    
    // Get train info
    QModelIndex index = selection.first();
    QString trainId = trainsModel->data(
        trainsModel->index(index.row(), 0)).toString();
    QString trainName = trainsModel->data(
        trainsModel->index(index.row(), 1)).toString();
    
    // Confirm deletion
    QMessageBox::StandardButton reply = QMessageBox::question(this,
        tr("Conferma Eliminazione"),
        tr("Sei sicuro di voler eliminare il treno '%1'?").arg(trainName),
        QMessageBox::Yes | QMessageBox::No);
    
    if (reply == QMessageBox::Yes) {
        // Remove train
        trains.erase(
            std::remove_if(trains.begin(), trains.end(),
                [&trainId](const std::shared_ptr<Train>& t) {
                    return t->get_id() == trainId.toStdString();
                }),
            trains.end());
        
        // Update view
        updateTrainsView();
        
        // Mark as modified
        isModified = true;
        updateWindowTitle();
        
        statusBar()->showMessage(
            tr("Treno '%1' eliminato con successo").arg(trainName), 
            3000);
    }
}

void MainWindow::addSchedule() {
    ScheduleDialog dialog(network, trains, this);
    
    if (dialog.exec() == QDialog::Accepted) {
        if (dialog.validate()) {
            auto schedule = dialog.getSchedule();
            if (schedule) {
                // Generate unique schedule ID
                std::string scheduleId = "SCH_" + schedule->get_train_id() + "_" + 
                                       std::to_string(schedules.size() + 1);
                schedule->set_schedule_id(scheduleId);
                
                schedules.push_back(schedule);
                updateSchedulesView();
                setModified(true);
                
                QMessageBox::information(this, tr("Successo"),
                    tr("Orario creato con successo."));
            }
        }
    }
}

void MainWindow::editSchedule() {
    QModelIndexList selected = schedulesTreeView->selectionModel()->selectedRows();
    if (selected.isEmpty()) {
        QMessageBox::warning(this, tr("Nessuna Selezione"),
            tr("Seleziona un orario da modificare."));
        return;
    }
    
    int row = selected.first().row();
    if (row >= 0 && row < static_cast<int>(schedules.size())) {
        auto& schedule = schedules[row];
        
        ScheduleDialog dialog(network, trains, schedule, this);
        
        if (dialog.exec() == QDialog::Accepted) {
            if (dialog.validate()) {
                auto newSchedule = dialog.getSchedule();
                if (newSchedule) {
                    // Keep the same schedule ID
                    newSchedule->set_schedule_id(schedule->get_schedule_id());
                    schedules[row] = newSchedule;
                    updateSchedulesView();
                    setModified(true);
                    
                    QMessageBox::information(this, tr("Successo"),
                        tr("Orario modificato con successo."));
                }
            }
        }
    }
}

void MainWindow::deleteSchedule() {
    QModelIndexList selected = schedulesTreeView->selectionModel()->selectedRows();
    if (selected.isEmpty()) {
        QMessageBox::warning(this, tr("Nessuna Selezione"),
            tr("Seleziona un orario da eliminare."));
        return;
    }
    
    int row = selected.first().row();
    if (row >= 0 && row < static_cast<int>(schedules.size())) {
        const auto& schedule = schedules[row];
        
        QMessageBox::StandardButton reply = QMessageBox::question(this,
            tr("Conferma Eliminazione"),
            tr("Sei sicuro di voler eliminare l'orario per il treno '%1'?")
                .arg(QString::fromStdString(schedule->get_train_id())),
            QMessageBox::Yes | QMessageBox::No);
        
        if (reply == QMessageBox::Yes) {
            schedules.erase(schedules.begin() + row);
            updateSchedulesView();
            setModified(true);
        }
    }
}

void MainWindow::filterSchedulesByLine(int lineIndex) {
    // TODO: Implementare filtro schedules per linea
    Q_UNUSED(lineIndex);
}

void MainWindow::onStationSelectionChanged() {
    // TODO: Aggiornare dettagli stazione selezionata
}

void MainWindow::onConnectionSelectionChanged() {
    // TODO: Aggiornare dettagli connessione selezionata
}

void MainWindow::onLineSelectionChanged() {
    // TODO: Aggiornare dettagli linea selezionata
    QModelIndexList selected = linesListView->selectionModel()->selectedIndexes();
    if (selected.isEmpty()) {
        lineDetailsText->clear();
        return;
    }
    
    // Placeholder: mostra info linea
    lineDetailsText->setText(tr("Dettagli linea selezionata (da implementare)"));
}

void MainWindow::onScheduleSelectionChanged() {
    QModelIndexList selected = schedulesTreeView->selectionModel()->selectedRows();
    if (selected.isEmpty()) {
        scheduleDetailsText->clear();
        return;
    }
    
    int row = selected.first().row();
    if (row >= 0 && row < static_cast<int>(schedules.size())) {
        const auto& schedule = schedules[row];
        
        QString details = "<h3>📋 Dettagli Orario</h3>";
        
        // Train info
        details += "<p><b>Treno:</b> " + QString::fromStdString(schedule->get_train_id()) + "<br>";
        details += "<b>ID Orario:</b> " + QString::fromStdString(schedule->get_schedule_id()) + "</p>";
        
        // Find train details
        for (const auto& train : trains) {
            if (train->get_id() == schedule->get_train_id()) {
                details += "<p><b>Tipo:</b> " + QString::fromStdString(train_type_to_string(train->get_type())) + "<br>";
                details += "<b>Velocità Max:</b> " + QString::number(train->get_max_speed(), 'f', 0) + " km/h</p>";
                break;
            }
        }
        
        // Schedule summary
        auto totalDuration = schedule->get_total_duration();
        int hours = totalDuration.count() / 3600;
        int minutes = (totalDuration.count() % 3600) / 60;
        
        details += "<p><b>Durata Totale:</b> " + QString::number(hours) + "h " + 
                  QString::number(minutes) + "m<br>";
        details += "<b>Distanza Totale:</b> " + QString::number(schedule->get_total_distance(), 'f', 1) + " km<br>";
        details += "<b>Velocità Media:</b> " + QString::number(schedule->get_average_speed(), 'f', 1) + " km/h</p>";
        
        // Stops table
        details += "<h4>🚉 Fermate:</h4>";
        details += "<table border='1' cellpadding='5' cellspacing='0' style='border-collapse:collapse; width:100%'>";
        details += "<tr style='background-color:#e0e0e0'>";
        details += "<th>Stazione</th><th>Arrivo</th><th>Partenza</th><th>Binario</th><th>Sosta</th>";
        details += "</tr>";
        
        const auto& stops = schedule->get_stops();
        for (size_t i = 0; i < stops.size(); ++i) {
            const auto& stop = stops[i];
            auto node = network->get_node(stop.get_node_id());
            
            QString stationName = node ? QString::fromStdString(node->get_name()) 
                                      : QString::fromStdString(stop.get_node_id());
            
            auto arrivalTime = std::chrono::system_clock::to_time_t(stop.get_arrival());
            QDateTime arrivalQt = QDateTime::fromSecsSinceEpoch(arrivalTime);
            
            auto departureTime = std::chrono::system_clock::to_time_t(stop.get_departure());
            QDateTime departureQt = QDateTime::fromSecsSinceEpoch(departureTime);
            
            auto dwellTime = stop.get_dwell_time();
            int dwellMinutes = dwellTime.count() / 60;
            
            QString platform = stop.get_platform() ? QString::number(*stop.get_platform()) : "-";
            
            QString rowColor = (i % 2 == 0) ? "#ffffff" : "#f5f5f5";
            details += "<tr style='background-color:" + rowColor + "'>";
            details += "<td>" + stationName + "</td>";
            details += "<td>" + arrivalQt.toString("HH:mm") + "</td>";
            details += "<td>" + departureQt.toString("HH:mm") + "</td>";
            details += "<td align='center'>" + platform + "</td>";
            details += "<td align='center'>" + QString::number(dwellMinutes) + " min</td>";
            details += "</tr>";
        }
        
        details += "</table>";
        
        // Validation status
        if (schedule->is_valid()) {
            details += "<p style='color:green'>✅ <b>Orario valido</b></p>";
        } else {
            details += "<p style='color:red'>❌ <b>Orario non valido</b></p>";
        }
        
        scheduleDetailsText->setHtml(details);
    }
}

void MainWindow::updateWindowTitle() {
    QString title = tr("FDC Railway Manager");
    if (!currentFilePath.isEmpty()) {
        QFileInfo fileInfo(currentFilePath);
        title += QString(" - %1").arg(fileInfo.fileName());
    }
    if (isModified) {
        title += tr(" *");
    }
    setWindowTitle(title);
}

void MainWindow::updateStationsView() {
    stationsModel->removeRows(0, stationsModel->rowCount());
    
    auto nodes = network->get_all_nodes();
    for (const auto& node : nodes) {
        QList<QStandardItem*> row;
        row << new QStandardItem(QString::fromStdString(node->get_id()));
        row << new QStandardItem(QString::fromStdString(node->get_name()));
        row << new QStandardItem(QString::fromStdString(node_type_to_string(node->get_type())));
        row << new QStandardItem(QString::number(node->get_latitude(), 'f', 6));
        row << new QStandardItem(QString::number(node->get_longitude(), 'f', 6));
        row << new QStandardItem(QString::number(node->get_platforms()));
        stationsModel->appendRow(row);
    }
}

void MainWindow::updateConnectionsView() {
    connectionsModel->removeRows(0, connectionsModel->rowCount());
    
    auto edges = network->get_all_edges();
    for (const auto& edge : edges) {
        QList<QStandardItem*> row;
        
        // Ottieni i nodi dalla rete usando gli ID
        auto fromNode = network->get_node(edge->get_from_node());
        auto toNode = network->get_node(edge->get_to_node());
        
        row << new QStandardItem(fromNode ? QString::fromStdString(fromNode->get_name()) : tr("?"));
        row << new QStandardItem(toNode ? QString::fromStdString(toNode->get_name()) : tr("?"));
        row << new QStandardItem(QString::number(edge->get_distance(), 'f', 2));
        row << new QStandardItem(QString::fromStdString(track_type_to_string(edge->get_track_type())));
        row << new QStandardItem(QString::number(edge->get_max_speed(), 'f', 0));
        row << new QStandardItem(edge->is_bidirectional() ? tr("Sì") : tr("No"));
        connectionsModel->appendRow(row);
    }
}

void MainWindow::updateTrainsView() {
    trainsModel->removeRows(0, trainsModel->rowCount());
    
    for (const auto& train : trains) {
        QList<QStandardItem*> row;
        
        row << new QStandardItem(QString::fromStdString(train->get_id()));
        row << new QStandardItem(QString::fromStdString(train->get_name()));
        row << new QStandardItem(QString::fromStdString(train_type_to_string(train->get_type())));
        row << new QStandardItem(QString::number(train->get_max_speed(), 'f', 1));
        row << new QStandardItem(QString::number(train->get_acceleration(), 'f', 2));
        row << new QStandardItem(QString::number(train->get_deceleration(), 'f', 2));
        
        trainsModel->appendRow(row);
    }
}

void MainWindow::updateLinesView() {
    linesModel->clear();
    
    if (lines.isEmpty()) {
        linesModel->appendRow(new QStandardItem(tr("Nessuna linea definita")));
        return;
    }
    
    for (const Line& line : lines) {
        auto *item = new QStandardItem(line.name);
        
        // Set line color as icon
        QPixmap colorPixmap(16, 16);
        colorPixmap.fill(line.color);
        item->setIcon(QIcon(colorPixmap));
        
        // Add station count as tooltip
        item->setToolTip(tr("%1 stazioni").arg(line.stationIds.count()));
        
        linesModel->appendRow(item);
    }
}

void MainWindow::updateSchedulesView() {
    schedulesModel->removeRows(0, schedulesModel->rowCount());
    
    for (const auto& schedule : schedules) {
        QList<QStandardItem*> row;
        
        // Train ID
        row << new QStandardItem(QString::fromStdString(schedule->get_train_id()));
        
        // Train type - find the train to get its type
        QString trainType = tr("Sconosciuto");
        for (const auto& train : trains) {
            if (train->get_id() == schedule->get_train_id()) {
                trainType = QString::fromStdString(train_type_to_string(train->get_type()));
                break;
            }
        }
        row << new QStandardItem(trainType);
        
        const auto& stops = schedule->get_stops();
        if (!stops.empty()) {
            const auto& firstStop = stops.front();
            const auto& lastStop = stops.back();
            
            // Origin and destination stations
            auto firstNode = network->get_node(firstStop.get_node_id());
            auto lastNode = network->get_node(lastStop.get_node_id());
            
            if (firstNode && lastNode) {
                // Format departure time
                auto departureTime = std::chrono::system_clock::to_time_t(firstStop.get_departure());
                QDateTime departureQt = QDateTime::fromSecsSinceEpoch(departureTime);
                QString origin = QString::fromStdString(firstNode->get_name()) + 
                               " (" + departureQt.toString("HH:mm") + ")";
                
                // Format arrival time
                auto arrivalTime = std::chrono::system_clock::to_time_t(lastStop.get_arrival());
                QDateTime arrivalQt = QDateTime::fromSecsSinceEpoch(arrivalTime);
                QString destination = QString::fromStdString(lastNode->get_name()) + 
                                    " (" + arrivalQt.toString("HH:mm") + ")";
                
                row << new QStandardItem(origin);
                row << new QStandardItem(destination);
            } else {
                row << new QStandardItem(tr("-"));
                row << new QStandardItem(tr("-"));
            }
        } else {
            row << new QStandardItem(tr("-"));
            row << new QStandardItem(tr("-"));
        }
        
        schedulesModel->appendRow(row);
    }
}

bool MainWindow::maybeSave() {
    if (!isModified) return true;
    
    QMessageBox::StandardButton ret = QMessageBox::warning(this,
        tr("FDC Railway Manager"),
        tr("Il progetto è stato modificato.\nVuoi salvare le modifiche?"),
        QMessageBox::Save | QMessageBox::Discard | QMessageBox::Cancel);
    
    if (ret == QMessageBox::Save) {
        saveProject();
        return !isModified; // Ritorna false se il salvataggio è fallito
    } else if (ret == QMessageBox::Cancel) {
        return false;
    }
    return true;
}

void MainWindow::setModified(bool modified) {
    isModified = modified;
    updateWindowTitle();
}

void MainWindow::closeEvent(QCloseEvent *event) {
    if (maybeSave()) {
        event->accept();
    } else {
        event->ignore();
    }
}

} // namespace fdc
