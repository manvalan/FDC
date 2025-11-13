#!/usr/bin/env python3
"""
Railway Network Management GUI Application
Complete graphical interface for managing railway networks, trains, and schedules.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser, simpledialog
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import os
import networkx as nx

from node import Node, NodeType
from edge import Edge, TrackType
from railway_network import RailwayNetwork
from train import Train, TrainType
from schedule import ScheduleBuilder, TrainSchedule
from traffic_simulator import TrafficSimulator
from visualization import plot_timetable
from database import DatabaseManager
from database_sqlite import SQLiteDatabaseManager


class RailwayLine:
    """Represents a railway line with a color and set of stations."""
    
    def __init__(self, line_id: str, name: str, color: str, route: List[str]):
        self.line_id = line_id
        self.name = name
        self.color = color
        self.route = route  # List of node IDs
        
    def to_dict(self) -> dict:
        return {
            'line_id': self.line_id,
            'name': self.name,
            'color': self.color,
            'route': self.route
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'RailwayLine':
        return RailwayLine(
            data['line_id'],
            data['name'],
            data['color'],
            data['route']
        )


class RailwayGUI:
    """Main GUI application for railway network management."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("FDC - Railway Network Manager")
        self.root.geometry("1400x900")
        
        # Data structures
        self.network = RailwayNetwork("New Railway Network")
        self.lines: Dict[str, RailwayLine] = {}
        self.schedules: List[TrainSchedule] = []
        self.current_file: Optional[str] = None
        self.db: Optional[SQLiteDatabaseManager] = None  # Can be SQLite or MySQL
        self.db_type: str = "none"  # "sqlite", "mysql", or "none"
        self.modified: bool = False  # Track unsaved changes
        
        # Setup GUI
        self.setup_menu()
        self.setup_toolbar()
        self.setup_main_area()
        self.setup_statusbar()
        
        # Update displays
        self.update_all_displays()
    
    def setup_menu(self):
        """Create menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Nuovo Progetto", command=self.new_project, accelerator="Ctrl+N")
        file_menu.add_command(label="Apri...", command=self.open_project, accelerator="Ctrl+O")
        file_menu.add_command(label="Salva", command=self.save_project, accelerator="Ctrl+S")
        file_menu.add_command(label="Salva con nome...", command=self.save_project_as, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="Esci", command=self.root.quit)
        
        # Database menu
        db_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Database", menu=db_menu)
        db_menu.add_command(label="Usa SQLite (Predefinito)", command=self.connect_sqlite)
        db_menu.add_command(label="Connetti a MySQL...", command=self.connect_mysql)
        db_menu.add_separator()
        db_menu.add_command(label="Salva Rete nel Database", command=self.save_to_database)
        db_menu.add_command(label="Carica Rete dal Database...", command=self.load_from_database)
        db_menu.add_separator()
        db_menu.add_command(label="🗑️ Gestisci Salvataggi...", command=self.manage_database_saves)
        db_menu.add_separator()
        db_menu.add_command(label="Stato Connessione", command=self.show_db_status)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Modifica", menu=edit_menu)
        edit_menu.add_command(label="Aggiungi Stazione", command=self.add_station_dialog)
        edit_menu.add_command(label="Aggiungi Connessione", command=self.add_connection_dialog)
        edit_menu.add_separator()
        edit_menu.add_command(label="Gestisci Linee", command=self.manage_lines_dialog)
        
        # Trains menu
        trains_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Treni", menu=trains_menu)
        trains_menu.add_command(label="Nuovo Treno", command=self.add_train_dialog)
        trains_menu.add_command(label="➕ Serie di Treni (Cadenzati)", command=self.add_train_series_dialog)
        trains_menu.add_command(label="Gestisci Orari", command=self.manage_schedules_dialog)
        trains_menu.add_separator()
        trains_menu.add_command(label="🚉 Gestione Binari", command=self.show_platform_manager)
        trains_menu.add_command(label="🔄 Riassegna Binari Automaticamente", command=lambda: [self.auto_assign_all_platforms(), messagebox.showinfo("Completato", "Binari riassegnati automaticamente")])
        trains_menu.add_separator()
        trains_menu.add_command(label="Simula Traffico", command=self.simulate_traffic)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Visualizza", menu=view_menu)
        view_menu.add_command(label="Mappa Rete", command=self.show_network_map)
        view_menu.add_command(label="Grafico Orario", command=self.show_timetable_diagram)
        view_menu.add_separator()
        view_menu.add_command(label="🗺️ Mappa Metro - Tutte le Linee", command=self.show_all_metro_maps)
        view_menu.add_command(label="🗺️ Mappa Metro - Selezione Linee...", command=self.show_metro_map_selection)
        view_menu.add_separator()
        view_menu.add_command(label="Statistiche Rete", command=self.show_network_stats)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Aiuto", menu=help_menu)
        help_menu.add_command(label="Informazioni", command=self.show_about)
        
        # Keyboard shortcuts
        self.root.bind('<Control-n>', lambda e: self.new_project())
        self.root.bind('<Control-o>', lambda e: self.open_project())
        self.root.bind('<Control-s>', lambda e: self.save_project())
    
    def setup_toolbar(self):
        """Create toolbar with quick access buttons."""
        toolbar = ttk.Frame(self.root, relief=tk.RAISED, padding=5)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # Icons (using text for now, could use images)
        ttk.Button(toolbar, text="➕ Stazione", command=self.add_station_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🔗 Connessione", command=self.add_connection_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        ttk.Button(toolbar, text="🚂 Treno", command=self.add_train_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📅 Orari", command=self.manage_schedules_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🚉 Binari", command=self.show_platform_manager).pack(side=tk.LEFT, padx=2)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        ttk.Button(toolbar, text="🗺️ Mappa", command=self.show_network_map).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📊 Grafico", command=self.show_timetable_diagram).pack(side=tk.LEFT, padx=2)
    
    def setup_main_area(self):
        """Create main working area with tabs."""
        # Create notebook (tabbed interface)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tab 1: Network Overview
        self.network_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.network_tab, text="Rete Ferroviaria")
        self.setup_network_tab()
        
        # Tab 2: Lines Management
        self.lines_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.lines_tab, text="Linee")
        self.setup_lines_tab()
        
        # Tab 3: Trains & Schedules
        self.trains_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.trains_tab, text="Treni e Orari")
        self.setup_trains_tab()
    
    def setup_network_tab(self):
        """Setup network overview tab."""
        # Split into stations and connections
        paned = ttk.PanedWindow(self.network_tab, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # Stations panel
        stations_frame = ttk.LabelFrame(paned, text="Stazioni", padding=10)
        paned.add(stations_frame, weight=1)
        
        # Stations list
        self.stations_tree = ttk.Treeview(stations_frame, columns=('Type', 'Lat', 'Lon', 'Platforms'), 
                                          show='tree headings', height=15)
        self.stations_tree.heading('#0', text='ID / Nome')
        self.stations_tree.heading('Type', text='Tipo')
        self.stations_tree.heading('Lat', text='Latitudine')
        self.stations_tree.heading('Lon', text='Longitudine')
        self.stations_tree.heading('Platforms', text='Binari')
        
        self.stations_tree.column('#0', width=200)
        self.stations_tree.column('Type', width=100)
        self.stations_tree.column('Lat', width=80)
        self.stations_tree.column('Lon', width=80)
        self.stations_tree.column('Platforms', width=60)
        
        scrollbar = ttk.Scrollbar(stations_frame, orient=tk.VERTICAL, command=self.stations_tree.yview)
        self.stations_tree.configure(yscrollcommand=scrollbar.set)
        
        self.stations_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons
        btn_frame = ttk.Frame(stations_frame)
        btn_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Button(btn_frame, text="Modifica", command=self.edit_station).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Elimina", command=self.delete_station).pack(side=tk.LEFT, padx=2)
        
        # Connections panel
        connections_frame = ttk.LabelFrame(paned, text="Connessioni", padding=10)
        paned.add(connections_frame, weight=1)
        
        # Connections list
        self.connections_tree = ttk.Treeview(connections_frame, 
                                            columns=('From', 'To', 'Distance', 'Type', 'Speed'),
                                            show='headings', height=15)
        self.connections_tree.heading('From', text='Da')
        self.connections_tree.heading('To', text='A')
        self.connections_tree.heading('Distance', text='Distanza (km)')
        self.connections_tree.heading('Type', text='Tipo Binario')
        self.connections_tree.heading('Speed', text='Velocità (km/h)')
        
        self.connections_tree.column('From', width=100)
        self.connections_tree.column('To', width=100)
        self.connections_tree.column('Distance', width=100)
        self.connections_tree.column('Type', width=100)
        self.connections_tree.column('Speed', width=100)
        
        scrollbar2 = ttk.Scrollbar(connections_frame, orient=tk.VERTICAL, command=self.connections_tree.yview)
        self.connections_tree.configure(yscrollcommand=scrollbar2.set)
        
        self.connections_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar2.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons
        btn_frame2 = ttk.Frame(connections_frame)
        btn_frame2.pack(fill=tk.X, pady=(5, 0))
        ttk.Button(btn_frame2, text="Modifica", command=self.edit_connection).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame2, text="Elimina", command=self.delete_connection).pack(side=tk.LEFT, padx=2)
    
    def setup_lines_tab(self):
        """Setup lines management tab."""
        # Lines list
        list_frame = ttk.LabelFrame(self.lines_tab, text="Linee Ferroviarie", padding=10)
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 2), pady=5)
        
        self.lines_tree = ttk.Treeview(list_frame, columns=('Name', 'Color', 'Stations'),
                                       show='tree headings', height=20)
        self.lines_tree.heading('#0', text='ID')
        self.lines_tree.heading('Name', text='Nome')
        self.lines_tree.heading('Color', text='Colore')
        self.lines_tree.heading('Stations', text='N° Stazioni')
        
        self.lines_tree.column('#0', width=80)
        self.lines_tree.column('Name', width=200)
        self.lines_tree.column('Color', width=100)
        self.lines_tree.column('Stations', width=100)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.lines_tree.yview)
        self.lines_tree.configure(yscrollcommand=scrollbar.set)
        
        self.lines_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons
        btn_frame = ttk.Frame(list_frame)
        btn_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Button(btn_frame, text="➕ Nuova Linea", command=self.add_line_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="✏️ Modifica", command=self.edit_line).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="🗑️ Elimina", command=self.delete_line).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="🗺️ Mappa Metro", command=self.show_metro_map).pack(side=tk.LEFT, padx=2)
        
        # Line details panel
        details_frame = ttk.LabelFrame(self.lines_tab, text="Dettagli Linea", padding=10)
        details_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(2, 5), pady=5)
        
        self.line_details_text = tk.Text(details_frame, wrap=tk.WORD, height=20, width=40)
        self.line_details_text.pack(fill=tk.BOTH, expand=True)
        
        # Bind selection event
        self.lines_tree.bind('<<TreeviewSelect>>', self.on_line_selected)
    
    def setup_trains_tab(self):
        """Setup trains and schedules tab."""
        # Main container
        main_container = ttk.Frame(self.trains_tab)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Filter bar at top
        filter_frame = ttk.Frame(main_container)
        filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(filter_frame, text="Filtra per Linea:").pack(side=tk.LEFT, padx=5)
        
        self.train_filter_var = tk.StringVar(value="Tutte le linee")
        self.train_filter_combo = ttk.Combobox(filter_frame, textvariable=self.train_filter_var, 
                                               width=30, state='readonly')
        self.train_filter_combo['values'] = ["Tutte le linee"]
        self.train_filter_combo.pack(side=tk.LEFT, padx=5)
        self.train_filter_combo.bind('<<ComboboxSelected>>', lambda e: self.update_trains_list())
        
        ttk.Button(filter_frame, text="🔄 Aggiorna", command=self.update_trains_list).pack(side=tk.LEFT, padx=5)
        
        # Split into trains list and schedule details
        paned = ttk.PanedWindow(main_container, orient=tk.VERTICAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # Trains list - EXPANDED HEIGHT
        trains_frame = ttk.LabelFrame(paned, text="Treni e Orari", padding=10)
        paned.add(trains_frame, weight=2)  # Increased weight from 1 to 2
        
        self.trains_tree = ttk.Treeview(trains_frame, 
                                       columns=('Train', 'Type', 'Line', 'Origin', 'Dest', 'Departure', 'Arrival'),
                                       show='tree headings', height=18)  # Increased height from 10 to 18
        self.trains_tree.heading('#0', text='Schedule ID')
        self.trains_tree.heading('Train', text='Treno')
        self.trains_tree.heading('Type', text='Tipo')
        self.trains_tree.heading('Line', text='Linea')
        self.trains_tree.heading('Origin', text='Origine')
        self.trains_tree.heading('Dest', text='Destinazione')
        self.trains_tree.heading('Departure', text='Partenza')
        self.trains_tree.heading('Arrival', text='Arrivo')
        
        # Adjusted column widths to prevent overlapping
        self.trains_tree.column('#0', width=100)
        self.trains_tree.column('Train', width=120)
        self.trains_tree.column('Type', width=80)
        self.trains_tree.column('Line', width=100)
        self.trains_tree.column('Origin', width=120)
        self.trains_tree.column('Dest', width=120)
        self.trains_tree.column('Departure', width=70)
        self.trains_tree.column('Arrival', width=70)
        
        scrollbar = ttk.Scrollbar(trains_frame, orient=tk.VERTICAL, command=self.trains_tree.yview)
        self.trains_tree.configure(yscrollcommand=scrollbar.set)
        
        self.trains_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Schedule details - Split into two sections: info (left) and diagram (right)
        details_frame = ttk.LabelFrame(paned, text="Dettagli Orario", padding=10)
        paned.add(details_frame, weight=1)
        
        # Split details_frame horizontally
        details_paned = ttk.PanedWindow(details_frame, orient=tk.HORIZONTAL)
        details_paned.pack(fill=tk.BOTH, expand=True)
        
        # Left side: Text info
        info_frame = ttk.Frame(details_paned)
        details_paned.add(info_frame, weight=1)
        
        self.schedule_details_text = tk.Text(info_frame, wrap=tk.WORD, height=15)
        scrollbar2 = ttk.Scrollbar(info_frame, orient=tk.VERTICAL, command=self.schedule_details_text.yview)
        self.schedule_details_text.configure(yscrollcommand=scrollbar2.set)
        
        self.schedule_details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar2.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Right side: Diagram canvas
        diagram_frame = ttk.Frame(details_paned)
        details_paned.add(diagram_frame, weight=1)
        
        # Canvas for embedding matplotlib figure
        self.diagram_canvas = None
        self.diagram_frame_container = diagram_frame
        
        # Create context menu for trains
        self.trains_menu = tk.Menu(self.root, tearoff=0)
        self.trains_menu.add_command(label="✏️ Modifica Treno", command=self.edit_schedule)
        self.trains_menu.add_command(label="🗑️ Elimina Treno", command=self.delete_schedule)
        # Nota: Il grafico è già visualizzato nel pannello a destra quando si seleziona un treno
        
        # Bind events
        self.trains_tree.bind('<<TreeviewSelect>>', self.on_schedule_selected)
        self.trains_tree.bind('<Double-Button-1>', lambda e: self.edit_schedule())
        self.trains_tree.bind('<Button-2>', self.show_trains_context_menu)  # Right-click on Mac
        self.trains_tree.bind('<Button-3>', self.show_trains_context_menu)  # Right-click on Windows/Linux
    
    def setup_statusbar(self):
        """Create status bar."""
        self.statusbar = ttk.Label(self.root, text="Pronto", relief=tk.SUNKEN, anchor=tk.W)
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def update_status(self, message: str):
        """Update status bar message."""
        self.statusbar.config(text=message)
        self.root.update_idletasks()
    
    # ========================================================================
    # FILE OPERATIONS
    # ========================================================================
    
    def new_project(self):
        """Create new project."""
        if messagebox.askyesno("Nuovo Progetto", "Creare un nuovo progetto? I dati non salvati andranno persi."):
            self.network = RailwayNetwork("New Railway Network")
            self.lines = {}
            self.schedules = []
            self.current_file = None
            self.update_all_displays()
            self.update_status("Nuovo progetto creato")
    
    def open_project(self):
        """Open existing project from JSON."""
        filename = filedialog.askopenfilename(
            title="Apri Progetto",
            filetypes=[("FDC Project", "*.fdc"), ("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Load network
                self.network = RailwayNetwork(data.get('network_name', 'Railway Network'))
                self.network.import_from_json(filename)
                
                # Load lines
                self.lines = {}
                for line_data in data.get('lines', []):
                    line = RailwayLine.from_dict(line_data)
                    self.lines[line.line_id] = line
                
                # Load schedules
                self.schedules = []
                for sched_data in data.get('schedules', []):
                    try:
                        schedule = TrainSchedule.from_dict(sched_data)
                        self.schedules.append(schedule)
                    except Exception as e:
                        print(f"Errore nel caricamento schedule: {e}")
                
                # Auto-assign platforms after loading
                if self.schedules:
                    self.auto_assign_all_platforms()
                
                self.current_file = filename
                self.update_all_displays()
                self.update_status(f"Progetto caricato: {os.path.basename(filename)} - {len(self.schedules)} treni caricati")
                
            except Exception as e:
                messagebox.showerror("Errore", f"Impossibile aprire il file:\n{str(e)}")
    
    def load_ferrovie_contea(self):
        """Load Ferrovie della Contea network."""
        # Path to the Ferrovie della Contea JSON file
        json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                 'examples', 'ferrovie_contea_fdc.json')
        
        if not os.path.exists(json_path):
            messagebox.showerror("Errore", 
                f"File non trovato:\n{json_path}\n\n"
                "Assicurati che il file 'ferrovie_contea_fdc.json' sia nella cartella examples/")
            return
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Create new network
            network_name = data.get('name', 'Ferrovie della Contea')
            self.network = RailwayNetwork(network_name)
            
            # Import nodes (stations)
            for node_data in data.get('nodes', []):
                # Convert type string to NodeType enum
                node_type_str = node_data.get('type', 'station').upper()
                if node_type_str == 'STATION':
                    node_type = NodeType.STATION
                elif node_type_str == 'INTERCHANGE':
                    node_type = NodeType.INTERCHANGE
                elif node_type_str == 'DEPOT':
                    node_type = NodeType.DEPOT
                else:
                    node_type = NodeType.STATION
                
                node = Node(
                    node_id=node_data['id'],
                    name=node_data.get('name', node_data['id']),
                    node_type=node_type,
                    latitude=node_data.get('latitude', 0.0),
                    longitude=node_data.get('longitude', 0.0),
                    capacity=node_data.get('capacity', 2),
                    platforms=node_data.get('platforms', 2)
                )
                self.network.add_node(node)
            
            # Import edges (connections)
            for edge_data in data.get('edges', []):
                from_id = edge_data['from_node']
                to_id = edge_data['to_node']
                
                # Convert track type string to TrackType enum
                track_type_str = edge_data.get('track_type', 'single').upper()
                if track_type_str == 'SINGLE':
                    track_type = TrackType.SINGLE
                elif track_type_str == 'DOUBLE':
                    track_type = TrackType.DOUBLE
                else:
                    track_type = TrackType.SINGLE
                
                if from_id in self.network.nodes and to_id in self.network.nodes:
                    edge = Edge(
                        from_node=from_id,
                        to_node=to_id,
                        distance=edge_data['distance'],
                        track_type=track_type,
                        max_speed=edge_data.get('max_speed', 100.0)
                    )
                    self.network.add_edge(edge)
            
            # Clear existing lines (the JSON doesn't have lines predefined)
            self.lines = {}
            
            self.current_file = None  # Mark as unsaved
            self.update_all_displays()
            
            # Show info message
            stats = self.network.get_network_stats()
            messagebox.showinfo("Rete Caricata",
                f"✅ {network_name} caricata con successo!\n\n"
                f"📍 Stazioni: {stats['num_nodes']}\n"
                f"🔗 Connessioni: {stats['num_edges']}\n"
                f"📏 Lunghezza totale: {stats['total_track_length']:.1f} km")
            
            self.update_status(f"{network_name} caricata")
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            messagebox.showerror("Errore", 
                f"Impossibile caricare la rete:\n{str(e)}\n\n"
                f"Dettagli:\n{error_details}")
    
    def load_ferrovie_contea_av(self):
        """Load Ferrovie della Contea network with AV infrastructure."""
        json_path = os.path.join(os.path.dirname(__file__), '..', 'examples', 'ferrovie_contea_con_av.json')
        
        if not os.path.exists(json_path):
            messagebox.showerror("Errore", 
                f"File non trovato:\n{json_path}\n\n"
                "Eseguire prima lo script create_av_infrastructure_specific.py")
            return
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Create new network
            network_name = data.get('name', 'Ferrovie della Contea con AV')
            self.network = RailwayNetwork(network_name)
            
            # Import nodes (stations)
            for node_data in data.get('nodes', []):
                # Convert type string to NodeType enum
                node_type_str = node_data.get('type', 'station').upper()
                if node_type_str == 'STATION':
                    node_type = NodeType.STATION
                elif node_type_str == 'INTERCHANGE':
                    node_type = NodeType.INTERCHANGE
                elif node_type_str == 'DEPOT':
                    node_type = NodeType.DEPOT
                else:
                    node_type = NodeType.STATION
                
                node = Node(
                    node_id=node_data['id'],
                    name=node_data.get('name', node_data['id']),
                    node_type=node_type,
                    latitude=node_data.get('latitude', 0.0),
                    longitude=node_data.get('longitude', 0.0),
                    capacity=node_data.get('capacity', 2),
                    platforms=node_data.get('platforms', 2)
                )
                self.network.add_node(node)
            
            # Import edges (connections)
            for edge_data in data.get('edges', []):
                from_id = edge_data['from_node']
                to_id = edge_data['to_node']
                
                # Convert track type string to TrackType enum
                track_type_str = edge_data.get('track_type', 'single').upper()
                if track_type_str == 'SINGLE':
                    track_type = TrackType.SINGLE
                elif track_type_str == 'DOUBLE':
                    track_type = TrackType.DOUBLE
                else:
                    track_type = TrackType.SINGLE
                
                if from_id in self.network.nodes and to_id in self.network.nodes:
                    edge = Edge(
                        from_node=from_id,
                        to_node=to_id,
                        distance=edge_data.get('distance', 10.0),
                        track_type=track_type,
                        max_speed=edge_data.get('max_speed', 100),
                        capacity=edge_data.get('capacity', 1)
                    )
                    self.network.add_edge(edge)
            
            # Clear existing data
            self.lines.clear()
            self.schedules.clear()
            
            # Update all displays
            self.update_all_displays()
            
            # Show statistics with AV info
            stats = self.network.get_network_stats()
            av_stations = [node_id for node_id in self.network.nodes if '_AV' in node_id]
            av_connections = [edge for edge in self.network.edges 
                            if '_AV' in edge.from_node or '_AV' in edge.to_node]
            
            messagebox.showinfo("Rete Caricata", 
                f"✅ {network_name} caricata con successo!\n\n"
                f"📊 RETE TOTALE:\n"
                f"📍 Stazioni: {stats['num_nodes']}\n"
                f"🔗 Connessioni: {stats['num_edges']}\n"
                f"📏 Lunghezza totale: {stats['total_track_length']:.1f} km\n\n"
                f"🚄 INFRASTRUTTURA AV:\n"
                f"📍 Stazioni AV: {len(av_stations)}\n"
                f"🔗 Connessioni AV: {len([e for e in av_connections if '_AV' in e.from_node and '_AV' in e.to_node])}\n"
                f"⚡ Velocità max: 300 km/h\n"
                f"🔄 Interscambi: {len([e for e in av_connections if not ('_AV' in e.from_node and '_AV' in e.to_node)])}")
            
            self.update_status(f"{network_name} caricata con infrastruttura AV")
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            messagebox.showerror("Errore", 
                f"Impossibile caricare la rete:\n{str(e)}\n\n"
                f"Dettagli:\n{error_details}")
    
    def save_project(self):
        """Save current project."""
        if self.current_file:
            self._save_to_file(self.current_file)
        else:
            self.save_project_as()
    
    def save_project_as(self):
        """Save project with new filename."""
        filename = filedialog.asksaveasfilename(
            title="Salva Progetto",
            defaultextension=".fdc",
            filetypes=[("FDC Project", "*.fdc"), ("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self._save_to_file(filename)
            self.current_file = filename
    
    def _save_to_file(self, filename: str):
        """Save project to file."""
        try:
            # Build complete project data
            project_data = {
                'network_name': self.network.name,
                'nodes': [node.to_dict() for node in self.network.nodes.values()],
                'edges': [edge.to_dict() for edge in self.network.edges],
                'lines': [line.to_dict() for line in self.lines.values()],
                'schedules': [schedule.to_dict() for schedule in self.schedules]
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=2, ensure_ascii=False)
            
            self.update_status(f"Progetto salvato: {os.path.basename(filename)} - {len(self.schedules)} treni salvati")
            
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile salvare il file:\n{str(e)}")
    
    # ========================================================================
    # DIALOGS
    # ========================================================================
    
    def add_station_dialog(self):
        """Show dialog to add new station."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Aggiungi Stazione")
        dialog.geometry("400x350")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Form fields
        ttk.Label(dialog, text="ID Stazione:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        id_entry = ttk.Entry(dialog, width=30)
        id_entry.grid(row=0, column=1, padx=10, pady=5)
        
        ttk.Label(dialog, text="Nome:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        name_entry = ttk.Entry(dialog, width=30)
        name_entry.grid(row=1, column=1, padx=10, pady=5)
        
        ttk.Label(dialog, text="Tipo:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        type_var = tk.StringVar(value="STATION")
        type_combo = ttk.Combobox(dialog, textvariable=type_var, width=28,
                                  values=["STATION", "INTERCHANGE", "DEPOT"])
        type_combo.grid(row=2, column=1, padx=10, pady=5)
        
        ttk.Label(dialog, text="Latitudine:").grid(row=3, column=0, sticky=tk.W, padx=10, pady=5)
        lat_entry = ttk.Entry(dialog, width=30)
        lat_entry.insert(0, "45.0")
        lat_entry.grid(row=3, column=1, padx=10, pady=5)
        
        ttk.Label(dialog, text="Longitudine:").grid(row=4, column=0, sticky=tk.W, padx=10, pady=5)
        lon_entry = ttk.Entry(dialog, width=30)
        lon_entry.insert(0, "9.0")
        lon_entry.grid(row=4, column=1, padx=10, pady=5)
        
        ttk.Label(dialog, text="Capacità:").grid(row=5, column=0, sticky=tk.W, padx=10, pady=5)
        capacity_entry = ttk.Entry(dialog, width=30)
        capacity_entry.insert(0, "6")
        capacity_entry.grid(row=5, column=1, padx=10, pady=5)
        
        ttk.Label(dialog, text="N° Binari:").grid(row=6, column=0, sticky=tk.W, padx=10, pady=5)
        platforms_entry = ttk.Entry(dialog, width=30)
        platforms_entry.insert(0, "4")
        platforms_entry.grid(row=6, column=1, padx=10, pady=5)
        
        def save_station():
            try:
                node_id = id_entry.get().strip()
                if not node_id:
                    messagebox.showerror("Errore", "L'ID della stazione è obbligatorio")
                    return
                
                if node_id in self.network.nodes:
                    messagebox.showerror("Errore", f"Una stazione con ID '{node_id}' esiste già")
                    return
                
                node = Node(
                    node_id=node_id,
                    name=name_entry.get().strip() or node_id,
                    node_type=NodeType[type_var.get()],
                    latitude=float(lat_entry.get()),
                    longitude=float(lon_entry.get()),
                    capacity=int(capacity_entry.get()),
                    platforms=int(platforms_entry.get())
                )
                
                self.network.add_node(node)
                self.update_all_displays()
                self.update_status(f"Stazione '{node.name}' aggiunta")
                dialog.destroy()
                
            except ValueError as e:
                messagebox.showerror("Errore", f"Valori non validi:\n{str(e)}")
        
        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=7, column=0, columnspan=2, pady=20)
        ttk.Button(btn_frame, text="Salva", command=save_station).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Annulla", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def add_connection_dialog(self):
        """Show dialog to add new connection."""
        if len(self.network.nodes) < 2:
            messagebox.showwarning("Attenzione", "Servono almeno 2 stazioni per creare una connessione")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Aggiungi Connessione")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        station_ids = sorted(self.network.nodes.keys())
        
        # Form fields
        ttk.Label(dialog, text="Da:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        from_var = tk.StringVar()
        from_combo = ttk.Combobox(dialog, textvariable=from_var, width=28, values=station_ids)
        from_combo.grid(row=0, column=1, padx=10, pady=5)
        
        ttk.Label(dialog, text="A:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        to_var = tk.StringVar()
        to_combo = ttk.Combobox(dialog, textvariable=to_var, width=28, values=station_ids)
        to_combo.grid(row=1, column=1, padx=10, pady=5)
        
        ttk.Label(dialog, text="Distanza (km):").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        distance_entry = ttk.Entry(dialog, width=30)
        distance_entry.insert(0, "50.0")
        distance_entry.grid(row=2, column=1, padx=10, pady=5)
        
        ttk.Label(dialog, text="Tipo Binario:").grid(row=3, column=0, sticky=tk.W, padx=10, pady=5)
        track_var = tk.StringVar(value="DOUBLE")
        track_combo = ttk.Combobox(dialog, textvariable=track_var, width=28,
                                   values=["SINGLE", "DOUBLE", "HIGH_SPEED", "FREIGHT"])
        track_combo.grid(row=3, column=1, padx=10, pady=5)
        
        ttk.Label(dialog, text="Velocità Max (km/h):").grid(row=4, column=0, sticky=tk.W, padx=10, pady=5)
        speed_entry = ttk.Entry(dialog, width=30)
        speed_entry.insert(0, "160")
        speed_entry.grid(row=4, column=1, padx=10, pady=5)
        
        def save_connection():
            try:
                from_node = from_var.get()
                to_node = to_var.get()
                
                if not from_node or not to_node:
                    messagebox.showerror("Errore", "Selezionare stazioni di partenza e arrivo")
                    return
                
                if from_node == to_node:
                    messagebox.showerror("Errore", "Le stazioni devono essere diverse")
                    return
                
                edge = Edge(
                    from_node=from_node,
                    to_node=to_node,
                    distance=float(distance_entry.get()),
                    track_type=TrackType[track_var.get()],
                    max_speed=int(speed_entry.get()),
                    capacity=2 if track_var.get() == "DOUBLE" else 1
                )
                
                self.network.add_edge(edge)
                self.update_all_displays()
                self.update_status(f"Connessione {from_node} → {to_node} aggiunta")
                dialog.destroy()
                
            except ValueError as e:
                messagebox.showerror("Errore", f"Valori non validi:\n{str(e)}")
        
        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=20)
        ttk.Button(btn_frame, text="Salva", command=save_connection).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Annulla", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def add_line_dialog(self):
        """Show dialog to create a new railway line."""
        if len(self.network.nodes) < 2:
            messagebox.showwarning("Attenzione", "Servono almeno 2 stazioni per creare una linea")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Nuova Linea Ferroviaria")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Form fields
        ttk.Label(dialog, text="ID Linea:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        id_entry = ttk.Entry(dialog, width=30)
        id_entry.grid(row=0, column=1, padx=10, pady=5)
        
        ttk.Label(dialog, text="Nome:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        name_entry = ttk.Entry(dialog, width=30)
        name_entry.grid(row=1, column=1, padx=10, pady=5)
        
        ttk.Label(dialog, text="Colore:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        color_frame = ttk.Frame(dialog)
        color_frame.grid(row=2, column=1, sticky=tk.W, padx=10, pady=5)
        
        color_var = tk.StringVar(value="#FF0000")
        color_entry = ttk.Entry(color_frame, textvariable=color_var, width=20)
        color_entry.pack(side=tk.LEFT)
        
        def choose_color():
            color = colorchooser.askcolor(title="Scegli Colore")[1]
            if color:
                color_var.set(color)
        
        ttk.Button(color_frame, text="Scegli...", command=choose_color).pack(side=tk.LEFT, padx=5)
        
        # Station selection
        ttk.Label(dialog, text="Percorso (stazioni):").grid(row=3, column=0, sticky=tk.NW, padx=10, pady=5)
        
        route_frame = ttk.Frame(dialog)
        route_frame.grid(row=3, column=1, sticky=tk.NSEW, padx=10, pady=5)
        
        route_listbox = tk.Listbox(route_frame, height=10, width=40)
        route_scrollbar = ttk.Scrollbar(route_frame, orient=tk.VERTICAL, command=route_listbox.yview)
        route_listbox.configure(yscrollcommand=route_scrollbar.set)
        route_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        route_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Available stations (sorted alphabetically)
        station_ids = sorted(self.network.nodes.keys())
        
        def add_station_to_route():
            AddStationDialog(dialog, station_ids, route_listbox)
        
        def remove_from_route():
            selection = route_listbox.curselection()
            if selection:
                route_listbox.delete(selection)
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=4, column=1, sticky=tk.W, padx=10, pady=5)
        ttk.Button(btn_frame, text="➕ Aggiungi Stazione", command=add_station_to_route).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="➖ Rimuovi", command=remove_from_route).pack(side=tk.LEFT, padx=2)
        
        def save_line():
            line_id = id_entry.get().strip()
            if not line_id:
                messagebox.showerror("Errore", "L'ID della linea è obbligatorio")
                return
            
            if line_id in self.lines:
                messagebox.showerror("Errore", f"Una linea con ID '{line_id}' esiste già")
                return
            
            route = list(route_listbox.get(0, tk.END))
            if len(route) < 2:
                messagebox.showerror("Errore", "La linea deve avere almeno 2 stazioni")
                return
            
            line = RailwayLine(
                line_id=line_id,
                name=name_entry.get().strip() or line_id,
                color=color_var.get(),
                route=route
            )
            
            self.lines[line_id] = line
            self.update_all_displays()
            self.update_status(f"Linea '{line.name}' creata")
            dialog.destroy()
        
        # Save/Cancel buttons
        save_btn_frame = ttk.Frame(dialog)
        save_btn_frame.grid(row=5, column=0, columnspan=2, pady=20)
        ttk.Button(save_btn_frame, text="Salva", command=save_line).pack(side=tk.LEFT, padx=5)
        ttk.Button(save_btn_frame, text="Annulla", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def add_train_dialog(self):
        """Show dialog to add new train and schedule."""
        if len(self.network.nodes) < 2:
            messagebox.showwarning("Attenzione", "Servono almeno 2 stazioni per creare un treno")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Nuovo Treno e Orario")
        dialog.geometry("500x580")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Train info
        ttk.Label(dialog, text="ID Treno:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        train_id_entry = ttk.Entry(dialog, width=30)
        train_id_entry.grid(row=0, column=1, padx=10, pady=5)
        
        ttk.Label(dialog, text="Nome Treno:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        train_name_entry = ttk.Entry(dialog, width=30)
        train_name_entry.grid(row=1, column=1, padx=10, pady=5)
        
        ttk.Label(dialog, text="Tipo Treno:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        train_type_var = tk.StringVar(value="REGIONAL")
        train_type_combo = ttk.Combobox(dialog, textvariable=train_type_var, width=28,
                                        values=["HIGH_SPEED", "INTERCITY", "REGIONAL", "FREIGHT", "LOCAL"])
        train_type_combo.grid(row=2, column=1, padx=10, pady=5)
        
        # Schedule info
        ttk.Label(dialog, text="ID Orario:").grid(row=3, column=0, sticky=tk.W, padx=10, pady=5)
        schedule_id_entry = ttk.Entry(dialog, width=30)
        schedule_id_entry.grid(row=3, column=1, padx=10, pady=5)
        
        # Route selection
        ttk.Label(dialog, text="Seleziona Percorso:").grid(row=4, column=0, sticky=tk.NW, padx=10, pady=5)
        
        route_type = tk.StringVar(value="line")
        ttk.Radiobutton(dialog, text="Da Linea Esistente", variable=route_type, value="line").grid(row=4, column=1, sticky=tk.W, padx=10)
        ttk.Radiobutton(dialog, text="Personalizzato", variable=route_type, value="custom").grid(row=5, column=1, sticky=tk.W, padx=10)
        
        # Line selection
        ttk.Label(dialog, text="Linea:").grid(row=6, column=0, sticky=tk.W, padx=10, pady=5)
        line_var = tk.StringVar()
        line_names = [f"{lid}: {line.name}" for lid, line in self.lines.items()]
        line_combo = ttk.Combobox(dialog, textvariable=line_var, width=28, values=line_names)
        line_combo.grid(row=6, column=1, padx=10, pady=5)
        
        # Start/End station selection
        ttk.Label(dialog, text="Stazione Partenza:").grid(row=7, column=0, sticky=tk.W, padx=10, pady=5)
        start_station_var = tk.StringVar()
        start_station_combo = ttk.Combobox(dialog, textvariable=start_station_var, width=28, state='disabled')
        start_station_combo.grid(row=7, column=1, padx=10, pady=5)
        
        ttk.Label(dialog, text="Stazione Arrivo:").grid(row=8, column=0, sticky=tk.W, padx=10, pady=5)
        end_station_var = tk.StringVar()
        end_station_combo = ttk.Combobox(dialog, textvariable=end_station_var, width=28, state='disabled')
        end_station_combo.grid(row=8, column=1, padx=10, pady=5)
        
        def on_line_selected(event=None):
            """Update start/end station options when line is selected."""
            selected = line_var.get()
            if selected and ':' in selected:
                line_id = selected.split(':')[0].strip()
                if line_id in self.lines:
                    line_route = self.lines[line_id].route
                    start_station_combo['values'] = line_route
                    end_station_combo['values'] = line_route
                    start_station_combo['state'] = 'readonly'
                    end_station_combo['state'] = 'readonly'
                    if line_route:
                        start_station_var.set(line_route[0])
                        end_station_var.set(line_route[-1])
        
        line_combo.bind('<<ComboboxSelected>>', on_line_selected)
        
        # Departure time
        ttk.Label(dialog, text="Ora Partenza (HH:MM):").grid(row=9, column=0, sticky=tk.W, padx=10, pady=5)
        time_entry = ttk.Entry(dialog, width=30)
        time_entry.insert(0, "08:00")
        time_entry.grid(row=9, column=1, padx=10, pady=5)
        
        # Arrival time (optional - for constraint)
        ttk.Label(dialog, text="Ora Arrivo (HH:MM, opzionale):").grid(row=10, column=0, sticky=tk.W, padx=10, pady=5)
        arrival_time_entry = ttk.Entry(dialog, width=30)
        arrival_time_entry.insert(0, "")
        arrival_time_entry.grid(row=10, column=1, padx=10, pady=5)
        
        # Dwell time
        ttk.Label(dialog, text="Tempo Sosta (min):").grid(row=11, column=0, sticky=tk.W, padx=10, pady=5)
        dwell_entry = ttk.Entry(dialog, width=30)
        dwell_entry.insert(0, "3")
        dwell_entry.grid(row=11, column=1, padx=10, pady=5)
        
        def save_train():
            try:
                # Create train
                train = Train(
                    train_id=train_id_entry.get().strip(),
                    name=train_name_entry.get().strip(),
                    train_type=TrainType[train_type_var.get()]
                )
                
                # Get route
                if route_type.get() == "line":
                    selected = line_var.get()
                    if not selected:
                        messagebox.showerror("Errore", "Selezionare una linea")
                        return
                    line_id = selected.split(':')[0].strip()
                    full_route = self.lines[line_id].route
                    
                    # Get start and end stations
                    start_station = start_station_var.get()
                    end_station = end_station_var.get()
                    
                    if not start_station or not end_station:
                        messagebox.showerror("Errore", "Selezionare stazione di partenza e arrivo")
                        return
                    
                    # Extract sub-route between start and end
                    if start_station in full_route and end_station in full_route:
                        start_idx = full_route.index(start_station)
                        end_idx = full_route.index(end_station)
                        
                        if start_idx <= end_idx:
                            # Forward direction
                            route = full_route[start_idx:end_idx+1]
                        else:
                            # Reverse direction
                            route = full_route[end_idx:start_idx+1][::-1]
                    else:
                        messagebox.showerror("Errore", "Stazioni non trovate nella linea")
                        return
                else:
                    messagebox.showinfo("Info", "Percorso personalizzato non ancora implementato")
                    return
                
                # Parse departure time
                time_str = time_entry.get().strip()
                hour, minute = map(int, time_str.split(':'))
                start_time = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                # Parse arrival time (if specified)
                target_arrival_time = None
                arrival_str = arrival_time_entry.get().strip()
                if arrival_str:
                    try:
                        arr_hour, arr_minute = map(int, arrival_str.split(':'))
                        target_arrival_time = datetime.now().replace(hour=arr_hour, minute=arr_minute, second=0, microsecond=0)
                        # Handle case where arrival is next day
                        if target_arrival_time <= start_time:
                            target_arrival_time += timedelta(days=1)
                    except:
                        messagebox.showwarning("Attenzione", "Formato ora arrivo non valido, verrà ignorato")
                
                # Create schedule - generate ID if empty
                schedule_id_input = schedule_id_entry.get().strip()
                if not schedule_id_input:
                    # Generate unique schedule ID automatically
                    schedule_id_input = f"SCH_{train.id}_{int(start_time.timestamp())}"
                
                schedule = ScheduleBuilder.create_schedule(
                    schedule_id=schedule_id_input,
                    train=train,
                    route=route,
                    network=self.network,
                    start_time=start_time,
                    stop_duration_minutes=int(dwell_entry.get()),
                    target_arrival_time=target_arrival_time
                )
                
                if schedule:
                    self.schedules.append(schedule)
                    # Auto-assign platforms after adding train
                    self.auto_assign_all_platforms()
                    self.update_all_displays()
                    self.update_status(f"Treno '{train.name}' aggiunto")
                    dialog.destroy()
                else:
                    messagebox.showerror("Errore", "Impossibile creare l'orario")
                    
            except Exception as e:
                messagebox.showerror("Errore", f"Errore:\n{str(e)}")
        
        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=11, column=0, columnspan=2, pady=20)
        ttk.Button(btn_frame, text="Salva", command=save_train).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Annulla", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def add_train_series_dialog(self):
        """Show dialog to add multiple trains with regular intervals (cadenced service)."""
        if len(self.network.nodes) < 2:
            messagebox.showwarning("Attenzione", "Servono almeno 2 stazioni per creare treni")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Serie di Treni Cadenzati")
        dialog.geometry("550x680")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Info section
        info_frame = ttk.LabelFrame(dialog, text="ℹ️ Informazioni", padding=10)
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Label(info_frame, text="Crea una serie di treni con orari cadenzati\n(es. treni ogni 15 minuti dalle 6:00 alle 22:00)", 
                 font=('TkDefaultFont', 9, 'italic')).pack()
        
        # Train template info
        template_frame = ttk.LabelFrame(dialog, text="🚂 Modello Treno", padding=10)
        template_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(template_frame, text="Prefisso ID:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        train_prefix_entry = ttk.Entry(template_frame, width=20)
        train_prefix_entry.insert(0, "REG")
        train_prefix_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Label(template_frame, text="(es. REG → REG001, REG002, ...)", 
                 font=('TkDefaultFont', 8, 'italic')).grid(row=0, column=2, sticky=tk.W, padx=5)
        
        ttk.Label(template_frame, text="Nome Treno:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        train_name_entry = ttk.Entry(template_frame, width=20)
        train_name_entry.insert(0, "Regionale")
        train_name_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Label(template_frame, text="(+ progressivo)", 
                 font=('TkDefaultFont', 8, 'italic')).grid(row=1, column=2, sticky=tk.W, padx=5)
        
        ttk.Label(template_frame, text="Tipo Treno:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        train_type_var = tk.StringVar(value="REGIONAL")
        train_type_combo = ttk.Combobox(template_frame, textvariable=train_type_var, width=18, state='readonly',
                                        values=["HIGH_SPEED", "INTERCITY", "REGIONAL", "FREIGHT", "LOCAL"])
        train_type_combo.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Route selection
        route_frame = ttk.LabelFrame(dialog, text="🛤️ Percorso", padding=10)
        route_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(route_frame, text="Linea:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        line_var = tk.StringVar()
        line_names = [f"{lid}: {line.name}" for lid, line in self.lines.items()]
        if not line_names:
            line_names = ["Nessuna linea disponibile"]
        line_combo = ttk.Combobox(route_frame, textvariable=line_var, width=35, values=line_names, state='readonly')
        line_combo.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(route_frame, text="Da:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        start_station_var = tk.StringVar()
        start_station_combo = ttk.Combobox(route_frame, textvariable=start_station_var, width=35, state='disabled')
        start_station_combo.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(route_frame, text="A:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        end_station_var = tk.StringVar()
        end_station_combo = ttk.Combobox(route_frame, textvariable=end_station_var, width=35, state='disabled')
        end_station_combo.grid(row=2, column=1, padx=5, pady=5)
        
        def on_line_selected(event=None):
            """Update start/end station options when line is selected."""
            selected = line_var.get()
            if selected and ':' in selected:
                line_id = selected.split(':')[0].strip()
                if line_id in self.lines:
                    line_route = self.lines[line_id].route
                    start_station_combo['values'] = line_route
                    end_station_combo['values'] = line_route
                    start_station_combo['state'] = 'readonly'
                    end_station_combo['state'] = 'readonly'
                    if line_route:
                        start_station_var.set(line_route[0])
                        end_station_var.set(line_route[-1])
        
        line_combo.bind('<<ComboboxSelected>>', on_line_selected)
        
        # Time series settings
        series_frame = ttk.LabelFrame(dialog, text="⏰ Cadenzamento", padding=10)
        series_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(series_frame, text="Ora Inizio:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        start_time_frame = ttk.Frame(series_frame)
        start_time_frame.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        start_hour_var = tk.StringVar(value="06")
        start_min_var = tk.StringVar(value="00")
        ttk.Spinbox(start_time_frame, from_=0, to=23, width=4, textvariable=start_hour_var, format="%02.0f").pack(side=tk.LEFT)
        ttk.Label(start_time_frame, text=":").pack(side=tk.LEFT)
        ttk.Spinbox(start_time_frame, from_=0, to=59, width=4, textvariable=start_min_var, format="%02.0f").pack(side=tk.LEFT)
        
        ttk.Label(series_frame, text="Ora Fine:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        end_time_frame = ttk.Frame(series_frame)
        end_time_frame.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        end_hour_var = tk.StringVar(value="22")
        end_min_var = tk.StringVar(value="00")
        ttk.Spinbox(end_time_frame, from_=0, to=23, width=4, textvariable=end_hour_var, format="%02.0f").pack(side=tk.LEFT)
        ttk.Label(end_time_frame, text=":").pack(side=tk.LEFT)
        ttk.Spinbox(end_time_frame, from_=0, to=59, width=4, textvariable=end_min_var, format="%02.0f").pack(side=tk.LEFT)
        
        ttk.Label(series_frame, text="Intervallo (min):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        interval_var = tk.StringVar(value="15")
        ttk.Spinbox(series_frame, from_=1, to=240, width=10, textvariable=interval_var).grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(series_frame, text="Sosta (min):").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        dwell_var = tk.StringVar(value="3")
        ttk.Spinbox(series_frame, from_=0, to=30, width=10, textvariable=dwell_var).grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Preview
        preview_frame = ttk.LabelFrame(dialog, text="👁️ Anteprima", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        preview_text = tk.Text(preview_frame, height=8, width=60, state='disabled', font=('Courier', 9))
        preview_scroll = ttk.Scrollbar(preview_frame, orient="vertical", command=preview_text.yview)
        preview_text.configure(yscrollcommand=preview_scroll.set)
        preview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        preview_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        def update_preview(*args):
            """Update preview of trains to be created."""
            try:
                from datetime import datetime, timedelta
                
                start_h = int(start_hour_var.get())
                start_m = int(start_min_var.get())
                end_h = int(end_hour_var.get())
                end_m = int(end_min_var.get())
                interval = int(interval_var.get())
                prefix = train_prefix_entry.get().strip()
                
                start_time = datetime.now().replace(hour=start_h, minute=start_m, second=0, microsecond=0)
                end_time = datetime.now().replace(hour=end_h, minute=end_m, second=0, microsecond=0)
                
                preview_text.config(state='normal')
                preview_text.delete('1.0', tk.END)
                
                count = 0
                current_time = start_time
                while current_time <= end_time:
                    count += 1
                    train_id = f"{prefix}{count:03d}"
                    time_str = current_time.strftime("%H:%M")
                    preview_text.insert(tk.END, f"{train_id:12s} - Partenza: {time_str}\n")
                    current_time += timedelta(minutes=interval)
                
                preview_text.insert(tk.END, f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
                preview_text.insert(tk.END, f"Totale: {count} treni\n")
                preview_text.config(state='disabled')
                
            except Exception as e:
                preview_text.config(state='normal')
                preview_text.delete('1.0', tk.END)
                preview_text.insert(tk.END, f"Errore: {str(e)}")
                preview_text.config(state='disabled')
        
        # Bind updates to preview
        start_hour_var.trace_add('write', update_preview)
        start_min_var.trace_add('write', update_preview)
        end_hour_var.trace_add('write', update_preview)
        end_min_var.trace_add('write', update_preview)
        interval_var.trace_add('write', update_preview)
        train_prefix_entry.bind('<KeyRelease>', update_preview)
        
        # Initial preview
        update_preview()
        
        def create_series():
            """Create the series of trains."""
            try:
                from datetime import datetime, timedelta
                
                # Validate line selection
                selected = line_var.get()
                if not selected or ':' not in selected:
                    messagebox.showerror("Errore", "Selezionare una linea")
                    return
                
                line_id = selected.split(':')[0].strip()
                if line_id not in self.lines:
                    messagebox.showerror("Errore", "Linea non trovata")
                    return
                
                full_route = self.lines[line_id].route
                start_station = start_station_var.get()
                end_station = end_station_var.get()
                
                if not start_station or not end_station:
                    messagebox.showerror("Errore", "Selezionare stazioni di partenza e arrivo")
                    return
                
                # Extract sub-route
                if start_station in full_route and end_station in full_route:
                    start_idx = full_route.index(start_station)
                    end_idx = full_route.index(end_station)
                    
                    if start_idx <= end_idx:
                        route = full_route[start_idx:end_idx+1]
                    else:
                        route = full_route[end_idx:start_idx+1][::-1]
                else:
                    messagebox.showerror("Errore", "Stazioni non trovate nella linea")
                    return
                
                # Parse parameters
                start_h = int(start_hour_var.get())
                start_m = int(start_min_var.get())
                end_h = int(end_hour_var.get())
                end_m = int(end_min_var.get())
                interval = int(interval_var.get())
                dwell = int(dwell_var.get())
                prefix = train_prefix_entry.get().strip()
                name_base = train_name_entry.get().strip()
                train_type = TrainType[train_type_var.get()]
                
                start_time = datetime.now().replace(hour=start_h, minute=start_m, second=0, microsecond=0)
                end_time = datetime.now().replace(hour=end_h, minute=end_m, second=0, microsecond=0)
                
                # Create trains
                created_count = 0
                current_time = start_time
                count = 1
                
                while current_time <= end_time:
                    train_id = f"{prefix}{count:03d}"
                    train_name = f"{name_base}{count:03d}"
                    
                    # Create train
                    train = Train(
                        train_id=train_id,
                        name=train_name,
                        train_type=train_type
                    )
                    
                    # Create schedule
                    schedule_id = f"SCH_{train_id}"
                    schedule = ScheduleBuilder.create_schedule(
                        schedule_id=schedule_id,
                        train=train,
                        route=route,
                        network=self.network,
                        start_time=current_time,
                        stop_duration_minutes=dwell
                    )
                    
                    if schedule:
                        self.schedules.append(schedule)
                        created_count += 1
                    
                    current_time += timedelta(minutes=interval)
                    count += 1
                
                # Update displays
                self.update_all_displays()
                self.update_status(f"{created_count} treni creati")
                messagebox.showinfo("Successo", 
                                   f"Serie di treni creata con successo!\n\n"
                                   f"Treni creati: {created_count}\n"
                                   f"Intervallo: {interval} minuti\n"
                                   f"Orario: {start_h:02d}:{start_m:02d} - {end_h:02d}:{end_m:02d}")
                dialog.destroy()
                
            except Exception as e:
                messagebox.showerror("Errore", f"Errore nella creazione:\n{str(e)}")
        
        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="✅ Crea Serie", command=create_series, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="❌ Annulla", command=dialog.destroy, width=15).pack(side=tk.LEFT, padx=5)
    
    def manage_lines_dialog(self):
        """Switch to lines tab."""
        self.notebook.select(1)
    
    def manage_schedules_dialog(self):
        """Switch to trains tab."""
        self.notebook.select(2)
    
    # ========================================================================
    # EDIT/DELETE OPERATIONS
    # ========================================================================
    
    def edit_station(self):
        """Edit selected station."""
        selection = self.stations_tree.selection()
        if not selection:
            messagebox.showwarning("Attenzione", "Selezionare una stazione da modificare")
            return
        
        item = self.stations_tree.item(selection[0])
        node_id = item['text'].split(' / ')[0]
        node = self.network.get_node(node_id)
        
        if not node:
            messagebox.showerror("Errore", "Stazione non trovata")
            return
        
        # Create edit dialog
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Modifica Stazione: {node_id}")
        dialog.geometry("400x350")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Form fields pre-filled with current values
        ttk.Label(dialog, text="ID Stazione:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        id_label = ttk.Label(dialog, text=node_id, font=('TkDefaultFont', 10, 'bold'))
        id_label.grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)
        
        ttk.Label(dialog, text="Nome:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        name_entry = ttk.Entry(dialog, width=30)
        name_entry.insert(0, node.name)
        name_entry.grid(row=1, column=1, padx=10, pady=5)
        
        ttk.Label(dialog, text="Tipo:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        type_var = tk.StringVar(value=node.node_type.value.upper())
        type_combo = ttk.Combobox(dialog, textvariable=type_var, width=28,
                                  values=["STATION", "INTERCHANGE", "DEPOT"])
        type_combo.grid(row=2, column=1, padx=10, pady=5)
        
        ttk.Label(dialog, text="Latitudine:").grid(row=3, column=0, sticky=tk.W, padx=10, pady=5)
        lat_entry = ttk.Entry(dialog, width=30)
        lat_entry.insert(0, str(node.latitude))
        lat_entry.grid(row=3, column=1, padx=10, pady=5)
        
        ttk.Label(dialog, text="Longitudine:").grid(row=4, column=0, sticky=tk.W, padx=10, pady=5)
        lon_entry = ttk.Entry(dialog, width=30)
        lon_entry.insert(0, str(node.longitude))
        lon_entry.grid(row=4, column=1, padx=10, pady=5)
        
        ttk.Label(dialog, text="Capacità:").grid(row=5, column=0, sticky=tk.W, padx=10, pady=5)
        capacity_entry = ttk.Entry(dialog, width=30)
        capacity_entry.insert(0, str(node.capacity))
        capacity_entry.grid(row=5, column=1, padx=10, pady=5)
        
        ttk.Label(dialog, text="Binari:").grid(row=6, column=0, sticky=tk.W, padx=10, pady=5)
        platforms_entry = ttk.Entry(dialog, width=30)
        platforms_entry.insert(0, str(node.platforms))
        platforms_entry.grid(row=6, column=1, padx=10, pady=5)
        
        def save_changes():
            try:
                # Update node properties
                node.name = name_entry.get().strip()
                
                type_str = type_var.get().upper()
                if type_str == 'STATION':
                    node.node_type = NodeType.STATION
                elif type_str == 'INTERCHANGE':
                    node.node_type = NodeType.INTERCHANGE
                elif type_str == 'DEPOT':
                    node.node_type = NodeType.DEPOT
                
                node.latitude = float(lat_entry.get())
                node.longitude = float(lon_entry.get())
                node.capacity = int(capacity_entry.get())
                node.platforms = int(platforms_entry.get())
                
                self.update_all_displays()
                self.update_status(f"Stazione '{node_id}' modificata")
                dialog.destroy()
                
            except ValueError as e:
                messagebox.showerror("Errore", f"Valori non validi:\n{str(e)}")
        
        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=7, column=0, columnspan=2, pady=20)
        ttk.Button(btn_frame, text="Salva", command=save_changes).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Annulla", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def delete_station(self):
        """Delete selected station."""
        selection = self.stations_tree.selection()
        if not selection:
            messagebox.showwarning("Attenzione", "Selezionare una stazione da eliminare")
            return
        
        item = self.stations_tree.item(selection[0])
        node_id = item['text'].split(' / ')[0]
        
        if messagebox.askyesno("Conferma", f"Eliminare la stazione '{node_id}'?"):
            self.network.remove_node(node_id)
            self.update_all_displays()
            self.update_status(f"Stazione '{node_id}' eliminata")
    
    def edit_connection(self):
        """Edit selected connection."""
        selection = self.connections_tree.selection()
        if not selection:
            messagebox.showwarning("Attenzione", "Selezionare una connessione da modificare")
            return
        
        item = self.connections_tree.item(selection[0])
        from_node = item['values'][0]
        to_node = item['values'][1]
        
        # Find the edge
        edge = None
        for e in self.network.edges:
            if e.from_node == from_node and e.to_node == to_node:
                edge = e
                break
        
        if not edge:
            messagebox.showerror("Errore", "Connessione non trovata")
            return
        
        # Create edit dialog
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Modifica Connessione: {from_node} → {to_node}")
        dialog.geometry("400x250")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Form fields
        ttk.Label(dialog, text="Da:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        from_label = ttk.Label(dialog, text=from_node, font=('TkDefaultFont', 10, 'bold'))
        from_label.grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)
        
        ttk.Label(dialog, text="A:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        to_label = ttk.Label(dialog, text=to_node, font=('TkDefaultFont', 10, 'bold'))
        to_label.grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)
        
        ttk.Label(dialog, text="Distanza (km):").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        distance_entry = ttk.Entry(dialog, width=30)
        distance_entry.insert(0, str(edge.distance))
        distance_entry.grid(row=2, column=1, padx=10, pady=5)
        
        ttk.Label(dialog, text="Tipo Binario:").grid(row=3, column=0, sticky=tk.W, padx=10, pady=5)
        track_var = tk.StringVar(value=edge.track_type.value.upper())
        track_combo = ttk.Combobox(dialog, textvariable=track_var, width=28,
                                   values=["SINGLE", "DOUBLE"])
        track_combo.grid(row=3, column=1, padx=10, pady=5)
        
        ttk.Label(dialog, text="Velocità Max (km/h):").grid(row=4, column=0, sticky=tk.W, padx=10, pady=5)
        speed_entry = ttk.Entry(dialog, width=30)
        speed_entry.insert(0, str(edge.max_speed))
        speed_entry.grid(row=4, column=1, padx=10, pady=5)
        
        def save_changes():
            try:
                # Update edge properties
                edge.distance = float(distance_entry.get())
                edge.max_speed = float(speed_entry.get())
                
                track_str = track_var.get().upper()
                if track_str == 'SINGLE':
                    edge.track_type = TrackType.SINGLE
                    edge.capacity = 1
                elif track_str == 'DOUBLE':
                    edge.track_type = TrackType.DOUBLE
                    edge.capacity = 2
                
                self.update_all_displays()
                self.update_status(f"Connessione {from_node} → {to_node} modificata")
                dialog.destroy()
                
            except ValueError as e:
                messagebox.showerror("Errore", f"Valori non validi:\n{str(e)}")
        
        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=20)
        ttk.Button(btn_frame, text="Salva", command=save_changes).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Annulla", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def delete_connection(self):
        """Delete selected connection."""
        selection = self.connections_tree.selection()
        if not selection:
            messagebox.showwarning("Attenzione", "Selezionare una connessione da eliminare")
            return
        
        item = self.connections_tree.item(selection[0])
        from_node = item['values'][0]
        to_node = item['values'][1]
        
        if messagebox.askyesno("Conferma", f"Eliminare la connessione {from_node} → {to_node}?"):
            # Find and remove edge
            for edge in self.network.edges:
                if edge.from_node == from_node and edge.to_node == to_node:
                    self.network.remove_edge(from_node, to_node)
                    break
            self.update_all_displays()
            self.update_status("Connessione eliminata")
    
    def edit_line(self):
        """Edit selected line."""
        selection = self.lines_tree.selection()
        if not selection:
            messagebox.showwarning("Attenzione", "Selezionare una linea da modificare")
            return
        
        item = self.lines_tree.item(selection[0])
        line_id = item['text']
        
        if line_id not in self.lines:
            messagebox.showerror("Errore", "Linea non trovata")
            return
        
        line = self.lines[line_id]
        
        # Create edit dialog
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Modifica Linea: {line_id}")
        dialog.geometry("500x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Form fields
        ttk.Label(dialog, text="ID Linea:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        id_label = ttk.Label(dialog, text=line_id, font=('TkDefaultFont', 10, 'bold'))
        id_label.grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)
        
        ttk.Label(dialog, text="Nome:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        name_entry = ttk.Entry(dialog, width=30)
        name_entry.insert(0, line.name)
        name_entry.grid(row=1, column=1, padx=10, pady=5)
        
        # Color picker
        ttk.Label(dialog, text="Colore:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        color_frame = ttk.Frame(dialog)
        color_frame.grid(row=2, column=1, sticky=tk.W, padx=10, pady=5)
        
        color_var = tk.StringVar(value=line.color)
        color_entry = ttk.Entry(color_frame, textvariable=color_var, width=10)
        color_entry.pack(side=tk.LEFT)
        
        def choose_color():
            color = colorchooser.askcolor(title="Scegli Colore", initialcolor=line.color)[1]
            if color:
                color_var.set(color)
        
        ttk.Button(color_frame, text="Scegli...", command=choose_color).pack(side=tk.LEFT, padx=5)
        
        # Station selection
        ttk.Label(dialog, text="Percorso (stazioni):").grid(row=3, column=0, sticky=tk.NW, padx=10, pady=5)
        
        route_frame = ttk.Frame(dialog)
        route_frame.grid(row=3, column=1, sticky=tk.NSEW, padx=10, pady=5)
        
        route_listbox = tk.Listbox(route_frame, height=10, width=40)
        route_scrollbar = ttk.Scrollbar(route_frame, orient=tk.VERTICAL, command=route_listbox.yview)
        route_listbox.configure(yscrollcommand=route_scrollbar.set)
        route_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        route_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Pre-fill with current route
        for station_id in line.route:
            route_listbox.insert(tk.END, station_id)
        
        # Available stations (sorted alphabetically)
        station_ids = sorted(self.network.nodes.keys())
        
        def add_station_to_route():
            AddStationDialog(dialog, station_ids, route_listbox)
        
        def remove_from_route():
            selection = route_listbox.curselection()
            if selection:
                route_listbox.delete(selection)
        
        def move_up():
            selection = route_listbox.curselection()
            if selection and selection[0] > 0:
                idx = selection[0]
                item = route_listbox.get(idx)
                route_listbox.delete(idx)
                route_listbox.insert(idx - 1, item)
                route_listbox.selection_set(idx - 1)
        
        def move_down():
            selection = route_listbox.curselection()
            if selection and selection[0] < route_listbox.size() - 1:
                idx = selection[0]
                item = route_listbox.get(idx)
                route_listbox.delete(idx)
                route_listbox.insert(idx + 1, item)
                route_listbox.selection_set(idx + 1)
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=4, column=1, sticky=tk.W, padx=10, pady=5)
        ttk.Button(btn_frame, text="➕ Aggiungi", command=add_station_to_route).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="➖ Rimuovi", command=remove_from_route).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="⬆️ Su", command=move_up).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="⬇️ Giù", command=move_down).pack(side=tk.LEFT, padx=2)
        
        def save_changes():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("Errore", "Il nome della linea è obbligatorio")
                return
            
            route = list(route_listbox.get(0, tk.END))
            if len(route) < 2:
                messagebox.showerror("Errore", "La linea deve avere almeno 2 stazioni")
                return
            
            # Update line
            line.name = name
            line.color = color_var.get()
            line.route = route
            
            self.update_all_displays()
            self.update_status(f"Linea '{line_id}' modificata")
            dialog.destroy()
        
        # Save/Cancel buttons
        save_frame = ttk.Frame(dialog)
        save_frame.grid(row=5, column=0, columnspan=2, pady=20)
        ttk.Button(save_frame, text="Salva", command=save_changes).pack(side=tk.LEFT, padx=5)
        ttk.Button(save_frame, text="Annulla", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def delete_line(self):
        """Delete selected line."""
        selection = self.lines_tree.selection()
        if not selection:
            messagebox.showwarning("Attenzione", "Selezionare una linea da eliminare")
            return
        
        item = self.lines_tree.item(selection[0])
        line_id = item['text']
        
        if messagebox.askyesno("Conferma", f"Eliminare la linea '{line_id}'?"):
            del self.lines[line_id]
            self.update_all_displays()
            self.update_status(f"Linea '{line_id}' eliminata")
    
    def edit_schedule(self):
        """Show train schedule info (read-only view with click-to-edit rows)."""
        selection = self.trains_tree.selection()
        if not selection:
            messagebox.showwarning("Attenzione", "Selezionare un treno da visualizzare")
            return
        
        item = self.trains_tree.item(selection[0])
        schedule_id = item['text']
        
        # Find schedule
        schedule = None
        for s in self.schedules:
            if s.schedule_id == schedule_id:
                schedule = s
                break
        
        if not schedule:
            messagebox.showerror("Errore", "Orario non trovato")
            return
        
        # Create info dialog - LARGER SIZE for better visibility
        dialog = tk.Toplevel(self.root)
        dialog.title(f"📋 Info Treno: {schedule.train.name}")
        dialog.geometry("800x600")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Main container
        main_frame = ttk.Frame(dialog, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ═══════════════════════════════════════════════════════════════
        # SEZIONE 1: INFORMAZIONI TRENO (READ-ONLY)
        # ═══════════════════════════════════════════════════════════════
        info_frame = ttk.LabelFrame(main_frame, text="⚙️ Informazioni Treno", padding=10)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        first_stop = schedule.stops[0]
        last_stop = schedule.stops[-1]
        origin_name = self.network.nodes[first_stop.node_id].name if first_stop.node_id in self.network.nodes else first_stop.node_id
        dest_name = self.network.nodes[last_stop.node_id].name if last_stop.node_id in self.network.nodes else last_stop.node_id
        
        info_text = f"""
        🚂 Treno: {schedule.train.name}
        📍 Percorso: {origin_name} → {dest_name}
        🏷️ Tipo: {schedule.train.train_type.value}
        ⚡ Velocità max: {schedule.train.max_speed} km/h
        🎯 Priorità: {schedule.priority}
        🕐 Partenza: {first_stop.departure_time.strftime('%H:%M')}
        🏁 Arrivo: {last_stop.arrival_time.strftime('%H:%M') if last_stop.arrival_time else '--:--'}
        """
        
        info_label = ttk.Label(info_frame, text=info_text, font=('TkDefaultFont', 10))
        info_label.pack(anchor=tk.W)
        
        # ═══════════════════════════════════════════════════════════════
        # SEZIONE 2: ORARIO DETTAGLIATO (READ-ONLY + CLICKABLE)
        # ═══════════════════════════════════════════════════════════════
        schedule_frame = ttk.LabelFrame(main_frame, text="🛤️ Orario Dettagliato (Doppio click su riga per modificare)", padding=10)
        schedule_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create Treeview for schedule
        columns = ('station', 'arrival', 'departure', 'dwell', 'platform')
        tree = ttk.Treeview(schedule_frame, columns=columns, show='headings', height=15)
        
        tree.heading('station', text='Stazione')
        tree.heading('arrival', text='Arrivo')
        tree.heading('departure', text='Partenza')
        tree.heading('dwell', text='Sosta (min)')
        tree.heading('platform', text='Binario')
        
        tree.column('station', width=250, anchor=tk.W)
        tree.column('arrival', width=100, anchor=tk.CENTER)
        tree.column('departure', width=100, anchor=tk.CENTER)
        tree.column('dwell', width=100, anchor=tk.CENTER)
        tree.column('platform', width=100, anchor=tk.CENTER)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(schedule_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate treeview
        for idx, stop in enumerate(schedule.stops):
            station_name = self.network.nodes[stop.node_id].name if stop.node_id in self.network.nodes else stop.node_id
            arrival_str = stop.arrival_time.strftime('%H:%M') if stop.arrival_time else '--:--'
            departure_str = stop.departure_time.strftime('%H:%M') if stop.departure_time else '--:--'
            dwell_str = str(stop.stop_duration)
            platform_str = str(stop.platform) if stop.platform else '1'
            
            tree.insert('', tk.END, iid=str(idx), values=(station_name, arrival_str, departure_str, dwell_str, platform_str))
        
        # ═══════════════════════════════════════════════════════════════
        # FUNZIONE: MODIFICA SINGOLA FERMATA
        # ═══════════════════════════════════════════════════════════════
        def edit_single_stop(event):
            """Edit single stop when clicking on row."""
            selected = tree.selection()
            if not selected:
                return
            
            stop_idx = int(selected[0])
            stop = schedule.stops[stop_idx]
            station_name = self.network.nodes[stop.node_id].name if stop.node_id in self.network.nodes else stop.node_id
            
            # Create edit popup
            edit_dialog = tk.Toplevel(dialog)
            edit_dialog.title(f"✏️ Modifica Fermata: {station_name}")
            edit_dialog.geometry("500x520")
            edit_dialog.transient(dialog)
            edit_dialog.grab_set()
            
            edit_frame = ttk.Frame(edit_dialog, padding=15)
            edit_frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(edit_frame, text=f"🚉 Stazione: {station_name}", font=('TkDefaultFont', 11, 'bold')).pack(pady=(0, 15))
            
            # Arrival time
            arrival_frame = ttk.LabelFrame(edit_frame, text="⏰ Orario Arrivo", padding=10)
            arrival_frame.pack(fill=tk.X, pady=5)
            
            if stop.arrival_time:
                arr_time_frame = ttk.Frame(arrival_frame)
                arr_time_frame.pack()
                
                ttk.Label(arr_time_frame, text="Ore:").pack(side=tk.LEFT, padx=5)
                arr_hour_var = tk.StringVar(value=f"{stop.arrival_time.hour:02d}")
                arr_hour = ttk.Spinbox(arr_time_frame, from_=0, to=23, width=5, textvariable=arr_hour_var, format="%02.0f")
                arr_hour.pack(side=tk.LEFT, padx=5)
                
                ttk.Label(arr_time_frame, text="Minuti:").pack(side=tk.LEFT, padx=5)
                arr_min_var = tk.StringVar(value=f"{stop.arrival_time.minute:02d}")
                arr_min = ttk.Spinbox(arr_time_frame, from_=0, to=59, width=5, textvariable=arr_min_var, format="%02.0f")
                arr_min.pack(side=tk.LEFT, padx=5)
            else:
                ttk.Label(arrival_frame, text="(Prima stazione - nessun arrivo)", font=('TkDefaultFont', 9, 'italic')).pack()
                arr_hour_var = None
                arr_min_var = None
            
            # Departure time
            departure_frame = ttk.LabelFrame(edit_frame, text="🚀 Orario Partenza", padding=10)
            departure_frame.pack(fill=tk.X, pady=5)
            
            if stop.departure_time:
                dep_time_frame = ttk.Frame(departure_frame)
                dep_time_frame.pack()
                
                ttk.Label(dep_time_frame, text="Ore:").pack(side=tk.LEFT, padx=5)
                dep_hour_var = tk.StringVar(value=f"{stop.departure_time.hour:02d}")
                dep_hour = ttk.Spinbox(dep_time_frame, from_=0, to=23, width=5, textvariable=dep_hour_var, format="%02.0f")
                dep_hour.pack(side=tk.LEFT, padx=5)
                
                ttk.Label(dep_time_frame, text="Minuti:").pack(side=tk.LEFT, padx=5)
                dep_min_var = tk.StringVar(value=f"{stop.departure_time.minute:02d}")
                dep_min = ttk.Spinbox(dep_time_frame, from_=0, to=59, width=5, textvariable=dep_min_var, format="%02.0f")
                dep_min.pack(side=tk.LEFT, padx=5)
            else:
                ttk.Label(departure_frame, text="(Ultima stazione - nessuna partenza)", font=('TkDefaultFont', 9, 'italic')).pack()
                dep_hour_var = None
                dep_min_var = None
            
            # Stop duration
            dwell_frame = ttk.LabelFrame(edit_frame, text="⏱️ Tempo di Sosta", padding=10)
            dwell_frame.pack(fill=tk.X, pady=5)
            
            dwell_time_frame = ttk.Frame(dwell_frame)
            dwell_time_frame.pack()
            
            ttk.Label(dwell_time_frame, text="Minuti:").pack(side=tk.LEFT, padx=5)
            dwell_var = tk.StringVar(value=str(stop.stop_duration))
            dwell_spin = ttk.Spinbox(dwell_time_frame, from_=0, to=120, width=10, textvariable=dwell_var)
            dwell_spin.pack(side=tk.LEFT, padx=5)
            
            # Platform
            platform_frame = ttk.LabelFrame(edit_frame, text="🛤️ Binario", padding=10)
            platform_frame.pack(fill=tk.X, pady=5)
            
            platform_time_frame = ttk.Frame(platform_frame)
            platform_time_frame.pack()
            
            ttk.Label(platform_time_frame, text="Numero:").pack(side=tk.LEFT, padx=5)
            platform_var = tk.StringVar(value=str(stop.platform) if stop.platform else '1')
            platform_spin = ttk.Spinbox(platform_time_frame, from_=1, to=20, width=10, textvariable=platform_var)
            platform_spin.pack(side=tk.LEFT, padx=5)
            
            def save_stop_changes():
                """Save changes to this stop and recalculate subsequent or previous stops."""
                try:
                    # Salva i valori originali per confronto
                    old_arrival = stop.arrival_time
                    old_departure = stop.departure_time
                    old_dwell = stop.stop_duration
                    
                    # Update arrival
                    if arr_hour_var and arr_min_var:
                        stop.arrival_time = stop.arrival_time.replace(
                            hour=int(arr_hour_var.get()),
                            minute=int(arr_min_var.get())
                        )
                    
                    # Update departure
                    if dep_hour_var and dep_min_var:
                        stop.departure_time = stop.departure_time.replace(
                            hour=int(dep_hour_var.get()),
                            minute=int(dep_min_var.get())
                        )
                    
                    # Update dwell time
                    new_dwell = int(dwell_var.get())
                    stop.stop_duration = new_dwell
                    
                    # Se la sosta è cambiata E c'è sia arrivo che partenza,
                    # aggiorna la partenza = arrivo + sosta
                    if old_dwell != new_dwell and stop.arrival_time and stop.departure_time:
                        from datetime import timedelta
                        stop.departure_time = stop.arrival_time + timedelta(minutes=new_dwell)
                    
                    # Update platform
                    stop.platform = int(platform_var.get())
                    
                    # Verifica se QUALCHE orario è stato modificato e ricalcola AUTOMATICAMENTE
                    time_changed = (old_arrival != stop.arrival_time or 
                                  old_departure != stop.departure_time or 
                                  old_dwell != new_dwell)
                    
                    recalc_backward = False
                    recalc_forward = False
                    
                    # Ricalcolo AUTOMATICO senza conferma utente
                    if time_changed:
                        # Determina la direzione del ricalcolo automatico
                        can_recalc_backward = stop_idx > 0  # Non è la prima fermata
                        can_recalc_forward = stop_idx < len(schedule.stops) - 1  # Non è l'ultima fermata
                        
                        # LOGICA AUTOMATICA:
                        # - Se arrivo è cambiato → ricalcola all'INDIETRO
                        # - Altrimenti (partenza o sosta cambiati) → ricalcola in AVANTI
                        if old_arrival != stop.arrival_time and can_recalc_backward:
                            # Arrivo modificato → ricalcola precedenti
                            recalc_backward = True
                        elif (old_departure != stop.departure_time or old_dwell != new_dwell) and can_recalc_forward:
                            # Partenza o sosta modificata → ricalcola successivi
                            recalc_forward = True
                    
                    # Esegui ricalcolo all'INDIETRO se richiesto
                    if recalc_backward and stop_idx > 0:
                        from datetime import timedelta
                        
                        # Partendo dall'arrivo desiderato, calcola a ritroso
                        target_arrival = stop.arrival_time
                        
                        for i in range(stop_idx - 1, -1, -1):  # Da stop_idx-1 a 0 (indietro)
                            curr_stop = schedule.stops[i]
                            next_stop = schedule.stops[i+1]
                            
                            # Calcola distanza tra stazioni
                            try:
                                path = nx.shortest_path(self.network.graph, 
                                                      curr_stop.node_id, 
                                                      next_stop.node_id,
                                                      weight='distance')
                                distance_km = sum(self.network.graph[path[j]][path[j+1]]['distance'] 
                                                for j in range(len(path)-1))
                                
                                # Ottieni velocità massima del percorso
                                max_speed = min(self.network.graph[path[j]][path[j+1]].get('max_speed', 200) 
                                              for j in range(len(path)-1))
                            except:
                                distance_km = 0
                                max_speed = 200
                            
                            # Calcola tempo di viaggio usando la funzione corretta
                            if distance_km > 0:
                                travel_details = schedule.train.calculate_travel_time(
                                    distance_km,
                                    max_speed,
                                    stop_at_end=True
                                )
                                # calculate_travel_time ritorna il tempo in SECONDI, convertilo in ore
                                travel_time_hours = travel_details['total_time'] / 3600.0
                            else:
                                travel_time_hours = 0
                            
                            # Calcola a ritroso: partenza = arrivo_successivo - tempo_viaggio
                            next_arrival = next_stop.arrival_time
                            curr_stop.departure_time = next_arrival - timedelta(hours=travel_time_hours)
                            
                            # Calcola arrivo = partenza - sosta (solo se non è la prima)
                            if i > 0:
                                curr_stop.arrival_time = curr_stop.departure_time - timedelta(minutes=curr_stop.stop_duration)
                            else:
                                # Prima fermata: non ha arrivo
                                curr_stop.arrival_time = None
                    
                    # Esegui ricalcolo in AVANTI se richiesto
                    if recalc_forward and stop_idx < len(schedule.stops) - 1:
                        from datetime import timedelta
                        
                        for i in range(stop_idx + 1, len(schedule.stops)):
                            prev_stop = schedule.stops[i-1]
                            curr_stop = schedule.stops[i]
                            
                            # Calcola distanza tra stazioni
                            try:
                                path = nx.shortest_path(self.network.graph, 
                                                      prev_stop.node_id, 
                                                      curr_stop.node_id,
                                                      weight='distance')
                                distance_km = sum(self.network.graph[path[j]][path[j+1]]['distance'] 
                                                for j in range(len(path)-1))
                                
                                # Ottieni velocità massima del percorso
                                max_speed = min(self.network.graph[path[j]][path[j+1]].get('max_speed', 200) 
                                              for j in range(len(path)-1))
                            except:
                                distance_km = 0
                                max_speed = 200
                            
                            # Calcola tempo di viaggio usando la funzione corretta
                            if distance_km > 0:
                                travel_details = schedule.train.calculate_travel_time(
                                    distance_km,
                                    max_speed,
                                    stop_at_end=True
                                )
                                # calculate_travel_time ritorna il tempo in SECONDI, convertilo in ore
                                travel_time_hours = travel_details['total_time'] / 3600.0
                            else:
                                travel_time_hours = 0
                            
                            # Aggiorna orario arrivo
                            departure_base = prev_stop.departure_time if prev_stop.departure_time else prev_stop.arrival_time
                            curr_stop.arrival_time = departure_base + timedelta(hours=travel_time_hours)
                            
                            # Aggiorna orario partenza (solo se non è l'ultima)
                            if i < len(schedule.stops) - 1:
                                curr_stop.departure_time = curr_stop.arrival_time + timedelta(minutes=curr_stop.stop_duration)
                    
                    # Aggiorna treeview per TUTTE le fermate
                    for idx in range(len(schedule.stops)):
                        s = schedule.stops[idx]
                        node_name = self.network.nodes[s.node_id].name if s.node_id in self.network.nodes else s.node_id
                        arrival_str = s.arrival_time.strftime('%H:%M') if s.arrival_time else '--:--'
                        departure_str = s.departure_time.strftime('%H:%M') if s.departure_time else '--:--'
                        tree.item(str(idx), values=(node_name, arrival_str, departure_str, 
                                                   str(s.stop_duration), str(s.platform)))
                    
                    # Mark as modified
                    self.modified = True
                    self.update_all_displays()
                    self.update_status(f"✓ Fermata '{station_name}' modificata")
                    
                    edit_dialog.destroy()
                    
                    # Mostra messaggio appropriato in base al tipo di ricalcolo
                    if recalc_backward or recalc_forward:
                        direction = "precedenti" if recalc_backward else "successivi"
                        messagebox.showinfo("Salvato", 
                                          f"✓ Modifiche salvate!\n\n"
                                          f"📊 Orari {direction} ricalcolati automaticamente\n\n"
                                          "💾 Ricorda di salvare il file: File → Salva (Ctrl+S)")
                    else:
                        messagebox.showinfo("Salvato", 
                                          f"✓ Modifiche alla fermata '{station_name}' salvate!\n\n"
                                          "💾 Ricorda di salvare il file: File → Salva (Ctrl+S)")
                    
                except Exception as e:
                    messagebox.showerror("Errore", f"Errore nel salvataggio:\n{str(e)}")
            
            # Buttons
            btn_frame = ttk.Frame(edit_frame)
            btn_frame.pack(pady=15)
            
            ttk.Button(btn_frame, text="💾 Salva", command=save_stop_changes, width=15).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="❌ Annulla", command=edit_dialog.destroy, width=15).pack(side=tk.LEFT, padx=5)
        
        # Bind double-click to edit
        tree.bind('<Double-Button-1>', edit_single_stop)
        
        # ═══════════════════════════════════════════════════════════════
        # BUTTON: Modifica Proprietà Treno
        # ═══════════════════════════════════════════════════════════════
        def edit_train_properties():
            """Edit train type and priority."""
            prop_dialog = tk.Toplevel(dialog)
            prop_dialog.title(f"⚙️ Proprietà Treno: {schedule.train.name}")
            prop_dialog.geometry("500x350")
            prop_dialog.transient(dialog)
            prop_dialog.grab_set()
            
            prop_frame = ttk.Frame(prop_dialog, padding=15)
            prop_frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(prop_frame, text=f"🚂 Treno: {schedule.train.name}", font=('TkDefaultFont', 11, 'bold')).pack(pady=(0, 15))
            
            # Type
            type_frame = ttk.LabelFrame(prop_frame, text="🏷️ Tipo Treno", padding=10)
            type_frame.pack(fill=tk.X, pady=5)
            
            type_var = tk.StringVar(value=schedule.train.train_type.value)
            type_combo = ttk.Combobox(type_frame, textvariable=type_var, width=25, state='readonly',
                                     values=[t.value for t in TrainType])
            type_combo.pack(pady=5)
            
            # Priority
            priority_frame = ttk.LabelFrame(prop_frame, text="🎯 Priorità", padding=10)
            priority_frame.pack(fill=tk.X, pady=5)
            
            priority_var = tk.StringVar(value=str(schedule.priority))
            priority_spin = ttk.Spinbox(priority_frame, from_=1, to=10, width=25, textvariable=priority_var)
            priority_spin.pack(pady=5)
            
            def save_properties():
                """Save train properties."""
                try:
                    # Update type
                    train_type_str = type_var.get()
                    old_type = schedule.train.train_type.value
                    for tt in TrainType:
                        if tt.value == train_type_str:
                            schedule.train.train_type = tt
                            schedule.train.update_characteristics_from_type(tt)
                            break
                    
                    # Update priority
                    schedule.priority = int(priority_var.get())
                    
                    # Ricalcola orari se il tipo di treno è cambiato (velocità diversa)
                    if old_type != train_type_str:
                        response = messagebox.askyesno(
                            "Ricalcolare Orari?",
                            f"Il tipo di treno è cambiato da '{old_type}' a '{train_type_str}'.\n"
                            f"Velocità massima: {schedule.train.max_speed} km/h\n\n"
                            "Vuoi ricalcolare gli orari con la nuova velocità?"
                        )
                        
                        if response:
                            # Ricalcola tutti gli orari
                            from schedule import ScheduleBuilder
                            start_time = schedule.stops[0].departure_time
                            route = [stop.node_id for stop in schedule.stops]
                            stop_duration = schedule.stops[1].stop_duration if len(schedule.stops) > 1 else 5
                            
                            # Crea nuovo schedule con orari ricalcolati
                            new_schedule = ScheduleBuilder.create_schedule(
                                schedule_id=schedule.schedule_id,
                                train=schedule.train,
                                route=route,
                                network=self.network,
                                start_time=start_time,
                                stop_duration_minutes=stop_duration
                            )
                            
                            if new_schedule:
                                # Aggiorna gli orari
                                for i, stop in enumerate(schedule.stops):
                                    if i < len(new_schedule.stops):
                                        stop.arrival_time = new_schedule.stops[i].arrival_time
                                        stop.departure_time = new_schedule.stops[i].departure_time
                                
                                # Aggiorna la treeview
                                for i, stop in enumerate(schedule.stops):
                                    node_name = self.network.nodes[stop.node_id].name if stop.node_id in self.network.nodes else stop.node_id
                                    arrival_str = stop.arrival_time.strftime('%H:%M') if stop.arrival_time else '--:--'
                                    departure_str = stop.departure_time.strftime('%H:%M') if stop.departure_time else '--:--'
                                    tree.item(str(i), values=(node_name, arrival_str, departure_str, 
                                                            str(stop.stop_duration), str(stop.platform)))
                    
                    # Update info display
                    info_label.config(text=f"""
        🚂 Treno: {schedule.train.name}
        📍 Percorso: {origin_name} → {dest_name}
        🏷️ Tipo: {schedule.train.train_type.value}
        ⚡ Velocità max: {schedule.train.max_speed} km/h
        🎯 Priorità: {schedule.priority}
        🕐 Partenza: {first_stop.departure_time.strftime('%H:%M')}
        🏁 Arrivo: {last_stop.arrival_time.strftime('%H:%M') if last_stop.arrival_time else '--:--'}
        """)
                    
                    self.modified = True
                    self.update_all_displays()
                    self.update_status(f"✓ Proprietà treno '{schedule.train.name}' modificate")
                    
                    prop_dialog.destroy()
                    messagebox.showinfo("Salvato", f"✓ Proprietà treno modificate!\n\n"
                                       f"Tipo: {schedule.train.train_type.value}\n"
                                       f"Velocità: {schedule.train.max_speed} km/h\n"
                                       f"Priorità: {schedule.priority}\n\n"
                                       "💾 Ricorda di salvare il file: File → Salva (Ctrl+S)")
                    
                except Exception as e:
                    messagebox.showerror("Errore", f"Errore nel salvataggio:\n{str(e)}")
            
            btn_frame = ttk.Frame(prop_frame)
            btn_frame.pack(pady=15)
            
            ttk.Button(btn_frame, text="💾 Salva", command=save_properties, width=15).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="❌ Annulla", command=prop_dialog.destroy, width=15).pack(side=tk.LEFT, padx=5)
        
        # ═══════════════════════════════════════════════════════════════
        # BUTTONS FINALI
        # ═══════════════════════════════════════════════════════════════
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(btn_frame, text="⚙️ Modifica Proprietà Treno", command=edit_train_properties, width=25).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="✅ Chiudi", command=dialog.destroy, width=15).pack(side=tk.RIGHT, padx=5)
        
        # Help label
        help_label = ttk.Label(main_frame, 
                              text="💡 Doppio click su una riga per modificare quella fermata",
                              font=('TkDefaultFont', 9, 'italic'),
                              foreground='gray')
        help_label.pack(pady=5)

    def show_trains_context_menu(self, event):
        """Show context menu for trains."""
        # Select item under cursor
        item = self.trains_tree.identify_row(event.y)
        if item:
            self.trains_tree.selection_set(item)
            self.trains_menu.post(event.x_root, event.y_root)
    
    def show_train_diagram(self):
        """Show train diagram (grafico marcia) for selected train with all traffic on same line."""
        selection = self.trains_tree.selection()
        if not selection:
            messagebox.showwarning("Attenzione", "Selezionare un treno")
            return
        
        item = self.trains_tree.item(selection[0])
        schedule_id = item['text']
        
        # Find schedule
        schedule = None
        for s in self.schedules:
            if s.schedule_id == schedule_id:
                schedule = s
                break
        
        if not schedule:
            return
        
        try:
            from visualization import plot_timetable
            from datetime import timedelta
            
            # Get route from selected schedule
            route = [stop.node_id for stop in schedule.stops]
            
            # Get time window from selected schedule
            first_stop = schedule.stops[0]
            last_stop = schedule.stops[-1]
            start_time = first_stop.departure_time
            end_time = last_stop.arrival_time if last_stop.arrival_time else last_stop.departure_time
            
            # Expand time window by 2 hours before and after to show context
            time_buffer = timedelta(hours=2)
            window_start = start_time - time_buffer
            window_end = end_time + time_buffer
            
            # Find all schedules that use the same route (same line)
            # A schedule uses the same line if it has the same stations in the same order
            route_set = set(route)
            schedules_on_line = []
            
            for s in self.schedules:
                s_route = [stop.node_id for stop in s.stops]
                s_route_set = set(s_route)
                
                # Check if schedule is on same line:
                # 1. Has significant overlap with route (at least 50% of stations)
                # 2. Is in the time window
                overlap = len(route_set & s_route_set)
                if overlap >= len(route_set) * 0.5:  # At least 50% overlap
                    s_first = s.stops[0]
                    s_last = s.stops[-1]
                    s_start = s_first.departure_time
                    s_end = s_last.arrival_time if s_last.arrival_time else s_last.departure_time
                    
                    # Check if schedule is in time window
                    if (s_start <= window_end and s_end >= window_start):
                        schedules_on_line.append(s)
            
            # If no other schedules found, just show the selected one
            if len(schedules_on_line) == 0:
                schedules_on_line = [schedule]
            
            # Sort by departure time
            schedules_on_line.sort(key=lambda s: s.stops[0].departure_time)
            
            plot_timetable(route, schedules_on_line, self.network,
                          show_conflicts=True)
        except Exception as e:
            import traceback
            messagebox.showerror("Errore", f"Impossibile visualizzare il grafico:\n{str(e)}\n\n{traceback.format_exc()}")
    
    def show_metro_map(self, lines_to_show=None):
        """Show metro-style map for selected line(s).
        
        Args:
            lines_to_show: List of line objects to show, or None to use selected line
        """
        if lines_to_show is None:
            # Use selected line from tree
            selection = self.lines_tree.selection()
            if not selection:
                messagebox.showwarning("Attenzione", "Selezionare una linea")
                return
            
            item = self.lines_tree.item(selection[0])
            line_id = item['text']
            
            if line_id not in self.lines:
                return
            
            lines_to_show = [self.lines[line_id]]
        
        if not lines_to_show:
            messagebox.showwarning("Attenzione", "Nessuna linea da visualizzare")
            return
        
        try:
            import matplotlib.pyplot as plt
            import matplotlib.patches as patches
            
            # Calculate figure size based on number of lines
            num_lines = len(lines_to_show)
            fig_height = max(8, 3 * num_lines)
            fig, ax = plt.subplots(figsize=(16, fig_height))
            
            # Draw each line
            for line_idx, line in enumerate(lines_to_show):
                route = line.route
                if len(route) < 2:
                    continue
                
                # Calculate cumulative distances
                distances = [0]
                for i in range(len(route) - 1):
                    from_node = route[i]
                    to_node = route[i + 1]
                    
                    # Find edge distance
                    edge_distance = 10  # Default
                    for edge in self.network.edges:
                        if ((edge.from_node == from_node and edge.to_node == to_node) or
                            (edge.bidirectional and edge.from_node == to_node and edge.to_node == from_node)):
                            edge_distance = edge.distance
                            break
                    
                    distances.append(distances[-1] + edge_distance)
                
                # Normalize distances for visualization
                max_distance = distances[-1] if distances[-1] > 0 else 100
                positions = [(d / max_distance) * 14 for d in distances]  # Scale to 14 units
                
                # Calculate y position for this line
                y_spacing = 3.0
                y_center = fig_height - 2 - (line_idx * y_spacing)
                
                # Draw the line segments
                for i in range(len(positions) - 1):
                    x1, x2 = positions[i], positions[i + 1]
                    # Add slight vertical offset for visual interest
                    y_offset = 0.05 * (1 if i % 2 == 0 else -1)
                    ax.plot([x1, x2], [y_center + y_offset, y_center + y_offset], 
                           color=line.color, linewidth=8, solid_capstyle='round', alpha=0.8)
                
                # Draw stations
                drawn_stations = {}  # Track which stations we've drawn
                for i, (node_id, pos) in enumerate(zip(route, positions)):
                    node = self.network.get_node(node_id)
                    station_name = node.name if node else node_id
                    
                    # Draw station circle
                    circle = patches.Circle((pos, y_center), 0.12, 
                                           facecolor='white', 
                                           edgecolor=line.color, 
                                           linewidth=3, 
                                           zorder=10)
                    ax.add_patch(circle)
                    
                    # Add station name (only if not drawn yet or at edges)
                    if node_id not in drawn_stations or i == 0 or i == len(route) - 1:
                        # Alternate labels above and below
                        if i % 2 == 0:
                            y_text = y_center + 0.4
                            va = 'bottom'
                        else:
                            y_text = y_center - 0.4
                            va = 'top'
                        
                        ax.text(pos, y_text, station_name,
                               ha='center', va=va,
                               fontsize=8, fontweight='bold',
                               rotation=45 if len(station_name) > 12 else 0)
                        drawn_stations[node_id] = True
                
                # Add line name on the left
                ax.text(-0.5, y_center, line.name,
                       ha='right', va='center',
                       fontsize=11, fontweight='bold',
                       color=line.color,
                       bbox=dict(boxstyle='round,pad=0.5', facecolor='white', 
                                edgecolor=line.color, linewidth=2))
                
                # Add distance info on the right
                total_distance = distances[-1]
                ax.text(14.5, y_center, f'{total_distance:.1f} km\n{len(route)} fermate',
                       ha='left', va='center',
                       fontsize=8, color='gray')
            
            # Add title
            if num_lines == 1:
                title = f'Mappa Metro - {lines_to_show[0].name}'
            else:
                title = f'Mappa Metro - {num_lines} Linee'
            
            ax.text(0.5, 0.98, title,
                   transform=ax.transAxes,
                   ha='center', va='top',
                   fontsize=16, fontweight='bold')
            
            # Set axis properties
            ax.set_xlim(-2, 16)
            ax.set_ylim(0, fig_height)
            ax.set_aspect('equal')
            ax.axis('off')
            
            plt.tight_layout()
            plt.show()
            
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile visualizzare la mappa:\n{str(e)}")
    
    def show_all_metro_maps(self):
        """Show metro map with all lines."""
        if not self.lines:
            messagebox.showwarning("Attenzione", "Nessuna linea disponibile")
            return
        
        all_lines = list(self.lines.values())
        self.show_metro_map(all_lines)
    
    def show_metro_map_selection(self):
        """Show dialog to select which lines to display on metro map."""
        if not self.lines:
            messagebox.showwarning("Attenzione", "Nessuna linea disponibile")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Selezione Linee per Mappa Metro")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Instructions
        ttk.Label(dialog, text="Seleziona le linee da visualizzare sulla mappa:", 
                 font=('Arial', 11, 'bold')).pack(pady=10, padx=10)
        
        # Frame for checkboxes with scrollbar
        canvas_frame = ttk.Frame(dialog)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        canvas = tk.Canvas(canvas_frame)
        scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Create checkboxes for each line
        line_vars = {}
        for line_id, line in self.lines.items():
            var = tk.BooleanVar(value=True)
            line_vars[line_id] = var
            
            frame = ttk.Frame(scrollable_frame)
            frame.pack(fill=tk.X, pady=2, padx=5)
            
            # Checkbox
            cb = ttk.Checkbutton(frame, variable=var)
            cb.pack(side=tk.LEFT)
            
            # Color indicator
            color_label = tk.Label(frame, text="█", fg=line.color, font=('Arial', 16))
            color_label.pack(side=tk.LEFT, padx=5)
            
            # Line info
            info_text = f"{line.name} ({len(line.route)} fermate)"
            ttk.Label(frame, text=info_text, font=('Arial', 10)).pack(side=tk.LEFT)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons frame
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        
        def select_all():
            for var in line_vars.values():
                var.set(True)
        
        def deselect_all():
            for var in line_vars.values():
                var.set(False)
        
        def show_selected():
            selected_lines = [
                self.lines[line_id] 
                for line_id, var in line_vars.items() 
                if var.get()
            ]
            
            if not selected_lines:
                messagebox.showwarning("Attenzione", "Selezionare almeno una linea")
                return
            
            dialog.destroy()
            self.show_metro_map(selected_lines)
        
        ttk.Button(btn_frame, text="Seleziona Tutte", command=select_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Deseleziona Tutte", command=deselect_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Visualizza Mappa", command=show_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Annulla", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def delete_schedule(self):
        """Delete selected schedule."""
        selection = self.trains_tree.selection()
        if not selection:
            messagebox.showwarning("Attenzione", "Selezionare un orario da eliminare")
            return
        
        item = self.trains_tree.item(selection[0])
        schedule_id = item['text']
        
        if messagebox.askyesno("Conferma", f"Eliminare l'orario '{schedule_id}'?"):
            self.schedules = [s for s in self.schedules if s.schedule_id != schedule_id]
            self.update_all_displays()
            self.update_status(f"Orario '{schedule_id}' eliminato")
    
    # ========================================================================
    # VIEW OPERATIONS
    # ========================================================================
    
    def show_network_map(self):
        """Show network topology visualization."""
        if len(self.network.nodes) == 0:
            messagebox.showwarning("Attenzione", "La rete non contiene stazioni")
            return
        
        try:
            self.network.visualize(save_path="temp_network_map.png")
            self.update_status("Mappa rete generata")
        except Exception as e:
            messagebox.showerror("Errore", f"Errore nella generazione della mappa:\n{str(e)}")
    
    def show_timetable_diagram(self):
        """Show time-distance diagram with line selection."""
        if not self.schedules:
            messagebox.showwarning("Attenzione", "Non ci sono orari da visualizzare")
            return
        
        if not self.lines:
            messagebox.showwarning("Attenzione", "Creare almeno una linea per visualizzare il grafico orario")
            return
        
        # Create line selection dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Seleziona Linea per Grafico Orario")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Seleziona una linea per visualizzare il grafico orario:", 
                 font=('TkDefaultFont', 10, 'bold')).pack(pady=10, padx=10)
        
        # Create listbox with lines
        list_frame = ttk.Frame(dialog)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        listbox = tk.Listbox(list_frame, height=10)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar.set)
        
        # Populate listbox with lines
        line_data = []
        for line_id, line in self.lines.items():
            display_text = f"{line.name} ({len(line.route)} stazioni)"
            listbox.insert(tk.END, display_text)
            line_data.append((line_id, line))
        
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Select first line by default
        if line_data:
            listbox.selection_set(0)
        
        def show_diagram():
            """Show diagram for selected line."""
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("Attenzione", "Selezionare una linea")
                return
            
            line_id, line = line_data[selection[0]]
            
            # Filter schedules that use this line
            line_schedules = []
            for schedule in self.schedules:
                # Check if schedule route matches line route (at least partially)
                schedule_nodes = [stop.node_id for stop in schedule.stops]
                if any(node in line.route for node in schedule_nodes):
                    line_schedules.append(schedule)
            
            if not line_schedules:
                messagebox.showinfo("Informazione", 
                                   f"Nessun treno trovato sulla linea '{line.name}'")
                dialog.destroy()
                return
            
            try:
                from visualization import plot_timetable
                # Use line route for the diagram
                plot_timetable(line.route, line_schedules, self.network,
                              show_conflicts=True)
                self.update_status(f"Grafico orario generato per linea '{line.name}' ({len(line_schedules)} treni)")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Errore", f"Errore nella generazione del grafico:\n{str(e)}")
        
        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Visualizza Grafico", command=show_diagram).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Annulla", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def show_network_stats(self):
        """Show network statistics dialog."""
        stats = self.network.get_network_stats()
        
        msg = f"""Statistiche Rete: {self.network.name}
        
Stazioni: {stats['num_nodes']}
  - Stazioni normali: {stats['num_stations']}
  - Interscambi: {stats['num_interchanges']}

Connessioni: {stats['num_edges']}
Lunghezza totale binari: {stats['total_track_length']:.1f} km
Rete connessa: {'Sì' if stats['is_connected'] else 'No'}
Grado medio: {stats['average_degree']:.2f}

Linee ferroviarie: {len(self.lines)}
Treni schedulati: {len(self.schedules)}
"""
        
        messagebox.showinfo("Statistiche Rete", msg)
    
    def simulate_traffic(self):
        """Run traffic simulation."""
        if not self.schedules:
            messagebox.showwarning("Attenzione", "Non ci sono treni da simulare")
            return
        
        try:
            simulator = TrafficSimulator(self.network)
            conflicts = simulator.detect_conflicts(self.schedules)
            
            if conflicts:
                msg = f"Rilevati {len(conflicts)} conflitti!\n\n"
                for i, conflict in enumerate(conflicts[:5], 1):
                    msg += f"{i}. {conflict}\n"
                if len(conflicts) > 5:
                    msg += f"\n... e altri {len(conflicts) - 5} conflitti"
                
                # Resolve conflicts
                if messagebox.askyesno("Conflitti Rilevati", msg + "\n\nRisolvere automaticamente?"):
                    simulator.resolve_conflicts(self.schedules)
                    self.update_all_displays()
                    self.update_status("Conflitti risolti")
                    messagebox.showinfo("Successo", "Conflitti risolti con successo")
            else:
                messagebox.showinfo("Simulazione Traffico", "Nessun conflitto rilevato!\nTutti i treni possono circolare senza problemi.")
                
        except Exception as e:
            messagebox.showerror("Errore", f"Errore nella simulazione:\n{str(e)}")
    
    # ========================================================================
    # DATABASE OPERATIONS
    # ========================================================================
    
    def connect_sqlite(self):
        """Connect to SQLite database (default, no configuration needed)."""
        try:
            db_path = "railway_network.db"
            self.db = SQLiteDatabaseManager(db_path)
            self.db.connect()
            self.db_type = "sqlite"
            
            stats = self.db.get_statistics()
            messagebox.showinfo("SQLite",
                f"✅ Connesso a SQLite!\n\n"
                f"Database: {db_path}\n\n"
                f"Reti nel database: {stats['networks']}\n"
                f"Treni nel database: {stats['trains']}\n"
                f"Orari nel database: {stats['schedules']}")
            
            self.update_status("Connesso a SQLite database")
            
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile connettersi a SQLite:\n{str(e)}")
    
    def connect_mysql(self):
        """Connect to MySQL database."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Connetti a MySQL Database")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Connection parameters
        ttk.Label(dialog, text="Host:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        host_entry = ttk.Entry(dialog, width=30)
        host_entry.insert(0, "localhost")
        host_entry.grid(row=0, column=1, padx=10, pady=5)
        
        ttk.Label(dialog, text="Porta:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        port_entry = ttk.Entry(dialog, width=30)
        port_entry.insert(0, "3306")
        port_entry.grid(row=1, column=1, padx=10, pady=5)
        
        ttk.Label(dialog, text="Database:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        db_entry = ttk.Entry(dialog, width=30)
        db_entry.insert(0, "railway_network")
        db_entry.grid(row=2, column=1, padx=10, pady=5)
        
        ttk.Label(dialog, text="Utente:").grid(row=3, column=0, sticky=tk.W, padx=10, pady=5)
        user_entry = ttk.Entry(dialog, width=30)
        user_entry.insert(0, "root")
        user_entry.grid(row=3, column=1, padx=10, pady=5)
        
        ttk.Label(dialog, text="Password:").grid(row=4, column=0, sticky=tk.W, padx=10, pady=5)
        password_entry = ttk.Entry(dialog, width=30, show="*")
        password_entry.grid(row=4, column=1, padx=10, pady=5)
        
        def connect():
            try:
                host = host_entry.get()
                port = int(port_entry.get())
                database = db_entry.get()
                user = user_entry.get()
                password = password_entry.get()
                
                self.db = DatabaseManager(
                    host=host,
                    port=port,
                    database=database,
                    user=user,
                    password=password
                )
                
                self.db.connect()
                messagebox.showinfo("Successo", "Connessione al database riuscita!")
                self.update_status("Connesso al database MySQL")
                dialog.destroy()
                
            except Exception as e:
                messagebox.showerror("Errore", f"Impossibile connettersi al database:\n{str(e)}")
        
        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=20)
        ttk.Button(btn_frame, text="Connetti", command=connect).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Annulla", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def save_to_database(self):
        """Save current network to database."""
        if not self.db:
            messagebox.showwarning("Attenzione", 
                "Nessuna connessione al database.\n"
                "Usa 'Database → Connetti a MySQL...' prima di salvare.")
            return
        
        if len(self.network.nodes) == 0:
            messagebox.showwarning("Attenzione", "La rete è vuota")
            return
        
        try:
            # Save network
            network_id = self.db.save_network(self.network)
            
            # Save trains and schedules
            saved_schedules = 0
            for schedule in self.schedules:
                train_id = self.db.save_train(schedule.train)
                self.db.save_schedule(schedule, network_id)
                saved_schedules += 1
            
            messagebox.showinfo("Successo",
                f"Rete salvata nel database!\n\n"
                f"Network ID: {network_id}\n"
                f"Stazioni: {len(self.network.nodes)}\n"
                f"Connessioni: {len(self.network.edges)}\n"
                f"Orari salvati: {saved_schedules}")
            
            self.update_status(f"Rete salvata nel database (ID: {network_id})")
            
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile salvare nel database:\n{str(e)}")
    
    def load_from_database(self):
        """Load network from database."""
        if not self.db:
            messagebox.showwarning("Attenzione",
                "Nessuna connessione al database.\n"
                "Usa 'Database → Connetti a MySQL...' prima di caricare.")
            return
        
        try:
            # Get list of networks
            if self.db_type == "sqlite":
                networks = self.db.get_all_networks()
            else:  # MySQL
                cursor = self.db.connection.cursor(dictionary=True)
                cursor.execute("SELECT id, name, created_at FROM networks ORDER BY created_at DESC")
                networks = cursor.fetchall()
                cursor.close()
            
            if not networks:
                messagebox.showinfo("Info", "Nessuna rete trovata nel database")
                return
            
            # Create selection dialog
            dialog = tk.Toplevel(self.root)
            dialog.title("Carica Rete dal Database")
            dialog.geometry("600x400")
            dialog.transient(self.root)
            dialog.grab_set()
            
            ttk.Label(dialog, text="Seleziona una rete da caricare:", 
                     font=('TkDefaultFont', 10, 'bold')).pack(padx=10, pady=10)
            
            # Networks list
            tree = ttk.Treeview(dialog, columns=('ID', 'Nome', 'Data'), show='headings', height=15)
            tree.heading('ID', text='ID')
            tree.heading('Nome', text='Nome')
            tree.heading('Data', text='Data Creazione')
            
            tree.column('ID', width=50)
            tree.column('Nome', width=300)
            tree.column('Data', width=200)
            
            for net in networks:
                # Handle date formatting for both SQLite (string) and MySQL (datetime)
                created_at = net['created_at']
                if isinstance(created_at, str):
                    date_str = created_at[:19] if len(created_at) > 19 else created_at
                elif hasattr(created_at, 'strftime'):
                    date_str = created_at.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    date_str = 'N/A'
                    
                tree.insert('', tk.END, values=(
                    net['id'],
                    net['name'],
                    date_str
                ))
            
            tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            def load_selected():
                selection = tree.selection()
                if not selection:
                    messagebox.showwarning("Attenzione", "Selezionare una rete")
                    return
                
                item = tree.item(selection[0])
                network_id = item['values'][0]
                
                try:
                    # Load network
                    loaded_network = self.db.load_network(network_id)
                    if loaded_network:
                        self.network = loaded_network
                        
                        # Clear lines (not stored in DB yet)
                        self.lines = {}
                        
                        # Load schedules
                        self.schedules = self.db.load_schedules_by_network(network_id)
                        
                        self.current_file = None
                        self.update_all_displays()
                        
                        messagebox.showinfo("Successo",
                            f"Rete caricata dal database!\n\n"
                            f"Network ID: {network_id}\n"
                            f"Nome: {self.network.name}\n"
                            f"Stazioni: {len(self.network.nodes)}\n"
                            f"Connessioni: {len(self.network.edges)}\n"
                            f"Orari: {len(self.schedules)}")
                        
                        self.update_status(f"Rete '{self.network.name}' caricata dal database")
                        dialog.destroy()
                    else:
                        messagebox.showerror("Errore", "Impossibile caricare la rete")
                        
                except Exception as e:
                    messagebox.showerror("Errore", f"Errore nel caricamento:\n{str(e)}")
            
            # Buttons
            btn_frame = ttk.Frame(dialog)
            btn_frame.pack(pady=10)
            ttk.Button(btn_frame, text="Carica", command=load_selected).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="Annulla", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
            
        except Exception as e:
            messagebox.showerror("Errore", f"Errore nell'accesso al database:\n{str(e)}")
    
    def show_db_status(self):
        """Show database connection status."""
        if self.db and self.db_type != "none":
            try:
                if self.db_type == "sqlite":
                    stats = self.db.get_statistics()
                    messagebox.showinfo("Stato Database",
                        f"✅ Connesso a SQLite\n\n"
                        f"Database: {self.db.db_path}\n\n"
                        f"Reti nel database: {stats['networks']}\n"
                        f"Treni nel database: {stats['trains']}\n"
                        f"Orari nel database: {stats['schedules']}")
                        
                elif self.db_type == "mysql" and self.db.connection and self.db.connection.is_connected():
                    cursor = self.db.connection.cursor(dictionary=True)
                    
                    # Get counts
                    cursor.execute("SELECT COUNT(*) as count FROM networks")
                    networks_count = cursor.fetchone()['count']
                    
                    cursor.execute("SELECT COUNT(*) as count FROM trains")
                    trains_count = cursor.fetchone()['count']
                    
                    cursor.execute("SELECT COUNT(*) as count FROM schedules")
                    schedules_count = cursor.fetchone()['count']
                    
                    cursor.close()
                    
                    messagebox.showinfo("Stato Database",
                        f"✅ Connesso a MySQL\n\n"
                        f"Database: {self.db.database}\n"
                        f"Host: {self.db.host}:{self.db.port}\n\n"
                        f"Reti nel database: {networks_count}\n"
                        f"Treni nel database: {trains_count}\n"
                        f"Orari nel database: {schedules_count}")
                else:
                    messagebox.showinfo("Stato Database",
                        "❌ Connessione persa")
            except Exception as e:
                messagebox.showerror("Errore", f"Errore nel recupero dello stato:\n{str(e)}")
        else:
            messagebox.showinfo("Stato Database",
                "❌ Non connesso al database\n\n"
                "Usa:\n"
                "• 'Database → Usa SQLite' (predefinito, nessuna configurazione)\n"
                "• 'Database → Connetti a MySQL...' (richiede server)")
    
    def manage_database_saves(self):
        """Show dialog to manage (view/delete) saved networks in database."""
        if not self.db or self.db_type == "none":
            messagebox.showwarning("Attenzione", 
                "Non sei connesso a un database.\n\n"
                "Usa 'Database → Usa SQLite' o 'Database → Connetti a MySQL...'")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Gestisci Salvataggi Database")
        dialog.geometry("800x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Instructions
        ttk.Label(dialog, text="Reti salvate nel database:", 
                 font=('Arial', 12, 'bold')).pack(pady=10, padx=10)
        
        # Frame for treeview
        tree_frame = ttk.Frame(dialog)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Treeview for networks
        columns = ('Name', 'Date', 'Nodes', 'Edges')
        tree = ttk.Treeview(tree_frame, columns=columns, show='tree headings')
        tree.heading('#0', text='ID')
        tree.heading('Name', text='Nome')
        tree.heading('Date', text='Data Creazione')
        tree.heading('Nodes', text='Stazioni')
        tree.heading('Edges', text='Connessioni')
        
        tree.column('#0', width=80)
        tree.column('Name', width=250)
        tree.column('Date', width=150)
        tree.column('Nodes', width=100)
        tree.column('Edges', width=100)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Load networks from database
        def load_networks():
            """Load all networks from database."""
            tree.delete(*tree.get_children())
            
            try:
                if self.db_type == "sqlite":
                    networks = self.db.get_all_networks()
                elif self.db_type == "mysql":
                    cursor = self.db.connection.cursor(dictionary=True)
                    cursor.execute("""
                        SELECT n.network_id, n.name, n.created_at,
                               COUNT(DISTINCT nd.node_id) as node_count,
                               COUNT(DISTINCT e.edge_id) as edge_count
                        FROM networks n
                        LEFT JOIN nodes nd ON n.network_id = nd.network_id
                        LEFT JOIN edges e ON n.network_id = e.network_id
                        GROUP BY n.network_id, n.name, n.created_at
                        ORDER BY n.created_at DESC
                    """)
                    networks = cursor.fetchall()
                    cursor.close()
                else:
                    return
                
                for network in networks:
                    net_id = network.get('network_id', network.get('id'))
                    name = network.get('name', 'Senza nome')
                    created = network.get('created_at', 'N/A')
                    if created != 'N/A' and hasattr(created, 'strftime'):
                        created = created.strftime('%Y-%m-%d %H:%M')
                    nodes = network.get('node_count', 0)
                    edges = network.get('edge_count', 0)
                    
                    tree.insert('', 'end', text=str(net_id), 
                               values=(name, created, nodes, edges))
                
                if not networks:
                    ttk.Label(tree_frame, text="Nessuna rete salvata nel database",
                             font=('Arial', 10, 'italic')).place(relx=0.5, rely=0.5, anchor='center')
                    
            except Exception as e:
                messagebox.showerror("Errore", f"Errore nel caricamento delle reti:\n{str(e)}")
        
        # Buttons frame
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        
        def delete_selected():
            """Delete selected network from database."""
            selection = tree.selection()
            if not selection:
                messagebox.showwarning("Attenzione", "Selezionare una rete da eliminare")
                return
            
            item = tree.item(selection[0])
            net_id = item['text']
            net_name = item['values'][0]
            
            if not messagebox.askyesno("Conferma Eliminazione",
                f"Vuoi eliminare la rete:\n\n"
                f"ID: {net_id}\n"
                f"Nome: {net_name}\n\n"
                f"⚠️ Questa operazione eliminerà:\n"
                f"• La rete\n"
                f"• Tutte le stazioni\n"
                f"• Tutte le connessioni\n"
                f"• Tutti i treni associati\n"
                f"• Tutti gli orari\n\n"
                f"Questa azione non può essere annullata!"):
                return
            
            try:
                if self.db_type == "sqlite":
                    # SQLite with foreign keys will cascade delete
                    self.db.cursor.execute("DELETE FROM networks WHERE network_id = ?", (net_id,))
                    self.db.connection.commit()
                elif self.db_type == "mysql":
                    cursor = self.db.connection.cursor()
                    # MySQL with ON DELETE CASCADE will handle related records
                    cursor.execute("DELETE FROM networks WHERE network_id = %s", (net_id,))
                    self.db.connection.commit()
                    cursor.close()
                
                messagebox.showinfo("Successo", f"Rete '{net_name}' eliminata dal database")
                load_networks()  # Refresh list
                
            except Exception as e:
                messagebox.showerror("Errore", f"Errore nell'eliminazione:\n{str(e)}")
        
        def refresh_list():
            """Refresh the networks list."""
            load_networks()
        
        ttk.Button(btn_frame, text="🔄 Aggiorna", command=refresh_list).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑️ Elimina Selezionata", command=delete_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Chiudi", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Load networks initially
        load_networks()
    
    def show_about(self):
        """Show about dialog."""
        messagebox.showinfo("Informazioni", 
                          "FDC - Railway Network Manager\n\n"
                          "Sistema di gestione e simulazione\n"
                          "di reti ferroviarie\n\n"
                          "Versione 1.0\n\n"
                          "© 2025 FDC Team")
    
    # ========================================================================
    # UPDATE DISPLAYS
    # ========================================================================
    
    def auto_assign_all_platforms(self):
        """Automatically assign platforms to all trains."""
        from schedule import auto_assign_platforms
        
        if not self.schedules:
            return
        
        issues = auto_assign_platforms(self.schedules, self.network)
        
        if issues:
            # Show issues to user
            issue_msg = "Alcuni treni hanno conflitti di binario:\n\n"
            for schedule_id, issue_list in issues.items():
                issue_msg += f"• {schedule_id}:\n"
                for issue in issue_list:
                    issue_msg += f"  - {issue}\n"
            messagebox.showwarning("Conflitti Binario", issue_msg)
    
    def show_platform_manager(self):
        """Show platform assignment manager dialog."""
        if not self.schedules:
            messagebox.showinfo("Info", "Nessun treno da gestire")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Gestione Assegnazione Binari")
        dialog.geometry("900x600")
        dialog.transient(self.root)
        
        # Info
        info_frame = ttk.LabelFrame(dialog, text="ℹ️ Informazioni", padding=10)
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(info_frame, text="Gestisci l'assegnazione dei binari per ogni treno in ogni stazione.\nI conflitti sono evidenziati in rosso.",
                 font=('TkDefaultFont', 9, 'italic')).pack()
        
        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(btn_frame, text="🔄 Riassegna Automaticamente", 
                  command=lambda: [self.auto_assign_all_platforms(), self.update_platform_display(tree, conflict_label)]).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="✓ Chiudi", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        
        # Conflict status
        conflict_label = ttk.Label(dialog, text="", font=('TkDefaultFont', 10, 'bold'))
        conflict_label.pack(fill=tk.X, padx=10)
        
        # Tree view
        tree_frame = ttk.Frame(dialog)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        columns = ('train', 'station', 'arrival', 'departure', 'platform')
        tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=20)
        tree.heading('train', text='Treno')
        tree.heading('station', text='Stazione')
        tree.heading('arrival', text='Arrivo')
        tree.heading('departure', text='Partenza')
        tree.heading('platform', text='Binario')
        
        tree.column('train', width=150)
        tree.column('station', width=200)
        tree.column('arrival', width=100)
        tree.column('departure', width=100)
        tree.column('platform', width=80)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        def on_double_click(event):
            selection = tree.selection()
            if not selection:
                return
            
            item = tree.item(selection[0])
            values = item['values']
            schedule_id = item['tags'][0] if item['tags'] else None
            stop_index = int(item['tags'][1]) if len(item['tags']) > 1 else None
            
            if not schedule_id or stop_index is None:
                return
            
            # Find schedule and stop
            schedule = next((s for s in self.schedules if s.schedule_id == schedule_id), None)
            if not schedule or stop_index >= len(schedule.stops):
                return
            
            stop = schedule.stops[stop_index]
            node = self.network.get_node(stop.node_id)
            
            if not node:
                return
            
            # Ask for new platform
            new_platform = simpledialog.askinteger(
                "Modifica Binario",
                f"Stazione: {node.name}\nTreno: {schedule.train.name}\n\nInserisci nuovo binario (1-{node.platforms}):",
                minvalue=1,
                maxvalue=node.platforms,
                initialvalue=stop.platform or 1
            )
            
            if new_platform:
                stop.platform = new_platform
                self.modified = True
                self.update_platform_display(tree, conflict_label)
        
        tree.bind('<Double-Button-1>', on_double_click)
        
        self.update_platform_display(tree, conflict_label)
    
    def update_platform_display(self, tree, conflict_label):
        """Update platform assignment display."""
        from schedule import check_platform_conflicts
        
        tree.delete(*tree.get_children())
        
        # Add all stops
        for schedule in sorted(self.schedules, key=lambda s: s.stops[0].departure_time if s.stops[0].departure_time else datetime.max):
            for idx, stop in enumerate(schedule.stops):
                node = self.network.get_node(stop.node_id)
                if not node:
                    continue
                
                arrival = stop.arrival_time.strftime('%H:%M') if stop.arrival_time else '---'
                departure = stop.departure_time.strftime('%H:%M') if stop.departure_time else '---'
                platform = str(stop.platform) if stop.platform else '-'
                
                tree.insert('', tk.END,
                           values=(schedule.train.name, node.name, arrival, departure, platform),
                           tags=(schedule.schedule_id, str(idx)))
        
        # Check conflicts
        conflicts = check_platform_conflicts(self.schedules, self.network)
        
        if conflicts:
            conflict_label.config(text=f"⚠️ {len(conflicts)} conflitti rilevati!", foreground='red')
            
            # Highlight conflicts
            for item in tree.get_children():
                values = tree.item(item)['values']
                tags = tree.item(item)['tags']
                
                if not tags:
                    continue
                
                schedule_id = tags[0]
                stop_index = int(tags[1])
                
                # Check if this stop is in conflict
                schedule = next((s for s in self.schedules if s.schedule_id == schedule_id), None)
                if not schedule or stop_index >= len(schedule.stops):
                    continue
                
                stop = schedule.stops[stop_index]
                
                for conflict in conflicts:
                    if conflict['node_id'] == stop.node_id and conflict['platform'] == stop.platform:
                        if conflict['train1'] == schedule.train.name or conflict['train2'] == schedule.train.name:
                            tree.item(item, tags=tags + ('conflict',))
                            # Color red for conflicts
                            tree.tag_configure('conflict', background='#ffcccc')
        else:
            conflict_label.config(text="✓ Nessun conflitto di binario", foreground='green')
    
    def update_all_displays(self):
        """Update all display elements."""
        self.update_stations_list()
        self.update_connections_list()
        self.update_lines_list()
        self.update_trains_list()
        
        # Aggiorna anche il grafico se c'è un treno selezionato
        selection = self.trains_tree.selection()
        if selection:
            item = self.trains_tree.item(selection[0])
            schedule_id = item['text']
            for s in self.schedules:
                if s.schedule_id == schedule_id:
                    self._draw_train_diagram(s)
                    break
    
    def update_stations_list(self):
        """Update stations tree view."""
        self.stations_tree.delete(*self.stations_tree.get_children())
        
        # Sort stations alphabetically by node_id
        for node_id in sorted(self.network.nodes.keys()):
            node = self.network.nodes[node_id]
            self.stations_tree.insert('', tk.END, 
                                     text=f"{node_id} / {node.name}",
                                     values=(node.node_type.name, 
                                           f"{node.latitude:.4f}",
                                           f"{node.longitude:.4f}",
                                           node.platforms))
    
    def update_connections_list(self):
        """Update connections tree view."""
        self.connections_tree.delete(*self.connections_tree.get_children())
        
        for edge in self.network.edges:
            self.connections_tree.insert('', tk.END,
                                        values=(edge.from_node,
                                               edge.to_node,
                                               f"{edge.distance:.1f}",
                                               edge.track_type.name,
                                               edge.max_speed))
    
    def update_lines_list(self):
        """Update lines tree view."""
        self.lines_tree.delete(*self.lines_tree.get_children())
        
        for line_id, line in self.lines.items():
            self.lines_tree.insert('', tk.END,
                                  text=line_id,
                                  values=(line.name,
                                         line.color,
                                         len(line.route)))
    
    def update_trains_list(self):
        """Update trains/schedules tree view with optional line filter."""
        self.trains_tree.delete(*self.trains_tree.get_children())
        
        # Update filter combo with available lines
        if hasattr(self, 'train_filter_combo'):
            line_names = ["Tutte le linee"] + [f"{lid}: {line.name}" for lid, line in self.lines.items()]
            self.train_filter_combo['values'] = line_names
        
        # Get selected filter
        selected_filter = self.train_filter_var.get() if hasattr(self, 'train_filter_var') else "Tutte le linee"
        
        for schedule in self.schedules:
            # Apply line filter
            if selected_filter != "Tutte le linee":
                # Extract line ID from filter (format: "LINE_ID: Line Name")
                filter_line_id = selected_filter.split(':')[0].strip()
                
                # Check if schedule belongs to this line (including partial routes)
                schedule_route = [stop.node_id for stop in schedule.stops]
                line_matches = False
                
                for line_id, line in self.lines.items():
                    if line_id == filter_line_id:
                        # Check if schedule route is exact match or contiguous subset
                        if (schedule_route == line.route or 
                            schedule_route == list(reversed(line.route))):
                            line_matches = True
                            break
                        
                        # Check if schedule is a contiguous portion of the line
                        line_route_str = ','.join(line.route)
                        schedule_route_str = ','.join(schedule_route)
                        schedule_route_reversed_str = ','.join(reversed(schedule_route))
                        
                        if (schedule_route_str in line_route_str or 
                            schedule_route_reversed_str in line_route_str):
                            line_matches = True
                            break
                
                if not line_matches:
                    continue
            
            dep = schedule.get_departure_time()
            arr = schedule.get_arrival_time()
            
            # Get station names instead of IDs
            origin_name = schedule.origin
            destination_name = schedule.destination
            
            if schedule.origin in self.network.nodes:
                origin_name = self.network.nodes[schedule.origin].name
            
            if schedule.destination in self.network.nodes:
                destination_name = self.network.nodes[schedule.destination].name
            
            # Find which line this schedule belongs to
            # A train belongs to a line if its route is a SUBSET (portion) of the line route
            line_name = "-"
            schedule_route = [stop.node_id for stop in schedule.stops]
            
            for line_id, line in self.lines.items():
                # Check if schedule route is exact match (forward or reverse)
                if (schedule_route == line.route or 
                    schedule_route == list(reversed(line.route))):
                    line_name = line.name
                    break
                
                # Check if schedule route is a CONTIGUOUS SUBSET of the line route
                # This handles trains that travel only PART of the line
                line_route_str = ','.join(line.route)
                schedule_route_str = ','.join(schedule_route)
                schedule_route_reversed_str = ','.join(reversed(schedule_route))
                
                # Check if schedule is a substring (contiguous portion) of line route
                if (schedule_route_str in line_route_str or 
                    schedule_route_reversed_str in line_route_str):
                    line_name = line.name
                    break
            
            self.trains_tree.insert('', tk.END,
                                   text=schedule.schedule_id,
                                   values=(schedule.train.name,
                                          schedule.train.train_type.name,
                                          line_name,
                                          origin_name,
                                          destination_name,
                                          dep.strftime('%H:%M') if dep else '---',
                                          arr.strftime('%H:%M') if arr else '---'))
    
    def on_line_selected(self, event):
        """Handle line selection."""
        selection = self.lines_tree.selection()
        if not selection:
            return
        
        item = self.lines_tree.item(selection[0])
        line_id = item['text']
        line = self.lines.get(line_id)
        
        if line:
            details = f"Linea: {line.name}\n"
            details += f"ID: {line.line_id}\n"
            details += f"Colore: {line.color}\n"
            details += f"\nPercorso ({len(line.route)} stazioni):\n"
            details += "-" * 40 + "\n"
            
            for i, station_id in enumerate(line.route, 1):
                station_name = self.network.nodes[station_id].name if station_id in self.network.nodes else station_id
                details += f"{i}. {station_name} ({station_id})\n"
            
            self.line_details_text.delete('1.0', tk.END)
            self.line_details_text.insert('1.0', details)
    
    def on_schedule_selected(self, event):
        """Handle schedule selection."""
        selection = self.trains_tree.selection()
        if not selection:
            # Clear details when nothing is selected
            self.schedule_details_text.delete('1.0', tk.END)
            self._clear_diagram()
            return
        
        item = self.trains_tree.item(selection[0])
        schedule_id = item['text']
        
        schedule = None
        for s in self.schedules:
            if s.schedule_id == schedule_id:
                schedule = s
                break
        
        if schedule:
            # Get station names instead of IDs
            origin_name = schedule.origin
            destination_name = schedule.destination
            
            if schedule.origin in self.network.nodes:
                origin_name = self.network.nodes[schedule.origin].name
            
            if schedule.destination in self.network.nodes:
                destination_name = self.network.nodes[schedule.destination].name
            
            details = f"Orario: {schedule.schedule_id}\n"
            details += f"Treno: {schedule.train.name} ({schedule.train.train_type.name})\n"
            details += f"Percorso: {origin_name} → {destination_name}\n"
            details += f"Priorità: {schedule.priority}\n"
            details += f"\nFermate:\n"
            details += "-" * 60 + "\n"
            details += f"{'Stazione':<25} {'Arrivo':<10} {'Partenza':<10} {'Sosta':<6}\n"
            details += "-" * 60 + "\n"
            
            for stop in schedule.stops:
                station_name = self.network.nodes[stop.node_id].name if stop.node_id in self.network.nodes else stop.node_id
                arr = stop.arrival_time.strftime('%H:%M') if stop.arrival_time else '---'
                dep = stop.departure_time.strftime('%H:%M') if stop.departure_time else '---'
                dwell = f"{stop.stop_duration}min" if stop.stop_duration else '---'
                details += f"{station_name:<25} {arr:<10} {dep:<10} {dwell:<6}\n"
            
            self.schedule_details_text.delete('1.0', tk.END)
            self.schedule_details_text.insert('1.0', details)
            
            # Draw diagram in the right panel
            self._draw_train_diagram(schedule)
    
    def _clear_diagram(self):
        """Clear the diagram canvas."""
        if self.diagram_canvas:
            try:
                self.diagram_canvas.destroy()
            except:
                pass
            self.diagram_canvas = None
        
        # Clear all children of diagram frame
        for widget in self.diagram_frame_container.winfo_children():
            widget.destroy()
    
    def _draw_train_diagram(self, schedule):
        """Draw train diagram in the right panel."""
        try:
            import tempfile
            import os
            from PIL import Image, ImageTk
            from datetime import timedelta
            
            # Clear previous diagram
            self._clear_diagram()
            
            # Find all trains on the same line within time window
            schedules_on_line = self._find_schedules_on_same_line(schedule)
            
            if not schedules_on_line:
                # If no schedules found, just show the selected one
                schedules_on_line = [schedule]
            
            # Extract route from the selected schedule
            route = [stop.node_id for stop in schedule.stops]
            
            # Use visualization module to plot to a temporary file
            from visualization import plot_timetable
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            temp_file.close()
            
            # Generate plot and save to file
            plot_timetable(route, schedules_on_line, self.network, 
                          filename=temp_file.name,
                          figsize=(6, 4),
                          show_conflicts=True)
            
            # Load image and display in tkinter
            img = Image.open(temp_file.name)
            
            # Resize to fit panel if needed
            max_width = 500
            max_height = 350
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(img)
            
            # Create label to show image
            img_label = tk.Label(self.diagram_frame_container, image=photo)
            img_label.image = photo  # Keep a reference to prevent garbage collection
            img_label.pack(fill=tk.BOTH, expand=True)
            
            # Store label to clear later
            self.diagram_canvas = img_label
            
            # Clean up temporary file
            try:
                os.unlink(temp_file.name)
            except:
                pass
            
        except Exception as e:
            # If there's an error, show a message in the diagram area
            error_label = ttk.Label(self.diagram_frame_container, 
                                   text=f"Impossibile generare il grafico:\n{str(e)}",
                                   justify=tk.CENTER)
            error_label.pack(expand=True)
            print(f"Errore nel disegno del grafico: {e}")
            import traceback
            traceback.print_exc()
    
    def _find_schedules_on_same_line(self, selected_schedule):
        """Find all schedules on the same line as the selected schedule."""
        # Get route of selected schedule
        selected_route = set([stop.node_id for stop in selected_schedule.stops])
        
        # Get time window (±2 hours from selected schedule)
        if selected_schedule.stops:
            first_stop = selected_schedule.stops[0]
            departure_time = first_stop.departure_time if first_stop.departure_time else first_stop.arrival_time
            
            if departure_time:
                from datetime import timedelta
                time_start = departure_time - timedelta(hours=2)
                time_end = departure_time + timedelta(hours=4)
                
                # Find schedules with overlapping routes and time window
                schedules_on_line = []
                for s in self.schedules:
                    s_route = set([stop.node_id for stop in s.stops])
                    
                    # Check if routes overlap (at least 50% of stops in common)
                    overlap = len(selected_route & s_route)
                    if overlap >= len(selected_route) * 0.5:
                        # Check time window
                        if s.stops:
                            s_first_stop = s.stops[0]
                            s_departure = s_first_stop.departure_time if s_first_stop.departure_time else s_first_stop.arrival_time
                            
                            if s_departure and time_start <= s_departure <= time_end:
                                schedules_on_line.append(s)
                
                return sorted(schedules_on_line, key=lambda x: x.stops[0].departure_time or x.stops[0].arrival_time)
        
        return [selected_schedule]


class AddStationDialog:
    """Helper dialog for adding station to route."""
    
    def __init__(self, parent, available_stations, listbox):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Aggiungi Stazione")
        self.dialog.geometry("300x150")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.listbox = listbox
        
        ttk.Label(self.dialog, text="Seleziona stazione:").pack(pady=10)
        
        self.station_var = tk.StringVar()
        combo = ttk.Combobox(self.dialog, textvariable=self.station_var, 
                            values=available_stations, width=30)
        combo.pack(pady=10)
        
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Aggiungi", command=self.add).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Chiudi", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def add(self):
        station = self.station_var.get()
        if station:
            self.listbox.insert(tk.END, station)


def main():
    """Main entry point."""
    root = tk.Tk()
    app = RailwayGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
