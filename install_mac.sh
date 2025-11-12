#!/bin/bash

###############################################################################
#                                                                             #
#  FDC - Railway Network Management System                                   #
#  Installazione Automatica per macOS                                        #
#                                                                             #
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}  $1"
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}\n"
}

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    print_error "Questo script funziona solo su macOS"
    exit 1
fi

print_header "Installazione FDC - Railway Network Management System"

# Get installation directory
if [ -z "$1" ]; then
    INSTALL_DIR="$HOME/FDC"
    print_info "Nessuna directory specificata, uso predefinita: $INSTALL_DIR"
else
    INSTALL_DIR="$1"
    print_info "Directory di installazione: $INSTALL_DIR"
fi

# Ask for confirmation
echo ""
read -p "Continuare con l'installazione in $INSTALL_DIR? (s/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[SsYy]$ ]]; then
    print_warning "Installazione annullata"
    exit 0
fi

# Create installation directory
print_info "Creazione directory di installazione..."
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"
print_success "Directory creata: $INSTALL_DIR"

# Check for Homebrew
print_header "Verifica Prerequisiti"
if ! command -v brew &> /dev/null; then
    print_warning "Homebrew non trovato. Installazione in corso..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add Homebrew to PATH for Apple Silicon Macs
    if [[ $(uname -m) == 'arm64' ]]; then
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/opt/homebrew/bin/brew shellenv)"
    fi
    
    print_success "Homebrew installato"
else
    print_success "Homebrew già installato"
fi

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    print_warning "Python 3 non trovato. Installazione in corso..."
    brew install python@3.11
    print_success "Python 3 installato"
else
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    print_success "Python 3 già installato (versione $PYTHON_VERSION)"
fi

# Check for git
if ! command -v git &> /dev/null; then
    print_warning "Git non trovato. Installazione in corso..."
    brew install git
    print_success "Git installato"
else
    print_success "Git già installato"
fi

# Clone or copy repository
print_header "Download Codice Sorgente"
if [ -d ".git" ]; then
    print_info "Repository git già presente, aggiornamento..."
    git pull origin main
else
    # Check if we're running from the repo
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
        print_info "Copia files dal repository locale..."
        cp -r "$SCRIPT_DIR"/* "$INSTALL_DIR/"
        print_success "Files copiati"
    else
        print_info "Clone del repository..."
        git clone https://github.com/manvalan/FDC.git .
        print_success "Repository clonato"
    fi
fi

# Create virtual environment
print_header "Configurazione Ambiente Python"
print_info "Creazione ambiente virtuale Python..."
python3 -m venv .venv
print_success "Ambiente virtuale creato"

# Activate virtual environment
source .venv/bin/activate
print_success "Ambiente virtuale attivato"

# Upgrade pip
print_info "Aggiornamento pip..."
pip install --upgrade pip --quiet
print_success "Pip aggiornato"

# Install Python packages
print_info "Installazione dipendenze Python..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --quiet
    print_success "Dipendenze Python installate"
else
    print_warning "File requirements.txt non trovato, installazione pacchetti base..."
    pip install networkx numpy matplotlib tkinter --quiet
    print_success "Pacchetti base installati"
fi

# Create database directory
print_info "Creazione directory database..."
mkdir -p data
print_success "Directory database creata"

# Create desktop shortcut
print_header "Creazione Shortcuts"
APP_NAME="FDC Railway Manager"
DESKTOP_FILE="$HOME/Desktop/$APP_NAME.command"

cat > "$DESKTOP_FILE" << EOF
#!/bin/bash
cd "$INSTALL_DIR"
source .venv/bin/activate
cd examples
python3 run_gui.py
EOF

chmod +x "$DESKTOP_FILE"
print_success "Shortcut creato sul Desktop"

# Create alias in shell profile
SHELL_PROFILE="$HOME/.zshrc"
if [ -f "$HOME/.bash_profile" ]; then
    SHELL_PROFILE="$HOME/.bash_profile"
fi

if ! grep -q "alias fdc=" "$SHELL_PROFILE" 2>/dev/null; then
    echo "" >> "$SHELL_PROFILE"
    echo "# FDC Railway Manager" >> "$SHELL_PROFILE"
    echo "alias fdc='cd $INSTALL_DIR && source .venv/bin/activate && cd examples && python3 run_gui.py'" >> "$SHELL_PROFILE"
    print_success "Alias 'fdc' aggiunto a $SHELL_PROFILE"
else
    print_info "Alias 'fdc' già presente"
fi

# Create launcher script
print_info "Creazione script di avvio..."
cat > "$INSTALL_DIR/start_fdc.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source .venv/bin/activate
cd examples
python3 run_gui.py
EOF

chmod +x "$INSTALL_DIR/start_fdc.sh"
print_success "Script di avvio creato"

# Check for optional dependencies
print_header "Verifica Dipendenze Opzionali"

# Check for MySQL (optional)
if command -v mysql &> /dev/null; then
    print_success "MySQL trovato (opzionale per database avanzato)"
else
    print_info "MySQL non trovato (opzionale)"
    print_info "  Per installarlo: brew install mysql"
fi

# Test installation
print_header "Test Installazione"
print_info "Verifica importazione moduli..."

python3 << 'PYTHON_TEST'
import sys
errors = []

try:
    import networkx
    print("✅ NetworkX OK")
except ImportError:
    errors.append("NetworkX")

try:
    import numpy
    print("✅ NumPy OK")
except ImportError:
    errors.append("NumPy")

try:
    import matplotlib
    print("✅ Matplotlib OK")
except ImportError:
    errors.append("Matplotlib")

try:
    import tkinter
    print("✅ Tkinter OK")
except ImportError:
    errors.append("Tkinter")

if errors:
    print(f"\n❌ Errori nell'importazione: {', '.join(errors)}")
    sys.exit(1)
else:
    print("\n✅ Tutti i moduli importati correttamente")
    sys.exit(0)
PYTHON_TEST

if [ $? -eq 0 ]; then
    print_success "Test completato con successo"
else
    print_error "Problemi rilevati durante il test"
    exit 1
fi

# Print summary
print_header "Installazione Completata!"

cat << EOF

${GREEN}╔════════════════════════════════════════════════════════════╗
║                                                            ║
║  ✅ FDC INSTALLATO CON SUCCESSO!                          ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝${NC}

${BLUE}📁 Directory Installazione:${NC}
   $INSTALL_DIR

${BLUE}🚀 Come Avviare l'Applicazione:${NC}

   ${YELLOW}Metodo 1 - Shortcut Desktop:${NC}
   • Doppio click su "${APP_NAME}.command" sul Desktop

   ${YELLOW}Metodo 2 - Da Terminale con Alias:${NC}
   • Apri un nuovo terminale e digita: ${GREEN}fdc${NC}

   ${YELLOW}Metodo 3 - Script Diretto:${NC}
   • cd $INSTALL_DIR
   • ./start_fdc.sh

   ${YELLOW}Metodo 4 - Manuale:${NC}
   • cd $INSTALL_DIR
   • source .venv/bin/activate
   • cd examples
   • python3 run_gui.py

${BLUE}📚 Documentazione:${NC}
   • README: $INSTALL_DIR/README.md
   • Esempi: $INSTALL_DIR/examples/

${BLUE}🗄️ Database:${NC}
   • SQLite (predefinito): $INSTALL_DIR/data/
   • MySQL (opzionale): Configura dall'applicazione

${BLUE}⚙️ Configurazione:${NC}
   • Files .fdc salvati in: $INSTALL_DIR/data/
   • Esporta JSON da: Menu File → Salva

${BLUE}🆘 Supporto:${NC}
   • Issues: https://github.com/manvalan/FDC/issues
   • Documentazione: Vedi README.md

${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}

${YELLOW}⚡ AVVIO RAPIDO:${NC}
   Digita '${GREEN}fdc${NC}' in un nuovo terminale per iniziare!

${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}

EOF

# Ask if user wants to start now
echo ""
read -p "Vuoi avviare FDC ora? (s/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[SsYy]$ ]]; then
    print_info "Avvio FDC..."
    cd examples
    python3 run_gui.py
fi

print_success "Installazione completata!"
