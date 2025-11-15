#include "main_window.hpp"
#include "settings_dialog.hpp"
#include "../include/train_type.hpp"
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
#include <sstream>
#include <iomanip>
#include <ctime>
#include <cmath>
#include <map>
#include <QMap>

// Helper functions for time conversion
namespace {
    std::string time_point_to_iso8601(const std::chrono::system_clock::time_point& tp) {
        std::time_t tt = std::chrono::system_clock::to_time_t(tp);
        std::tm tm = *std::gmtime(&tt);
        char buffer[64];
        strftime(buffer, sizeof(buffer), "%Y-%m-%dT%H:%M:%SZ", &tm);
        return std::string(buffer);
    }
    
    std::chrono::system_clock::time_point iso8601_to_time_point(const std::string& iso_str) {
        std::tm tm = {};
        std::istringstream ss(iso_str);
        ss >> std::get_time(&tm, "%Y-%m-%dT%H:%M:%S");
        return std::chrono::system_clock::from_time_t(std::mktime(&tm));
    }
}

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
    , scheduleDetailsTable(nullptr)
    , scheduleDetailsInfo(nullptr)
    , lineFilterCombo(nullptr)
    , currentScheduleIndex(-1)
    , isUpdatingScheduleDetails(false)
    , network(std::make_shared<RailwayNetwork>())
    , isModified(false)
{
    qDebug() << "========== MainWindow Constructor START ==========";
    qDebug() << "Calling setupUI()...";
    setupUI();
    qDebug() << "setupUI() completed";
    qDebug() << "Calling setupMenuBar()...";
    setupMenuBar();
    qDebug() << "Calling setupToolBar()...";
    setupToolBar();
    qDebug() << "Calling setupStatusBar()...";
    setupStatusBar();
    qDebug() << "Calling createConnections()...";
    createConnections();
    
    qDebug() << "Setting window title...";
    updateWindowTitle();
    qDebug() << "Resizing window...";
    resize(DEFAULT_WIDTH, DEFAULT_HEIGHT);
    
    qDebug() << "Centering window...";
    // Centro la finestra sullo schermo (stile macOS) - Qt6
    QScreen *screen = QApplication::primaryScreen();
    if (screen) {
        QRect screenGeometry = screen->geometry();
        int x = (screenGeometry.width() - DEFAULT_WIDTH) / 2;
        int y = (screenGeometry.height() - DEFAULT_HEIGHT) / 2;
        move(x, y);
    }
    qDebug() << "========== MainWindow Constructor END ==========";
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
    
    // Schedule Menu
    QMenu *scheduleMenu = menuBar()->addMenu(tr("&Orari"));
    
    QAction *addScheduleAction = scheduleMenu->addAction(tr("Nuovo &Orario"));
    addScheduleAction->setShortcut(QKeySequence(tr("Cmd+Shift+O")));
    connect(addScheduleAction, &QAction::triggered, this, &MainWindow::addSchedule);
    
    QAction *batchScheduleAction = scheduleMenu->addAction(tr("Treni &Multipli..."));
    batchScheduleAction->setShortcut(QKeySequence(tr("Cmd+Shift+M")));
    connect(batchScheduleAction, &QAction::triggered, this, &MainWindow::addBatchSchedules);
    
    QAction *duplicateScheduleAction = scheduleMenu->addAction(tr("&Duplica Orario"));
    duplicateScheduleAction->setShortcut(QKeySequence(tr("Cmd+D")));
    connect(duplicateScheduleAction, &QAction::triggered, this, &MainWindow::duplicateSchedule);
    
    scheduleMenu->addSeparator();
    
    QAction *exportScheduleAction = scheduleMenu->addAction(tr("&Esporta Orario..."));
    connect(exportScheduleAction, &QAction::triggered, this, &MainWindow::exportSchedule);
    
    QAction *importScheduleAction = scheduleMenu->addAction(tr("&Importa Orario..."));
    connect(importScheduleAction, &QAction::triggered, this, &MainWindow::importSchedule);
    
    scheduleMenu->addSeparator();
    
    QAction *validateSchedulesAction = scheduleMenu->addAction(tr("&Valida Tutti gli Orari"));
    connect(validateSchedulesAction, &QAction::triggered, this, &MainWindow::validateAllSchedules);
    
    QAction *scheduleStatsAction = scheduleMenu->addAction(tr("&Statistiche"));
    connect(scheduleStatsAction, &QAction::triggered, this, &MainWindow::showScheduleStatistics);
    
    // Settings Menu
    QMenu *settingsMenu = menuBar()->addMenu(tr("&Impostazioni"));
    
    QAction *preferencesAction = settingsMenu->addAction(tr("&Preferenze..."));
    preferencesAction->setShortcut(QKeySequence::Preferences);
    connect(preferencesAction, &QAction::triggered, this, &MainWindow::showSettings);
    
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
    
    // Nascondi la colonna ID (colonna 0)
    stationsTable->setColumnHidden(0, true);
    
    stationsTable->setStyleSheet(
        "QTableView { "
        "   background-color: white; "
        "   color: black; "
        "   alternate-background-color: #f0f0f0; "
        "   selection-background-color: #0078d4; "
        "   selection-color: white; "
        "}"
        "QHeaderView::section { "
        "   background-color: #e0e0e0; "
        "   color: black; "
        "   padding: 4px; "
        "   border: 1px solid #c0c0c0; "
        "}"
    );
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
    connectionsTable->setStyleSheet(
        "QTableView { "
        "   background-color: white; "
        "   color: black; "
        "   alternate-background-color: #f0f0f0; "
        "   selection-background-color: #0078d4; "
        "   selection-color: white; "
        "}"
        "QHeaderView::section { "
        "   background-color: #e0e0e0; "
        "   color: black; "
        "   padding: 4px; "
        "   border: 1px solid #c0c0c0; "
        "}"
    );
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
    
    // Splitter principale: Lista linee | (Mappa + Dettagli)
    QSplitter *mainSplitter = new QSplitter(Qt::Horizontal);
    
    // ===== PANNELLO SINISTRA: LISTA LINEE =====
    QWidget *leftPanel = new QWidget();
    QVBoxLayout *leftLayout = new QVBoxLayout(leftPanel);
    leftLayout->setContentsMargins(5, 5, 5, 5);
    
    QLabel *linesLabel = new QLabel(tr("🚇 Linee Ferroviarie"));
    linesLabel->setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50; padding: 5px;");
    leftLayout->addWidget(linesLabel);
    
    linesListView = new QListView();
    linesModel = new QStandardItemModel(this);
    linesListView->setModel(linesModel);
    linesListView->setAlternatingRowColors(true);
    linesListView->setSelectionBehavior(QAbstractItemView::SelectRows);
    linesListView->setSelectionMode(QAbstractItemView::SingleSelection);
    linesListView->setStyleSheet(
        "QListView { "
        "   background-color: white; "
        "   color: black; "
        "   alternate-background-color: #f0f0f0; "
        "   selection-background-color: #0078d4; "
        "   selection-color: white; "
        "}"
    );
    connect(linesListView->selectionModel(), &QItemSelectionModel::currentChanged,
            this, &MainWindow::onLineSelectionChanged);
    leftLayout->addWidget(linesListView);
    
    // Pulsanti linee
    QHBoxLayout *lineButtonsLayout = new QHBoxLayout();
    QPushButton *addLineBtn = new QPushButton(tr("➕ Aggiungi"));
    QPushButton *editLineBtn = new QPushButton(tr("✏️ Modifica"));
    QPushButton *deleteLineBtn = new QPushButton(tr("🗑️ Elimina"));
    addLineBtn->setStyleSheet("background-color: #4CAF50; color: white; padding: 6px; font-weight: bold;");
    editLineBtn->setStyleSheet("background-color: #2196F3; color: white; padding: 6px;");
    deleteLineBtn->setStyleSheet("background-color: #f44336; color: white; padding: 6px;");
    connect(addLineBtn, &QPushButton::clicked, this, &MainWindow::addLine);
    connect(editLineBtn, &QPushButton::clicked, this, &MainWindow::editLine);
    connect(deleteLineBtn, &QPushButton::clicked, this, &MainWindow::deleteLine);
    lineButtonsLayout->addWidget(addLineBtn);
    lineButtonsLayout->addWidget(editLineBtn);
    lineButtonsLayout->addWidget(deleteLineBtn);
    leftLayout->addLayout(lineButtonsLayout);
    
    // Pulsante "Crea Orario" separato
    QPushButton *createScheduleBtn = new QPushButton(tr("🚂 Crea Orario da Linea"));
    createScheduleBtn->setStyleSheet("background-color: #673AB7; color: white; padding: 8px; font-weight: bold;");
    connect(createScheduleBtn, &QPushButton::clicked, this, &MainWindow::createScheduleFromLine);
    leftLayout->addWidget(createScheduleBtn);
    
    mainSplitter->addWidget(leftPanel);
    
    // ===== PANNELLO DESTRA: SPLITTER VERTICALE (MAPPA + DETTAGLI) =====
    QSplitter *rightSplitter = new QSplitter(Qt::Vertical);
    
    // === MAPPA RETE (stile metropolitana) ===
    QWidget *mapPanel = new QWidget();
    QVBoxLayout *mapLayout = new QVBoxLayout(mapPanel);
    mapLayout->setContentsMargins(0, 0, 0, 0);  // Rimuovi margini per massimizzare spazio
    mapLayout->setSpacing(0);
    
    networkMapWidget = new NetworkMapWidget();
    connect(networkMapWidget, &NetworkMapWidget::stationClicked,
            this, [this](const QString& stationId) {
                qDebug() << "Stazione cliccata:" << stationId;
                // TODO: Mostra dettagli stazione
            });
    mapLayout->addWidget(networkMapWidget);
    
    // Controlli mappa
    QHBoxLayout *mapControlsLayout = new QHBoxLayout();
    QPushButton *centerMapBtn = new QPushButton(tr("🎯 Centra Vista"));
    QPushButton *zoomInBtn = new QPushButton(tr("🔍+ Zoom In"));
    QPushButton *zoomOutBtn = new QPushButton(tr("🔍- Zoom Out"));
    centerMapBtn->setStyleSheet("padding: 4px;");
    zoomInBtn->setStyleSheet("padding: 4px;");
    zoomOutBtn->setStyleSheet("padding: 4px;");
    connect(centerMapBtn, &QPushButton::clicked, networkMapWidget, &NetworkMapWidget::centerView);
    connect(zoomInBtn, &QPushButton::clicked, [this]() {
        networkMapWidget->setZoom(networkMapWidget->getZoom() * 1.2);
    });
    connect(zoomOutBtn, &QPushButton::clicked, [this]() {
        networkMapWidget->setZoom(networkMapWidget->getZoom() / 1.2);
    });
    mapControlsLayout->addWidget(centerMapBtn);
    mapControlsLayout->addWidget(zoomInBtn);
    mapControlsLayout->addWidget(zoomOutBtn);
    mapControlsLayout->addStretch();
    mapLayout->addLayout(mapControlsLayout);
    
    rightSplitter->addWidget(mapPanel);
    
    // === DETTAGLI LINEA ===
    QWidget *detailsPanel = new QWidget();
    QVBoxLayout *detailsLayout = new QVBoxLayout(detailsPanel);
    detailsLayout->setContentsMargins(5, 5, 5, 5);
    
    QLabel *detailsLabel = new QLabel(tr("📋 Dettagli Linea"));
    detailsLabel->setStyleSheet("font-size: 13px; font-weight: bold; color: #2c3e50;");
    detailsLayout->addWidget(detailsLabel);
    
    lineDetailsText = new QTextEdit();
    lineDetailsText->setReadOnly(true);
    lineDetailsText->setStyleSheet(
        "QTextEdit { background-color: white; color: black; padding: 8px; }"
    );
    detailsLayout->addWidget(lineDetailsText);
    
    rightSplitter->addWidget(detailsPanel);
    
    // Proporzioni verticali: 2:1 (mappa più grande dei dettagli)
    rightSplitter->setStretchFactor(0, 2);
    rightSplitter->setStretchFactor(1, 1);
    
    mainSplitter->addWidget(rightSplitter);
    
    // Proporzioni orizzontali: 1:3 (lista:vista)
    mainSplitter->setStretchFactor(0, 1);
    mainSplitter->setStretchFactor(1, 3);
    
    mainLayout->addWidget(mainSplitter);
    tabWidget->addTab(linesWidget, tr("Linee"));
}

void MainWindow::setupSchedulesTab() {
    qDebug() << "  >> setupSchedulesTab() START";
    QWidget *schedulesWidget = new QWidget();
    QVBoxLayout *mainLayout = new QVBoxLayout(schedulesWidget);
    
    qDebug() << "  >> Creating schedulesModel...";
    // Inizializza schedulesModel per la lista orari
    schedulesModel = new QStandardItemModel(this);
    schedulesModel->setHorizontalHeaderLabels({tr("Treno"), tr("Da → A"), tr("Partenza"), tr("Arrivo")});
    
    // Inizializza trainsModel per tab separato
    trainsModel = new QStandardItemModel(this);
    trainsModel->setHorizontalHeaderLabels({
        tr("ID"), tr("Nome"), tr("Tipo"), tr("Vel. Max"), tr("Accel."), tr("Decel.")
    });
    
    // ===== SPLITTER PRINCIPALE: LISTA ORARI | (GRAFICO / TABELLA) =====
    QSplitter *mainSplitter = new QSplitter(Qt::Horizontal);
    
    // ===== PANNELLO SINISTRA: LISTA ORARI + FILTRO LINEA =====
    QWidget *leftPanel = new QWidget();
    QVBoxLayout *leftLayout = new QVBoxLayout(leftPanel);
    leftLayout->setContentsMargins(5, 5, 5, 5);
    
    QLabel *schedulesLabel = new QLabel(tr("📋 Orari Treni"));
    schedulesLabel->setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50; padding: 5px;");
    leftLayout->addWidget(schedulesLabel);
    
    // Filtro per linea
    QHBoxLayout *filterLayout = new QHBoxLayout();
    filterLayout->addWidget(new QLabel(tr("Filtra per linea:")));
    lineFilterCombo = new QComboBox();
    lineFilterCombo->addItem(tr("Tutte le linee"), -1);
    connect(lineFilterCombo, QOverload<int>::of(&QComboBox::currentIndexChanged),
            this, &MainWindow::filterSchedulesByLine);
    filterLayout->addWidget(lineFilterCombo, 1);
    leftLayout->addLayout(filterLayout);
    
    // Tabella orari (schedules) - sostituisce la vecchia trainsTable
    schedulesTreeView = new QTreeView();
    schedulesTreeView->setModel(schedulesModel);
    schedulesTreeView->setAlternatingRowColors(true);
    schedulesTreeView->setSelectionBehavior(QAbstractItemView::SelectRows);
    schedulesTreeView->setSelectionMode(QAbstractItemView::SingleSelection);
    schedulesTreeView->setRootIsDecorated(false);
    schedulesTreeView->header()->setStretchLastSection(true);
    schedulesTreeView->setStyleSheet(
        "QTreeView { "
        "   background-color: white; "
        "   color: black; "
        "   alternate-background-color: #f0f0f0; "
        "   selection-background-color: #0078d4; "
        "   selection-color: white; "
        "}"
        "QHeaderView::section { "
        "   background-color: #e0e0e0; "
        "   color: black; "
        "   padding: 4px; "
        "   border: 1px solid #c0c0c0; "
        "}"
    );
    connect(schedulesTreeView->selectionModel(), &QItemSelectionModel::currentChanged,
            this, &MainWindow::onScheduleSelectionChanged);
    leftLayout->addWidget(schedulesTreeView);
    
    // Pulsanti orari
    QHBoxLayout *scheduleButtonsLayout = new QHBoxLayout();
    QPushButton *addScheduleBtn = new QPushButton(tr("➕ Nuovo"));
    QPushButton *batchScheduleBtn = new QPushButton(tr("📋 Multipli"));
    QPushButton *deleteScheduleBtn = new QPushButton(tr("🗑️ Elimina"));
    addScheduleBtn->setStyleSheet("background-color: #4CAF50; color: white; padding: 6px; font-weight: bold;");
    batchScheduleBtn->setStyleSheet("background-color: #2196F3; color: white; padding: 6px; font-weight: bold;");
    deleteScheduleBtn->setStyleSheet("background-color: #f44336; color: white; padding: 6px;");
    addScheduleBtn->setToolTip(tr("Crea un singolo schedule"));
    batchScheduleBtn->setToolTip(tr("Crea treni multipli sulla stessa linea"));
    connect(addScheduleBtn, &QPushButton::clicked, this, &MainWindow::addSchedule);
    connect(batchScheduleBtn, &QPushButton::clicked, this, &MainWindow::addBatchSchedules);
    connect(deleteScheduleBtn, &QPushButton::clicked, this, &MainWindow::deleteSchedule);
    scheduleButtonsLayout->addWidget(addScheduleBtn);
    scheduleButtonsLayout->addWidget(batchScheduleBtn);
    scheduleButtonsLayout->addWidget(deleteScheduleBtn);
    leftLayout->addLayout(scheduleButtonsLayout);
    
    mainSplitter->addWidget(leftPanel);
    
    // ===== PANNELLO DESTRA: SPLITTER VERTICALE (GRAFICO + TABELLA) =====
    QSplitter *rightSplitter = new QSplitter(Qt::Vertical);
    
    // === SEZIONE SUPERIORE: GRAFICO ===
    QWidget *graphPanel = new QWidget();
    QVBoxLayout *graphLayout = new QVBoxLayout(graphPanel);
    graphLayout->setContentsMargins(5, 5, 5, 5);
    
    // Rimossa la scritta "Diagramma Spazio-Tempo" come richiesto
    
    scheduleGraphWidget = new ScheduleGraphWidget();
    graphLayout->addWidget(scheduleGraphWidget);
    
    rightSplitter->addWidget(graphPanel);
    
    // === SEZIONE INFERIORE: TABELLA MODIFICABILE ===
    QWidget *tablePanel = new QWidget();
    QVBoxLayout *tableLayout = new QVBoxLayout(tablePanel);
    tableLayout->setContentsMargins(5, 5, 5, 5);
    
    // Info treno
    scheduleDetailsInfo = new QLabel(tr("Seleziona un treno dalla lista"));
    scheduleDetailsInfo->setWordWrap(true);
    scheduleDetailsInfo->setStyleSheet(
        "background-color: #e3f2fd; padding: 8px; border-radius: 4px; "
        "color: #1976d2; font-size: 12px; border: 1px solid #90caf9;"
    );
    tableLayout->addWidget(scheduleDetailsInfo);
    
    // Tabella orari
    scheduleDetailsTable = new QTableWidget(0, 4);
    scheduleDetailsTable->setHorizontalHeaderLabels({tr("Stazione"), tr("Arrivo"), tr("Partenza"), tr("Binario")});
    scheduleDetailsTable->horizontalHeader()->setSectionResizeMode(0, QHeaderView::Stretch);
    scheduleDetailsTable->horizontalHeader()->setSectionResizeMode(1, QHeaderView::Fixed);
    scheduleDetailsTable->horizontalHeader()->setSectionResizeMode(2, QHeaderView::Fixed);
    scheduleDetailsTable->horizontalHeader()->setSectionResizeMode(3, QHeaderView::Fixed);
    scheduleDetailsTable->setColumnWidth(1, 80);
    scheduleDetailsTable->setColumnWidth(2, 80);
    scheduleDetailsTable->setColumnWidth(3, 70);
    scheduleDetailsTable->setStyleSheet(
        "QTableWidget { background-color: white; gridline-color: #e0e0e0; }"
        "QTableWidget::item { color: black; padding: 6px; }"
        "QTableWidget::item:selected { background-color: #bbdefb; color: black; }"
        "QHeaderView::section { background-color: #f5f5f5; color: #424242; padding: 8px; font-weight: bold; border: 1px solid #e0e0e0; }"
    );
    connect(scheduleDetailsTable, &QTableWidget::itemChanged, this, &MainWindow::onScheduleDetailItemChanged);
    tableLayout->addWidget(scheduleDetailsTable);
    
    // Bottoni OK / Annulla
    QHBoxLayout *confirmLayout = new QHBoxLayout();
    confirmLayout->addStretch();
    QPushButton *cancelBtn = new QPushButton(tr("Annulla"));
    QPushButton *okBtn = new QPushButton(tr("OK"));
    cancelBtn->setFixedWidth(100);
    okBtn->setFixedWidth(100);
    cancelBtn->setStyleSheet("background-color: #9e9e9e; color: white; padding: 8px; font-size: 13px;");
    okBtn->setStyleSheet("background-color: #2196F3; color: white; padding: 8px; font-size: 13px; font-weight: bold;");
    connect(cancelBtn, &QPushButton::clicked, this, &MainWindow::onScheduleEditCancel);
    connect(okBtn, &QPushButton::clicked, this, &MainWindow::onScheduleEditConfirm);
    confirmLayout->addWidget(cancelBtn);
    confirmLayout->addWidget(okBtn);
    tableLayout->addLayout(confirmLayout);
    
    rightSplitter->addWidget(tablePanel);
    
    // Proporzioni verticali: 1:1 (grafico e tabella uguale spazio - 50:50)
    rightSplitter->setStretchFactor(0, 1);
    rightSplitter->setStretchFactor(1, 1);
    
    mainSplitter->addWidget(rightSplitter);
    
    // Proporzioni orizzontali: 1:2 (lista:dettagli)
    mainSplitter->setStretchFactor(0, 1);
    mainSplitter->setStretchFactor(1, 2);
    
    mainLayout->addWidget(mainSplitter);
    
    QWidget *schedulesTabWidget = new QWidget();
    schedulesTabWidget->setLayout(mainLayout);
    tabWidget->addTab(schedulesTabWidget, tr("Orari"));
    
    // Crea tab separato per parco treni
    QWidget *trainsTabWidget = new QWidget();
    QVBoxLayout *trainsTabLayout = new QVBoxLayout(trainsTabWidget);
    
    trainsTable = new QTableView();
    trainsTable->setModel(trainsModel);
    trainsTable->setAlternatingRowColors(true);
    trainsTable->setSelectionBehavior(QAbstractItemView::SelectRows);
    trainsTable->setSelectionMode(QAbstractItemView::SingleSelection);
    trainsTable->horizontalHeader()->setStretchLastSection(true);
    trainsTable->setStyleSheet(
        "QTableView { "
        "   background-color: white; "
        "   color: black; "
        "   alternate-background-color: #f0f0f0; "
        "   selection-background-color: #0078d4; "
        "   selection-color: white; "
        "}"
        "QHeaderView::section { "
        "   background-color: #e0e0e0; "
        "   color: black; "
        "   padding: 4px; "
        "   border: 1px solid #c0c0c0; "
        "}"
    );
    trainsTabLayout->addWidget(trainsTable);
    
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
    trainsTabLayout->addLayout(trainButtonsLayout);
    
    tabWidget->addTab(trainsTabWidget, tr("Parco Treni"));
    
    qDebug() << "  >> setupSchedulesTab() END";
    qDebug() << "  >> Final widget pointers:";
    qDebug() << "     schedulesTreeView:" << (void*)schedulesTreeView;
    qDebug() << "     scheduleDetailsTable:" << (void*)scheduleDetailsTable;
    qDebug() << "     scheduleDetailsInfo:" << (void*)scheduleDetailsInfo;
    qDebug() << "     lineFilterCombo:" << (void*)lineFilterCombo;
}

void MainWindow::createConnections() {
    // Connessioni per selezione elementi
    connect(stationsTable->selectionModel(), &QItemSelectionModel::selectionChanged,
            this, &MainWindow::onStationSelectionChanged);
    connect(connectionsTable->selectionModel(), &QItemSelectionModel::selectionChanged,
            this, &MainWindow::onConnectionSelectionChanged);
    connect(linesListView->selectionModel(), &QItemSelectionModel::selectionChanged,
            this, &MainWindow::onLineSelectionChanged);
    // Schedule selection now handled by combobox signal
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
    qDebug() << "\n========== openProject() START ==========";
    
    if (!maybeSave()) return;
    
    QString fileName = QFileDialog::getOpenFileName(this,
        tr("Apri Progetto"), QString(), tr("File FDC (*.fdc *.json)"));
    
    if (fileName.isEmpty()) {
        qDebug() << "No file selected";
        return;
    }
    
    qDebug() << "Opening file:" << fileName;
    
    try {
        qDebug() << "Reading JSON...";
        // Read complete project JSON
        std::ifstream file(fileName.toStdString());
        nlohmann::json projectJson;
        file >> projectJson;
        file.close();
        qDebug() << "JSON read successfully";
        
        // 1. Load network
        if (projectJson.contains("network")) {
            network = railway_network_from_json(projectJson["network"]);
        } else {
            // Backward compatibility: old format without "network" wrapper
            network = railway_network_from_json(projectJson);
        }
        
        qDebug() << "\n========== NETWORK CARICATO ==========";
        qDebug() << "Nodi (stazioni):" << network->num_nodes();
        qDebug() << "Edges (connessioni):" << network->num_edges();
        
        if (network->num_edges() == 0) {
            qWarning() << "⚠️ ATTENZIONE: Nessuna connessione (edge) trovata nel network!";
            qWarning() << "Questo causerà distanze = 0 km tra tutte le stazioni.";
        }
        
        // Mostra alcuni edges di esempio
        auto allEdges = network->get_all_edges();
        qDebug() << "Primi 5 edges:";
        for (size_t i = 0; i < std::min(size_t(5), allEdges.size()); ++i) {
            qDebug() << "  " << QString::fromStdString(allEdges[i]->get_from_node()) 
                     << "→" << QString::fromStdString(allEdges[i]->get_to_node())
                     << ":" << allEdges[i]->get_distance() << "km";
        }
        qDebug() << "======================================\n";
        
        // 2. Load trains
        trains.clear();
        if (projectJson.contains("trains")) {
            for (const auto& trainJson : projectJson["trains"]) {
                std::string id = trainJson["id"];
                std::string name = trainJson["name"];
                std::string typeStr = trainJson["type"];
                TrainType type = string_to_train_type(typeStr);
                double max_speed = trainJson["max_speed"];
                double acceleration = trainJson["acceleration"];
                double deceleration = trainJson["deceleration"];
                
                auto train = std::make_shared<Train>(id, name, type, max_speed, acceleration, deceleration);
                trains.push_back(train);
            }
        }
        
        // 3. Load lines
        lines.clear();
        if (projectJson.contains("lines")) {
            for (const auto& lineJson : projectJson["lines"]) {
                Line line;
                // Carica ID se presente, altrimenti sarà assegnato dalla pulizia automatica
                if (lineJson.contains("id")) {
                    line.id = QString::fromStdString(lineJson["id"]);
                }
                line.name = QString::fromStdString(lineJson["name"]);
                line.color = QColor(QString::fromStdString(lineJson["color"]));
                
                for (const auto& stationId : lineJson["stations"]) {
                    line.stationIds.append(QString::fromStdString(stationId));
                }
                
                lines.append(line);
            }
        }
        
        // 4. Load schedules
        schedules.clear();
        if (projectJson.contains("schedules")) {
            for (const auto& scheduleJson : projectJson["schedules"]) {
                std::string train_id = scheduleJson["train_id"];
                std::string schedule_id = scheduleJson["schedule_id"];
                
                auto schedule = std::make_shared<TrainSchedule>(train_id, schedule_id, network);
                
                for (const auto& stopJson : scheduleJson["stops"]) {
                    std::string node_id = stopJson["node_id"];
                    std::string arrival_str = stopJson["arrival"];
                    std::string departure_str = stopJson["departure"];
                    bool is_stop = stopJson["is_stop"];
                    
                    // Parse ISO 8601 datetime
                    std::tm arrival_tm = {}, departure_tm = {};
                    std::istringstream arrival_ss(arrival_str);
                    std::istringstream departure_ss(departure_str);
                    arrival_ss >> std::get_time(&arrival_tm, "%Y-%m-%dT%H:%M:%S");
                    departure_ss >> std::get_time(&departure_tm, "%Y-%m-%dT%H:%M:%S");
                    
                    auto arrival = std::chrono::system_clock::from_time_t(std::mktime(&arrival_tm));
                    auto departure = std::chrono::system_clock::from_time_t(std::mktime(&departure_tm));
                    
                    try {
                        // Prova a creare lo stop - potrebbe fallire se departure < arrival
                        ScheduleStop stop(node_id, arrival, departure, is_stop);
                        
                        if (!stopJson["platform"].is_null()) {
                            stop.set_platform(stopJson["platform"]);
                        }
                        
                        schedule->add_stop(stop);
                    } catch (const std::invalid_argument& e) {
                        // Orario invalido (departure < arrival): crea comunque lo stop con orari invertiti
                        // Verrà segnalato in rosso nella tabella
                        qWarning() << "Invalid schedule time for stop" << QString::fromStdString(node_id)
                                   << "in schedule" << QString::fromStdString(schedule_id)
                                   << ":" << e.what()
                                   << "- Loading anyway with corrected times";
                        
                        // Scambia arrival e departure per permettere il caricamento
                        ScheduleStop stop(node_id, departure, arrival, is_stop);
                        
                        if (!stopJson["platform"].is_null()) {
                            stop.set_platform(stopJson["platform"]);
                        }
                        
                        schedule->add_stop(stop);
                    }
                }
                
                schedules.push_back(schedule);
            }
        }
        
        qDebug() << "Schedules loaded:" << schedules.size();
        
        currentFilePath = fileName;
        qDebug() << "currentFilePath set to:" << currentFilePath;
        
        qDebug() << "Calling updateStationsView()...";
        updateStationsView();
        qDebug() << "updateStationsView() completed";
        
        qDebug() << "Calling updateConnectionsView()...";
        updateConnectionsView();
        qDebug() << "updateConnectionsView() completed";
        
        qDebug() << "Calling updateTrainsView()...";
        updateTrainsView();
        qDebug() << "updateTrainsView() completed";
        
        qDebug() << "Calling updateLinesView()...";
        updateLinesView();
        qDebug() << "updateLinesView() completed";
        
        qDebug() << "Calling updateSchedulesView()...";
        updateSchedulesView();
        qDebug() << "updateSchedulesView() completed";
        
        // Pulizia automatica ID illegali per stazioni, linee e treni
        qDebug() << "Checking for invalid IDs...";
        auto stationIdMap = cleanupInvalidStationIds();
        auto lineIdMap = cleanupInvalidLineIds();
        auto trainIdMap = cleanupInvalidTrainIds();
        
        // Combina tutti i problemi trovati
        bool hasInvalidIds = !stationIdMap.empty() || !lineIdMap.empty() || !trainIdMap.empty();
        
        if (hasInvalidIds) {
            // Costruisci messaggio dettagliato
            QString details;
            
            if (!stationIdMap.empty()) {
                details += tr("=== STAZIONI (%1) ===\n").arg(stationIdMap.size());
                for (const auto& pair : stationIdMap) {
                    details += QString("• %1 → %2\n")
                        .arg(QString::fromStdString(pair.first))
                        .arg(QString::fromStdString(pair.second));
                }
                details += "\n";
            }
            
            if (!lineIdMap.empty()) {
                details += tr("=== LINEE (%1) ===\n").arg(lineIdMap.size());
                for (auto it = lineIdMap.begin(); it != lineIdMap.end(); ++it) {
                    details += QString("• %1 → %2\n")
                        .arg(it.key().isEmpty() ? "(vuoto)" : it.key())
                        .arg(it.value());
                }
                details += "\n";
            }
            
            if (!trainIdMap.empty()) {
                details += tr("=== TRENI (%1) ===\n").arg(trainIdMap.size());
                for (const auto& pair : trainIdMap) {
                    details += QString("• %1 → %2\n")
                        .arg(QString::fromStdString(pair.first))
                        .arg(QString::fromStdString(pair.second));
                }
                details += "\n";
            }
            
            details += tr("Tutte le connessioni, linee e orari sono stati aggiornati automaticamente.\n"
                         "SALVA SUBITO il file per mantenere le correzioni.");
            
            QMessageBox msgBox(this);
            msgBox.setIcon(QMessageBox::Warning);
            msgBox.setWindowTitle(tr("ID Corretti Automaticamente"));
            msgBox.setText(tr("⚠️ Sono stati trovati ID con caratteri illegali."));
            msgBox.setInformativeText(tr("Totale correzioni: %1 stazioni, %2 linee, %3 treni.\n"
                                        "Gli ID sono stati sostituiti automaticamente. "
                                        "È necessario salvare il file adesso.")
                                        .arg(stationIdMap.size())
                                        .arg(lineIdMap.size())
                                        .arg(trainIdMap.size()));
            msgBox.setDetailedText(details);
            msgBox.setStandardButtons(QMessageBox::Save | QMessageBox::Cancel);
            msgBox.setDefaultButton(QMessageBox::Save);
            
            int ret = msgBox.exec();
            if (ret == QMessageBox::Save) {
                // Salva immediatamente
                saveProject();
            } else {
                // L'utente ha annullato, marca come modificato
                setModified(true);
            }
        } else {
            setModified(false);
        }
        
        qDebug() << "setModified status set";
        
        QString message = tr("Progetto caricato: %1").arg(fileName);
        if (projectJson.contains("metadata")) {
            message += tr(" (%1 treni, %2 linee, %3 orari)")
                .arg(trains.size())
                .arg(lines.size())
                .arg(schedules.size());
        }
        statusBar()->showMessage(message, 5000);
        qDebug() << "========== openProject() END (SUCCESS) ==========";
    } catch (const std::exception& e) {
        qDebug() << "========== openProject() END (EXCEPTION) ==========";
        qDebug() << "Exception:" << e.what();
        QMessageBox::critical(this, tr("Errore"),
            tr("Impossibile aprire il file:\n%1").arg(e.what()));
    }
    qDebug() << "========== openProject() FUNCTION EXIT ==========";
}

void MainWindow::saveProject() {
    if (currentFilePath.isEmpty()) {
        saveProjectAs();
        return;
    }
    
    try {
        // Create complete project JSON
        nlohmann::json projectJson;
        
        // 1. Save network (nodes + edges)
        projectJson["network"] = railway_network_to_json(*network);
        
        // 2. Save trains
        nlohmann::json trainsArray = nlohmann::json::array();
        for (const auto& train : trains) {
            nlohmann::json trainJson;
            trainJson["id"] = train->get_id();
            trainJson["name"] = train->get_name();
            trainJson["type"] = train_type_to_string(train->get_type());
            trainJson["max_speed"] = train->get_max_speed();
            trainJson["acceleration"] = train->get_acceleration();
            trainJson["deceleration"] = train->get_deceleration();
            trainsArray.push_back(trainJson);
        }
        projectJson["trains"] = trainsArray;
        
        // 3. Save lines
        nlohmann::json linesArray = nlohmann::json::array();
        for (const auto& line : lines) {
            nlohmann::json lineJson;
            lineJson["id"] = line.id.toStdString();
            lineJson["name"] = line.name.toStdString();
            lineJson["color"] = line.color.name().toStdString();
            nlohmann::json stationsArray = nlohmann::json::array();
            for (const auto& stationId : line.stationIds) {
                stationsArray.push_back(stationId.toStdString());
            }
            lineJson["stations"] = stationsArray;
            linesArray.push_back(lineJson);
        }
        projectJson["lines"] = linesArray;
        
        // 4. Save schedules
        nlohmann::json schedulesArray = nlohmann::json::array();
        for (const auto& schedule : schedules) {
            nlohmann::json scheduleJson;
            scheduleJson["train_id"] = schedule->get_train_id();
            scheduleJson["schedule_id"] = schedule->get_schedule_id();
            
            nlohmann::json stopsArray = nlohmann::json::array();
            for (const auto& stop : schedule->get_stops()) {
                nlohmann::json stopJson;
                stopJson["node_id"] = stop.get_node_id();
                
                // Convert time_point to ISO 8601 string
                auto arrival_t = std::chrono::system_clock::to_time_t(stop.get_arrival());
                auto departure_t = std::chrono::system_clock::to_time_t(stop.get_departure());
                
                char arrival_str[30], departure_str[30];
                std::strftime(arrival_str, sizeof(arrival_str), "%Y-%m-%dT%H:%M:%S", std::localtime(&arrival_t));
                std::strftime(departure_str, sizeof(departure_str), "%Y-%m-%dT%H:%M:%S", std::localtime(&departure_t));
                
                stopJson["arrival"] = arrival_str;
                stopJson["departure"] = departure_str;
                stopJson["is_stop"] = stop.is_stop();
                
                if (stop.get_platform()) {
                    stopJson["platform"] = *stop.get_platform();
                } else {
                    stopJson["platform"] = nullptr;
                }
                
                stopsArray.push_back(stopJson);
            }
            scheduleJson["stops"] = stopsArray;
            schedulesArray.push_back(scheduleJson);
        }
        projectJson["schedules"] = schedulesArray;
        
        // 5. Add metadata
        projectJson["metadata"] = {
            {"version", "0.2.0"},
            {"created_by", "FDC Railway Manager C++"},
            {"num_trains", trains.size()},
            {"num_lines", lines.size()},
            {"num_schedules", schedules.size()}
        };
        
        // Write to file with pretty printing
        std::ofstream file(currentFilePath.toStdString());
        file << projectJson.dump(2);
        file.close();
        
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

std::string MainWindow::generateUniqueStationId() {
    // Trova il numero più alto tra gli ID esistenti con pattern STATION_XXX
    int maxNumber = 0;
    auto nodes = network->get_all_nodes();
    
    for (const auto& node : nodes) {
        std::string id = node->get_id();
        // Cerca pattern STATION_XXX
        if (id.substr(0, 8) == "STATION_") {
            try {
                int number = std::stoi(id.substr(8));
                if (number > maxNumber) {
                    maxNumber = number;
                }
            } catch (...) {
                // Ignora ID con formato non valido
            }
        }
    }
    
    // Genera nuovo ID
    std::ostringstream oss;
    oss << "STATION_" << std::setfill('0') << std::setw(3) << (maxNumber + 1);
    return oss.str();
}

QString MainWindow::generateUniqueLineId() {
    // Trova il numero più alto tra gli ID esistenti con pattern LINE_XXX
    int maxNumber = 0;
    
    for (const auto& line : lines) {
        QString id = line.id;
        // Cerca pattern LINE_XXX
        if (id.startsWith("LINE_")) {
            bool ok;
            int number = id.mid(5).toInt(&ok);
            if (ok && number > maxNumber) {
                maxNumber = number;
            }
        }
    }
    
    // Genera nuovo ID
    return QString("LINE_%1").arg(maxNumber + 1, 3, 10, QChar('0'));
}

std::string MainWindow::generateUniqueTrainId() {
    // Trova il numero più alto tra gli ID esistenti con pattern TRAIN_XXX
    int maxNumber = 0;
    
    for (const auto& train : trains) {
        std::string id = train->get_id();
        // Cerca pattern TRAIN_XXX
        if (id.substr(0, 6) == "TRAIN_") {
            try {
                int number = std::stoi(id.substr(6));
                if (number > maxNumber) {
                    maxNumber = number;
                }
            } catch (...) {
                // Ignora ID con formato non valido
            }
        }
    }
    
    // Genera nuovo ID
    std::ostringstream oss;
    oss << "TRAIN_" << std::setfill('0') << std::setw(3) << (maxNumber + 1);
    return oss.str();
}

bool MainWindow::isValidStationId(const std::string& id) {
    // ID valido: solo lettere, numeri e underscore (no spazi o caratteri speciali)
    for (char c : id) {
        if (!std::isalnum(c) && c != '_') {
            return false;
        }
    }
    return !id.empty();
}

bool MainWindow::isValidId(const QString& id) {
    // ID valido: solo lettere, numeri e underscore (no spazi o caratteri speciali)
    for (QChar c : id) {
        if (!c.isLetterOrNumber() && c != '_') {
            return false;
        }
    }
    return !id.isEmpty();
}

std::map<std::string, std::string> MainWindow::cleanupInvalidStationIds() {
    std::map<std::string, std::string> idMap; // oldId -> newId
    std::vector<std::shared_ptr<Node>> nodesToFix;
    
    qDebug() << "\n========== PULIZIA ID STAZIONI ==========";
    
    // 1. Trova tutte le stazioni con ID illegali
    auto nodes = network->get_all_nodes();
    for (const auto& node : nodes) {
        std::string oldId = node->get_id();
        if (!isValidStationId(oldId)) {
            nodesToFix.push_back(node);
            qDebug() << "ID illegale trovato:" << QString::fromStdString(oldId);
        }
    }
    
    if (nodesToFix.empty()) {
        qDebug() << "Nessun ID illegale trovato";
        return idMap;
    }
    
    // 2. Genera nuovi ID univoci per le stazioni problematiche
    for (const auto& node : nodesToFix) {
        std::string oldId = node->get_id();
        std::string newId = generateUniqueStationId();
        idMap[oldId] = newId;
        
        qDebug() << "  Mapping:" << QString::fromStdString(oldId) 
                 << "→" << QString::fromStdString(newId);
        
        // Aggiorna la stazione con il nuovo ID
        Node updatedNode(newId, node->get_name(), node->get_type(),
                        node->get_latitude(), node->get_longitude(),
                        node->get_capacity(), node->get_platforms());
        
        network->remove_node(oldId);
        network->add_node(updatedNode);
    }
    
    // 3. Aggiorna tutti gli edges
    qDebug() << "\n--- Aggiornamento Connessioni ---";
    std::vector<std::shared_ptr<Edge>> edgesToUpdate;
    for (auto& edge : network->get_all_edges()) {
        std::string from = edge->get_from_node();
        std::string to = edge->get_to_node();
        
        if (idMap.count(from) || idMap.count(to)) {
            edgesToUpdate.push_back(edge);
        }
    }
    
    for (auto& edge : edgesToUpdate) {
        std::string oldFrom = edge->get_from_node();
        std::string oldTo = edge->get_to_node();
        
        std::string newFrom = idMap.count(oldFrom) ? idMap[oldFrom] : oldFrom;
        std::string newTo = idMap.count(oldTo) ? idMap[oldTo] : oldTo;
        
        Edge newEdge(newFrom, newTo, edge->get_distance(), edge->get_track_type(),
                    edge->get_max_speed(), edge->get_capacity(), edge->is_bidirectional());
        
        network->remove_edge(oldFrom, oldTo);
        network->add_edge(newEdge);
        
        qDebug() << "  ✓" << QString::fromStdString(oldFrom) << "→" << QString::fromStdString(oldTo)
                 << "diventa" << QString::fromStdString(newFrom) << "→" << QString::fromStdString(newTo);
    }
    
    // 4. Aggiorna linee
    qDebug() << "\n--- Aggiornamento Linee ---";
    for (Line& line : lines) {
        for (int i = 0; i < line.stationIds.size(); ++i) {
            std::string stationId = line.stationIds[i].toStdString();
            if (idMap.count(stationId)) {
                line.stationIds[i] = QString::fromStdString(idMap[stationId]);
                qDebug() << "  ✓ Linea" << line.name << ":" 
                         << QString::fromStdString(stationId) 
                         << "→" << line.stationIds[i];
            }
        }
    }
    
    // 5. Aggiorna schedules
    qDebug() << "\n--- Aggiornamento Orari ---";
    for (auto& schedule : schedules) {
        for (size_t i = 0; i < schedule->get_stop_count(); ++i) {
            auto& stop = schedule->get_stop(i);
            std::string nodeId = stop.get_node_id();
            if (idMap.count(nodeId)) {
                stop.set_node_id(idMap[nodeId]);
                qDebug() << "  ✓ Orario" << QString::fromStdString(schedule->get_schedule_id())
                         << ":" << QString::fromStdString(nodeId) 
                         << "→" << QString::fromStdString(idMap[nodeId]);
            }
        }
    }
    
    // 6. Verifica finale: controlla che nessun vecchio ID sia rimasto
    qDebug() << "\n--- Verifica Finale ---";
    bool allGood = true;
    
    // Verifica stazioni
    for (const auto& node : network->get_all_nodes()) {
        if (!isValidStationId(node->get_id())) {
            qDebug() << "  ⚠️ ATTENZIONE: Stazione con ID illegale ancora presente:" 
                     << QString::fromStdString(node->get_id());
            allGood = false;
        }
    }
    
    // Verifica edges
    for (const auto& edge : network->get_all_edges()) {
        for (const auto& [oldId, newId] : idMap) {
            if (edge->get_from_node() == oldId || edge->get_to_node() == oldId) {
                qDebug() << "  ⚠️ ATTENZIONE: Edge con vecchio ID:" 
                         << QString::fromStdString(edge->get_from_node()) 
                         << "→" << QString::fromStdString(edge->get_to_node());
                allGood = false;
            }
        }
    }
    
    // Verifica linee
    for (const Line& line : lines) {
        for (const QString& stationId : line.stationIds) {
            for (const auto& [oldId, newId] : idMap) {
                if (stationId.toStdString() == oldId) {
                    qDebug() << "  ⚠️ ATTENZIONE: Linea" << line.name 
                             << "contiene vecchio ID:" << stationId;
                    allGood = false;
                }
            }
        }
    }
    
    // Verifica schedules
    for (const auto& schedule : schedules) {
        for (size_t i = 0; i < schedule->get_stop_count(); ++i) {
            const auto& stop = schedule->get_stop(i);
            for (const auto& [oldId, newId] : idMap) {
                if (stop.get_node_id() == oldId) {
                    qDebug() << "  ⚠️ ATTENZIONE: Orario" 
                             << QString::fromStdString(schedule->get_schedule_id())
                             << "contiene vecchio ID:" << QString::fromStdString(oldId);
                    allGood = false;
                }
            }
        }
    }
    
    if (allGood) {
        qDebug() << "  ✅ Tutti gli ID illegali sono stati sostituiti correttamente";
    }
    
    qDebug() << "\n========== PULIZIA COMPLETATA ==========";
    qDebug() << "Totale ID sostituiti:" << idMap.size();
    
    return idMap;
}

QMap<QString, QString> MainWindow::cleanupInvalidLineIds() {
    QMap<QString, QString> idMap; // oldId -> newId
    QVector<int> linesToFix;
    
    qDebug() << "\n========== PULIZIA ID LINEE ==========";
    
    // 1. Trova tutte le linee con ID illegali o vuoti
    for (int i = 0; i < lines.size(); ++i) {
        QString oldId = lines[i].id;
        if (oldId.isEmpty() || !isValidId(oldId)) {
            linesToFix.append(i);
            qDebug() << "ID linea illegale trovato:" << (oldId.isEmpty() ? "(vuoto)" : oldId);
        }
    }
    
    if (linesToFix.empty()) {
        qDebug() << "Nessun ID linea illegale trovato";
        return idMap;
    }
    
    // 2. Genera nuovi ID univoci per le linee problematiche
    for (int index : linesToFix) {
        QString oldId = lines[index].id;
        QString newId = generateUniqueLineId();
        idMap[oldId] = newId;
        
        qDebug() << "  Mapping:" << (oldId.isEmpty() ? "(vuoto)" : oldId) 
                 << "→" << newId;
        
        // Aggiorna la linea con il nuovo ID
        lines[index].id = newId;
    }
    
    qDebug() << "\n========== PULIZIA LINEE COMPLETATA ==========";
    qDebug() << "Totale ID linee sostituiti:" << idMap.size();
    
    return idMap;
}

std::map<std::string, std::string> MainWindow::cleanupInvalidTrainIds() {
    std::map<std::string, std::string> idMap; // oldId -> newId
    std::vector<std::shared_ptr<Train>> trainsToFix;
    
    qDebug() << "\n========== PULIZIA ID TRENI ==========";
    
    // 1. Trova tutti i treni con ID illegali
    for (const auto& train : trains) {
        std::string oldId = train->get_id();
        if (!isValidStationId(oldId)) { // Usa stessa validazione (alfanumerico + _)
            trainsToFix.push_back(train);
            qDebug() << "ID treno illegale trovato:" << QString::fromStdString(oldId);
        }
    }
    
    if (trainsToFix.empty()) {
        qDebug() << "Nessun ID treno illegale trovato";
        return idMap;
    }
    
    // 2. Genera nuovi ID univoci per i treni problematici
    for (const auto& train : trainsToFix) {
        std::string oldId = train->get_id();
        std::string newId = generateUniqueTrainId();
        idMap[oldId] = newId;
        
        qDebug() << "  Mapping:" << QString::fromStdString(oldId) 
                 << "→" << QString::fromStdString(newId);
        
        // Crea nuovo treno con ID aggiornato
        auto newTrain = std::make_shared<Train>(
            newId,
            train->get_name(),
            train->get_type(),
            train->get_max_speed(),
            train->get_acceleration(),
            train->get_deceleration()
        );
        
        // Sostituisci nel vettore
        for (size_t i = 0; i < trains.size(); ++i) {
            if (trains[i]->get_id() == oldId) {
                trains[i] = newTrain;
                break;
            }
        }
    }
    
    // 3. Aggiorna schedules
    qDebug() << "\n--- Aggiornamento Orari (train_id) ---";
    for (auto& schedule : schedules) {
        std::string trainId = schedule->get_train_id();
        if (idMap.count(trainId)) {
            // Devo ricreare lo schedule con il nuovo train_id
            std::string newTrainId = idMap[trainId];
            auto newSchedule = std::make_shared<TrainSchedule>(
                newTrainId,
                schedule->get_schedule_id(),
                network
            );
            
            // Copia tutti gli stop
            for (size_t i = 0; i < schedule->get_stop_count(); ++i) {
                newSchedule->add_stop(schedule->get_stop(i));
            }
            
            // Sostituisci
            for (size_t i = 0; i < schedules.size(); ++i) {
                if (schedules[i]->get_train_id() == trainId) {
                    schedules[i] = newSchedule;
                    qDebug() << "  ✓ Orario" << QString::fromStdString(schedule->get_schedule_id())
                             << ":" << QString::fromStdString(trainId) 
                             << "→" << QString::fromStdString(newTrainId);
                }
            }
        }
    }
    
    qDebug() << "\n========== PULIZIA TRENI COMPLETATA ==========";
    qDebug() << "Totale ID treni sostituiti:" << idMap.size();
    
    return idMap;
}

void MainWindow::addStation() {
    StationDialog dialog(this);
    
    // Genera automaticamente un ID univoco
    std::string autoId = generateUniqueStationId();
    dialog.setStationId(autoId);
    
    if (dialog.exec() == QDialog::Accepted) {
        auto station = dialog.getStation();
        
        // Verifica doppia sicurezza (non dovrebbe mai succedere)
        if (network->has_node(station->get_id())) {
            QMessageBox::warning(this, tr("Errore Interno"),
                tr("Errore nella generazione dell'ID univoco. Riprova."));
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
            tr("Stazione '%1' aggiunta con successo (ID: %2)")
                .arg(QString::fromStdString(station->get_name()))
                .arg(QString::fromStdString(station->get_id())), 
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
        std::string stationId = station->get_id();
        
        // L'ID non può essere modificato (read-only nel dialog)
        // quindi aggiorniamo solo le altre proprietà (nome, tipo, coordinate, binari)
        
        // Remove old station and add updated one
        network->remove_node(stationId);
        network->add_node(*updatedStation);
        
        // Update all views
        updateStationsView();
        updateConnectionsView();
        updateLinesView();
        updateSchedulesView();
        
        // Update network map if visible
        if (networkMapWidget && network) {
            networkMapWidget->setNetwork(network);
            networkMapWidget->setLines(lines);
        }
        
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
        
        // Genera automaticamente un ID univoco
        line.id = generateUniqueLineId();
        
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

void MainWindow::createScheduleFromLine() {
    // Check if there are trains
    if (trains.empty()) {
        QMessageBox::warning(this, tr("Nessun Treno"),
            tr("Devi prima creare almeno un treno.\nVai al Tab 'Treni e Orari' per aggiungere treni."));
        return;
    }
    
    // Get selected line
    QModelIndexList selection = linesListView->selectionModel()->selectedIndexes();
    if (selection.isEmpty()) {
        QMessageBox::information(this, tr("Nessuna Selezione"),
            tr("Seleziona una linea per creare un orario."));
        return;
    }
    
    int lineIndex = selection.first().row();
    if (lineIndex < 0 || lineIndex >= lines.size()) {
        return;
    }
    
    const auto& line = lines[lineIndex];
    
    if (line.stationIds.size() < 2) {
        QMessageBox::warning(this, tr("Linea Incompleta"),
            tr("La linea deve avere almeno 2 stazioni."));
        return;
    }
    
    // Create dialog for quick schedule creation
    QDialog dialog(this);
    dialog.setWindowTitle(tr("Crea Orario Rapido - Linea: %1").arg(line.name));
    dialog.resize(500, 400);
    
    auto* layout = new QVBoxLayout(&dialog);
    
    // Line info
    auto* infoLabel = new QLabel(tr("<b>Linea:</b> %1<br><b>Stazioni totali:</b> %2")
        .arg(line.name).arg(line.stationIds.size()));
    layout->addWidget(infoLabel);
    
    auto* formLayout = new QFormLayout();
    
    // Train selection mode
    auto* trainModeCombo = new QComboBox();
    trainModeCombo->addItem(tr("📋 Seleziona Treno Esistente"), "existing");
    trainModeCombo->addItem(tr("➕ Crea Nuovo Treno"), "new");
    formLayout->addRow(tr("Modalità:"), trainModeCombo);
    
    // Existing train selection (shown when mode = existing)
    auto* trainCombo = new QComboBox();
    for (const auto& train : trains) {
        QString label = QString::fromStdString(
            train->get_id() + " - " + train->get_name() + " (" + 
            train_type_to_string(train->get_type()) + ")"
        );
        trainCombo->addItem(label, QString::fromStdString(train->get_id()));
    }
    auto* existingTrainLabel = new QLabel(tr("Treno Esistente:"));
    formLayout->addRow(existingTrainLabel, trainCombo);
    
    // New train fields (shown when mode = new)
    // ID is auto-generated, no need to ask user
    
    auto* newTrainNameEdit = new QLineEdit();
    newTrainNameEdit->setPlaceholderText("es: Frecciarossa 1000");
    newTrainNameEdit->setVisible(false);
    auto* newTrainNameLabel = new QLabel(tr("Nome Treno:"));
    newTrainNameLabel->setVisible(false);
    formLayout->addRow(newTrainNameLabel, newTrainNameEdit);
    
    auto* trainTypeCombo = new QComboBox();
    trainTypeCombo->addItem("🚄 High Speed (300 km/h)", "high_speed");
    trainTypeCombo->addItem("🚅 InterCity (200 km/h)", "intercity");
    trainTypeCombo->addItem("🚃 Regional (140 km/h)", "regional");
    trainTypeCombo->addItem("🚂 Freight (100 km/h)", "freight");
    trainTypeCombo->setVisible(false);
    auto* trainTypeLabel = new QLabel(tr("Tipo Treno:"));
    trainTypeLabel->setVisible(false);
    formLayout->addRow(trainTypeLabel, trainTypeCombo);
    
    // Toggle visibility based on mode
    QObject::connect(trainModeCombo, QOverload<int>::of(&QComboBox::currentIndexChanged), 
                    [existingTrainLabel, trainCombo, 
                     newTrainNameLabel, newTrainNameEdit, trainTypeLabel, trainTypeCombo](int index) {
        bool isNewMode = (index == 1);
        existingTrainLabel->setVisible(!isNewMode);
        trainCombo->setVisible(!isNewMode);
        newTrainNameLabel->setVisible(isNewMode);
        newTrainNameEdit->setVisible(isNewMode);
        trainTypeLabel->setVisible(isNewMode);
        trainTypeCombo->setVisible(isNewMode);
    });
    
    // Start station
    auto* startStationCombo = new QComboBox();
    for (const auto& stationId : line.stationIds) {
        auto node = network->get_node(stationId.toStdString());
        QString label = node ? QString::fromStdString(node->get_name()) : stationId;
        startStationCombo->addItem(label, stationId);
    }
    formLayout->addRow(tr("Stazione di Partenza:"), startStationCombo);
    
    // End station
    auto* endStationCombo = new QComboBox();
    for (const auto& stationId : line.stationIds) {
        auto node = network->get_node(stationId.toStdString());
        QString label = node ? QString::fromStdString(node->get_name()) : stationId;
        endStationCombo->addItem(label, stationId);
    }
    endStationCombo->setCurrentIndex(line.stationIds.size() - 1); // Default: ultima stazione
    formLayout->addRow(tr("Stazione di Arrivo:"), endStationCombo);
    
    // Departure time
    auto* departureTimeEdit = new QDateTimeEdit(QDateTime::currentDateTime());
    departureTimeEdit->setDisplayFormat("HH:mm");
    departureTimeEdit->setCalendarPopup(false);
    formLayout->addRow(tr("Orario Partenza:"), departureTimeEdit);
    
    // Dwell time (sosta)
    auto* dwellTimeSpin = new QSpinBox();
    dwellTimeSpin->setRange(1, 60);
    dwellTimeSpin->setValue(2); // 2 minuti default
    dwellTimeSpin->setSuffix(" min");
    formLayout->addRow(tr("Tempo Sosta:"), dwellTimeSpin);
    
    layout->addLayout(formLayout);
    
    // Info text
    auto* helpText = new QLabel(tr(
        "<i>Il sistema creerà automaticamente un orario con tutte le stazioni "
        "intermedie tra partenza e arrivo, calcolando i tempi di viaggio in base "
        "alle prestazioni del treno e alle distanze della rete.</i>"
    ));
    helpText->setWordWrap(true);
    helpText->setStyleSheet("color: #2c3e50; padding: 10px; background-color: #e3f2fd; border-radius: 5px; border: 1px solid #90caf9;");
    layout->addWidget(helpText);
    
    // Buttons
    auto* buttonBox = new QDialogButtonBox(QDialogButtonBox::Ok | QDialogButtonBox::Cancel);
    connect(buttonBox, &QDialogButtonBox::accepted, &dialog, &QDialog::accept);
    connect(buttonBox, &QDialogButtonBox::rejected, &dialog, &QDialog::reject);
    layout->addWidget(buttonBox);
    
    if (dialog.exec() == QDialog::Accepted) {
        int startIdx = startStationCombo->currentIndex();
        int endIdx = endStationCombo->currentIndex();
        
        if (startIdx == endIdx) {
            QMessageBox::warning(this, tr("Selezione Non Valida"),
                tr("La stazione di partenza e arrivo devono essere diverse."));
            return;
        }
        
        // Get or create train
        std::string trainId;
        std::shared_ptr<Train> selectedTrain = nullptr;
        
        bool isNewMode = (trainModeCombo->currentIndex() == 1);
        
        if (isNewMode) {
            // Create new train with auto-generated ID
            trainId = generateUniqueTrainId(); // Auto-generate unique ID
            std::string trainName = newTrainNameEdit->text().trimmed().toStdString();
            std::string trainTypeStr = trainTypeCombo->currentData().toString().toStdString();
            
            // Validation
            if (trainName.empty()) {
                QMessageBox::warning(this, tr("Campo Obbligatorio"),
                    tr("Inserisci il nome del treno."));
                return;
            }
            
            // Create train with type-based defaults
            TrainType trainType = string_to_train_type(trainTypeStr);
            selectedTrain = std::make_shared<Train>(Train::create_by_type(trainId, trainName, trainType));
            
            // Add to trains list
            trains.push_back(selectedTrain);
            updateTrainsView();
            
            QMessageBox::information(this, tr("Treno Creato"),
                tr("Nuovo treno '%1' creato con successo!").arg(QString::fromStdString(trainName)));
            
        } else {
            // Use existing train
            trainId = trainCombo->currentData().toString().toStdString();
            for (const auto& train : trains) {
                if (train->get_id() == trainId) {
                    selectedTrain = train;
                    break;
                }
            }
            
            if (!selectedTrain) {
                QMessageBox::critical(this, tr("Errore"), tr("Treno non trovato."));
                return;
            }
        }
        
        try {
            // Create schedule using ScheduleBuilder
            std::string scheduleId = "SCH_" + trainId + "_" + std::to_string(schedules.size() + 1);
            ScheduleBuilder builder(trainId, scheduleId, network, selectedTrain);
            
            auto startTime = std::chrono::system_clock::from_time_t(
                departureTimeEdit->dateTime().toSecsSinceEpoch()
            );
            builder.set_start_time(startTime);
            
            std::chrono::seconds dwellTime(dwellTimeSpin->value() * 60);
            
            // Add all stations from start to end (handle reverse direction)
            if (startIdx < endIdx) {
                // Normal direction: forward
                for (int i = startIdx; i <= endIdx; ++i) {
                    std::string stationId = line.stationIds[i].toStdString();
                    builder.add_stop_auto(stationId, dwellTime);
                }
            } else {
                // Reverse direction: backward
                for (int i = startIdx; i >= endIdx; --i) {
                    std::string stationId = line.stationIds[i].toStdString();
                    builder.add_stop_auto(stationId, dwellTime);
                }
            }
            
            // Enable automatic platform assignment
            builder.enable_auto_platform_assignment(true);
            
            // Build the schedule
            auto schedule = builder.build();
            schedules.push_back(schedule);
            
            // Update views
            updateSchedulesView();
            setModified(true);
            
            // Switch to schedules tab
            tabWidget->setCurrentIndex(2); // Tab 3: Treni e Orari
            
            QMessageBox::information(this, tr("Successo"),
                tr("Orario creato con successo!\n\n"
                   "Treno: %1\n"
                   "Fermate: %2\n"
                   "Da: %3\n"
                   "A: %4")
                    .arg(QString::fromStdString(trainId))
                    .arg(std::abs(endIdx - startIdx) + 1)
                    .arg(startStationCombo->currentText())
                    .arg(endStationCombo->currentText()));
            
        } catch (const std::exception& e) {
            QMessageBox::critical(this, tr("Errore"),
                tr("Impossibile creare l'orario:\n%1").arg(e.what()));
        }
    }
}

void MainWindow::addTrain() {
    TrainDialog dialog(this);
    
    // Genera automaticamente un ID univoco
    std::string autoId = generateUniqueTrainId();
    dialog.setTrainId(autoId);
    
    if (dialog.exec() == QDialog::Accepted) {
        auto train = dialog.getTrain();
        
        if (!train) {
            QMessageBox::critical(this, tr("Errore"),
                tr("Impossibile creare il treno. Dati non validi."));
            return;
        }
        
        // Verifica doppia sicurezza (non dovrebbe mai succedere)
        for (const auto& t : trains) {
            if (t->get_id() == train->get_id()) {
                QMessageBox::warning(this, tr("Errore Interno"),
                    tr("Errore nella generazione dell'ID univoco. Riprova."));
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
        
        QMessageBox::information(this, tr("Successo"),
            tr("Treno '%1' aggiunto con successo!")
                .arg(QString::fromStdString(train->get_name())));
        
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
    if (currentScheduleIndex < 0 || currentScheduleIndex >= static_cast<int>(schedules.size())) {
        QMessageBox::warning(this, tr("Nessuna Selezione"),
            tr("Seleziona un orario da modificare."));
        return;
    }
    
    auto& schedule = schedules[currentScheduleIndex];
    
    ScheduleDialog dialog(network, trains, schedule, this);
    
    if (dialog.exec() == QDialog::Accepted) {
        if (dialog.validate()) {
            auto newSchedule = dialog.getSchedule();
            if (newSchedule) {
                // Keep the same schedule ID
                newSchedule->set_schedule_id(schedule->get_schedule_id());
                schedules[currentScheduleIndex] = newSchedule;
                updateSchedulesView();
                setModified(true);
                
                QMessageBox::information(this, tr("Successo"),
                    tr("Orario modificato con successo."));
            }
        }
    }
}

void MainWindow::deleteSchedule() {
    if (currentScheduleIndex < 0 || currentScheduleIndex >= static_cast<int>(schedules.size())) {
        QMessageBox::warning(this, tr("Nessuna Selezione"),
            tr("Seleziona un orario da eliminare."));
        return;
    }
    
    const auto& schedule = schedules[currentScheduleIndex];
        
        QMessageBox::StandardButton reply = QMessageBox::question(this,
            tr("Conferma Eliminazione"),
            tr("Sei sicuro di voler eliminare l'orario per il treno '%1'?")
                .arg(QString::fromStdString(schedule->get_train_id())),
            QMessageBox::Yes | QMessageBox::No);
        
        if (reply == QMessageBox::Yes) {
            schedules.erase(schedules.begin() + currentScheduleIndex);
            currentScheduleIndex = -1;  // Reset selection
            updateSchedulesView();
            setModified(true);
        }
}

void MainWindow::addBatchSchedules() {
    if (schedules.empty()) {
        QMessageBox::information(this, tr("Info"),
            tr("Crea prima almeno uno schedule da usare come template."));
        return;
    }
    
    BatchScheduleDialog dialog(network, trains, schedules, this);
    
    if (dialog.exec() == QDialog::Accepted) {
        auto newTrains = dialog.getNewTrains();
        auto newSchedules = dialog.getNewSchedules();
        
        if (newTrains.size() != newSchedules.size()) {
            QMessageBox::warning(this, tr("Errore"),
                tr("Numero di treni e schedule non corrispondente."));
            return;
        }
        
        // Aggiungi i nuovi treni
        for (const auto& train : newTrains) {
            trains.push_back(train);
        }
        
        // Aggiungi i nuovi schedule
        for (const auto& schedule : newSchedules) {
            schedules.push_back(schedule);
        }
        
        updateTrainsView();
        updateSchedulesView();
        setModified(true);
        
        QMessageBox::information(this, tr("Successo"),
            tr("Aggiunti %1 treni e %2 schedule con successo!")
                .arg(newTrains.size())
                .arg(newSchedules.size()));
    }
}

void MainWindow::duplicateSchedule() {
    if (currentScheduleIndex < 0 || currentScheduleIndex >= static_cast<int>(schedules.size())) {
        QMessageBox::warning(this, tr("Nessuna Selezione"),
            tr("Seleziona un orario da duplicare."));
        return;
    }
    
    const auto& originalSchedule = schedules[currentScheduleIndex];
    
    // Trova il treno originale
    std::shared_ptr<Train> originalTrain;
    for (const auto& train : trains) {
        if (train && train->get_id() == originalSchedule->get_train_id()) {
            originalTrain = train;
            break;
        }
    }
    
    if (!originalTrain) {
        QMessageBox::warning(this, tr("Errore"),
            tr("Treno associato non trovato."));
        return;
    }
    
    // Genera nuovo ID treno e schedule
    std::string newTrainId = generateUniqueTrainId();
    std::string newTrainName = originalTrain->get_name() + " (copia)";
    std::string scheduleId = "SCH_" + newTrainId + "_1";
    
    // Crea nuovo treno
    auto newTrain = std::make_shared<Train>(
        newTrainId,
        newTrainName,
        originalTrain->get_type(),
        originalTrain->get_max_speed(),
        originalTrain->get_acceleration(),
        originalTrain->get_deceleration()
    );
    trains.push_back(newTrain);
    
    // Crea nuovo schedule (copia esatta degli orari)
    auto newSchedule = std::make_shared<TrainSchedule>(newTrainId, scheduleId, network);
    for (const auto& stop : originalSchedule->get_stops()) {
        newSchedule->add_stop(stop);
    }
    
    schedules.push_back(newSchedule);
    
    updateTrainsView();
    updateSchedulesView();
    setModified(true);
    
    QMessageBox::information(this, tr("Successo"),
        tr("Orario duplicato con successo."));
}

void MainWindow::exportSchedule() {
    if (currentScheduleIndex < 0 || currentScheduleIndex >= static_cast<int>(schedules.size())) {
        QMessageBox::warning(this, tr("Nessuna Selezione"),
            tr("Seleziona un orario da esportare."));
        return;
    }
    
    QString fileName = QFileDialog::getSaveFileName(this,
        tr("Esporta Schedule"), "",
        tr("JSON Files (*.json);;All Files (*)"));
    
    if (fileName.isEmpty()) return;
    
    try {
        const auto& schedule = schedules[currentScheduleIndex];
        nlohmann::json j;
        
        // Serializza solo questo schedule
        j["schedule_id"] = schedule->get_schedule_id();
        j["train_id"] = schedule->get_train_id();
        
        nlohmann::json stopsJson = nlohmann::json::array();
        for (const auto& stop : schedule->get_stops()) {
            nlohmann::json stopJson;
            stopJson["node_id"] = stop.get_node_id();
            stopJson["arrival"] = time_point_to_iso8601(stop.get_arrival());
            stopJson["departure"] = time_point_to_iso8601(stop.get_departure());
            stopJson["is_stop"] = stop.is_stop();
            if (stop.get_platform()) {
                stopJson["platform"] = *stop.get_platform();
            }
            stopsJson.push_back(stopJson);
        }
        j["stops"] = stopsJson;
        
        // Salva su file
        std::ofstream file(fileName.toStdString());
        file << j.dump(2);
        file.close();
        
        QMessageBox::information(this, tr("Successo"),
            tr("Schedule esportato con successo."));
            
    } catch (const std::exception& e) {
        QMessageBox::critical(this, tr("Errore"),
            tr("Errore durante l'esportazione:\n%1")
                .arg(QString::fromStdString(e.what())));
    }
}

void MainWindow::importSchedule() {
    QString fileName = QFileDialog::getOpenFileName(this,
        tr("Importa Schedule"), "",
        tr("JSON Files (*.json);;All Files (*)"));
    
    if (fileName.isEmpty()) return;
    
    try {
        std::ifstream file(fileName.toStdString());
        nlohmann::json j;
        file >> j;
        file.close();
        
        // Genera schedule ID
        std::string trainId = j["train_id"];
        std::string scheduleId = j.value("schedule_id", "");
        if (scheduleId.empty()) {
            scheduleId = "SCH_" + trainId + "_" + std::to_string(schedules.size() + 1);
        }
        
        // Crea nuovo schedule
        auto schedule = std::make_shared<TrainSchedule>(trainId, scheduleId, network);
        
        for (const auto& stopJson : j["stops"]) {
            std::string arrivalStr = stopJson["arrival"];
            std::string departureStr = stopJson["departure"];
            
            auto arrival = iso8601_to_time_point(arrivalStr);
            auto departure = iso8601_to_time_point(departureStr);
            
            ScheduleStop stop(
                stopJson["node_id"],
                arrival,
                departure,
                stopJson.value("is_stop", true)
            );
            
            if (stopJson.contains("platform")) {
                stop.set_platform(stopJson["platform"]);
            }
            
            schedule->add_stop(stop);
        }
        
        schedules.push_back(schedule);
        updateSchedulesView();
        setModified(true);
        
        QMessageBox::information(this, tr("Successo"),
            tr("Schedule importato con successo."));
            
    } catch (const std::exception& e) {
        QMessageBox::critical(this, tr("Errore"),
            tr("Errore durante l'importazione:\n%1")
                .arg(QString::fromStdString(e.what())));
    }
}

void MainWindow::validateAllSchedules() {
    if (schedules.empty()) {
        QMessageBox::information(this, tr("Info"),
            tr("Nessun orario da validare."));
        return;
    }
    
    QStringList errors;
    int validCount = 0;
    
    for (size_t i = 0; i < schedules.size(); ++i) {
        const auto& schedule = schedules[i];
        if (!schedule) continue;
        
        const auto& stops = schedule->get_stops();
        if (stops.size() < 2) {
            errors << tr("Schedule %1: Meno di 2 fermate")
                .arg(QString::fromStdString(schedule->get_schedule_id()));
            continue;
        }
        
        bool hasErrors = false;
        
        // Verifica ordine temporale
        for (size_t j = 1; j < stops.size(); ++j) {
            auto prevDep = QDateTime::fromString(
                QString::fromStdString(time_point_to_iso8601(stops[j-1].get_departure())), Qt::ISODate);
            auto currArr = QDateTime::fromString(
                QString::fromStdString(time_point_to_iso8601(stops[j].get_arrival())), Qt::ISODate);
            
            if (prevDep.isValid() && currArr.isValid() && prevDep >= currArr) {
                errors << tr("Schedule %1: Fermata %2 - arrivo prima della partenza precedente")
                    .arg(QString::fromStdString(schedule->get_schedule_id()))
                    .arg(j + 1);
                hasErrors = true;
            }
            
            // Verifica arrivo <= partenza nella stessa fermata
            auto currDep = QDateTime::fromString(
                QString::fromStdString(time_point_to_iso8601(stops[j].get_departure())), Qt::ISODate);
            if (currArr.isValid() && currDep.isValid() && currArr > currDep) {
                errors << tr("Schedule %1: Fermata %2 - arrivo dopo partenza")
                    .arg(QString::fromStdString(schedule->get_schedule_id()))
                    .arg(j + 1);
                hasErrors = true;
            }
        }
        
        // Verifica esistenza stazioni
        for (const auto& stop : stops) {
            auto node = network->get_node(stop.get_node_id());
            if (!node) {
                errors << tr("Schedule %1: Stazione '%2' non trovata nella rete")
                    .arg(QString::fromStdString(schedule->get_schedule_id()))
                    .arg(QString::fromStdString(stop.get_node_id()));
                hasErrors = true;
            }
        }
        
        if (!hasErrors) {
            validCount++;
        }
    }
    
    // Mostra risultati
    QString message;
    if (errors.isEmpty()) {
        message = tr("✅ Tutti gli %1 schedule sono validi!").arg(schedules.size());
        QMessageBox::information(this, tr("Validazione Completa"), message);
    } else {
        message = tr("✅ Schedule validi: %1/%2\n\n❌ Errori trovati:\n\n%3")
            .arg(validCount)
            .arg(schedules.size())
            .arg(errors.join("\n"));
        QMessageBox::warning(this, tr("Validazione Completa"), message);
    }
}

void MainWindow::showScheduleStatistics() {
    if (schedules.empty()) {
        QMessageBox::information(this, tr("Info"),
            tr("Nessun orario disponibile."));
        return;
    }
    
    int totalSchedules = schedules.size();
    int totalStops = 0;
    int totalTrains = trains.size();
    double totalDistance = 0.0;
    int totalDurationMinutes = 0;
    
    QMap<QString, int> trainTypes;
    
    for (const auto& schedule : schedules) {
        if (!schedule) continue;
        
        const auto& stops = schedule->get_stops();
        totalStops += stops.size();
        
        // Calcola distanza e durata
        if (stops.size() >= 2) {
            for (size_t i = 1; i < stops.size(); ++i) {
                double dist = network->calculate_distance(
                    stops[i-1].get_node_id(),
                    stops[i].get_node_id()
                );
                totalDistance += dist;
            }
            
            auto firstTime = QDateTime::fromString(
                QString::fromStdString(time_point_to_iso8601(stops.front().get_departure())), Qt::ISODate);
            auto lastTime = QDateTime::fromString(
                QString::fromStdString(time_point_to_iso8601(stops.back().get_arrival())), Qt::ISODate);
            
            if (firstTime.isValid() && lastTime.isValid()) {
                totalDurationMinutes += firstTime.secsTo(lastTime) / 60;
            }
        }
        
        // Conta tipi treni
        for (const auto& train : trains) {
            if (train && train->get_id() == schedule->get_train_id()) {
                QString type = QString::fromStdString(train_type_to_string(train->get_type()));
                trainTypes[type]++;
                break;
            }
        }
    }
    
    double avgStopsPerSchedule = totalSchedules > 0 ? 
        static_cast<double>(totalStops) / totalSchedules : 0.0;
    double avgDistancePerSchedule = totalSchedules > 0 ?
        totalDistance / totalSchedules : 0.0;
    double avgDurationMinutes = totalSchedules > 0 ?
        static_cast<double>(totalDurationMinutes) / totalSchedules : 0.0;
    
    QString stats = tr(
        "<h3>📊 Statistiche Orari</h3>"
        "<table cellpadding='5'>"
        "<tr><td><b>Totale schedule:</b></td><td>%1</td></tr>"
        "<tr><td><b>Totale treni:</b></td><td>%2</td></tr>"
        "<tr><td><b>Totale fermate:</b></td><td>%3</td></tr>"
        "<tr><td><b>Media fermate/schedule:</b></td><td>%.1f</td></tr>"
        "<tr><td><b>Distanza totale:</b></td><td>%.1f km</td></tr>"
        "<tr><td><b>Distanza media/schedule:</b></td><td>%.1f km</td></tr>"
        "<tr><td><b>Durata media:</b></td><td>%.0f min</td></tr>"
        "</table>"
    )
        .arg(totalSchedules)
        .arg(totalTrains)
        .arg(totalStops)
        .arg(avgStopsPerSchedule)
        .arg(totalDistance)
        .arg(avgDistancePerSchedule)
        .arg(avgDurationMinutes);
    
    if (!trainTypes.isEmpty()) {
        stats += tr("<br><h4>Tipi di Treno:</h4><ul>");
        for (auto it = trainTypes.begin(); it != trainTypes.end(); ++it) {
            stats += tr("<li>%1: %2</li>").arg(it.key()).arg(it.value());
        }
        stats += "</ul>";
    }
    
    QMessageBox msgBox(this);
    msgBox.setWindowTitle(tr("Statistiche Orari"));
    msgBox.setTextFormat(Qt::RichText);
    msgBox.setText(stats);
    msgBox.exec();
}

void MainWindow::filterSchedulesByLine(int comboIndex) {
    if (!lineFilterCombo || !schedulesModel || comboIndex < 0) {
        return;
    }
    
    // Ottieni l'indice della linea selezionata (-1 = tutte)
    int lineIndex = lineFilterCombo->itemData(comboIndex).toInt();
    
    qDebug() << "Filtro per linea - combo:" << comboIndex << "line:" << lineIndex;
    
    // Se "Tutte le linee" è selezionato, mostra tutti gli orari
    if (lineIndex < 0 || lineIndex >= lines.size()) {
        for (int row = 0; row < schedulesModel->rowCount(); ++row) {
            schedulesTreeView->setRowHidden(row, QModelIndex(), false);
        }
        return;
    }
    
    // Ottieni le stazioni della linea selezionata
    const Line& selectedLine = lines[lineIndex];
    QSet<QString> lineStations(selectedLine.stationIds.begin(), selectedLine.stationIds.end());
    
    qDebug() << "Stazioni linea:" << selectedLine.name << "->" << lineStations;
    
    // Filtra gli orari: mostra solo quelli che attraversano la linea
    for (int row = 0; row < schedulesModel->rowCount(); ++row) {
        auto item = schedulesModel->item(row, 0);
        if (!item) continue;
        
        int scheduleIdx = item->data(Qt::UserRole).toInt();
        if (scheduleIdx < 0 || scheduleIdx >= static_cast<int>(schedules.size())) continue;
        
        const auto& schedule = schedules[scheduleIdx];
        if (!schedule) continue;
        
        // Verifica se l'orario attraversa almeno una stazione della linea
        bool matchesLine = false;
        for (const auto& stop : schedule->get_stops()) {
            QString stationId = QString::fromStdString(stop.get_node_id());
            if (lineStations.contains(stationId)) {
                matchesLine = true;
                break;
            }
        }
        
        // Nascondi la riga se non corrisponde al filtro
        schedulesTreeView->setRowHidden(row, QModelIndex(), !matchesLine);
        qDebug() << "  Row" << row << ":" << (matchesLine ? "visible" : "hidden");
    }
}

// Helper function - non più utilizzata con combobox
void MainWindow::addScheduleToView(const std::shared_ptr<TrainSchedule>& schedule) {
    Q_UNUSED(schedule);
    // Non più necessaria: ora usiamo scheduleComboBox invece di schedulesModel
}

void MainWindow::onStationSelectionChanged() {
    // Station details can be shown in a future status bar update or tooltip
    // For now, just update selection state
    Q_UNUSED(this);
}

void MainWindow::onConnectionSelectionChanged() {
    // Connection details can be shown in a future status bar update or tooltip
    // For now, just update selection state
    Q_UNUSED(this);
}

void MainWindow::onLineSelectionChanged() {
    QModelIndexList selected = linesListView->selectionModel()->selectedIndexes();
    if (selected.isEmpty()) {
        lineDetailsText->clear();
        return;
    }
    
    int row = selected.first().row();
    if (row >= 0 && row < lines.size()) {
        const auto& line = lines[row];
        
        QString details = "<h3>🚉 Dettagli Linea</h3>";
        
        // Line info
        QString colorBox = QString("<span style='background-color:%1; padding:5px 15px; border:1px solid #333;'>&nbsp;&nbsp;&nbsp;</span>")
            .arg(line.color.name());
        details += "<p><b>Nome:</b> " + line.name + " " + colorBox + "</p>";
        details += "<p><b>Numero Stazioni:</b> " + QString::number(line.stationIds.size()) + "</p>";
        
        // Calculate total distance
        double totalDistance = 0.0;
        for (int i = 1; i < line.stationIds.size(); ++i) {
            double dist = network->calculate_distance(
                line.stationIds[i-1].toStdString(),
                line.stationIds[i].toStdString()
            );
            if (dist > 0) {
                totalDistance += dist;
            }
        }
        details += "<p><b>Lunghezza Totale:</b> " + QString::number(totalDistance, 'f', 1) + " km</p>";
        
        // Stations table
        details += "<h4>📍 Sequenza Stazioni:</h4>";
        details += "<table border='1' cellpadding='5' cellspacing='0' style='border-collapse:collapse; width:100%'>";
        details += "<tr style='background-color:#e0e0e0'>";
        details += "<th>#</th><th>Stazione</th><th>Distanza da Precedente</th><th>Distanza Progressiva</th>";
        details += "</tr>";
        
        double progressiveDistance = 0.0;
        for (int i = 0; i < line.stationIds.size(); ++i) {
            auto node = network->get_node(line.stationIds[i].toStdString());
            QString stationName = node ? QString::fromStdString(node->get_name()) 
                                      : line.stationIds[i];
            
            double segmentDistance = 0.0;
            if (i > 0) {
                segmentDistance = network->calculate_distance(
                    line.stationIds[i-1].toStdString(),
                    line.stationIds[i].toStdString()
                );
                if (segmentDistance > 0) {
                    progressiveDistance += segmentDistance;
                }
            }
            
            QString rowColor = (i % 2 == 0) ? "#ffffff" : "#f5f5f5";
            details += "<tr style='background-color:" + rowColor + "'>";
            details += "<td align='center'>" + QString::number(i + 1) + "</td>";
            details += "<td>" + stationName + "</td>";
            
            if (i == 0) {
                details += "<td align='center'>-</td>";
                details += "<td align='center'>0.0 km</td>";
            } else {
                details += "<td align='right'>" + QString::number(segmentDistance, 'f', 1) + " km</td>";
                details += "<td align='right'>" + QString::number(progressiveDistance, 'f', 1) + " km</td>";
            }
            details += "</tr>";
        }
        details += "</table>";
        
        // Count trains using this line
        int trainsUsingLine = 0;
        QStringList trainsList;
        for (const auto& schedule : schedules) {
            auto nodeSequence = schedule->get_node_sequence();
            
            // Check if schedule follows this line (all stations in order)
            bool matchesLine = true;
            size_t scheduleIdx = 0;
            for (const auto& stationId : line.stationIds) {
                // Find this station in schedule
                bool found = false;
                for (; scheduleIdx < nodeSequence.size(); ++scheduleIdx) {
                    if (nodeSequence[scheduleIdx] == stationId.toStdString()) {
                        found = true;
                        scheduleIdx++;
                        break;
                    }
                }
                if (!found) {
                    matchesLine = false;
                    break;
                }
            }
            
            if (matchesLine) {
                trainsUsingLine++;
                trainsList.append(QString::fromStdString(schedule->get_train_id()));
            }
        }
        
        details += "<h4>🚂 Treni su questa Linea:</h4>";
        if (trainsUsingLine > 0) {
            details += "<p><b>Numero Treni:</b> " + QString::number(trainsUsingLine) + "</p>";
            details += "<p>" + trainsList.join(", ") + "</p>";
        } else {
            details += "<p><i>Nessun treno configurato su questa linea</i></p>";
        }
        
        lineDetailsText->setHtml(details);
    }
}

void MainWindow::onScheduleSelectionChanged() {
    qDebug() << "\n========== onScheduleSelectionChanged ==========";
    
    if (!scheduleDetailsTable || !scheduleDetailsInfo || !network || !schedulesTreeView) {
        qDebug() << "Widget non inizializzati, uscita";
        return;
    }
    
    // Don't reload if we're in the middle of editing
    if (isUpdatingScheduleDetails) {
        qDebug() << "isUpdatingScheduleDetails=true, uscita";
        return;
    }
    
    // Ottieni l'indice dalla selezione corrente
    QModelIndex index = schedulesTreeView->currentIndex();
    if (!index.isValid()) {
        scheduleDetailsTable->setRowCount(0);
        scheduleDetailsInfo->setText(tr("Seleziona un orario dalla lista"));
        qDebug() << "Nessuna selezione valida";
        return;
    }
    
    // Recupera l'indice salvato nell'item
    QStandardItem *item = schedulesModel->itemFromIndex(index);
    if (!item) {
        qDebug() << "Item non valido";
        return;
    }
    
    currentScheduleIndex = item->data(Qt::UserRole).toInt();
    qDebug() << "currentScheduleIndex da TreeView:" << currentScheduleIndex;
    
    if (currentScheduleIndex < 0 || currentScheduleIndex >= static_cast<int>(schedules.size())) {
        scheduleDetailsTable->setRowCount(0);
        scheduleDetailsInfo->clear();
        qDebug() << "currentScheduleIndex non valido";
        return;
    }
    
    const auto& schedule = schedules[currentScheduleIndex];
    if (!schedule) {
        qDebug() << "Schedule nullo";
        return;
    }
    
    qDebug() << "Treno:" << QString::fromStdString(schedule->get_train_id());
    qDebug() << "Fermate:" << schedule->get_stop_count();
    
    // Salva backup
    originalSchedule = std::make_shared<TrainSchedule>(*schedule);
    qDebug() << "Backup salvato";
    
    qDebug() << "Caricamento dettagli treno:" << QString::fromStdString(schedule->get_train_id());
        
        // Update info label
        QString info = "<b>🚂 Treno:</b> " + QString::fromStdString(schedule->get_train_id()) + " | ";
        info += "<b>ID:</b> " + QString::fromStdString(schedule->get_schedule_id()) + "<br>";
        
        // Find train details
        for (const auto& train : trains) {
            if (train->get_id() == schedule->get_train_id()) {
                info += "<b>Tipo:</b> " + QString::fromStdString(train_type_to_string(train->get_type())) + " | ";
                info += "<b>V.Max:</b> " + QString::number(train->get_max_speed(), 'f', 0) + " km/h<br>";
                break;
            }
        }
        
        auto totalDuration = schedule->get_total_duration();
        int hours = totalDuration.count() / 3600;
        int minutes = (totalDuration.count() % 3600) / 60;
        
        info += "<b>Durata:</b> " + QString::number(hours) + "h " + QString::number(minutes) + "m | ";
        info += "<b>Distanza:</b> " + QString::number(schedule->get_total_distance(), 'f', 1) + " km | ";
        info += "<b>V.Media:</b> " + QString::number(schedule->get_average_speed(), 'f', 1) + " km/h";
        
        scheduleDetailsInfo->setText(info);
        
        // Populate table (block signals during rebuild)
        scheduleDetailsTable->blockSignals(true);
        scheduleDetailsTable->setRowCount(0);
        
        const auto& stops = schedule->get_stops();
        for (size_t i = 0; i < stops.size(); ++i) {
            const auto& stop = stops[i];
            int tableRow = scheduleDetailsTable->rowCount();
            scheduleDetailsTable->insertRow(tableRow);
            
            // Station name (non-editable)
            auto node = network->get_node(stop.get_node_id());
            QString stationName = node ? QString::fromStdString(node->get_name()) 
                                      : QString::fromStdString(stop.get_node_id());
            auto* nameItem = new QTableWidgetItem(stationName);
            nameItem->setFlags(nameItem->flags() & ~Qt::ItemIsEditable);
            scheduleDetailsTable->setItem(tableRow, 0, nameItem);
            
            // Arrival time (editable, except first stop)
            if (i == 0) {
                auto* arrivalItem = new QTableWidgetItem("-");
                arrivalItem->setFlags(arrivalItem->flags() & ~Qt::ItemIsEditable);
                arrivalItem->setTextAlignment(Qt::AlignCenter);
                scheduleDetailsTable->setItem(tableRow, 1, arrivalItem);
            } else {
                auto arrivalTime = std::chrono::system_clock::to_time_t(stop.get_arrival());
                QDateTime arrivalQt = QDateTime::fromSecsSinceEpoch(arrivalTime);
                scheduleDetailsTable->setItem(tableRow, 1, new QTableWidgetItem(arrivalQt.toString("HH:mm")));
            }
            
            // Departure time (editable, except last stop)
            if (i == stops.size() - 1) {
                auto* departureItem = new QTableWidgetItem("-");
                departureItem->setFlags(departureItem->flags() & ~Qt::ItemIsEditable);
                departureItem->setTextAlignment(Qt::AlignCenter);
                scheduleDetailsTable->setItem(tableRow, 2, departureItem);
            } else {
                auto departureTime = std::chrono::system_clock::to_time_t(stop.get_departure());
                QDateTime departureQt = QDateTime::fromSecsSinceEpoch(departureTime);
                scheduleDetailsTable->setItem(tableRow, 2, new QTableWidgetItem(departureQt.toString("HH:mm")));
            }
            
            // Platform (editable)
            auto platform = stop.get_platform();
            scheduleDetailsTable->setItem(tableRow, 3, new QTableWidgetItem(
                platform ? QString::number(*platform) : "Auto"
            ));
        }
        
        scheduleDetailsTable->blockSignals(false);
        
        // Aggiorna il grafico con tutti i treni sulla stessa linea
        if (scheduleGraphWidget) {
            // Trova tutti i treni che attraversano le stesse stazioni
            std::vector<std::shared_ptr<TrainSchedule>> relatedSchedules;
            std::vector<std::string> selectedNodes;
            
            // Estrai le stazioni del treno selezionato
            for (const auto& stop : stops) {
                selectedNodes.push_back(stop.get_node_id());
            }
            
            // Trova window temporale
            auto selectedFirstTime = std::chrono::system_clock::to_time_t(stops.front().get_departure());
            auto selectedLastTime = std::chrono::system_clock::to_time_t(stops.back().get_arrival());
            int selectedDuration = (selectedLastTime - selectedFirstTime) / 60; // minuti
            
            // Aggiungi prima il treno selezionato
            relatedSchedules.push_back(schedule);
            
            // Calcola finestra temporale una volta
            int timeWindowMinutes = AppSettings::instance().getTrafficTimeWindowMinutes();
            int timeWindowSeconds = timeWindowMinutes * 60;
            std::time_t windowStart = selectedFirstTime - timeWindowSeconds;
            std::time_t windowEnd = selectedLastTime + timeWindowSeconds;
            
            // Cerca altri treni che circolano sulla stessa tratta
            for (size_t i = 0; i < schedules.size(); ++i) {
                if (static_cast<int>(i) == currentScheduleIndex) continue;
                
                const auto& otherSchedule = schedules[i];
                if (!otherSchedule || otherSchedule->get_stop_count() < 2) continue;
                
                const auto& otherStops = otherSchedule->get_stops();
                
                // Conta stazioni in comune CHE IL TRENO ATTRAVERSA NELLA FINESTRA TEMPORALE
                int commonStations = 0;
                bool hasStopInWindow = false;
                
                for (const auto& otherStop : otherStops) {
                    // Controlla se questa fermata è in una stazione comune
                    bool isCommonStation = false;
                    for (const auto& selectedNode : selectedNodes) {
                        if (otherStop.get_node_id() == selectedNode) {
                            isCommonStation = true;
                            commonStations++;
                            break;
                        }
                    }
                    
                    // Se è una stazione comune, controlla se il treno ci passa nella finestra temporale
                    if (isCommonStation) {
                        auto stopTime = std::chrono::system_clock::to_time_t(otherStop.get_arrival());
                        if (stopTime >= windowStart && stopTime <= windowEnd) {
                            hasStopInWindow = true;
                        }
                    }
                }
                
                // Il treno è rilevante solo se:
                // 1. Ha almeno N stazioni in comune
                // 2. Passa per almeno una di queste stazioni DURANTE la finestra temporale
                if (!hasStopInWindow) continue; // Non passa nella finestra temporale
                
                // Se ha abbastanza stazioni in comune, mostralo (usa impostazioni)
                int minStations = AppSettings::instance().getMinCommonStations();
                if (commonStations >= minStations) {
                    relatedSchedules.push_back(otherSchedule);
                }
            }
            
            qDebug() << "Trovati" << relatedSchedules.size() << "treni sulla stessa linea (includendo selezionato)";
            
            // Imposta finestra temporale per limitare la visualizzazione
            scheduleGraphWidget->setTimeWindow(windowStart, windowEnd);
            
            // Usa setSchedules per visualizzazione multipla
            if (relatedSchedules.size() > 1) {
                scheduleGraphWidget->setSchedules(relatedSchedules, network, 0);
            } else {
                scheduleGraphWidget->setSchedule(schedule, network);
            }
        }
}

// Intercetta modifiche e ricalcola tutto l'orario
void MainWindow::onScheduleDetailItemChanged(QTableWidgetItem* item) {
    qDebug() << "\n********** onScheduleDetailItemChanged **********";
    
    if (!item) {
        qDebug() << "Item è NULL, uscita";
        return;
    }
    
    if (currentScheduleIndex < 0 || currentScheduleIndex >= static_cast<int>(schedules.size())) {
        qDebug() << "currentScheduleIndex non valido:" << currentScheduleIndex;
        return;
    }
    
    if (isUpdatingScheduleDetails) {
        qDebug() << "isUpdatingScheduleDetails=true, uscita (evito ricorsione)";
        return;
    }
    
    isUpdatingScheduleDetails = true;
    
    auto schedule = schedules[currentScheduleIndex];
    int row = item->row();
    int col = item->column();
    QString valueText = item->text().trimmed();
    
    qDebug() << "===== DATI MODIFICA =====";
    qDebug() << "Riga:" << row << "| Colonna:" << col;
    qDebug() << "Valore inserito:" << valueText;
    
    // Determina stazione e tipo modifica
    if (row >= 0 && row < scheduleDetailsTable->rowCount()) {
        QString stationName = scheduleDetailsTable->item(row, 0)->text();
        qDebug() << "Stazione:" << stationName;
        
        if (col == 1) {
            qDebug() << "Tipo modifica: ARRIVO";
        } else if (col == 2) {
            qDebug() << "Tipo modifica: PARTENZA";
        } else if (col == 3) {
            qDebug() << "Tipo modifica: BINARIO";
        }
    }
    
    // Trova il treno per i calcoli
    std::shared_ptr<Train> train = nullptr;
    std::string scheduleTrainId = schedule->get_train_id();
    
    qDebug() << "\n===== DEBUG RICERCA TRENO =====";
    qDebug() << "Schedule Train ID:" << QString::fromStdString(scheduleTrainId);
    qDebug() << "Numero treni disponibili:" << trains.size();
    
    for (size_t i = 0; i < trains.size(); ++i) {
        const auto& t = trains[i];
        std::string trainId = t->get_id();
        qDebug() << "  Treno" << i << "- ID:" << QString::fromStdString(trainId);
        
        if (trainId == scheduleTrainId) {
            train = t;
            qDebug() << "  ✓ MATCH TROVATO!";
            break;
        }
    }
    
    // Se treno non trovato, usa valori di default ma NON bloccare
    double maxSpeed = 160.0; // Default 160 km/h
    if (train) {
        maxSpeed = train->get_max_speed();
        qDebug() << "✓ Treno trovato - Vel. max:" << maxSpeed << "km/h";
    } else {
        qDebug() << "✗ ATTENZIONE: Treno NON trovato! Uso velocità default:" << maxSpeed << "km/h";
    }
    qDebug() << "===============================\n";
    
    try {
        qDebug() << "col =" << col << "| row =" << row;
        
        // Modifica ARRIVO (col 1)
        if (col == 1 && row > 0) {
            qDebug() << "ENTRANDO NEL BLOCCO ARRIVO";
            
            // BLOCCA SEGNALI SUBITO per evitare ricorsione
            scheduleDetailsTable->blockSignals(true);
            
            QString timeStr = item->text().trimmed();
            QTime time = QTime::fromString(timeStr, "H:mm");
            
            // Se formato H:mm fallisce, prova HH:mm
            if (!time.isValid()) {
                time = QTime::fromString(timeStr, "HH:mm");
            }
            
            // Se ancora invalido, segna in rosso e FERMATI
            if (!time.isValid()) {
                item->setForeground(QBrush(Qt::red));
                scheduleDetailsTable->blockSignals(false);
                isUpdatingScheduleDetails = false;
                return;
            }
            
            // Reset colore se valido
            item->setForeground(QBrush(Qt::black));
            
            // Applica il nuovo arrivo
            auto& stop = schedule->get_stop(row);
            auto currentArrival = stop.get_arrival();
            auto currentDeparture = stop.get_departure();
            
            auto currentDate = std::chrono::system_clock::to_time_t(currentArrival);
            QDateTime currentDateTime = QDateTime::fromSecsSinceEpoch(currentDate);
            QDateTime newDateTime(currentDateTime.date(), time);
            auto newArrival = std::chrono::system_clock::from_time_t(newDateTime.toSecsSinceEpoch());
            
            qDebug() << "Vecchio arrivo:" << currentDateTime.toString("HH:mm");
            qDebug() << "Nuovo arrivo:" << newDateTime.toString("HH:mm");
            
            // MANTIENI la partenza esistente - l'utente può modificarla manualmente
            // Questo permette di impostare manualmente il tempo di sosta desiderato
            stop.set_times(newArrival, currentDeparture);
            
            auto depTime = std::chrono::system_clock::to_time_t(currentDeparture);
            QDateTime depQt = QDateTime::fromSecsSinceEpoch(depTime);
            qDebug() << "Partenza (INVARIATA):" << depQt.toString("HH:mm");
            
            // NON ricalcola le fermate successive quando si modifica l'ARRIVO
            qDebug() << "\n>>> ARRIVO modificato: ricalcolo SOLO fermate precedenti (non successive)";
            
            // RICALCOLA TUTTE LE FERMATE PRECEDENTI
            qDebug() << "\n----- RICALCOLO FERMATE PRECEDENTI -----";
            for (int i = row - 1; i >= 0; --i) {
                auto& currStop = schedule->get_stop(i);
                auto& nextStop = schedule->get_stop(i + 1);
                
                auto currNode = network->get_node(currStop.get_node_id());
                auto nextNode = network->get_node(nextStop.get_node_id());
                
                qDebug() << "\nFermata" << i << ":" << (currNode ? QString::fromStdString(currNode->get_name()) : "?");
                
                auto nextArrival = nextStop.get_arrival();
                double distance = network->calculate_distance(currStop.get_node_id(), nextStop.get_node_id());
                
                // Se distanza = 0, calcola distanza geografica (Haversine)
                if (distance == 0.0 && currNode && nextNode) {
                    double lat1 = currNode->get_latitude() * M_PI / 180.0;
                    double lon1 = currNode->get_longitude() * M_PI / 180.0;
                    double lat2 = nextNode->get_latitude() * M_PI / 180.0;
                    double lon2 = nextNode->get_longitude() * M_PI / 180.0;
                    
                    double dlat = lat2 - lat1;
                    double dlon = lon2 - lon1;
                    double a = sin(dlat/2) * sin(dlat/2) + 
                              cos(lat1) * cos(lat2) * sin(dlon/2) * sin(dlon/2);
                    double c = 2 * atan2(sqrt(a), sqrt(1-a));
                    distance = 6371.0 * c; // Raggio Terra in km
                    
                    qDebug() << "  Distanza (geografica calcolata):" << distance << "km";
                } else {
                    qDebug() << "  Distanza (da grafo):" << distance << "km";
                }
                
                // Calcola tempo di viaggio (anche se distanza = 0, usa tempo minimo di 2 minuti)
                int travelSeconds = 120; // default 2 minuti se distanza = 0
                
                if (distance > 0) {
                    double avgSpeed = maxSpeed * 0.75;
                    double travelHours = distance / avgSpeed;
                    travelSeconds = static_cast<int>(travelHours * 3600);
                } else {
                    qDebug() << "  ATTENZIONE: Distanza = 0! Uso tempo default";
                }
                
                qDebug() << "  Tempo viaggio:" << travelSeconds << "secondi (" << (travelSeconds/60) << "minuti)";
                
                auto calcDeparture = nextArrival - std::chrono::seconds(travelSeconds);
                
                auto depTime = std::chrono::system_clock::to_time_t(calcDeparture);
                QDateTime depQt = QDateTime::fromSecsSinceEpoch(depTime);
                qDebug() << "  Partenza calcolata:" << depQt.toString("HH:mm");
                
                if (i == 0) {
                    qDebug() << "  (Prima fermata - arrival = departure)";
                    currStop.set_times(calcDeparture, calcDeparture);
                } else {
                    // Usa dwell time fisso di 2 minuti
                    auto calcArrival = calcDeparture - std::chrono::seconds(120);
                    auto arrTime = std::chrono::system_clock::to_time_t(calcArrival);
                    QDateTime arrQt = QDateTime::fromSecsSinceEpoch(arrTime);
                    qDebug() << "  Arrivo calcolato:" << arrQt.toString("HH:mm");
                    
                    currStop.set_times(calcArrival, calcDeparture);
                }
            }
            qDebug() << ">>> FINE BLOCCO ARRIVO - ora aggiorno tabella";
        } // chiude if (col == 1 && row > 0)
        
        // Modifica PARTENZA (col 2)
        else if (col == 2) {
            qDebug() << "ENTRANDO NEL BLOCCO PARTENZA";
            
            // BLOCCA SEGNALI SUBITO per evitare ricorsione
            scheduleDetailsTable->blockSignals(true);
            
            QString timeStr = item->text().trimmed();
            QTime time = QTime::fromString(timeStr, "H:mm");
            
            // Se formato H:mm fallisce, prova HH:mm
            if (!time.isValid()) {
                time = QTime::fromString(timeStr, "HH:mm");
            }
            
            // Se ancora invalido, segna in rosso e FERMATI
            if (!time.isValid()) {
                item->setForeground(QBrush(Qt::red));
                scheduleDetailsTable->blockSignals(false);
                isUpdatingScheduleDetails = false;
                return;
            }
            
            // Reset colore se valido
            item->setForeground(QBrush(Qt::black));
            
            auto& stop = schedule->get_stop(row);
            auto currentDeparture = stop.get_departure();
            auto currentDate = std::chrono::system_clock::to_time_t(currentDeparture);
            QDateTime currentDateTime = QDateTime::fromSecsSinceEpoch(currentDate);
            QDateTime newDateTime(currentDateTime.date(), time);
            auto newDeparture = std::chrono::system_clock::from_time_t(newDateTime.toSecsSinceEpoch());
            
            qDebug() << "Vecchia partenza:" << currentDateTime.toString("HH:mm");
            qDebug() << "Nuova partenza:" << newDateTime.toString("HH:mm");
            
            // Per la prima fermata, arrivo = partenza (non c'è viaggio prima)
            qDebug() << ">>> PRIMA di set_times - row =" << row;
            if (row == 0) {
                qDebug() << ">>> Prima fermata: uso set_times() per impostare arrival = departure";
                // Per la prima fermata, arrival = departure
                stop.set_times(newDeparture, newDeparture);
                qDebug() << "Prima fermata: arrival e departure aggiornati (entrambi uguali)";
            } else {
                qDebug() << ">>> Fermata intermedia: MANTIENI arrivo esistente, cambia SOLO partenza";
                // MANTIENI l'arrivo esistente, cambia SOLO la partenza
                auto existingArrival = stop.get_arrival();
                stop.set_times(existingArrival, newDeparture);
                
                auto arrTime = std::chrono::system_clock::to_time_t(existingArrival);
                QDateTime arrQt = QDateTime::fromSecsSinceEpoch(arrTime);
                qDebug() << "Arrivo (INVARIATO):" << arrQt.toString("HH:mm");
            }
            
            qDebug() << "\n----- RICALCOLO FERMATE SUCCESSIVE (da partenza) -----";
            // RICALCOLA SUCCESSIVE
            for (size_t i = row + 1; i < schedule->get_stop_count(); ++i) {
                auto& prevStop = schedule->get_stop(i - 1);
                auto& currStop = schedule->get_stop(i);
                
                auto prevNode = network->get_node(prevStop.get_node_id());
                auto currNode = network->get_node(currStop.get_node_id());
                qDebug() << "\nFermata" << i << ":" << (currNode ? QString::fromStdString(currNode->get_name()) : "?");
                
                auto previousDeparture = prevStop.get_departure();
                double distance = network->calculate_distance(prevStop.get_node_id(), currStop.get_node_id());
                
                // Se distanza = 0, calcola distanza geografica (Haversine)
                if (distance == 0.0 && prevNode && currNode) {
                    double lat1 = prevNode->get_latitude() * M_PI / 180.0;
                    double lon1 = prevNode->get_longitude() * M_PI / 180.0;
                    double lat2 = currNode->get_latitude() * M_PI / 180.0;
                    double lon2 = currNode->get_longitude() * M_PI / 180.0;
                    
                    double dlat = lat2 - lat1;
                    double dlon = lon2 - lon1;
                    double a = sin(dlat/2) * sin(dlat/2) + 
                              cos(lat1) * cos(lat2) * sin(dlon/2) * sin(dlon/2);
                    double c = 2 * atan2(sqrt(a), sqrt(1-a));
                    distance = 6371.0 * c; // Raggio Terra in km
                    
                    qDebug() << "  Distanza (geografica calcolata):" << distance << "km";
                } else {
                    qDebug() << "  Distanza (da grafo):" << distance << "km";
                }
                
                // Calcola tempo di viaggio (anche se distanza = 0, usa tempo minimo di 2 minuti)
                int travelSeconds = 120; // default 2 minuti se distanza = 0
                
                if (distance > 0) {
                    double avgSpeed = maxSpeed * 0.75;
                    double travelHours = distance / avgSpeed;
                    travelSeconds = static_cast<int>(travelHours * 3600);
                } else {
                    qDebug() << "  ATTENZIONE: Distanza = 0! Uso tempo default";
                }
                
                qDebug() << "  Tempo viaggio:" << travelSeconds << "sec (" << (travelSeconds/60) << "min)";
                
                auto calcArrival = previousDeparture + std::chrono::seconds(travelSeconds);
                
                auto arrTime = std::chrono::system_clock::to_time_t(calcArrival);
                QDateTime arrQt = QDateTime::fromSecsSinceEpoch(arrTime);
                qDebug() << "  Arrivo:" << arrQt.toString("HH:mm");
                
                // Usa dwell time fisso di 2 minuti
                auto calcDeparture = calcArrival + std::chrono::seconds(120);
                currStop.set_times(calcArrival, calcDeparture);
                
                auto depTime = std::chrono::system_clock::to_time_t(calcDeparture);
                QDateTime depQt = QDateTime::fromSecsSinceEpoch(depTime);
                qDebug() << "  Partenza:" << depQt.toString("HH:mm");
            }
            
            // NON ricalcola le fermate precedenti quando si modifica la PARTENZA
            qDebug() << "\n>>> PARTENZA modificata: ricalcolo SOLO fermate successive (non precedenti)";
            qDebug() << ">>> FINE BLOCCO PARTENZA - ora aggiorno tabella";
        } // chiude if (col == 2)
        
        // Modifica BINARIO (col 3)
        else if (col == 3) {
            qDebug() << "ENTRANDO NEL BLOCCO BINARIO";
            
            // BLOCCA SEGNALI per evitare ricorsione
            scheduleDetailsTable->blockSignals(true);
            
            QString platformStr = item->text().trimmed();
            auto& stop = schedule->get_stop(row);
            
            if (platformStr.isEmpty() || platformStr.toLower() == "auto") {
                stop.clear_platform();
            } else {
                bool ok;
                int platform = platformStr.toInt(&ok);
                if (ok && platform > 0) {
                    stop.set_platform(platform);
                }
            }
            
            // SBLOCCA SEGNALI per il binario (non passa da aggiornamento tabella)
            scheduleDetailsTable->blockSignals(false);
        }
        
        // Aggiorna TUTTA la tabella (comune per arrivo e partenza)
        if (col == 1 || col == 2) {
            qDebug() << "\n===== AGGIORNAMENTO TABELLA =====";
            // Segnali già bloccati all'inizio del blocco ARRIVO/PARTENZA
            for (size_t i = 0; i < schedule->get_stop_count(); ++i) {
                auto& s = schedule->get_stop(i);
                auto node = network->get_node(s.get_node_id());
                
                // Aggiorna ARRIVO (tutte le righe tranne la prima)
                if (i > 0) {
                    QTableWidgetItem* arrItem = scheduleDetailsTable->item(i, 1);
                    if (arrItem) {
                        auto arr = std::chrono::system_clock::to_time_t(s.get_arrival());
                        QString arrText = QDateTime::fromSecsSinceEpoch(arr).toString("HH:mm");
                        arrItem->setText(arrText);
                        
                        // Verifica incongruenza: arrivo > partenza nella stessa fermata
                        if (s.get_arrival() > s.get_departure()) {
                            arrItem->setForeground(QBrush(Qt::red));
                        } else {
                            arrItem->setForeground(QBrush(Qt::black));
                        }
                        
                        qDebug() << "Riga" << i << (node ? QString::fromStdString(node->get_name()) : "?") 
                                 << "- Arrivo aggiornato:" << arrText;
                    } else {
                        qDebug() << "ERRORE: arrItem è NULL per riga" << i;
                    }
                }
                
                // Aggiorna PARTENZA (tutte le righe tranne l'ultima)
                if (i < schedule->get_stop_count() - 1) {
                    QTableWidgetItem* depItem = scheduleDetailsTable->item(i, 2);
                    if (depItem) {
                        auto dep = std::chrono::system_clock::to_time_t(s.get_departure());
                        QString depText = QDateTime::fromSecsSinceEpoch(dep).toString("HH:mm");
                        depItem->setText(depText);
                        
                        // Verifica incongruenza: partenza di questa fermata > arrivo della prossima
                        if (i + 1 < schedule->get_stop_count()) {
                            auto& nextStop = schedule->get_stop(i + 1);
                            if (s.get_departure() > nextStop.get_arrival()) {
                                depItem->setForeground(QBrush(Qt::red));
                            } else {
                                depItem->setForeground(QBrush(Qt::black));
                            }
                        } else {
                            depItem->setForeground(QBrush(Qt::black));
                        }
                        
                        qDebug() << "Riga" << i << (node ? QString::fromStdString(node->get_name()) : "?") 
                                 << "- Partenza aggiornata:" << depText;
                    } else {
                        qDebug() << "ERRORE: depItem è NULL per riga" << i;
                    }
                }
                // Ultima fermata: NON aggiornare la partenza (deve rimanere "-")
            }
            scheduleDetailsTable->blockSignals(false);
            qDebug() << "===== FINE AGGIORNAMENTO TABELLA =====\n";
        }
        
        // Aggiorna info
        auto totalDuration = schedule->get_total_duration();
        int hours = totalDuration.count() / 3600;
        int minutes = (totalDuration.count() % 3600) / 60;
        
        QString info = "<b>🚂 Treno:</b> " + QString::fromStdString(schedule->get_train_id()) + " | ";
        info += "<b>ID:</b> " + QString::fromStdString(schedule->get_schedule_id()) + "<br>";
        info += "<b>Durata:</b> " + QString::number(hours) + "h " + QString::number(minutes) + "m | ";
        info += "<b>Distanza:</b> " + QString::number(schedule->get_total_distance(), 'f', 1) + " km | ";
        info += "<b>V.Media:</b> " + QString::number(schedule->get_average_speed(), 'f', 1) + " km/h";
        
        scheduleDetailsInfo->setText(info);
        
        // Aggiorna il grafico dopo le modifiche - con traffico correlato
        if (scheduleGraphWidget) {
            // Trova tutti i treni sulla stessa linea con orari vicini
            std::vector<std::shared_ptr<TrainSchedule>> relatedSchedules;
            relatedSchedules.push_back(schedule); // Il treno selezionato è sempre il primo
            
            // Usa il vettore schedules della MainWindow
            const auto& stops = schedule->get_stops();
            
            if (!stops.empty()) {
                // Estrai gli ID delle stazioni dal treno selezionato
                std::vector<std::string> selectedNodes;
                for (const auto& stop : stops) {
                    selectedNodes.push_back(stop.get_node_id());
                }
                
                // Ottieni il tempo di partenza del primo stop
                auto selectedFirstTime = std::chrono::system_clock::to_time_t(stops.front().get_departure());
                auto selectedLastTime = std::chrono::system_clock::to_time_t(stops.back().get_arrival());
                
                // Calcola finestra temporale una volta
                int timeWindowMinutes = AppSettings::instance().getTrafficTimeWindowMinutes();
                int timeWindowSeconds = timeWindowMinutes * 60;
                std::time_t windowStart = selectedFirstTime - timeWindowSeconds;
                std::time_t windowEnd = selectedLastTime + timeWindowSeconds;
                
                // Cerca altri treni con stazioni in comune
                for (size_t i = 0; i < schedules.size(); ++i) {
                    auto otherSchedule = schedules[i];
                    if (otherSchedule->get_schedule_id() == schedule->get_schedule_id()) {
                        continue; // Salta il treno selezionato
                    }
                    
                    const auto& otherStops = otherSchedule->get_stops();
                    if (otherStops.empty()) continue;
                    
                    // Conta stazioni in comune CHE IL TRENO ATTRAVERSA NELLA FINESTRA TEMPORALE
                    int commonStations = 0;
                    bool hasStopInWindow = false;
                    
                    for (const auto& otherStop : otherStops) {
                        // Controlla se questa fermata è in una stazione comune
                        bool isCommonStation = false;
                        for (const auto& selectedNode : selectedNodes) {
                            if (otherStop.get_node_id() == selectedNode) {
                                isCommonStation = true;
                                commonStations++;
                                break;
                            }
                        }
                        
                        // Se è una stazione comune, controlla se il treno ci passa nella finestra temporale
                        if (isCommonStation) {
                            auto stopTime = std::chrono::system_clock::to_time_t(otherStop.get_arrival());
                            if (stopTime >= windowStart && stopTime <= windowEnd) {
                                hasStopInWindow = true;
                            }
                        }
                    }
                    
                    // Il treno è rilevante solo se passa per stazioni comuni nella finestra temporale
                    if (!hasStopInWindow) {
                        continue; // Non passa nella finestra temporale
                    }
                    
                    // Se hanno abbastanza stazioni in comune (configurabile), aggiungi alla lista
                    int minStations = AppSettings::instance().getMinCommonStations();
                    if (commonStations >= minStations) {
                        relatedSchedules.push_back(otherSchedule);
                    }
                }
                
                qDebug() << "Treni trovati sulla stessa linea:" << relatedSchedules.size();
                
                // Imposta finestra temporale per limitare la visualizzazione
                scheduleGraphWidget->setTimeWindow(windowStart, windowEnd);
                
                // Usa la visualizzazione multi-treno se ci sono altri treni correlati
                if (relatedSchedules.size() > 1) {
                    scheduleGraphWidget->setSchedules(relatedSchedules, network, 0); // Il primo è sempre evidenziato
                } else {
                    scheduleGraphWidget->setSchedule(schedule, network);
                }
                scheduleGraphWidget->repaint(); // Forza il repaint immediato e sincrono
            }
        }
        
        // Salva l'indice corrente per ripristinare la selezione dopo l'aggiornamento
        int savedScheduleIndex = currentScheduleIndex;
        
        // Blocca temporaneamente i segnali del TreeView per evitare re-trigger di selezione
        if (schedulesTreeView) {
            schedulesTreeView->blockSignals(true);
        }
        
        // Aggiorna la vista TreeView degli schedules (orari aggiornati)
        updateSchedulesView();
        
        // Ripristina la selezione
        currentScheduleIndex = savedScheduleIndex;
        
        // Sblocca i segnali
        if (schedulesTreeView) {
            schedulesTreeView->blockSignals(false);
        }
        
    } catch (const std::exception& e) {
        qDebug() << "ECCEZIONE CATTURATA:" << e.what();
        
        // SBLOCCA SEGNALI
        scheduleDetailsTable->blockSignals(false);
        
        // Non ripristina, non mostra errori - lascia che l'utente veda l'errore in rosso nella tabella
        
        isUpdatingScheduleDetails = false;
        return;
    }
    
    isUpdatingScheduleDetails = false;
}

void MainWindow::onScheduleEditConfirm() {
    if (currentScheduleIndex < 0 || currentScheduleIndex >= static_cast<int>(schedules.size())) {
        return;
    }
    
    // I dati sono già stati applicati da onScheduleDetailItemChanged
    // Qui aggiorniamo solo il backup e segniamo come modificato
    auto schedule = schedules[currentScheduleIndex];
    originalSchedule = std::make_shared<TrainSchedule>(*schedule);
    
    isModified = true;
    updateWindowTitle();
    
    QMessageBox::information(this, tr("OK"), tr("Modifiche confermate"));
}

void MainWindow::onScheduleEditCancel() {
    if (!originalSchedule || currentScheduleIndex < 0 || 
        currentScheduleIndex >= static_cast<int>(schedules.size())) {
        return;
    }
    
    // Ripristina lo schedule originale
    schedules[currentScheduleIndex] = std::make_shared<TrainSchedule>(*originalSchedule);
    
    // Ricarica la vista
    onScheduleSelectionChanged();
    
    QMessageBox::information(this, tr("Annullato"), tr("Modifiche annullate"));
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
    if (!stationsModel || !network) return;  // Safety check
    
    stationsModel->removeRows(0, stationsModel->rowCount());
    
    auto nodes = network->get_all_nodes();
    
    // Ordina le stazioni alfabeticamente per nome
    std::vector<std::shared_ptr<Node>> sortedNodes(nodes.begin(), nodes.end());
    std::sort(sortedNodes.begin(), sortedNodes.end(), 
        [](const std::shared_ptr<Node>& a, const std::shared_ptr<Node>& b) {
            return a->get_name() < b->get_name();
        });
    
    for (const auto& node : sortedNodes) {
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
    if (!connectionsModel || !network) return;  // Safety check
    
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
    if (!trainsModel) return;  // Safety check
    
    trainsModel->removeRows(0, trainsModel->rowCount());
    
    for (const auto& train : trains) {
        if (!train) continue;  // Skip null trains
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
    if (!linesModel) return;  // Safety check
    
    linesModel->clear();
    
    if (lines.isEmpty()) {
        linesModel->appendRow(new QStandardItem(tr("Nessuna linea definita")));
        
        // Aggiorna mappa anche se vuota
        if (networkMapWidget) {
            networkMapWidget->clear();
        }
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
    
    // Aggiorna la mappa della rete
    if (networkMapWidget && network) {
        networkMapWidget->setNetwork(network);
        networkMapWidget->setLines(lines);
    }
}

void MainWindow::updateSchedulesView() {
    qDebug() << "updateSchedulesView() START";
    
    if (!schedulesModel || !lineFilterCombo || !network) {
        qDebug() << "ERROR: nullptr detected";
        return;
    }
    
    // BLOCCA i signal per evitare trigger durante l'update
    if (schedulesTreeView) {
        schedulesTreeView->blockSignals(true);
    }
    lineFilterCombo->blockSignals(true);
    
    // Pulisci e aggiorna la lista orari
    schedulesModel->removeRows(0, schedulesModel->rowCount());
    
    for (size_t i = 0; i < schedules.size(); ++i) {
        const auto& schedule = schedules[i];
        if (!schedule) continue;  // Skip null schedules
        
        const auto& stops = schedule->get_stops();
        QString trainId = QString::fromStdString(schedule->get_train_id());
        
        // Get train name from trains vector
        QString trainLabel = trainId;  // Default to ID if train not found
        for (const auto& train : trains) {
            if (train && train->get_id() == schedule->get_train_id()) {
                QString trainName = QString::fromStdString(train->get_name());
                if (!trainName.isEmpty()) {
                    trainLabel = trainName;
                } else {
                    trainLabel = trainId;  // Fallback to ID if name is empty
                }
                break;
            }
        }
        
        QString route = "";
        QString departureTime = "";
        QString arrivalTime = "";
        
        if (!stops.empty()) {
            auto firstNode = network->get_node(stops.front().get_node_id());
            auto lastNode = network->get_node(stops.back().get_node_id());
            
            if (firstNode && lastNode) {
                route = QString::fromStdString(firstNode->get_name()) + 
                       " → " + QString::fromStdString(lastNode->get_name());
            }
            
            // Estrai orari di partenza e arrivo
            auto firstDep = std::chrono::system_clock::to_time_t(stops.front().get_departure());
            auto lastArr = std::chrono::system_clock::to_time_t(stops.back().get_arrival());
            
            departureTime = QDateTime::fromSecsSinceEpoch(firstDep).toString("HH:mm");
            arrivalTime = QDateTime::fromSecsSinceEpoch(lastArr).toString("HH:mm");
        }
        
        QList<QStandardItem*> row;
        auto *trainItem = new QStandardItem(trainLabel);  // Use train name instead of ID
        auto *routeItem = new QStandardItem(route);
        auto *depItem = new QStandardItem(departureTime);
        auto *arrItem = new QStandardItem(arrivalTime);
        
        // Salva l'indice nell'item per poterlo recuperare
        trainItem->setData(static_cast<int>(i), Qt::UserRole);
        
        row << trainItem << routeItem << depItem << arrItem;
        schedulesModel->appendRow(row);
    }
    
    // Update line filter combo
    lineFilterCombo->clear();
    lineFilterCombo->addItem(tr("Tutte le linee"), -1);
    for (int i = 0; i < lines.size(); ++i) {
        lineFilterCombo->addItem(lines[i].name, i);
    }
    
    // SBLOCCA i signal
    if (schedulesTreeView) {
        schedulesTreeView->blockSignals(false);
    }
    lineFilterCombo->blockSignals(false);
    
    qDebug() << "updateSchedulesView() END";
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

void MainWindow::showSettings() {
    SettingsDialog dialog(this);
    if (dialog.exec() == QDialog::Accepted) {
        // Le impostazioni sono già state salvate dal dialog
        // Eventualmente aggiorna la UI se necessario
        QMessageBox::information(this, tr("Impostazioni"),
            tr("Le modifiche alle impostazioni saranno applicate alle prossime operazioni."));
    }
}

void MainWindow::closeEvent(QCloseEvent *event) {
    if (maybeSave()) {
        event->accept();
    } else {
        event->ignore();
    }
}

} // namespace fdc
