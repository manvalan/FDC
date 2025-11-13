#include "connection_dialog.hpp"
#include <QVBoxLayout>
#include <QFormLayout>
#include <QLabel>
#include <QDialogButtonBox>
#include <QMessageBox>
#include <QGroupBox>
#include <QSpinBox>
#include <QRegularExpression>

namespace fdc {

ConnectionDialog::ConnectionDialog(std::shared_ptr<RailwayNetwork> net, 
                                   QWidget *parent)
    : QDialog(parent)
    , network(net)
    , existingConnection(nullptr)
    , isEditMode(false)
{
    setupUI();
    populateStationCombos();
    setWindowTitle("Aggiungi Connessione");
}

ConnectionDialog::ConnectionDialog(std::shared_ptr<RailwayNetwork> net,
                                   std::shared_ptr<Edge> connection,
                                   QWidget *parent)
    : QDialog(parent)
    , network(net)
    , existingConnection(connection)
    , isEditMode(true)
{
    setupUI();
    populateStationCombos();
    loadConnectionData();
    setWindowTitle("Modifica Connessione");
}

void ConnectionDialog::setupUI() {
    auto *mainLayout = new QVBoxLayout(this);
    
    // Form group
    auto *formGroup = new QGroupBox("Dati Connessione", this);
    auto *formLayout = new QFormLayout();
    
    // Station selection
    fromStationCombo = new QComboBox(this);
    fromStationCombo->setPlaceholderText("Seleziona stazione partenza");
    formLayout->addRow("Da *:", fromStationCombo);
    
    toStationCombo = new QComboBox(this);
    toStationCombo->setPlaceholderText("Seleziona stazione arrivo");
    formLayout->addRow("A *:", toStationCombo);
    
    // Distance
    distanceSpinBox = new QDoubleSpinBox(this);
    distanceSpinBox->setRange(0.1, 10000.0);
    distanceSpinBox->setDecimals(2);
    distanceSpinBox->setSingleStep(1.0);
    distanceSpinBox->setValue(10.0);
    distanceSpinBox->setSuffix(" km");
    formLayout->addRow("Distanza *:", distanceSpinBox);
    
    // Track type
    trackTypeCombo = new QComboBox(this);
    trackTypeCombo->addItem("Binario Singolo", static_cast<int>(TrackType::SINGLE));
    trackTypeCombo->addItem("Binario Doppio", static_cast<int>(TrackType::DOUBLE));
    trackTypeCombo->addItem("Alta Velocità", static_cast<int>(TrackType::HIGH_SPEED));
    trackTypeCombo->addItem("Merci", static_cast<int>(TrackType::FREIGHT));
    trackTypeCombo->setCurrentIndex(1); // Default: DOUBLE
    formLayout->addRow("Tipo Binario *:", trackTypeCombo);
    
    // Max speed
    maxSpeedSpinBox = new QDoubleSpinBox(this);
    maxSpeedSpinBox->setRange(20.0, 400.0);
    maxSpeedSpinBox->setDecimals(1);
    maxSpeedSpinBox->setSingleStep(10.0);
    maxSpeedSpinBox->setValue(160.0);
    maxSpeedSpinBox->setSuffix(" km/h");
    formLayout->addRow("Velocità Max *:", maxSpeedSpinBox);
    
    // Capacity
    capacitySpinBox = new QSpinBox(this);
    capacitySpinBox->setRange(1, 50);
    capacitySpinBox->setValue(5);
    capacitySpinBox->setSuffix(" treni");
    formLayout->addRow("Capacità *:", capacitySpinBox);
    
    // Bidirectional
    bidirectionalCheck = new QCheckBox("Bidirezionale", this);
    bidirectionalCheck->setChecked(true);
    formLayout->addRow("", bidirectionalCheck);
    
    formGroup->setLayout(formLayout);
    mainLayout->addWidget(formGroup);
    
    // Estimated time info
    auto *infoGroup = new QGroupBox("Informazioni", this);
    auto *infoLayout = new QVBoxLayout();
    
    estimatedTimeLabel = new QLabel(this);
    estimatedTimeLabel->setWordWrap(true);
    estimatedTimeLabel->setStyleSheet("color: #555; padding: 5px;");
    infoLayout->addWidget(estimatedTimeLabel);
    
    infoGroup->setLayout(infoLayout);
    mainLayout->addWidget(infoGroup);
    
    // Required fields note
    auto *noteLabel = new QLabel("* Campi obbligatori", this);
    noteLabel->setStyleSheet("color: gray; font-style: italic;");
    mainLayout->addWidget(noteLabel);
    
    // Button box
    auto *buttonBox = new QDialogButtonBox(
        QDialogButtonBox::Ok | QDialogButtonBox::Cancel,
        this);
    
    connect(buttonBox, &QDialogButtonBox::accepted, this, &ConnectionDialog::validate);
    connect(buttonBox, &QDialogButtonBox::rejected, this, &QDialog::reject);
    
    // Connect signals for live updates
    connect(distanceSpinBox, QOverload<double>::of(&QDoubleSpinBox::valueChanged),
            this, &ConnectionDialog::updateEstimatedTime);
    connect(maxSpeedSpinBox, QOverload<double>::of(&QDoubleSpinBox::valueChanged),
            this, &ConnectionDialog::updateEstimatedTime);
    
    mainLayout->addWidget(buttonBox);
    
    setLayout(mainLayout);
    setMinimumWidth(450);
    
    updateEstimatedTime();
}

void ConnectionDialog::populateStationCombos() {
    if (!network) return;
    
    fromStationCombo->clear();
    toStationCombo->clear();
    
    for (const auto& node : network->get_all_nodes()) {
        QString displayText = QString("%1 - %2")
            .arg(QString::fromStdString(node->get_id()))
            .arg(QString::fromStdString(node->get_name()));
        
        fromStationCombo->addItem(displayText, 
                                  QString::fromStdString(node->get_id()));
        toStationCombo->addItem(displayText, 
                               QString::fromStdString(node->get_id()));
    }
}

void ConnectionDialog::loadConnectionData() {
    if (!existingConnection) return;
    
    // Find and set from station
    QString fromId = QString::fromStdString(existingConnection->get_from_node());
    int fromIndex = fromStationCombo->findData(fromId);
    if (fromIndex >= 0) {
        fromStationCombo->setCurrentIndex(fromIndex);
    }
    
    // Find and set to station
    QString toId = QString::fromStdString(existingConnection->get_to_node());
    int toIndex = toStationCombo->findData(toId);
    if (toIndex >= 0) {
        toStationCombo->setCurrentIndex(toIndex);
    }
    
    distanceSpinBox->setValue(existingConnection->get_distance());
    
    // Set track type combo
    int typeIndex = trackTypeCombo->findData(
        static_cast<int>(existingConnection->get_track_type()));
    if (typeIndex >= 0) {
        trackTypeCombo->setCurrentIndex(typeIndex);
    }
    
    maxSpeedSpinBox->setValue(existingConnection->get_max_speed());
    capacitySpinBox->setValue(existingConnection->get_capacity());
    
    // Note: bidirectional is always true in current implementation
    bidirectionalCheck->setChecked(true);
    
    updateEstimatedTime();
}

void ConnectionDialog::updateEstimatedTime() {
    double distance = distanceSpinBox->value();
    double maxSpeed = maxSpeedSpinBox->value();
    
    // Calculate minimum travel time (assuming constant max speed)
    double hours = distance / maxSpeed;
    int minutes = static_cast<int>(hours * 60);
    
    QString timeText = QString("Tempo minimo di percorrenza: %1 minuti "
                              "(alla velocità massima)")
                           .arg(minutes);
    
    estimatedTimeLabel->setText(timeText);
}

void ConnectionDialog::validate() {
    // Check station selection
    if (fromStationCombo->currentIndex() < 0) {
        QMessageBox::warning(this, "Selezione Obbligatoria",
                           "Seleziona la stazione di partenza.");
        fromStationCombo->setFocus();
        return;
    }
    
    if (toStationCombo->currentIndex() < 0) {
        QMessageBox::warning(this, "Selezione Obbligatoria",
                           "Seleziona la stazione di arrivo.");
        toStationCombo->setFocus();
        return;
    }
    
    // Check that from and to are different
    QString fromId = fromStationCombo->currentData().toString();
    QString toId = toStationCombo->currentData().toString();
    
    if (fromId == toId) {
        QMessageBox::warning(this, "Connessione Non Valida",
                           "La stazione di partenza e di arrivo devono essere diverse.");
        toStationCombo->setFocus();
        return;
    }
    
    // Check if connection already exists (only for new connections)
    if (!isEditMode && network) {
        if (network->has_edge(fromId.toStdString(), toId.toStdString())) {
            QMessageBox::warning(this, "Connessione Esistente",
                               "Esiste già una connessione tra queste due stazioni.");
            return;
        }
    }
    
    accept();
}

std::shared_ptr<Edge> ConnectionDialog::getConnection() const {
    std::string fromNode = fromStationCombo->currentData().toString().toStdString();
    std::string toNode = toStationCombo->currentData().toString().toStdString();
    double distance = distanceSpinBox->value();
    TrackType trackType = static_cast<TrackType>(trackTypeCombo->currentData().toInt());
    double maxSpeed = maxSpeedSpinBox->value();
    int capacity = capacitySpinBox->value();
    
    return std::make_shared<Edge>(fromNode, toNode, distance, trackType, 
                                  maxSpeed, capacity);
}

} // namespace fdc
