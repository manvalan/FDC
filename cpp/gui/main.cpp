#include <QApplication>
#include <QStyle>
#include <QStyleFactory>
#include "main_window.hpp"

int main(int argc, char *argv[]) {
    // Qt6 gestisce automaticamente High DPI su macOS Retina displays
    // Non servono più AA_EnableHighDpiScaling e AA_UseHighDpiPixmaps
    
    QApplication app(argc, argv);
    
    // Informazioni applicazione per QSettings
    app.setOrganizationName("FDC Project");
    app.setOrganizationDomain("fdc-railway.org");
    app.setApplicationName("FDC Railway Manager");
    app.setApplicationVersion("0.2.0");
    
    // Su macOS usa lo stile nativo
    #ifdef Q_OS_MAC
    // macOS usa automaticamente lo stile nativo (Aqua/Dark mode)
    // Non serve impostare nulla, Qt6 lo gestisce automaticamente
    #endif
    
    // Crea e mostra la finestra principale
    fdc::MainWindow mainWindow;
    mainWindow.show();
    
    return app.exec();
}
