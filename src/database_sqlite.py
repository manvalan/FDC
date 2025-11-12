"""
SQLite Database Manager for Railway Network System.
Provides persistent storage for networks, trains, and schedules using SQLite.
"""
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict
from railway_network import RailwayNetwork
from node import Node, NodeType
from edge import Edge, TrackType
from train import Train, TrainType
from schedule import TrainSchedule


class SQLiteDatabaseManager:
    """Manages SQLite database operations for railway network data."""
    
    def __init__(self, db_path: str = "railway_network.db"):
        """
        Initialize SQLite database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
        
    def connect(self):
        """Connect to SQLite database and create tables if needed."""
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row  # Enable column access by name
        self.create_tables()
        
    def create_tables(self):
        """Create database tables if they don't exist."""
        cursor = self.connection.cursor()
        
        # Networks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS networks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Nodes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                network_id INTEGER NOT NULL,
                node_id TEXT NOT NULL,
                name TEXT NOT NULL,
                node_type TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                capacity INTEGER NOT NULL,
                platforms INTEGER NOT NULL,
                FOREIGN KEY (network_id) REFERENCES networks(id) ON DELETE CASCADE,
                UNIQUE(network_id, node_id)
            )
        """)
        
        # Edges table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                network_id INTEGER NOT NULL,
                from_node TEXT NOT NULL,
                to_node TEXT NOT NULL,
                distance REAL NOT NULL,
                track_type TEXT NOT NULL,
                max_speed REAL NOT NULL,
                FOREIGN KEY (network_id) REFERENCES networks(id) ON DELETE CASCADE
            )
        """)
        
        # Trains table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trains (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                train_id TEXT UNIQUE NOT NULL,
                train_type TEXT NOT NULL,
                max_speed REAL NOT NULL,
                acceleration REAL NOT NULL,
                braking REAL NOT NULL,
                priority INTEGER NOT NULL
            )
        """)
        
        # Schedules table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                schedule_id TEXT UNIQUE NOT NULL,
                train_id TEXT NOT NULL,
                network_id INTEGER NOT NULL,
                departure_time TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (train_id) REFERENCES trains(train_id) ON DELETE CASCADE,
                FOREIGN KEY (network_id) REFERENCES networks(id) ON DELETE CASCADE
            )
        """)
        
        # Schedule stops table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schedule_stops (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                schedule_id TEXT NOT NULL,
                station_id TEXT NOT NULL,
                arrival_time TEXT NOT NULL,
                departure_time TEXT NOT NULL,
                stop_order INTEGER NOT NULL,
                FOREIGN KEY (schedule_id) REFERENCES schedules(schedule_id) ON DELETE CASCADE
            )
        """)
        
        self.connection.commit()
        
    def save_network(self, network: RailwayNetwork) -> int:
        """
        Save a railway network to database.
        
        Args:
            network: RailwayNetwork instance to save
            
        Returns:
            Network ID in database
        """
        cursor = self.connection.cursor()
        
        # Insert network
        cursor.execute(
            "INSERT INTO networks (name) VALUES (?)",
            (network.name,)
        )
        network_id = cursor.lastrowid
        
        # Insert nodes
        for node in network.nodes.values():
            cursor.execute(
                """INSERT INTO nodes 
                   (network_id, node_id, name, node_type, latitude, longitude, capacity, platforms)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (network_id, node.id, node.name, node.node_type.value,
                 node.latitude, node.longitude, node.capacity, node.platforms)
            )
        
        # Insert edges
        for edge in network.edges:
            cursor.execute(
                """INSERT INTO edges
                   (network_id, from_node, to_node, distance, track_type, max_speed)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (network_id, edge.from_node, edge.to_node, edge.distance,
                 edge.track_type.value, edge.max_speed)
            )
        
        self.connection.commit()
        return network_id
    
    def load_network(self, network_id: int) -> Optional[RailwayNetwork]:
        """
        Load a railway network from database.
        
        Args:
            network_id: ID of network to load
            
        Returns:
            RailwayNetwork instance or None if not found
        """
        cursor = self.connection.cursor()
        
        # Get network info
        cursor.execute("SELECT * FROM networks WHERE id = ?", (network_id,))
        network_row = cursor.fetchone()
        
        if not network_row:
            return None
        
        network = RailwayNetwork(network_row['name'])
        
        # Load nodes
        cursor.execute("SELECT * FROM nodes WHERE network_id = ?", (network_id,))
        for row in cursor.fetchall():
            node_type = NodeType(row['node_type'])
            node = Node(
                node_id=row['node_id'],
                name=row['name'],
                node_type=node_type,
                latitude=row['latitude'],
                longitude=row['longitude'],
                capacity=row['capacity'],
                platforms=row['platforms']
            )
            network.add_node(node)
        
        # Load edges
        cursor.execute("SELECT * FROM edges WHERE network_id = ?", (network_id,))
        for row in cursor.fetchall():
            track_type = TrackType(row['track_type'])
            edge = Edge(
                from_node=row['from_node'],
                to_node=row['to_node'],
                distance=row['distance'],
                track_type=track_type,
                max_speed=row['max_speed']
            )
            network.add_edge(edge)
        
        return network
    
    def save_train(self, train: Train) -> int:
        """
        Save a train to database.
        
        Args:
            train: Train instance to save
            
        Returns:
            Train ID in database
        """
        cursor = self.connection.cursor()
        
        # Check if train already exists
        cursor.execute("SELECT id FROM trains WHERE train_id = ?", (train.train_id,))
        existing = cursor.fetchone()
        
        if existing:
            return existing['id']
        
        cursor.execute(
            """INSERT INTO trains
               (train_id, train_type, max_speed, acceleration, braking, priority)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (train.train_id, train.train_type.value, train.max_speed,
             train.acceleration, train.braking, train.priority)
        )
        
        self.connection.commit()
        return cursor.lastrowid
    
    def save_schedule(self, schedule: TrainSchedule, network_id: int) -> int:
        """
        Save a train schedule to database.
        
        Args:
            schedule: TrainSchedule instance to save
            network_id: ID of associated network
            
        Returns:
            Schedule ID in database
        """
        cursor = self.connection.cursor()
        
        # Save schedule
        cursor.execute(
            """INSERT INTO schedules
               (schedule_id, train_id, network_id, departure_time)
               VALUES (?, ?, ?, ?)""",
            (schedule.schedule_id, schedule.train.train_id, network_id,
             schedule.departure_time.isoformat())
        )
        
        # Save stops
        for i, stop in enumerate(schedule.stops):
            cursor.execute(
                """INSERT INTO schedule_stops
                   (schedule_id, station_id, arrival_time, departure_time, stop_order)
                   VALUES (?, ?, ?, ?, ?)""",
                (schedule.schedule_id, stop['station'], 
                 stop['arrival'].isoformat(), stop['departure'].isoformat(), i)
            )
        
        self.connection.commit()
        return cursor.lastrowid
    
    def load_schedules_by_network(self, network_id: int) -> List[TrainSchedule]:
        """
        Load all schedules for a network.
        
        Args:
            network_id: ID of network
            
        Returns:
            List of TrainSchedule instances
        """
        cursor = self.connection.cursor()
        schedules = []
        
        # Get schedules
        cursor.execute(
            "SELECT * FROM schedules WHERE network_id = ?",
            (network_id,)
        )
        
        for sched_row in cursor.fetchall():
            # Get train
            cursor.execute(
                "SELECT * FROM trains WHERE train_id = ?",
                (sched_row['train_id'],)
            )
            train_row = cursor.fetchone()
            
            if not train_row:
                continue
            
            train_type = TrainType(train_row['train_type'])
            train = Train(
                train_id=train_row['train_id'],
                train_type=train_type,
                max_speed=train_row['max_speed'],
                acceleration=train_row['acceleration'],
                braking=train_row['braking'],
                priority=train_row['priority']
            )
            
            # Get stops
            cursor.execute(
                "SELECT * FROM schedule_stops WHERE schedule_id = ? ORDER BY stop_order",
                (sched_row['schedule_id'],)
            )
            
            stops = []
            route = []
            for stop_row in cursor.fetchall():
                stops.append({
                    'station': stop_row['station_id'],
                    'arrival': datetime.fromisoformat(stop_row['arrival_time']),
                    'departure': datetime.fromisoformat(stop_row['departure_time'])
                })
                route.append(stop_row['station_id'])
            
            schedule = TrainSchedule(
                schedule_id=sched_row['schedule_id'],
                train=train,
                route=route,
                departure_time=datetime.fromisoformat(sched_row['departure_time']),
                stops=stops
            )
            
            schedules.append(schedule)
        
        return schedules
    
    def get_all_networks(self) -> List[Dict]:
        """
        Get list of all networks in database.
        
        Returns:
            List of network dictionaries with id, name, created_at
        """
        cursor = self.connection.cursor()
        cursor.execute("SELECT id, name, created_at FROM networks ORDER BY created_at DESC")
        
        networks = []
        for row in cursor.fetchall():
            networks.append({
                'id': row['id'],
                'name': row['name'],
                'created_at': row['created_at']
            })
        
        return networks
    
    def delete_network(self, network_id: int):
        """Delete a network and all associated data."""
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM networks WHERE id = ?", (network_id,))
        self.connection.commit()
    
    def get_statistics(self) -> Dict:
        """Get database statistics."""
        cursor = self.connection.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM networks")
        networks_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM trains")
        trains_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM schedules")
        schedules_count = cursor.fetchone()['count']
        
        return {
            'networks': networks_count,
            'trains': trains_count,
            'schedules': schedules_count
        }
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
