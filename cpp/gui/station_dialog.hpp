#ifndef FDC_STATION_DIALOG_HPP
#define FDC_STATION_DIALOG_HPP

#include <QDialog>
#include <QLineEdit>
#include <QSpinBox>
#include <QDoubleSpinBox>
#include <QComboBox>
#include <memory>
#include "node.hpp"

namespace fdc {

/**
 * @brief Dialog for adding/editing railway stations
 */
class StationDialog : public QDialog {
    Q_OBJECT

public:
    /**
     * @brief Constructor for new station
     */
    explicit StationDialog(QWidget *parent = nullptr);
    
    /**
     * @brief Constructor for editing existing station
     */
    StationDialog(std::shared_ptr<Node> station, QWidget *parent = nullptr);
    
    /**
     * @brief Get the station data from dialog
     */
    std::shared_ptr<Node> getStation() const;

private slots:
    void validate();

private:
    void setupUI();
    void loadStationData();
    
    // Form widgets
    QLineEdit *idEdit;
    QLineEdit *nameEdit;
    QComboBox *typeCombo;
    QDoubleSpinBox *latitudeSpinBox;
    QDoubleSpinBox *longitudeSpinBox;
    QSpinBox *capacitySpinBox;
    QSpinBox *platformsSpinBox;
    
    // Data
    std::shared_ptr<Node> existingStation;
    bool isEditMode;
};

} // namespace fdc

#endif // FDC_STATION_DIALOG_HPP
