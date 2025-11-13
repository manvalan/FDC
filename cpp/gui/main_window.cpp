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
    QMessageBox::information(this, tr("Aggiungi Stazione"),
        tr("Dialog aggiunta stazione - da implementare"));
}

void MainWindow::editStation() {
    QMessageBox::information(this, tr("Modifica Stazione"),
        tr("Dialog modifica stazione - da implementare"));
}

void MainWindow::deleteStation() {
    QMessageBox::information(this, tr("Elimina Stazione"),
        tr("Funzione elimina stazione - da implementare"));
}

void MainWindow::addConnection() {
    QMessageBox::information(this, tr("Aggiungi Connessione"),
        tr("Dialog aggiunta connessione - da implementare"));
}

void MainWindow::editConnection() {
    QMessageBox::information(this, tr("Modifica Connessione"),
        tr("Dialog modifica connessione - da implementare"));
}

void MainWindow::deleteConnection() {
    QMessageBox::information(this, tr("Elimina Connessione"),
        tr("Funzione elimina connessione - da implementare"));
}

void MainWindow::addLine() {
    QMessageBox::information(this, tr("Aggiungi Linea"),
        tr("Dialog aggiunta linea - da implementare"));
}

void MainWindow::editLine() {
    QMessageBox::information(this, tr("Modifica Linea"),
        tr("Dialog modifica linea - da implementare"));
}

void MainWindow::deleteLine() {
    QMessageBox::information(this, tr("Elimina Linea"),
        tr("Funzione elimina linea - da implementare"));
}

void MainWindow::addSchedule() {
    QMessageBox::information(this, tr("Aggiungi Treno"),
        tr("Dialog aggiunta treno/orario - da implementare"));
}

void MainWindow::editSchedule() {
    QMessageBox::information(this, tr("Modifica Orario"),
        tr("Dialog modifica orario - da implementare"));
}

void MainWindow::deleteSchedule() {
    QMessageBox::information(this, tr("Elimina Orario"),
        tr("Funzione elimina orario - da implementare"));
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
    // TODO: Aggiornare dettagli schedule selezionato
    QModelIndexList selected = schedulesTreeView->selectionModel()->selectedIndexes();
    if (selected.isEmpty()) {
        scheduleDetailsText->clear();
        return;
    }
    
    // Placeholder: mostra info schedule
    scheduleDetailsText->setText(tr("Dettagli orario selezionato (da implementare)"));
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

void MainWindow::updateLinesView() {
    linesModel->clear();
    // TODO: Implementare gestione linee
    // Per ora placeholder
    linesModel->appendRow(new QStandardItem(tr("Nessuna linea definita")));
}

void MainWindow::updateSchedulesView() {
    schedulesModel->removeRows(0, schedulesModel->rowCount());
    
    for (const auto& schedule : schedules) {
        QList<QStandardItem*> row;
        row << new QStandardItem(QString::fromStdString(schedule->get_train_id()));
        row << new QStandardItem(tr("Regionale")); // TODO: get train type
        
        const auto& stops = schedule->get_stops();
        if (!stops.empty()) {
            const auto& firstStop = stops.front();
            const auto& lastStop = stops.back();
            
            // Ottieni i nodi dalla rete usando gli ID
            auto firstNode = network->get_node(firstStop.get_node_id());
            auto lastNode = network->get_node(lastStop.get_node_id());
            
            if (firstNode && lastNode) {
                row << new QStandardItem(QString::fromStdString(firstNode->get_name()));
                row << new QStandardItem(QString::fromStdString(lastNode->get_name()));
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
