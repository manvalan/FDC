"""
Railway Network module.
Main class for managing the railway infrastructure as a graph.
"""

import networkx as nx
import matplotlib.pyplot as plt
from typing import List, Optional, Dict, Tuple
import json
from datetime import datetime

from node import Node, NodeType
from edge import Edge, TrackType


class RailwayNetwork:
    """
    Manages the railway network as a directed graph.
    
    Attributes:
        graph: NetworkX DiGraph representing the railway network
        nodes: Dictionary of Node objects indexed by node_id
        edges: List of Edge objects
    """
    
    def __init__(self, name: str = "Railway Network"):
        self.name = name
        self.graph = nx.DiGraph()
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []
    
    def add_node(self, node: Node) -> bool:
        """
        Add a node to the network.
        
        Args:
            node: Node object to add
            
        Returns:
            bool: True if added, False if already exists
        """
        if node.id in self.nodes:
            return False
        
        self.nodes[node.id] = node
        self.graph.add_node(
            node.id,
            name=node.name,
            type=node.node_type.value,
            pos=(node.longitude, node.latitude)
        )
        return True
    
    def add_edge(self, edge: Edge) -> bool:
        """
        Add an edge to the network.
        
        Args:
            edge: Edge object to add
            
        Returns:
            bool: True if added, False if nodes don't exist
        """
        if edge.from_node not in self.nodes or edge.to_node not in self.nodes:
            return False
        
        self.edges.append(edge)
        self.graph.add_edge(
            edge.from_node,
            edge.to_node,
            weight=edge.get_weight(),
            distance=edge.distance,
            max_speed=edge.max_speed,
            track_type=edge.track_type.value
        )
        
        # Add reverse edge if bidirectional
        if edge.bidirectional:
            self.graph.add_edge(
                edge.to_node,
                edge.from_node,
                weight=edge.get_weight(),
                distance=edge.distance,
                max_speed=edge.max_speed,
                track_type=edge.track_type.value
            )
        
        return True
    
    def remove_node(self, node_id: str) -> bool:
        """Remove a node from the network."""
        if node_id not in self.nodes:
            return False
        
        del self.nodes[node_id]
        self.graph.remove_node(node_id)
        
        # Remove edges connected to this node
        self.edges = [e for e in self.edges 
                     if e.from_node != node_id and e.to_node != node_id]
        return True
    
    def get_node(self, node_id: str) -> Optional[Node]:
        """Get a node by ID."""
        return self.nodes.get(node_id)
    
    def find_shortest_path(
        self,
        start_id: str,
        end_id: str,
        weight: str = 'weight'
    ) -> Optional[Tuple[List[str], float]]:
        """
        Find the shortest path between two nodes using Dijkstra's algorithm.
        
        Args:
            start_id: Starting node ID
            end_id: Destination node ID
            weight: Edge attribute to use as weight (default: 'weight')
            
        Returns:
            Tuple of (path as list of node IDs, total distance) or None if no path exists
        """
        if start_id not in self.nodes or end_id not in self.nodes:
            return None
        
        try:
            path = nx.shortest_path(
                self.graph,
                start_id,
                end_id,
                weight=weight
            )
            distance = nx.shortest_path_length(
                self.graph,
                start_id,
                end_id,
                weight=weight
            )
            return path, distance
        except nx.NetworkXNoPath:
            return None
    
    def find_all_paths(
        self,
        start_id: str,
        end_id: str,
        max_paths: int = 5
    ) -> List[List[str]]:
        """
        Find multiple paths between two nodes.
        
        Args:
            start_id: Starting node ID
            end_id: Destination node ID
            max_paths: Maximum number of paths to return
            
        Returns:
            List of paths (each path is a list of node IDs)
        """
        if start_id not in self.nodes or end_id not in self.nodes:
            return []
        
        try:
            paths = list(nx.shortest_simple_paths(
                self.graph,
                start_id,
                end_id,
                weight='weight'
            ))
            return paths[:max_paths]
        except nx.NetworkXNoPath:
            return []
    
    def get_connected_nodes(self, node_id: str) -> List[str]:
        """Get all nodes directly connected to the given node."""
        if node_id not in self.nodes:
            return []
        return list(self.graph.neighbors(node_id))
    
    def get_network_stats(self) -> Dict:
        """Get statistics about the network."""
        return {
            'num_nodes': len(self.nodes),
            'num_edges': len(self.edges),
            'num_stations': sum(1 for n in self.nodes.values() 
                              if n.node_type == NodeType.STATION),
            'num_interchanges': sum(1 for n in self.nodes.values() 
                                   if n.node_type == NodeType.INTERCHANGE),
            'total_track_length': sum(e.distance for e in self.edges),
            'is_connected': nx.is_weakly_connected(self.graph),
            'average_degree': sum(dict(self.graph.degree()).values()) / len(self.nodes) 
                            if self.nodes else 0
        }
    
    def visualize(
        self,
        figsize: Optional[Tuple[int, int]] = None,
        with_labels: bool = True,
        save_path: Optional[str] = None
    ):
        """
        Visualize the railway network.
        
        Args:
            figsize: Figure size (width, height). If None, auto-calculated from data
            with_labels: Whether to show node labels
            save_path: Path to save the figure (optional)
        """
        # Get positions
        pos = nx.get_node_attributes(self.graph, 'pos')
        
        # If no positions set, use spring layout
        if not pos:
            pos = nx.spring_layout(self.graph, k=2, iterations=50)
        
        # Auto-calculate figsize based on coordinate range if not specified
        if figsize is None and pos:
            x_coords = [p[0] for p in pos.values()]
            y_coords = [p[1] for p in pos.values()]
            x_range = max(x_coords) - min(x_coords)
            y_range = max(y_coords) - min(y_coords)
            
            # Calculate aspect ratio, with reasonable limits
            aspect_ratio = x_range / y_range if y_range > 0 else 1.0
            
            # Base size with reasonable bounds
            base_height = min(max(10, y_range / 50), 20)  # Between 10 and 20
            base_width = base_height * aspect_ratio
            
            # Ensure width is also within reasonable bounds
            base_width = min(max(12, base_width), 24)
            
            figsize = (base_width, base_height)
        elif figsize is None:
            figsize = (12, 8)
        
        plt.figure(figsize=figsize)
        
        # Color nodes by type
        node_colors = []
        for node_id in self.graph.nodes():
            node = self.nodes[node_id]
            if node.node_type == NodeType.STATION:
                node_colors.append('lightblue')
            elif node.node_type == NodeType.INTERCHANGE:
                node_colors.append('orange')
            else:
                node_colors.append('lightgreen')
        
        # Draw the network
        nx.draw_networkx_nodes(
            self.graph,
            pos,
            node_color=node_colors,
            node_size=500,
            alpha=0.9
        )
        
        nx.draw_networkx_edges(
            self.graph,
            pos,
            alpha=0.5,
            arrows=True,
            arrowsize=20,
            edge_color='gray'
        )
        
        if with_labels:
            labels = {node_id: self.nodes[node_id].name 
                     for node_id in self.graph.nodes()}
            nx.draw_networkx_labels(self.graph, pos, labels, font_size=8)
            
            # Draw edge labels (distances)
            edge_labels = nx.get_edge_attributes(self.graph, 'distance')
            edge_labels = {k: f"{v:.1f}km" for k, v in edge_labels.items()}
            nx.draw_networkx_edge_labels(self.graph, pos, edge_labels, font_size=6)
        
        plt.title(f"{self.name}\n{len(self.nodes)} nodes, {len(self.edges)} tracks", 
                 fontsize=12, pad=20)
        plt.axis('off')
        
        # Optimize layout to fit visible window
        plt.tight_layout(pad=0.5)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', pad_inches=0.1)
        
        plt.show()
    
    def export_to_json(self, filepath: str, include_stats: bool = True):
        """Export network to JSON file.
        
        Args:
            filepath: Path to save JSON file
            include_stats: Whether to include network statistics
        """
        data = {
            'name': self.name,
            'nodes': [node.to_dict() for node in self.nodes.values()],
            'edges': [edge.to_dict() for edge in self.edges]
        }
        
        if include_stats:
            data['statistics'] = self.get_network_stats()
            data['export_timestamp'] = datetime.now().isoformat()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def import_from_json(self, filepath: str):
        """Import network from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.name = data.get('name', 'Railway Network')
        
        # Import nodes
        for node_data in data.get('nodes', []):
            node = Node(
                node_id=node_data['id'],
                name=node_data['name'],
                node_type=NodeType(node_data['type']),
                latitude=node_data.get('latitude', 0.0),
                longitude=node_data.get('longitude', 0.0),
                capacity=node_data.get('capacity', 2),
                platforms=node_data.get('platforms', 2)
            )
            self.add_node(node)
        
        # Import edges
        for edge_data in data.get('edges', []):
            edge = Edge(
                from_node=edge_data['from_node'],
                to_node=edge_data['to_node'],
                distance=edge_data['distance'],
                track_type=TrackType(edge_data.get('track_type', 'single')),
                max_speed=edge_data.get('max_speed', 120),
                capacity=edge_data.get('capacity', 1),
                bidirectional=edge_data.get('bidirectional', True)
            )
            self.add_edge(edge)
    
    def __str__(self) -> str:
        return f"RailwayNetwork('{self.name}', {len(self.nodes)} nodes, {len(self.edges)} edges)"
    
    def __repr__(self) -> str:
        return self.__str__()
