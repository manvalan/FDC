#include "train_dialog.hpp"
#include <QVBoxLayout>
#include <QFormLayout>
#include <QLabel>
#include <QDialogButtonBox>
#include <QMessageBox>
#include <QGroupBox>
#include <QRegularExpression>

namespace fdc {

TrainDialog::TrainDialog(QWidget *parent)
    : QDialog(parent)
    , existingTrain(nullptr)
    , isEditMode(false)
{
    setupUI();
    setWindowTitle("Aggiungi Treno");
}

TrainDialog::TrainDialog(std::shared_ptr<Train> train, QWidget *parent)
    : QDialog(parent)
    , existingTrain(train)
    , isEditMode(true)
{
    setupUI();
    loadTrainData();
    setWindowTitle("Modifica Treno");
    idEdit->setEnabled(false); // ID cannot be changed
}

void TrainDialog::setupUI() {
    auto *mainLayout = new QVBoxLayout(this);
    
    // Form group
    auto *formGroup = new QGroupBox("Dati Treno", this);
    auto *formLayout = new QFormLayout();
    
    // ID field
    idEdit = new QLineEdit(this);
    idEdit->setPlaceholderText("es: FR9612, IC456, REG123");
    formLayout->addRow("ID *:", idEdit);
    
    // Name field
    nameEdit = new QLineEdit(this);
    nameEdit->setPlaceholderText("es: Frecciarossa 1000, InterCity Notte");
    formLayout->addRow("Nome *:", nameEdit);
    
    // Type combo
    typeCombo = new QComboBox(this);
    typeCombo->addItem("🚄 Alta Velocità", static_cast<int>(TrainType::HIGH_SPEED));
    typeCombo->addItem("🚅 InterCity", static_cast<int>(TrainType::INTERCITY));
    typeCombo->addItem("🚃 Regionale", static_cast<int>(TrainType::REGIONAL));
    typeCombo->addItem("🚂 Merci", static_cast<int>(TrainType::FREIGHT));
    formLayout->addRow("Tipo *:", typeCombo);
    
    // Performance group
    auto *perfGroup = new QGroupBox("Prestazioni", this);
    auto *perfLayout = new QFormLayout();
    
    maxSpeedSpinBox = new QDoubleSpinBox(this);
    maxSpeedSpinBox->setRange(40.0, 400.0);
    maxSpeedSpinBox->setDecimals(1);
    maxSpeedSpinBox->setSingleStep(10.0);
    maxSpeedSpinBox->setValue(160.0);
    maxSpeedSpinBox->setSuffix(" km/h");
    perfLayout->addRow("Velocità Max *:", maxSpeedSpinBox);
    
    accelerationSpinBox = new QDoubleSpinBox(this);
    accelerationSpinBox->setRange(0.1, 2.0);
    accelerationSpinBox->setDecimals(2);
    accelerationSpinBox->setSingleStep(0.1);
    accelerationSpinBox->setValue(0.5);
    accelerationSpinBox->setSuffix(" m/s²");
    perfLayout->addRow("Accelerazione *:", accelerationSpinBox);
    
    decelerationSpinBox = new QDoubleSpinBox(this);
    decelerationSpinBox->setRange(0.1, 2.0);
    decelerationSpinBox->setDecimals(2);
    decelerationSpinBox->setSingleStep(0.1);
    decelerationSpinBox->setValue(0.7);
    decelerationSpinBox->setSuffix(" m/s²");
    perfLayout->addRow("Decelerazione *:", decelerationSpinBox);
    
    perfGroup->setLayout(perfLayout);
    
    formGroup->setLayout(formLayout);
    
    // Add groups to main layout
    mainLayout->addWidget(formGroup);
    mainLayout->addWidget(perfGroup);
    
    // Info label
    auto *infoLabel = new QLabel(
        "💡 Suggerimento: Seleziona il tipo di treno per applicare "
        "valori predefiniti realistici.", this);
    infoLabel->setWordWrap(true);
    infoLabel->setStyleSheet("color: #555; font-style: italic; padding: 5px;");
    mainLayout->addWidget(infoLabel);
    
    // Required fields note
    auto *noteLabel = new QLabel("* Campi obbligatori", this);
    noteLabel->setStyleSheet("color: gray; font-style: italic;");
    mainLayout->addWidget(noteLabel);
    
    // Button box
    auto *buttonBox = new QDialogButtonBox(
        QDialogButtonBox::Ok | QDialogButtonBox::Cancel,
        this);
    
    connect(buttonBox, &QDialogButtonBox::accepted, this, &TrainDialog::validate);
    connect(buttonBox, &QDialogButtonBox::rejected, this, &QDialog::reject);
    
    // Connect type change to update defaults
    connect(typeCombo, QOverload<int>::of(&QComboBox::currentIndexChanged),
            this, &TrainDialog::onTypeChanged);
    
    mainLayout->addWidget(buttonBox);
    
    setLayout(mainLayout);
    setMinimumWidth(400);
}

void TrainDialog::loadTrainData() {
    if (!existingTrain) return;
    
    idEdit->setText(QString::fromStdString(existingTrain->get_id()));
    nameEdit->setText(QString::fromStdString(existingTrain->get_name()));
    
    // Set type combo
    int typeIndex = typeCombo->findData(static_cast<int>(existingTrain->get_type()));
    if (typeIndex >= 0) {
        typeCombo->setCurrentIndex(typeIndex);
    }
    
    maxSpeedSpinBox->setValue(existingTrain->get_max_speed());
    accelerationSpinBox->setValue(existingTrain->get_acceleration());
    decelerationSpinBox->setValue(existingTrain->get_deceleration());
}

void TrainDialog::onTypeChanged(int index) {
    if (isEditMode) return; // Don't override when editing
    
    TrainType type = static_cast<TrainType>(typeCombo->currentData().toInt());
    updateDefaultsForType(type);
}

void TrainDialog::updateDefaultsForType(TrainType type) {
    // Set realistic defaults based on train type
    switch (type) {
        case TrainType::HIGH_SPEED:
            maxSpeedSpinBox->setValue(300.0);
            accelerationSpinBox->setValue(0.6);
            decelerationSpinBox->setValue(0.8);
            break;
        case TrainType::INTERCITY:
            maxSpeedSpinBox->setValue(200.0);
            accelerationSpinBox->setValue(0.5);
            decelerationSpinBox->setValue(0.7);
            break;
        case TrainType::REGIONAL:
            maxSpeedSpinBox->setValue(140.0);
            accelerationSpinBox->setValue(0.4);
            decelerationSpinBox->setValue(0.6);
            break;
        case TrainType::FREIGHT:
            maxSpeedSpinBox->setValue(100.0);
            accelerationSpinBox->setValue(0.2);
            decelerationSpinBox->setValue(0.4);
            break;
    }
}

void TrainDialog::validate() {
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

std::shared_ptr<Train> TrainDialog::getTrain() const {
    std::string id = idEdit->text().trimmed().toStdString();
    std::string name = nameEdit->text().trimmed().toStdString();
    TrainType type = static_cast<TrainType>(typeCombo->currentData().toInt());
    double maxSpeed = maxSpeedSpinBox->value();
    double acceleration = accelerationSpinBox->value();
    double deceleration = decelerationSpinBox->value();
    
    return std::make_shared<Train>(id, name, type, maxSpeed, acceleration, deceleration);
}

} // namespace fdc
