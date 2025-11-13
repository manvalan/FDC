#include "line_dialog.hpp"
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QFormLayout>
#include <QLabel>
#include <QDialogButtonBox>
#include <QMessageBox>
#include <QGroupBox>
#include <QColorDialog>
#include <QSplitter>

namespace fdc {

LineDialog::LineDialog(std::shared_ptr<RailwayNetwork> net, QWidget *parent)
    : QDialog(parent)
    , network(net)
    , selectedColor(Qt::blue)
    , isEditMode(false)
{
    setupUI();
    setWindowTitle("Aggiungi Linea");
}

LineDialog::LineDialog(std::shared_ptr<RailwayNetwork> net,
                       const Line& line,
                       QWidget *parent)
    : QDialog(parent)
    , network(net)
    , existingLine(line)
    , selectedColor(line.color)
    , isEditMode(true)
{
    setupUI();
    loadLineData();
    setWindowTitle("Modifica Linea");
}

void LineDialog::setupUI() {
    auto *mainLayout = new QVBoxLayout(this);
    
    // Basic info group
    auto *infoGroup = new QGroupBox("Informazioni Linea", this);
    auto *infoLayout = new QFormLayout();
    
    // Name field
    nameEdit = new QLineEdit(this);
    nameEdit->setPlaceholderText("es: Linea Rossa, M1, Direttissima");
    infoLayout->addRow("Nome *:", nameEdit);
    
    // Color button
    colorButton = new QPushButton("Scegli Colore...", this);
    connect(colorButton, &QPushButton::clicked, this, &LineDialog::chooseColor);
    infoLayout->addRow("Colore *:", colorButton);
    
    infoGroup->setLayout(infoLayout);
    mainLayout->addWidget(infoGroup);
    
    // Stations selection group
    auto *stationsGroup = new QGroupBox("Sequenza Stazioni", this);
    auto *stationsLayout = new QHBoxLayout();
    
    // Available stations (left side)
    auto *availableLayout = new QVBoxLayout();
    availableLayout->addWidget(new QLabel("Stazioni Disponibili:"));
    availableStationsList = new QListWidget(this);
    availableLayout->addWidget(availableStationsList);
    
    // Control buttons (center)
    auto *controlLayout = new QVBoxLayout();
    controlLayout->addStretch();
    
    addButton = new QPushButton("→ Aggiungi", this);
    addButton->setToolTip("Aggiungi stazione alla linea");
    connect(addButton, &QPushButton::clicked, this, &LineDialog::addStation);
    controlLayout->addWidget(addButton);
    
    removeButton = new QPushButton("← Rimuovi", this);
    removeButton->setToolTip("Rimuovi stazione dalla linea");
    connect(removeButton, &QPushButton::clicked, this, &LineDialog::removeStation);
    controlLayout->addWidget(removeButton);
    
    controlLayout->addStretch();
    
    // Selected stations (right side)
    auto *selectedLayout = new QVBoxLayout();
    selectedLayout->addWidget(new QLabel("Stazioni nella Linea:"));
    
    auto *listAndOrderLayout = new QHBoxLayout();
    stationsList = new QListWidget(this);
    listAndOrderLayout->addWidget(stationsList);
    
    // Order buttons
    auto *orderLayout = new QVBoxLayout();
    upButton = new QPushButton("↑", this);
    upButton->setToolTip("Sposta su");
    upButton->setMaximumWidth(40);
    connect(upButton, &QPushButton::clicked, this, &LineDialog::moveStationUp);
    orderLayout->addWidget(upButton);
    
    downButton = new QPushButton("↓", this);
    downButton->setToolTip("Sposta giù");
    downButton->setMaximumWidth(40);
    connect(downButton, &QPushButton::clicked, this, &LineDialog::moveStationDown);
    orderLayout->addWidget(downButton);
    
    orderLayout->addStretch();
    listAndOrderLayout->addLayout(orderLayout);
    
    selectedLayout->addLayout(listAndOrderLayout);
    
    // Add all layouts to splitter
    stationsLayout->addLayout(availableLayout, 1);
    stationsLayout->addLayout(controlLayout, 0);
    stationsLayout->addLayout(selectedLayout, 1);
    
    stationsGroup->setLayout(stationsLayout);
    mainLayout->addWidget(stationsGroup);
    
    // Info label
    auto *infoLabel = new QLabel(
        "💡 Seleziona le stazioni nell'ordine in cui il treno le attraverserà.", this);
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
    
    connect(buttonBox, &QDialogButtonBox::accepted, this, &LineDialog::validate);
    connect(buttonBox, &QDialogButtonBox::rejected, this, &QDialog::reject);
    
    mainLayout->addWidget(buttonBox);
    
    setLayout(mainLayout);
    setMinimumSize(700, 500);
    
    // Populate available stations
    updateStationList();
    updateColorButton();
}

void LineDialog::loadLineData() {
    nameEdit->setText(existingLine.name);
    
    // Load stations in line
    for (const QString& stationId : existingLine.stationIds) {
        auto node = network->get_node(stationId.toStdString());
        if (node) {
            QString displayText = QString("%1 - %2")
                .arg(QString::fromStdString(node->get_id()))
                .arg(QString::fromStdString(node->get_name()));
            
            auto *item = new QListWidgetItem(displayText);
            item->setData(Qt::UserRole, QString::fromStdString(node->get_id()));
            stationsList->addItem(item);
        }
    }
    
    updateStationList();
}

void LineDialog::updateStationList() {
    availableStationsList->clear();
    
    // Get IDs of stations already in line
    QSet<QString> usedStations;
    for (int i = 0; i < stationsList->count(); ++i) {
        usedStations.insert(stationsList->item(i)->data(Qt::UserRole).toString());
    }
    
    // Add only unused stations to available list
    for (const auto& node : network->get_all_nodes()) {
        QString stationId = QString::fromStdString(node->get_id());
        if (!usedStations.contains(stationId)) {
            QString displayText = QString("%1 - %2")
                .arg(stationId)
                .arg(QString::fromStdString(node->get_name()));
            
            auto *item = new QListWidgetItem(displayText);
            item->setData(Qt::UserRole, stationId);
            availableStationsList->addItem(item);
        }
    }
}

void LineDialog::updateColorButton() {
    QString styleSheet = QString(
        "QPushButton { "
        "background-color: %1; "
        "color: %2; "
        "border: 2px solid #555; "
        "padding: 5px; "
        "}"
    ).arg(selectedColor.name())
     .arg(selectedColor.lightness() > 128 ? "#000" : "#fff");
    
    colorButton->setStyleSheet(styleSheet);
    colorButton->setText(selectedColor.name().toUpper());
}

void LineDialog::chooseColor() {
    QColor color = QColorDialog::getColor(selectedColor, this, "Scegli Colore Linea");
    if (color.isValid()) {
        selectedColor = color;
        updateColorButton();
    }
}

void LineDialog::addStation() {
    auto *item = availableStationsList->currentItem();
    if (!item) {
        QMessageBox::information(this, "Nessuna Selezione",
                               "Seleziona una stazione da aggiungere.");
        return;
    }
    
    // Create new item for line list
    auto *newItem = new QListWidgetItem(item->text());
    newItem->setData(Qt::UserRole, item->data(Qt::UserRole));
    stationsList->addItem(newItem);
    
    // Update available list
    updateStationList();
}

void LineDialog::removeStation() {
    auto *item = stationsList->currentItem();
    if (!item) {
        QMessageBox::information(this, "Nessuna Selezione",
                               "Seleziona una stazione da rimuovere.");
        return;
    }
    
    delete item;
    updateStationList();
}

void LineDialog::moveStationUp() {
    int currentRow = stationsList->currentRow();
    if (currentRow <= 0) return;
    
    auto *item = stationsList->takeItem(currentRow);
    stationsList->insertItem(currentRow - 1, item);
    stationsList->setCurrentRow(currentRow - 1);
}

void LineDialog::moveStationDown() {
    int currentRow = stationsList->currentRow();
    if (currentRow < 0 || currentRow >= stationsList->count() - 1) return;
    
    auto *item = stationsList->takeItem(currentRow);
    stationsList->insertItem(currentRow + 1, item);
    stationsList->setCurrentRow(currentRow + 1);
}

void LineDialog::validate() {
    // Check required fields
    if (nameEdit->text().trimmed().isEmpty()) {
        QMessageBox::warning(this, "Campo Obbligatorio",
                           "Il campo Nome è obbligatorio.");
        nameEdit->setFocus();
        return;
    }
    
    // Check that at least 2 stations are selected
    if (stationsList->count() < 2) {
        QMessageBox::warning(this, "Stazioni Insufficienti",
                           "Una linea deve avere almeno 2 stazioni.");
        return;
    }
    
    accept();
}

Line LineDialog::getLine() const {
    Line line;
    line.name = nameEdit->text().trimmed();
    line.color = selectedColor;
    
    // Get station IDs in order
    for (int i = 0; i < stationsList->count(); ++i) {
        line.stationIds.append(stationsList->item(i)->data(Qt::UserRole).toString());
    }
    
    return line;
}

} // namespace fdc
