#ifndef FDC_MAIN_WINDOW_HPP
#define FDC_MAIN_WINDOW_HPP

#include <QMainWindow>
#include <QTabWidget>
#include <QTableView>
#include <QTreeView>
#include <QListView>
#include <QTextEdit>
#include <QStandardItemModel>
#include <QMenuBar>
#include <QToolBar>
#include <QStatusBar>
#include <QComboBox>
#include <QString>
#include <QVector>
#include <memory>

#include "../include/railway_network.hpp"
#include "../include/schedule.hpp"
#include "../include/serialization.hpp"
#include "station_dialog.hpp"
#include "connection_dialog.hpp"

namespace fdc {

/**
 * @brief Main window dell'applicazione FDC Railway Manager
 * 
 * Interfaccia GUI principale con stile nativo macOS che permette di:
 * - Gestire reti ferroviarie (stazioni e connessioni)
 * - Definire linee colorate
 * - Creare e modificare orari dei treni
 * - Visualizzare grafici tempo-distanza
 * - Salvare/caricare progetti in formato JSON
 * - Connettersi a database MySQL (opzionale)
 */
class MainWindow : public QMainWindow {
    Q_OBJECT

public:
    explicit MainWindow(QWidget *parent = nullptr);
    ~MainWindow() override;

protected:
    void closeEvent(QCloseEvent *event) override;

private slots:
    // File menu actions
    void newProject();
    void openProject();
    void saveProject();
    void saveProjectAs();
    
    // View menu actions
    void showNetworkMap();
    void showTimetableGraph();
    void refreshViews();
    
    // Database menu actions (se BUILD_WITH_MYSQL è attivo)
    void connectToDatabase();
    void saveToDatabase();
    void loadFromDatabase();
    void showDatabaseStatus();
    
    // Help menu actions
    void showAboutDialog();
    void showDocumentation();
    
    // Tab 1: Rete Ferroviaria
    void addStation();
    void editStation();
    void deleteStation();
    void addConnection();
    void editConnection();
    void deleteConnection();
    
    // Tab 2: Linee
    void addLine();
    void editLine();
    void deleteLine();
    
    // Tab 3: Treni e Orari
    void addSchedule();
    void editSchedule();
    void deleteSchedule();
    void filterSchedulesByLine(int lineIndex);
    
    // Utility
    void onStationSelectionChanged();
    void onConnectionSelectionChanged();
    void onLineSelectionChanged();
    void onScheduleSelectionChanged();

private:
    // Setup methods
    void setupUI();
    void setupMenuBar();
    void setupToolBar();
    void setupStatusBar();
    void setupNetworkTab();
    void setupLinesTab();
    void setupSchedulesTab();
    void createConnections();
    
    // Helper methods
    void updateWindowTitle();
    void updateStationsView();
    void updateConnectionsView();
    void updateLinesView();
    void updateSchedulesView();
    bool maybeSave();
    void setModified(bool modified);
    
    // UI Components
    QTabWidget *tabWidget;
    
    // Tab 1: Rete Ferroviaria
    QTableView *stationsTable;
    QStandardItemModel *stationsModel;
    QTableView *connectionsTable;
    QStandardItemModel *connectionsModel;
    
    // Tab 2: Linee
    QListView *linesListView;
    QStandardItemModel *linesModel;
    QTextEdit *lineDetailsText;
    
    // Tab 3: Treni e Orari
    QTreeView *schedulesTreeView;
    QStandardItemModel *schedulesModel;
    QTextEdit *scheduleDetailsText;
    QComboBox *lineFilterCombo;
    
    // Toolbar actions
    QAction *actionNewStation;
    QAction *actionNewConnection;
    QAction *actionNewTrain;
    QAction *actionNewLine;
    
    // Data members
    std::shared_ptr<RailwayNetwork> network;
    std::vector<std::shared_ptr<TrainSchedule>> schedules;
    
    // State
    QString currentFilePath;
    bool isModified;
    
    // Configuration
    static constexpr int DEFAULT_WIDTH = 1200;
    static constexpr int DEFAULT_HEIGHT = 800;
};

} // namespace fdc

#endif // FDC_MAIN_WINDOW_HPP
