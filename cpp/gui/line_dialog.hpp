#ifndef FDC_LINE_DIALOG_HPP
#define FDC_LINE_DIALOG_HPP

#include <QDialog>
#include <QLineEdit>
#include <QPushButton>
#include <QListWidget>
#include <QColor>
#include <QStringList>
#include <memory>
#include "railway_network.hpp"

namespace fdc {

/**
 * @brief Simple structure to represent a railway line
 */
struct Line {
    QString name;
    QColor color;
    QStringList stationIds;
    
    Line() : color(Qt::blue) {}
    Line(const QString& n, const QColor& c, const QStringList& stations)
        : name(n), color(c), stationIds(stations) {}
};

/**
 * @brief Dialog for adding/editing railway lines
 */
class LineDialog : public QDialog {
    Q_OBJECT

public:
    /**
     * @brief Constructor for new line
     */
    LineDialog(std::shared_ptr<RailwayNetwork> network, QWidget *parent = nullptr);
    
    /**
     * @brief Constructor for editing existing line
     */
    LineDialog(std::shared_ptr<RailwayNetwork> network,
               const Line& line,
               QWidget *parent = nullptr);
    
    /**
     * @brief Get the line data from dialog
     */
    Line getLine() const;

private slots:
    void validate();
    void chooseColor();
    void addStation();
    void removeStation();
    void moveStationUp();
    void moveStationDown();

private:
    void setupUI();
    void loadLineData();
    void updateColorButton();
    void updateStationList();
    
    // Form widgets
    QLineEdit *nameEdit;
    QPushButton *colorButton;
    QListWidget *stationsList;
    QListWidget *availableStationsList;
    QPushButton *addButton;
    QPushButton *removeButton;
    QPushButton *upButton;
    QPushButton *downButton;
    
    // Data
    std::shared_ptr<RailwayNetwork> network;
    Line existingLine;
    QColor selectedColor;
    bool isEditMode;
};

} // namespace fdc

#endif // FDC_LINE_DIALOG_HPP
