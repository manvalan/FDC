#ifndef FDC_CONNECTION_DIALOG_HPP
#define FDC_CONNECTION_DIALOG_HPP

#include <QDialog>
#include <QComboBox>
#include <QDoubleSpinBox>
#include <QCheckBox>
#include <QLabel>
#include <QSpinBox>
#include <memory>
#include "edge.hpp"
#include "railway_network.hpp"

namespace fdc {

/**
 * @brief Dialog for adding/editing railway connections
 */
class ConnectionDialog : public QDialog {
    Q_OBJECT

public:
    /**
     * @brief Constructor for new connection
     */
    ConnectionDialog(std::shared_ptr<RailwayNetwork> network, 
                    QWidget *parent = nullptr);
    
    /**
     * @brief Constructor for editing existing connection
     */
    ConnectionDialog(std::shared_ptr<RailwayNetwork> network,
                    std::shared_ptr<Edge> connection,
                    QWidget *parent = nullptr);
    
    /**
     * @brief Get the connection data from dialog
     */
    std::shared_ptr<Edge> getConnection() const;

private slots:
    void validate();
    void updateEstimatedTime();

private:
    void setupUI();
    void loadConnectionData();
    void populateStationCombos();
    
    // Form widgets
    QComboBox *fromStationCombo;
    QComboBox *toStationCombo;
    QDoubleSpinBox *distanceSpinBox;
    QComboBox *trackTypeCombo;
    QDoubleSpinBox *maxSpeedSpinBox;
    QSpinBox *capacitySpinBox;
    QCheckBox *bidirectionalCheck;
    QLabel *estimatedTimeLabel;
    
    // Data
    std::shared_ptr<RailwayNetwork> network;
    std::shared_ptr<Edge> existingConnection;
    bool isEditMode;
};

} // namespace fdc

#endif // FDC_CONNECTION_DIALOG_HPP
