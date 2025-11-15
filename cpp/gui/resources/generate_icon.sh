#!/bin/bash

# Script per creare icona .icns da SVG su macOS
# Usa solo tool built-in (qlmanage, sips, iconutil)

SVG_FILE="icon.svg"
ICONSET_DIR="AppIcon.iconset"
ICNS_FILE="AppIcon.icns"

echo "🎨 FDC Icon Generator (macOS)"
echo "============================="
echo ""

# Verifica che il file SVG esista
if [ ! -f "$SVG_FILE" ]; then
    echo "❌ File $SVG_FILE non trovato!"
    exit 1
fi

# Crea directory iconset
mkdir -p "$ICONSET_DIR"
echo "📁 Creata directory $ICONSET_DIR"

# Prima converti SVG in PNG grande con qlmanage
echo "🔄 Conversione SVG → PNG..."
qlmanage -t -s 1024 -o . "$SVG_FILE" >/dev/null 2>&1

# Il file generato avrà estensione .png
TEMP_PNG="${SVG_FILE}.png"

if [ ! -f "$TEMP_PNG" ]; then
    echo "❌ Conversione fallita. Prova con:"
    echo "   brew install librsvg"
    echo "   rsvg-convert -w 1024 -h 1024 $SVG_FILE -o temp.png"
    exit 1
fi

# Ridimensiona per tutte le dimensioni richieste da macOS
declare -a sizes=(
    "16:icon_16x16.png"
    "32:icon_16x16@2x.png"
    "32:icon_32x32.png"
    "64:icon_32x32@2x.png"
    "128:icon_128x128.png"
    "256:icon_128x128@2x.png"
    "256:icon_256x256.png"
    "512:icon_256x256@2x.png"
    "512:icon_512x512.png"
    "1024:icon_512x512@2x.png"
)

echo "🖼️  Generazione dimensioni multiple..."
for spec in "${sizes[@]}"; do
    IFS=':' read -r size filename <<< "$spec"
    sips -z "$size" "$size" "$TEMP_PNG" --out "$ICONSET_DIR/$filename" >/dev/null 2>&1
    echo "  ✅ $filename ($size x $size)"
done

# Converti iconset in icns
echo ""
echo "🔨 Creazione file .icns..."
iconutil -c icns "$ICONSET_DIR" -o "$ICNS_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Icona creata: $ICNS_FILE"
    
    # Pulisci file temporanei
    rm -f "$TEMP_PNG"
    rm -rf "$ICONSET_DIR"
    
    # Genera anche PNG standalone per altri usi
    echo ""
    echo "📦 Generazione PNG standalone..."
    for size in 128 256 512 1024; do
        sips -Z "$size" "$SVG_FILE" --out "icon_${size}.png" >/dev/null 2>&1
        echo "  ✅ icon_${size}.png"
    done
    
    echo ""
    echo "🎉 Fatto!"
    echo ""
    echo "💡 Per usare l'icona nell'app:"
    echo "   1. Copia $ICNS_FILE nella directory Resources dell'app"
    echo "   2. Aggiorna Info.plist:"
    echo "      <key>CFBundleIconFile</key>"
    echo "      <string>AppIcon</string>"
    echo ""
    echo "   Oppure copia in: cpp/gui/resources/"
    echo "   e aggiungi a CMakeLists.txt:"
    echo "   set_target_properties(fdc_gui PROPERTIES"
    echo "       MACOSX_BUNDLE_ICON_FILE AppIcon.icns)"
else
    echo "❌ Errore durante creazione .icns"
    exit 1
fi
