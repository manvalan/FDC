#ifndef SCHEDULE_DIALOG_HPP
#define SCHEDULE_DIALOG_HPP

#include <QDialog>
#include <QComboBox>
#include <QTableWidget>
#include <QDateTimeEdit>
#include <QPushButton>
#include <QLabel>
#include <memory>
#include <vector>
#include "../include/schedule.hpp"
#include "../include/railway_network.hpp"
#include "../include/train.hpp"

using namespace fdc;

class ScheduleDialog : public QDialog {
    Q_OBJECT
    Q_DISABLE_COPY(ScheduleDialog)

public:
    // Constructor for new schedule
    explicit ScheduleDialog(
        std::shared_ptr<RailwayNetwork> network,
        const std::vector<std::shared_ptr<Train>>& trains,
        QWidget* parent = nullptr
    );
    
    // Constructor for editing existing schedule
    ScheduleDialog(
        std::shared_ptr<RailwayNetwork> network,
        const std::vector<std::shared_ptr<Train>>& trains,
        std::shared_ptr<TrainSchedule> schedule,
        QWidget* parent = nullptr
    );

    std::shared_ptr<TrainSchedule> getSchedule() const;
    bool validate();

private slots:
    void onTrainChanged(int index);
    void onAddStop();
    void onRemoveStop();
    void onMoveStopUp();
    void onMoveStopDown();
    void onCalculateTimes();
    void onAutoAssignPlatforms();
    void onStopSelectionChanged();

private:
    void setupUI();
    void populateTrainCombo();
    void updateStopsTable();
    void updateButtonStates();
    std::shared_ptr<Train> getSelectedTrain() const;
    
    // Data
    std::shared_ptr<RailwayNetwork> network;
    std::vector<std::shared_ptr<Train>> trains;
    std::shared_ptr<TrainSchedule> existingSchedule;
    std::vector<ScheduleStop> stops;
    
    // UI Components
    QComboBox* trainCombo;
    QLabel* trainInfoLabel;
    QDateTimeEdit* startTimeEdit;
    QTableWidget* stopsTable;
    QPushButton* addStopButton;
    QPushButton* removeStopButton;
    QPushButton* moveUpButton;
    QPushButton* moveDownButton;
    QPushButton* calculateTimesButton;
    QPushButton* autoAssignButton;
    QLabel* summaryLabel;
};

#endif // SCHEDULE_DIALOG_HPP
