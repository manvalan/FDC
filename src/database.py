"""
Database module for Railway Network System.
Provides MySQL persistence for networks, trains, schedules, and stations.
"""

import mysql.connector
from mysql.connector import Error
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

from node import Node, NodeType
from edge import Edge, TrackType
from train import Train, TrainType
from schedule import TrainSchedule, ScheduleStop
from railway_network import RailwayNetwork


class DatabaseManager:
    """Manages MySQL database connection and operations."""
    
    def __init__(self, host: str = "localhost", user: str = "root", 
                 password: str = "", database: str = "railway_network"):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
    
    def connect(self) -> bool:
        """Establish database connection."""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password
            )
            if self.connection.is_connected():
                cursor = self.connection.cursor()
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
                cursor.close()
                
                self.connection.database = self.database
                self._create_tables()
                return True
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            return False
    
    def disconnect(self):
        """Close database connection."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
    
    def _create_tables(self):
        """Create database schema if it doesn't exist."""
        cursor = self.connection.cursor()
        
        # Networks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS networks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata JSON
            )
        """)
        
        # Nodes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nodes (
                id VARCHAR(50) PRIMARY KEY,
                network_id INT,
                name VARCHAR(255) NOT NULL,
                node_type VARCHAR(50),
                latitude DOUBLE,
                longitude DOUBLE,
                capacity INT DEFAULT 2,
                platforms INT DEFAULT 2,
                FOREIGN KEY (network_id) REFERENCES networks(id) ON DELETE CASCADE
            )
        """)
        
        # Edges table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS edges (
                id INT AUTO_INCREMENT PRIMARY KEY,
                network_id INT,
                from_node VARCHAR(50),
                to_node VARCHAR(50),
                distance DOUBLE,
                track_type VARCHAR(50),
                max_speed INT,
                capacity INT DEFAULT 1,
                bidirectional BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (network_id) REFERENCES networks(id) ON DELETE CASCADE,
                FOREIGN KEY (from_node) REFERENCES nodes(id) ON DELETE CASCADE,
                FOREIGN KEY (to_node) REFERENCES nodes(id) ON DELETE CASCADE
            )
        """)
        
        # Trains table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trains (
                id VARCHAR(50) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                train_type VARCHAR(50),
                max_speed INT,
                acceleration DOUBLE,
                deceleration DOUBLE,
                length DOUBLE,
                capacity INT
            )
        """)
        
        # Schedules table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schedules (
                id VARCHAR(50) PRIMARY KEY,
                train_id VARCHAR(50),
                network_id INT,
                service_date DATE,
                priority INT DEFAULT 5,
                status VARCHAR(50) DEFAULT 'scheduled',
                total_delay INT DEFAULT 0,
                FOREIGN KEY (train_id) REFERENCES trains(id) ON DELETE CASCADE,
                FOREIGN KEY (network_id) REFERENCES networks(id) ON DELETE CASCADE
            )
        """)
        
        # Schedule stops table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schedule_stops (
                id INT AUTO_INCREMENT PRIMARY KEY,
                schedule_id VARCHAR(50),
                node_id VARCHAR(50),
                stop_order INT,
                arrival_time DATETIME,
                departure_time DATETIME,
                platform INT,
                stop_duration INT DEFAULT 2,
                delay_minutes INT DEFAULT 0,
                FOREIGN KEY (schedule_id) REFERENCES schedules(id) ON DELETE CASCADE,
                FOREIGN KEY (node_id) REFERENCES nodes(id) ON DELETE CASCADE
            )
        """)
        
        self.connection.commit()
        cursor.close()
    
    # ==================== NETWORK OPERATIONS ====================
    
    def save_network(self, network: RailwayNetwork) -> Optional[int]:
        """Save a railway network to database."""
        cursor = self.connection.cursor()
        
        try:
            # Insert network
            cursor.execute(
                "INSERT INTO networks (name, metadata) VALUES (%s, %s)",
                (network.name, json.dumps(network.get_network_stats()))
            )
            network_id = cursor.lastrowid
            
            # Insert nodes
            for node in network.nodes.values():
                cursor.execute("""
                    INSERT INTO nodes (id, network_id, name, node_type, latitude, 
                                     longitude, capacity, platforms)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (node.id, network_id, node.name, node.node_type.value,
                      node.latitude, node.longitude, node.capacity, node.platforms))
            
            # Insert edges
            for edge in network.edges:
                cursor.execute("""
                    INSERT INTO edges (network_id, from_node, to_node, distance,
                                     track_type, max_speed, capacity, bidirectional)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (network_id, edge.from_node, edge.to_node, edge.distance,
                      edge.track_type.value, edge.max_speed, edge.capacity, 
                      edge.bidirectional))
            
            self.connection.commit()
            return network_id
            
        except Error as e:
            print(f"Error saving network: {e}")
            self.connection.rollback()
            return None
        finally:
            cursor.close()
    
    def load_network(self, network_id: int) -> Optional[RailwayNetwork]:
        """Load a railway network from database."""
        cursor = self.connection.cursor(dictionary=True)
        
        try:
            # Get network info
            cursor.execute("SELECT * FROM networks WHERE id = %s", (network_id,))
            net_data = cursor.fetchone()
            if not net_data:
                return None
            
            network = RailwayNetwork(net_data['name'])
            
            # Load nodes
            cursor.execute("SELECT * FROM nodes WHERE network_id = %s", (network_id,))
            for row in cursor.fetchall():
                node = Node(
                    node_id=row['id'],
                    name=row['name'],
                    node_type=NodeType(row['node_type']),
                    latitude=row['latitude'],
                    longitude=row['longitude'],
                    capacity=row['capacity'],
                    platforms=row['platforms']
                )
                network.add_node(node)
            
            # Load edges
            cursor.execute("SELECT * FROM edges WHERE network_id = %s", (network_id,))
            for row in cursor.fetchall():
                edge = Edge(
                    from_node=row['from_node'],
                    to_node=row['to_node'],
                    distance=row['distance'],
                    track_type=TrackType(row['track_type']),
                    max_speed=row['max_speed'],
                    capacity=row['capacity'],
                    bidirectional=bool(row['bidirectional'])
                )
                network.add_edge(edge)
            
            return network
            
        except Error as e:
            print(f"Error loading network: {e}")
            return None
        finally:
            cursor.close()
    
    def list_networks(self) -> List[Dict]:
        """List all networks in database."""
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute("SELECT id, name, created_at FROM networks")
        networks = cursor.fetchall()
        cursor.close()
        return networks
    
    # ==================== TRAIN OPERATIONS ====================
    
    def save_train(self, train: Train) -> bool:
        """Save a train to database."""
        cursor = self.connection.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO trains (id, name, train_type, max_speed, acceleration,
                                  deceleration, length, capacity)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                name=VALUES(name), train_type=VALUES(train_type),
                max_speed=VALUES(max_speed), acceleration=VALUES(acceleration),
                deceleration=VALUES(deceleration), length=VALUES(length),
                capacity=VALUES(capacity)
            """, (train.id, train.name, train.train_type.value, train.max_speed,
                  train.acceleration, train.deceleration, train.length, train.capacity))
            
            self.connection.commit()
            return True
            
        except Error as e:
            print(f"Error saving train: {e}")
            self.connection.rollback()
            return False
        finally:
            cursor.close()
    
    def load_train(self, train_id: str) -> Optional[Train]:
        """Load a train from database."""
        cursor = self.connection.cursor(dictionary=True)
        
        try:
            cursor.execute("SELECT * FROM trains WHERE id = %s", (train_id,))
            row = cursor.fetchone()
            if not row:
                return None
            
            train = Train(
                train_id=row['id'],
                name=row['name'],
                train_type=TrainType(row['train_type']),
                max_speed=row['max_speed'],
                acceleration=row['acceleration'],
                deceleration=row['deceleration'],
                length=row['length'],
                capacity=row['capacity']
            )
            return train
            
        except Error as e:
            print(f"Error loading train: {e}")
            return None
        finally:
            cursor.close()
    
    # ==================== SCHEDULE OPERATIONS ====================
    
    def save_schedule(self, schedule: TrainSchedule, network_id: int) -> bool:
        """Save a train schedule to database."""
        cursor = self.connection.cursor()
        
        try:
            # Save train first
            self.save_train(schedule.train)
            
            # Save schedule
            cursor.execute("""
                INSERT INTO schedules (id, train_id, network_id, service_date,
                                     priority, status, total_delay)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                priority=VALUES(priority), status=VALUES(status),
                total_delay=VALUES(total_delay)
            """, (schedule.schedule_id, schedule.train.id, network_id,
                  schedule.service_date, schedule.priority, schedule.status,
                  schedule.total_delay))
            
            # Delete existing stops
            cursor.execute("DELETE FROM schedule_stops WHERE schedule_id = %s",
                          (schedule.schedule_id,))
            
            # Save stops
            for idx, stop in enumerate(schedule.stops):
                cursor.execute("""
                    INSERT INTO schedule_stops (schedule_id, node_id, stop_order,
                                               arrival_time, departure_time, platform,
                                               stop_duration, delay_minutes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (schedule.schedule_id, stop.node_id, idx,
                      stop.arrival_time, stop.departure_time, stop.platform,
                      stop.stop_duration, stop.delay_minutes))
            
            self.connection.commit()
            return True
            
        except Error as e:
            print(f"Error saving schedule: {e}")
            self.connection.rollback()
            return False
        finally:
            cursor.close()
    
    def load_schedule(self, schedule_id: str) -> Optional[TrainSchedule]:
        """Load a train schedule from database."""
        cursor = self.connection.cursor(dictionary=True)
        
        try:
            # Get schedule info
            cursor.execute("SELECT * FROM schedules WHERE id = %s", (schedule_id,))
            sched_data = cursor.fetchone()
            if not sched_data:
                return None
            
            # Load train
            train = self.load_train(sched_data['train_id'])
            if not train:
                return None
            
            # Load stops
            cursor.execute("""
                SELECT * FROM schedule_stops 
                WHERE schedule_id = %s 
                ORDER BY stop_order
            """, (schedule_id,))
            
            stops = []
            for row in cursor.fetchall():
                stop = ScheduleStop(
                    node_id=row['node_id'],
                    arrival_time=row['arrival_time'],
                    departure_time=row['departure_time'],
                    platform=row['platform'],
                    stop_duration=row['stop_duration']
                )
                stop.delay_minutes = row['delay_minutes']
                stops.append(stop)
            
            schedule = TrainSchedule(
                schedule_id=sched_data['id'],
                train=train,
                stops=stops,
                service_date=sched_data['service_date'],
                priority=sched_data['priority']
            )
            schedule.status = sched_data['status']
            schedule.total_delay = sched_data['total_delay']
            
            return schedule
            
        except Error as e:
            print(f"Error loading schedule: {e}")
            return None
        finally:
            cursor.close()
    
    def list_schedules(self, network_id: Optional[int] = None,
                      service_date: Optional[datetime] = None) -> List[Dict]:
        """List schedules with optional filters."""
        cursor = self.connection.cursor(dictionary=True)
        
        query = "SELECT s.*, t.name as train_name FROM schedules s JOIN trains t ON s.train_id = t.id WHERE 1=1"
        params = []
        
        if network_id:
            query += " AND s.network_id = %s"
            params.append(network_id)
        
        if service_date:
            query += " AND s.service_date = %s"
            params.append(service_date.date())
        
        cursor.execute(query, params)
        schedules = cursor.fetchall()
        cursor.close()
        return schedules
