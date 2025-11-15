#ifndef FDC_SCHEDULE_GRAPH_WIDGET_HPP
#define FDC_SCHEDULE_GRAPH_WIDGET_HPP

#include <QWidget>
#include <QColor>
#include <memory>
#include <vector>
#include "../include/schedule.hpp"
#include "../include/railway_network.hpp"

namespace fdc {

class ScheduleGraphWidget : public QWidget {
    Q_OBJECT

public:
    explicit ScheduleGraphWidget(QWidget *parent = nullptr);
    
    // Visualizza un singolo schedule (retrocompatibilità)
    void setSchedule(std::shared_ptr<TrainSchedule> schedule,
                    std::shared_ptr<RailwayNetwork> network);
    
    // Visualizza schedule multipli con colori diversi
    void setSchedules(const std::vector<std::shared_ptr<TrainSchedule>>& schedules,
                     std::shared_ptr<RailwayNetwork> network,
                     int highlightedIndex = 0);
    
    // Imposta finestra temporale per limitare la visualizzazione (0 = mostra tutto)
    void setTimeWindow(std::time_t windowStart, std::time_t windowEnd);
    
    void clear();

protected:
    void paintEvent(QPaintEvent *event) override;
    
private:
    struct ScheduleInfo {
        std::shared_ptr<TrainSchedule> schedule;
        QColor color;
        bool highlighted;
        QString trainName;
    };
    
    struct Conflict {
        int schedule1Index;
        int schedule2Index;
        double distance;  // Distanza alla quale si verifica il conflitto
        std::time_t time; // Tempo del conflitto
        QString location; // ID nodo/edge del conflitto
    };
    
    void drawTrainPath(QPainter& painter, 
                      const ScheduleInfo& info,
                      const std::vector<double>& cumulativeDistances,
                      double totalDistance,
                      std::time_t firstTime,
                      int totalMinutes,
                      int graphWidth,
                      int graphHeight,
                      int leftMargin,
                      int topMargin);
    
    QColor getColorForIndex(int index, bool highlighted) const;
    
    std::vector<Conflict> detectConflicts(
        const std::vector<ScheduleInfo>& schedules,
        const std::map<std::string, double>& nodeDistanceMap);
    
    void drawConflicts(QPainter& painter,
                      const std::vector<Conflict>& conflicts,
                      double totalDistance,
                      std::time_t firstTime,
                      int totalMinutes,
                      int graphWidth,
                      int graphHeight,
                      int leftMargin,
                      int topMargin);
    
    std::vector<ScheduleInfo> schedules_;
    std::shared_ptr<RailwayNetwork> network_;
    std::vector<Conflict> conflicts_;
    
    // Time window for limiting visualization (0 = show all)
    std::time_t timeWindowStart_ = 0;
    std::time_t timeWindowEnd_ = 0;
};

} // namespace fdc

#endif // FDC_SCHEDULE_GRAPH_WIDGET_HPP
