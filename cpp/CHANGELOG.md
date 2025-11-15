# Changelog

All notable changes to FDC Railway Manager will be documented in this file.

## [1.0.1] - 2025-01-20

### 🐛 Bug Fixes
- **Icon Visibility**: New modern icon design with purple gradient and geometric train
  - Created professional Mac-style icon (1024x1024 SVG)
  - Purple-blue gradient background (#667eea → #764ba2)
  - Minimalist geometric train with pink-red gradient
  - Perspective tracks with vanishing point
  - Location pin icon (railway metaphor)
  - Regenerated .icns bundle with all required sizes

- **Reverse Direction Trains**: Fixed "Create Train from Line" for reverse direction
  - Removed incorrect validation `if (startIdx >= endIdx)`
  - Added proper bidirectional loop logic
  - Now supports creating trains from last to first station
  - Correctly reverses station order when startIdx > endIdx

- **Traffic Graph Time Window**: Fixed visualization to respect ±15 minute window
  - Added `setTimeWindow()` method to ScheduleGraphWidget
  - Implemented time window filtering in `paintEvent()`
  - Graph now shows only trains within the time window
  - Prevents showing entire train journeys outside window

- **Graph Clipping**: Fixed train paths extending outside graph boundaries
  - Added clipping region to limit drawing to graph area
  - Train paths and conflict markers now properly clipped to axes
  - Prevents visual artifacts outside the graph borders

- **Train List Display**: Shows train names instead of IDs in schedules list
  - Modified `updateSchedulesView()` to lookup train names from trains vector
  - Falls back to ID if train name is empty or train not found
  - Improves readability of train schedules list

- **Line Dialog Improvements**: Better station selection experience
  - Station list now shows only names (no IDs)
  - Stations sorted alphabetically for easier finding
  - Added double-click to add station (in addition to button)
  - Cleaner, more intuitive interface

### 🔧 Changed
- Auto-generated train IDs (removed manual ID field from dialog)
- Improved time window handling in traffic visualization
- Train schedules list now displays train names for better user experience

## [1.0.0] - 2025-11-15

### 🎉 Major Release - Phase 6 Complete

#### ✨ Added
- **Bidirectional Batch Train Creation**: Create trains from any station to any station
  - Station selection ComboBoxes in Batch Schedule Dialog
  - Automatic route reversal support
  - Smart default selection (first → last)

- **Configurable Settings System**: 
  - New Settings Dialog with 4 tabs (Traffic, Conflicts, Scheduling, Routes)
  - AppSettings singleton with QSettings persistence
  - Settings menu with Preferences action (⌘,)
  - All parameters now user-configurable

- **Advanced Conflict Detection**:
  - Track-type specific rules:
    * Single track: 1 train max per section
    * Opposite direction on single track = immediate conflict
    * Same direction: configurable minimum separation (default 5km)
    * Double track: configurable minimum separation (default 5km)
  - Station conflict detection with time tolerance (default ±2 minutes)
  - Visual conflict markers (red triangles with "!" symbol)

- **Improved Traffic Visualization**:
  - Tightened time window to ±20 minutes (configurable 1-180)
  - Configurable minimum common stations filter (default 2)
  - Better performance with focused view

- **Custom App Icon**:
  - Professional macOS-style icon (1024x1024)
  - Modern design: high-speed train, double track, station
  - Blue gradient background with rounded corners
  - Integrated into app bundle with CMake

- **Comprehensive Documentation**:
  - Updated PROJECT_STATUS.md with all Phase 5-6 features
  - Added AI integration roadmap (Phase 7)
  - Detailed future development plan (Phases 8-12)
  - Visual identity guidelines

#### 🔧 Changed
- Traffic time window reduced from ±180 to ±20 minutes
- All hardcoded parameters moved to AppSettings
- Settings now persist across app restarts via QSettings

#### 🐛 Fixed
- Batch creation now supports any direction (not just first→last)
- Conflict detection now respects track types
- Better handling of reversed routes

---

## [0.9.0] - 2025-11-10

### Phase 5 - Multi-Train Visualization

#### ✨ Added
- Multi-train visualization in Schedule Graph Widget
- Color-coded trains for easy identification
- Traffic detection between schedules
- Batch schedule creation dialog

---

## [0.8.0] - 2025-11-05

### Phase 4 - Complete GUI

#### ✨ Added
- All dialogs completed (Station, Connection, Train, Line, Schedule)
- Network Map Widget with interactive visualization
- Schedule Graph Widget with time-distance chart
- Comprehensive menu system
- File import/export functionality

---

## [0.7.0] - 2025-10-28

### Phase 3 - Main Window & Basic Dialogs

#### ✨ Added
- Main Window with multi-tab interface
- Station Dialog with GPS coordinates
- Connection Dialog with track parameters
- Train Dialog with predefined types
- Basic visualization widgets

---

## [0.6.0] - 2025-10-20

### Phase 2 - Core Library Enhancement

#### ✨ Added
- Complete JSON serialization
- Pathfinding with Dijkstra algorithm
- Schedule calculation with physics
- Boost.Graph integration

---

## [0.5.0] - 2025-10-15

### Phase 1 - Foundation

#### ✨ Added
- Initial project structure
- Core classes (Node, Edge, RailwayNetwork)
- Basic train physics
- CMake build system

---

## Version Format
- MAJOR.MINOR.PATCH following Semantic Versioning
- Phase N completion = MAJOR version increment
- New features = MINOR version increment  
- Bug fixes = PATCH version increment

---

**Legend:**
- ✨ Added: New features
- 🔧 Changed: Changes in existing functionality
- 🐛 Fixed: Bug fixes
- 🗑️ Removed: Removed features
- 🔒 Security: Security fixes
- ⚡ Performance: Performance improvements
