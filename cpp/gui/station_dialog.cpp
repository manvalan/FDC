#include "station_dialog.hpp"
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QFormLayout>
#include <QLabel>
#include <QPushButton>
#include <QDialogButtonBox>
#include <QMessageBox>
#include <QGroupBox>

namespace fdc {

StationDialog::StationDialog(QWidget *parent)
    : QDialog(parent)
    , existingStation(nullptr)
    , isEditMode(false)
{
    setupUI();
    setWindowTitle("Aggiungi Stazione");
}

StationDialog::StationDialog(std::shared_ptr<Node> station, QWidget *parent)
    : QDialog(parent)
    , existingStation(station)
    , isEditMode(true)
{
    setupUI();
    loadStationData();
    setWindowTitle("Modifica Stazione");
    idEdit->setEnabled(false); // ID cannot be changed
}

void StationDialog::setupUI() {
    auto *mainLayout = new QVBoxLayout(this);
    
    // Form group
    auto *formGroup = new QGroupBox("Dati Stazione", this);
    auto *formLayout = new QFormLayout();
    
    // ID field
    idEdit = new QLineEdit(this);
    idEdit->setPlaceholderText("es: MI, ROMA, BO01");
    formLayout->addRow("ID *:", idEdit);
    
    // Name field
    nameEdit = new QLineEdit(this);
    nameEdit->setPlaceholderText("es: Milano Centrale");
    formLayout->addRow("Nome *:", nameEdit);
    
    // Type combo
    typeCombo = new QComboBox(this);
    typeCombo->addItem("Stazione", static_cast<int>(NodeType::STATION));
    typeCombo->addItem("Interscambio", static_cast<int>(NodeType::INTERCHANGE));
    typeCombo->addItem("Bivio", static_cast<int>(NodeType::JUNCTION));
    typeCombo->addItem("Deposito", static_cast<int>(NodeType::DEPOT));
    formLayout->addRow("Tipo *:", typeCombo);
    
    // Coordinates group
    auto *coordGroup = new QGroupBox("Coordinate GPS", this);
    auto *coordLayout = new QFormLayout();
    
    latitudeSpinBox = new QDoubleSpinBox(this);
    latitudeSpinBox->setRange(-90.0, 90.0);
    latitudeSpinBox->setDecimals(6);
    latitudeSpinBox->setSingleStep(0.1);
    latitudeSpinBox->setValue(45.0); // Default: Northern Italy
    latitudeSpinBox->setSuffix("°");
    coordLayout->addRow("Latitudine *:", latitudeSpinBox);
    
    longitudeSpinBox = new QDoubleSpinBox(this);
    longitudeSpinBox->setRange(-180.0, 180.0);
    longitudeSpinBox->setDecimals(6);
    longitudeSpinBox->setSingleStep(0.1);
    longitudeSpinBox->setValue(9.0); // Default: Northern Italy
    longitudeSpinBox->setSuffix("°");
    coordLayout->addRow("Longitudine *:", longitudeSpinBox);
    
    coordGroup->setLayout(coordLayout);
    
    // Capacity and platforms
    capacitySpinBox = new QSpinBox(this);
    capacitySpinBox->setRange(1, 100);
    capacitySpinBox->setValue(5);
    capacitySpinBox->setSuffix(" treni");
    formLayout->addRow("Capacità *:", capacitySpinBox);
    
    platformsSpinBox = new QSpinBox(this);
    platformsSpinBox->setRange(0, 50);
    platformsSpinBox->setValue(2);
    platformsSpinBox->setSuffix(" binari");
    formLayout->addRow("Binari *:", platformsSpinBox);
    
    formGroup->setLayout(formLayout);
    
    // Add groups to main layout
    mainLayout->addWidget(formGroup);
    mainLayout->addWidget(coordGroup);
    
    // Required fields note
    auto *noteLabel = new QLabel("* Campi obbligatori", this);
    noteLabel->setStyleSheet("color: gray; font-style: italic;");
    mainLayout->addWidget(noteLabel);
    
    // Button box
    auto *buttonBox = new QDialogButtonBox(
        QDialogButtonBox::Ok | QDialogButtonBox::Cancel,
        this);
    
    connect(buttonBox, &QDialogButtonBox::accepted, this, &StationDialog::validate);
    connect(buttonBox, &QDialogButtonBox::rejected, this, &QDialog::reject);
    
    mainLayout->addWidget(buttonBox);
    
    setLayout(mainLayout);
    setMinimumWidth(400);
}

void StationDialog::loadStationData() {
    if (!existingStation) return;
    
    idEdit->setText(QString::fromStdString(existingStation->get_id()));
    nameEdit->setText(QString::fromStdString(existingStation->get_name()));
    
    // Set type combo
    int typeIndex = typeCombo->findData(static_cast<int>(existingStation->get_type()));
    if (typeIndex >= 0) {
        typeCombo->setCurrentIndex(typeIndex);
    }
    
    latitudeSpinBox->setValue(existingStation->get_latitude());
    longitudeSpinBox->setValue(existingStation->get_longitude());
    capacitySpinBox->setValue(existingStation->get_capacity());
    platformsSpinBox->setValue(existingStation->get_platforms());
}

void StationDialog::validate() {
    // Check required fields
    if (idEdit->text().trimmed().isEmpty()) {
        QMessageBox::warning(this, "Campo Obbligatorio",
                           "Il campo ID è obbligatorio.");
        idEdit->setFocus();
        return;
    }
    
    if (nameEdit->text().trimmed().isEmpty()) {
        QMessageBox::warning(this, "Campo Obbligatorio",
                           "Il campo Nome è obbligatorio.");
        nameEdit->setFocus();
        return;
    }
    
    // Validate ID format (alphanumeric and underscore only)
    QString id = idEdit->text().trimmed();
    QRegularExpression idRegex("^[A-Za-z0-9_]+$");
    if (!idRegex.match(id).hasMatch()) {
        QMessageBox::warning(this, "ID Non Valido",
                           "L'ID deve contenere solo lettere, numeri e underscore.");
        idEdit->setFocus();
        return;
    }
    
    accept();
}

std::shared_ptr<Node> StationDialog::getStation() const {
    std::string id = idEdit->text().trimmed().toStdString();
    std::string name = nameEdit->text().trimmed().toStdString();
    NodeType type = static_cast<NodeType>(typeCombo->currentData().toInt());
    double latitude = latitudeSpinBox->value();
    double longitude = longitudeSpinBox->value();
    int capacity = capacitySpinBox->value();
    int platforms = platformsSpinBox->value();
    
    return std::make_shared<Node>(id, name, type, latitude, longitude, 
                                  capacity, platforms);
}

} // namespace fdc
