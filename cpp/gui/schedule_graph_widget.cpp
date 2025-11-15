#include "schedule_graph_widget.hpp"
#include "settings_dialog.hpp"
#include <QPainter>
#include <QPainterPath>
#include <QPen>
#include <QBrush>
#include <QDateTime>
#include <ctime>
#include <map>
#include <algorithm>

namespace fdc {

ScheduleGraphWidget::ScheduleGraphWidget(QWidget *parent)
    : QWidget(parent)
    , network_(nullptr)
{
    setMinimumHeight(200);
    setStyleSheet("background-color: white; border: 1px solid #ccc;");
}

void ScheduleGraphWidget::setSchedule(std::shared_ptr<TrainSchedule> schedule,
                                      std::shared_ptr<RailwayNetwork> network)
{
    schedules_.clear();
    if (schedule) {
        ScheduleInfo info;
        info.schedule = schedule;
        info.color = QColor(0, 100, 200);
        info.highlighted = true;
        info.trainName = QString::fromStdString(schedule->get_train_id());
        schedules_.push_back(info);
    }
    network_ = network;
    update();
}

void ScheduleGraphWidget::setSchedules(const std::vector<std::shared_ptr<TrainSchedule>>& schedules,
                                       std::shared_ptr<RailwayNetwork> network,
                                       int highlightedIndex)
{
    schedules_.clear();
    for (size_t i = 0; i < schedules.size(); ++i) {
        if (!schedules[i]) continue;
        
        ScheduleInfo info;
        info.schedule = schedules[i];
        info.highlighted = (static_cast<int>(i) == highlightedIndex);
        info.color = getColorForIndex(i, info.highlighted);
        info.trainName = QString::fromStdString(schedules[i]->get_train_id());
        schedules_.push_back(info);
    }
    network_ = network;
    update();
}

void ScheduleGraphWidget::setTimeWindow(std::time_t windowStart, std::time_t windowEnd)
{
    timeWindowStart_ = windowStart;
    timeWindowEnd_ = windowEnd;
    update();
}

void ScheduleGraphWidget::clear()
{
    schedules_.clear();
    network_ = nullptr;
    timeWindowStart_ = 0;
    timeWindowEnd_ = 0;
    update();
}

QColor ScheduleGraphWidget::getColorForIndex(int index, bool highlighted) const
{
    if (highlighted) {
        return QColor(0, 100, 200);  // Blu per il treno selezionato
    }
    
    // Palette di colori per gli altri treni
    static const QColor colors[] = {
        QColor(220, 20, 60),   // Crimson
        QColor(34, 139, 34),   // Forest Green
        QColor(255, 140, 0),   // Dark Orange
        QColor(138, 43, 226),  // Blue Violet
        QColor(0, 128, 128),   // Teal
        QColor(199, 21, 133),  // Medium Violet Red
        QColor(210, 105, 30),  // Chocolate
        QColor(25, 25, 112),   // Midnight Blue
        QColor(178, 34, 34),   // Fire Brick
        QColor(70, 130, 180)   // Steel Blue
    };
    
    return colors[index % 10];
}

void ScheduleGraphWidget::paintEvent(QPaintEvent *event)
{
    Q_UNUSED(event);
    
    QPainter painter(this);
    painter.setRenderHint(QPainter::Antialiasing);
    
    // Background
    painter.fillRect(rect(), Qt::white);
    
    if (schedules_.empty() || !network_) {
        // Draw placeholder text
        painter.setPen(QColor(180, 180, 180));
        QFont font = painter.font();
        font.setPointSize(12);
        painter.setFont(font);
        painter.drawText(rect(), Qt::AlignCenter, 
                        tr("Seleziona un orario per\nvisualizzare il grafico"));
        return;
    }
    
    // Usa il primo schedule come riferimento per assi e stazioni
    const auto& refSchedule = schedules_[0].schedule;
    if (!refSchedule || refSchedule->get_stop_count() == 0) {
        return;
    }
    
    const int margin = 40;
    const int topMargin = 30;
    const int bottomMargin = 50;
    const int leftMargin = 80;
    const int rightMargin = 40;
    
    int graphWidth = width() - leftMargin - rightMargin;
    int graphHeight = height() - topMargin - bottomMargin;
    
    if (graphWidth <= 0 || graphHeight <= 0) return;
    
    // Get stops from reference schedule and calculate time/distance range
    const auto& refStops = refSchedule->get_stops();
    size_t numStops = refStops.size();
    
    if (numStops < 2) return;
    
    // Calculate total distance
    double totalDistance = 0.0;
    std::vector<double> cumulativeDistances;
    cumulativeDistances.push_back(0.0);
    
    for (size_t i = 1; i < numStops; ++i) {
        double dist = network_->calculate_distance(
            refStops[i-1].get_node_id(),
            refStops[i].get_node_id()
        );
        totalDistance += dist;
        cumulativeDistances.push_back(totalDistance);
    }
    
    // Get time range - use time window if set, otherwise use all schedules
    std::time_t earliestTime, latestTime;
    
    if (timeWindowStart_ != 0 && timeWindowEnd_ != 0) {
        // Use specified time window
        earliestTime = timeWindowStart_;
        latestTime = timeWindowEnd_;
    } else {
        // Calculate from ALL schedules to ensure proper scaling
        earliestTime = std::chrono::system_clock::to_time_t(refStops[0].get_departure());
        latestTime = std::chrono::system_clock::to_time_t(refStops[numStops-1].get_arrival());
        
        for (const auto& info : schedules_) {
            if (!info.schedule || info.schedule->get_stop_count() < 2) continue;
            const auto& stops = info.schedule->get_stops();
            
            auto firstT = std::chrono::system_clock::to_time_t(stops[0].get_departure());
            auto lastT = std::chrono::system_clock::to_time_t(stops[stops.size()-1].get_arrival());
            
            if (firstT < earliestTime) earliestTime = firstT;
            if (lastT > latestTime) latestTime = lastT;
        }
    }
    
    int totalMinutes = (latestTime - earliestTime) / 60;
    if (totalMinutes <= 0) totalMinutes = 1;
    
    // Draw axes
    painter.setPen(QPen(Qt::black, 2));
    painter.drawLine(leftMargin, topMargin, leftMargin, height() - bottomMargin);
    painter.drawLine(leftMargin, height() - bottomMargin, 
                    width() - rightMargin, height() - bottomMargin);
    
    // Draw title
    QFont titleFont = painter.font();
    titleFont.setPointSize(10);
    titleFont.setBold(true);
    painter.setFont(titleFont);
    painter.setPen(Qt::black);
    painter.drawText(QRect(0, 5, width(), 20), Qt::AlignCenter,
                    tr("Diagramma Spazio-Tempo"));
    
    // Draw station labels and horizontal lines
    QFont labelFont = painter.font();
    labelFont.setPointSize(8);
    painter.setFont(labelFont);
    
    for (size_t i = 0; i < numStops; ++i) {
        int y = topMargin + (graphHeight * cumulativeDistances[i] / totalDistance);
        
        // Horizontal grid line
        painter.setPen(QPen(QColor(200, 200, 200), 1, Qt::DashLine));
        painter.drawLine(leftMargin, y, width() - rightMargin, y);
        
        // Station name
        auto node = network_->get_node(refStops[i].get_node_id());
        QString stationName = node ? QString::fromStdString(node->get_name()) : "?";
        
        painter.setPen(Qt::black);
        painter.drawText(QRect(5, y - 10, leftMargin - 10, 20), 
                        Qt::AlignRight | Qt::AlignVCenter, stationName);
        
        // Distance marker
        painter.drawText(QRect(width() - rightMargin + 5, y - 10, rightMargin - 10, 20),
                        Qt::AlignLeft | Qt::AlignVCenter,
                        QString("%1 km").arg(cumulativeDistances[i], 0, 'f', 1));
    }
    
    // Draw time labels on X axis
    QDateTime firstDT = QDateTime::fromSecsSinceEpoch(earliestTime);
    for (int min = 0; min <= totalMinutes; min += (totalMinutes > 120 ? 30 : 15)) {
        int x = leftMargin + (graphWidth * min / totalMinutes);
        
        // Vertical grid line
        painter.setPen(QPen(QColor(200, 200, 200), 1, Qt::DashLine));
        painter.drawLine(x, topMargin, x, height() - bottomMargin);
        
        // Time label
        QDateTime dt = firstDT.addSecs(min * 60);
        painter.setPen(Qt::black);
        painter.drawText(QRect(x - 30, height() - bottomMargin + 5, 60, 20),
                        Qt::AlignCenter, dt.toString("HH:mm"));
    }
    
    // Set clipping region to graph area to prevent train paths from extending outside
    painter.save();
    QRect clipRect(leftMargin, topMargin, graphWidth, graphHeight);
    painter.setClipRect(clipRect);
    
    // Draw all train paths (non-highlighted first, then highlighted on top)
    for (int pass = 0; pass < 2; ++pass) {
        bool drawHighlighted = (pass == 1);
        
        for (const auto& info : schedules_) {
            if (info.highlighted != drawHighlighted) continue;
            
            drawTrainPath(painter, info, cumulativeDistances, totalDistance,
                         earliestTime, totalMinutes, graphWidth, graphHeight,
                         leftMargin, topMargin);
        }
    }
    
    // Restore painter state (remove clipping)
    painter.restore();
    
    // Detect and draw conflicts if multiple schedules
    if (schedules_.size() > 1) {
        // Build node distance map per rilevamento conflitti
        std::map<std::string, double> nodeDistanceMap;
        for (size_t i = 0; i < refStops.size() && i < cumulativeDistances.size(); ++i) {
            nodeDistanceMap[refStops[i].get_node_id()] = cumulativeDistances[i];
        }
        
        // Rileva conflitti
        auto conflicts = detectConflicts(schedules_, nodeDistanceMap);
        
        // Disegna conflitti (with clipping)
        if (!conflicts.empty()) {
            painter.save();
            painter.setClipRect(QRect(leftMargin, topMargin, graphWidth, graphHeight));
            
            drawConflicts(painter, conflicts, totalDistance, earliestTime, totalMinutes,
                         graphWidth, graphHeight, leftMargin, topMargin);
            
            painter.restore();
        }
    }
    
    // Draw legend if multiple schedules
    if (schedules_.size() > 1) {
        int legendX = width() - rightMargin - 150;
        int legendY = topMargin + 10;
        int lineHeight = 20;
        
        painter.setPen(QPen(Qt::black, 1));
        painter.setBrush(QBrush(QColor(255, 255, 255, 230)));
        painter.drawRect(legendX - 5, legendY - 5, 155, schedules_.size() * lineHeight + 10);
        
        QFont legendFont = painter.font();
        legendFont.setPointSize(7);
        painter.setFont(legendFont);
        
        for (size_t i = 0; i < schedules_.size(); ++i) {
            const auto& info = schedules_[i];
            int y = legendY + i * lineHeight;
            
            // Draw color line
            painter.setPen(QPen(info.color, info.highlighted ? 3 : 2));
            painter.drawLine(legendX, y + 8, legendX + 20, y + 8);
            
            // Draw train name
            painter.setPen(Qt::black);
            QString label = info.trainName;
            if (info.highlighted) label += " ★";
            painter.drawText(QRect(legendX + 25, y, 120, lineHeight),
                           Qt::AlignLeft | Qt::AlignVCenter, label);
        }
    }
    
    // Draw X axis label
    painter.setPen(Qt::black);
    painter.drawText(QRect(0, height() - 25, width(), 20),
                    Qt::AlignCenter, tr("Tempo (HH:mm)"));
    
    // Draw Y axis label (rotated)
    painter.save();
    painter.translate(15, height() / 2);
    painter.rotate(-90);
    painter.drawText(QRect(-50, -10, 100, 20), Qt::AlignCenter, tr("Distanza (km)"));
    painter.restore();
}

void ScheduleGraphWidget::drawTrainPath(QPainter& painter,
                                        const ScheduleInfo& info,
                                        const std::vector<double>& cumulativeDistances,
                                        double totalDistance,
                                        std::time_t firstTime,
                                        int totalMinutes,
                                        int graphWidth,
                                        int graphHeight,
                                        int leftMargin,
                                        int topMargin)
{
    if (!info.schedule || info.schedule->get_stop_count() == 0) return;
    
    const auto& stops = info.schedule->get_stops();
    QPainterPath trainPath;
    bool firstPoint = true;
    
    // Build a map of node_id to distance for quick lookup
    std::map<std::string, double> nodeDistanceMap;
    const auto& refSchedule = schedules_[0].schedule;
    const auto& refStops = refSchedule->get_stops();
    for (size_t i = 0; i < refStops.size() && i < cumulativeDistances.size(); ++i) {
        nodeDistanceMap[refStops[i].get_node_id()] = cumulativeDistances[i];
    }
    
    for (size_t i = 0; i < stops.size(); ++i) {
        const auto& stop = stops[i];
        
        // Find distance for this stop's station
        auto it = nodeDistanceMap.find(stop.get_node_id());
        if (it == nodeDistanceMap.end()) continue;  // Station not in reference path
        
        double distance = it->second;
        
        // Calculate arrival position
        auto stopTime = (i == 0) ? stop.get_departure() : stop.get_arrival();
        auto stopTimeT = std::chrono::system_clock::to_time_t(stopTime);
        int minutes = (stopTimeT - firstTime) / 60;
        
        int x = leftMargin + (graphWidth * minutes / totalMinutes);
        int y = topMargin + (graphHeight * distance / totalDistance);
        
        if (firstPoint) {
            trainPath.moveTo(x, y);
            firstPoint = false;
        } else {
            trainPath.lineTo(x, y);
        }
        
        // Draw departure for non-last stops (dwell time)
        if (i < stops.size() - 1) {
            auto depTime = std::chrono::system_clock::to_time_t(stop.get_departure());
            int depMinutes = (depTime - firstTime) / 60;
            int depX = leftMargin + (graphWidth * depMinutes / totalMinutes);
            
            // Horizontal line for dwell time
            if (depX != x) {
                trainPath.lineTo(depX, y);
            }
        }
        
        // Draw stop point
        int pointSize = info.highlighted ? 5 : 3;
        painter.setPen(QPen(info.color, 2));
        painter.setBrush(QBrush(Qt::white));
        painter.drawEllipse(QPointF(x, y), pointSize, pointSize);
    }
    
    // Draw train path line
    int lineWidth = info.highlighted ? 3 : 2;
    painter.setPen(QPen(info.color, lineWidth));
    painter.setBrush(Qt::NoBrush);
    painter.drawPath(trainPath);
}

std::vector<ScheduleGraphWidget::Conflict> ScheduleGraphWidget::detectConflicts(
    const std::vector<ScheduleInfo>& schedules,
    const std::map<std::string, double>& nodeDistanceMap)
{
    std::vector<Conflict> conflicts;
    
    // Compara ogni coppia di treni
    for (size_t i = 0; i < schedules.size(); ++i) {
        for (size_t j = i + 1; j < schedules.size(); ++j) {
            const auto& sched1 = schedules[i].schedule;
            const auto& sched2 = schedules[j].schedule;
            
            const auto& stops1 = sched1->get_stops();
            const auto& stops2 = sched2->get_stops();
            
            if (stops1.empty() || stops2.empty()) continue;
            
            // Analizza ogni segmento (edge) percorso dai treni
            for (size_t s1 = 1; s1 < stops1.size(); ++s1) {
                const auto& prevStop1 = stops1[s1-1];
                const auto& currStop1 = stops1[s1];
                
                // Tempo e distanza del treno 1 su questo segmento
                auto depTime1 = std::chrono::system_clock::to_time_t(prevStop1.get_departure());
                auto arrTime1 = std::chrono::system_clock::to_time_t(currStop1.get_arrival());
                
                auto it1Prev = nodeDistanceMap.find(prevStop1.get_node_id());
                auto it1Curr = nodeDistanceMap.find(currStop1.get_node_id());
                
                if (it1Prev == nodeDistanceMap.end() || it1Curr == nodeDistanceMap.end()) continue;
                
                double dist1Start = it1Prev->second;
                double dist1End = it1Curr->second;
                bool direction1Forward = (dist1End > dist1Start);
                
                // Ottieni edge per determinare tipo binario
                std::string edgeKey1 = prevStop1.get_node_id() + "-" + currStop1.get_node_id();
                auto edge1 = network_->get_edge(prevStop1.get_node_id(), currStop1.get_node_id());
                bool isDoubleTrack = edge1 && (edge1->get_track_type() == TrackType::DOUBLE);
                
                // Confronta con tutti i segmenti del treno 2
                for (size_t s2 = 1; s2 < stops2.size(); ++s2) {
                    const auto& prevStop2 = stops2[s2-1];
                    const auto& currStop2 = stops2[s2];
                    
                    auto depTime2 = std::chrono::system_clock::to_time_t(prevStop2.get_departure());
                    auto arrTime2 = std::chrono::system_clock::to_time_t(currStop2.get_arrival());
                    
                    auto it2Prev = nodeDistanceMap.find(prevStop2.get_node_id());
                    auto it2Curr = nodeDistanceMap.find(currStop2.get_node_id());
                    
                    if (it2Prev == nodeDistanceMap.end() || it2Curr == nodeDistanceMap.end()) continue;
                    
                    double dist2Start = it2Prev->second;
                    double dist2End = it2Curr->second;
                    bool direction2Forward = (dist2End > dist2Start);
                    
                    // Verifica sovrapposizione temporale
                    bool timeOverlap = !(arrTime1 <= depTime2 || arrTime2 <= depTime1);
                    if (!timeOverlap) continue;
                    
                    // Verifica se attraversano stesso edge (stessi nodi)
                    std::string edgeKey2 = prevStop2.get_node_id() + "-" + currStop2.get_node_id();
                    bool sameEdge = (prevStop1.get_node_id() == prevStop2.get_node_id() && 
                                    currStop1.get_node_id() == currStop2.get_node_id()) ||
                                   (prevStop1.get_node_id() == currStop2.get_node_id() && 
                                    currStop1.get_node_id() == prevStop2.get_node_id());
                    
                    if (sameEdge) {
                        // BINARIO SINGOLO: un solo treno per tratta
                        if (!isDoubleTrack) {
                            // CONFLITTO: binario singolo non può avere 2 treni contemporaneamente
                            Conflict conflict;
                            conflict.schedule1Index = i;
                            conflict.schedule2Index = j;
                            conflict.distance = (dist1Start + dist1End) / 2.0;
                            conflict.time = std::max(depTime1, depTime2);
                            conflict.location = QString::fromStdString(edgeKey1);
                            conflicts.push_back(conflict);
                            continue;
                        }
                        
                        // BINARIO DOPPIO: verifica direzione e separazione
                        bool oppositeDirection = (direction1Forward != direction2Forward);
                        
                        if (oppositeDirection) {
                            // Direzioni opposte su doppio binario = OK (non c'è conflitto)
                            continue;
                        } else {
                            // Stesso senso: verifica separazione 5 km
                            // Calcola posizione approssimativa di entrambi i treni nel tempo di overlap
                            double segmentLength1 = std::abs(dist1End - dist1Start);
                            double segmentLength2 = std::abs(dist2End - dist2Start);
                            
                            // Tempo di percorrenza
                            double duration1 = arrTime1 - depTime1;  // secondi
                            double duration2 = arrTime2 - depTime2;
                            
                            if (duration1 <= 0 || duration2 <= 0) continue;
                            
                            // Velocità media (km/h -> km/s)
                            double speed1 = segmentLength1 / duration1 * 3600.0;  // km/h
                            double speed2 = segmentLength2 / duration2 * 3600.0;
                            
                            // Trova il momento di massima vicinanza
                            // Momento centrale dell'overlap temporale
                            std::time_t overlapStart = std::max(depTime1, depTime2);
                            std::time_t overlapEnd = std::min(arrTime1, arrTime2);
                            std::time_t checkTime = (overlapStart + overlapEnd) / 2;
                            
                            // Posizione treno 1 al checkTime
                            double elapsed1 = checkTime - depTime1;
                            double progress1 = elapsed1 / duration1;  // 0.0 -> 1.0
                            double pos1 = dist1Start + (dist1End - dist1Start) * progress1;
                            
                            // Posizione treno 2 al checkTime
                            double elapsed2 = checkTime - depTime2;
                            double progress2 = elapsed2 / duration2;
                            double pos2 = dist2Start + (dist2End - dist2Start) * progress2;
                            
                            // Distanza tra i due treni
                            double separation = std::abs(pos1 - pos2);
                            
                            // CONFLITTO se separazione < 5 km
                            if (separation < 5.0) {
                                Conflict conflict;
                                conflict.schedule1Index = i;
                                conflict.schedule2Index = j;
                                conflict.distance = (pos1 + pos2) / 2.0;
                                conflict.time = checkTime;
                                conflict.location = QString::fromStdString(edgeKey1);
                                conflicts.push_back(conflict);
                            }
                        }
                    }
                }
            }
        }
    }
    
    return conflicts;
}

void ScheduleGraphWidget::drawConflicts(
    QPainter& painter,
    const std::vector<Conflict>& conflicts,
    double totalDistance,
    std::time_t firstTime,
    int totalMinutes,
    int graphWidth,
    int graphHeight,
    int leftMargin,
    int topMargin)
{
    if (conflicts.empty()) return;
    
    // Disegna icone di warning per i conflitti
    painter.setPen(QPen(QColor(255, 0, 0), 2));
    painter.setBrush(QBrush(QColor(255, 0, 0, 100)));
    
    for (const auto& conflict : conflicts) {
        int minutes = (conflict.time - firstTime) / 60;
        int x = leftMargin + (graphWidth * minutes / totalMinutes);
        int y = topMargin + (graphHeight * conflict.distance / totalDistance);
        
        // Disegna triangolo di warning
        QPolygonF triangle;
        triangle << QPointF(x, y - 8)
                << QPointF(x - 7, y + 4)
                << QPointF(x + 7, y + 4);
        painter.drawPolygon(triangle);
        
        // Disegna "!" al centro
        painter.setPen(QPen(Qt::white, 2));
        QFont font = painter.font();
        font.setBold(true);
        font.setPointSize(10);
        painter.setFont(font);
        painter.drawText(QRectF(x-5, y-6, 10, 12), Qt::AlignCenter, "!");
    }
}

} // namespace fdc
