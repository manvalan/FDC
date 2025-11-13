#ifndef FDC_TRAIN_DIALOG_HPP
#define FDC_TRAIN_DIALOG_HPP

#include <QDialog>
#include <QLineEdit>
#include <QComboBox>
#include <QDoubleSpinBox>
#include <memory>
#include "train.hpp"

namespace fdc {

/**
 * @brief Dialog for adding/editing trains
 */
class TrainDialog : public QDialog {
    Q_OBJECT

public:
    /**
     * @brief Constructor for new train
     */
    explicit TrainDialog(QWidget *parent = nullptr);
    
    /**
     * @brief Constructor for editing existing train
     */
    TrainDialog(std::shared_ptr<Train> train, QWidget *parent = nullptr);
    
    /**
     * @brief Get the train data from dialog
     */
    std::shared_ptr<Train> getTrain() const;

private slots:
    void validate();
    void onTypeChanged(int index);

private:
    void setupUI();
    void loadTrainData();
    void updateDefaultsForType(TrainType type);
    
    // Form widgets
    QLineEdit *idEdit;
    QLineEdit *nameEdit;
    QComboBox *typeCombo;
    QDoubleSpinBox *maxSpeedSpinBox;
    QDoubleSpinBox *accelerationSpinBox;
    QDoubleSpinBox *decelerationSpinBox;
    
    // Data
    std::shared_ptr<Train> existingTrain;
    bool isEditMode;
};

} // namespace fdc

#endif // FDC_TRAIN_DIALOG_HPP
