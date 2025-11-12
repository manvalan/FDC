# FDC - Railway Manager and Simulator

A comprehensive train timetable management system for rail networks, using a graph-based representation where stations and interchanges are nodes and track segments are edges/connections.

## Features

- **Graph-based Rail Network**: Model rail networks with stations (nodes) and track segments (edges)
- **Train Timetable Management**: Create and manage train schedules with multiple stops
- **Pathfinding Algorithms**: Find shortest paths between stations (by time or distance)
- **Timetable Queries**: Query trains by station, time, and route
- **Bidirectional/Unidirectional Tracks**: Support for both types of track segments
- **Interchange Stations**: Support for major hubs and connection points

## Installation

No external dependencies required. The system uses only Python standard library.

```bash
git clone https://github.com/manvalan/FDC.git
cd FDC
```

## Usage

### Basic Example

```python
from rail_network import Station, TrackSegment, RailNetwork, Train, ScheduleEntry, Timetable
from datetime import datetime, timedelta

# Create a rail network
network = RailNetwork()

# Add stations
central = Station("Central Station", "interchange")
airport = Station("Airport", "station")

# Add track segment
track = TrackSegment(central, airport, distance=20.0, travel_time=25, bidirectional=True)
network.add_track_segment(track)

# Create a timetable
timetable = Timetable(network)

# Add a train with schedule
train = Train("T001", "Airport Express")
train.add_stop(ScheduleEntry(
    central,
    datetime(2024, 1, 15, 8, 0),
    datetime(2024, 1, 15, 8, 5),
    platform="1"
))
train.add_stop(ScheduleEntry(
    airport,
    datetime(2024, 1, 15, 8, 30),
    datetime(2024, 1, 15, 8, 30),
    platform="2"
))
timetable.add_train(train)
```

### Running the Example

```bash
python3 example_usage.py
```

This will demonstrate:
- Creating a sample rail network with 6 stations and 7 track segments
- Finding shortest paths between stations
- Managing train schedules
- Querying trains at specific stations and times

### Running Tests

```bash
python3 -m unittest test_rail_network -v
```

## Core Components

### Station
Represents a station or interchange in the rail network.

```python
station = Station("Central Station", station_type="interchange")
```

### TrackSegment
Represents a track segment connecting two stations.

```python
track = TrackSegment(
    from_station=station_a,
    to_station=station_b,
    distance=10.0,  # kilometers
    travel_time=15,  # minutes
    bidirectional=True
)
```

### RailNetwork
Manages the graph structure of the rail network.

```python
network = RailNetwork()
network.add_station(station)
network.add_track_segment(track)

# Find shortest path
path, cost = network.find_shortest_path("Station A", "Station B", by_time=True)
```

### Train
Represents a train with its schedule.

```python
train = Train("T001", "Express Train")
train.add_stop(schedule_entry)
```

### Timetable
Manages all trains in the network.

```python
timetable = Timetable(network)
timetable.add_train(train)

# Query trains
trains = timetable.get_trains_at_station("Central Station", datetime(2024, 1, 15, 9, 0))
trains = timetable.get_trains_between("Station A", "Station B")
```

## Key Features Explained

### Pathfinding
The system uses Dijkstra's algorithm to find optimal routes between stations:
- **By Time**: Minimize total travel time
- **By Distance**: Minimize total distance

```python
# Find fastest route
path, time = network.find_shortest_path("Start", "End", by_time=True)

# Find shortest route
path, distance = network.find_shortest_path("Start", "End", by_time=False)
```

### Timetable Queries

**Get trains at a specific station and time:**
```python
trains = timetable.get_trains_at_station("Central Station", datetime(2024, 1, 15, 9, 0))
```

**Get trains between two stations:**
```python
trains = timetable.get_trains_between("Origin", "Destination")
```

## Architecture

The system follows object-oriented design principles:

- **Station**: Node in the graph
- **TrackSegment**: Edge in the graph
- **RailNetwork**: Graph data structure with adjacency list
- **ScheduleEntry**: Individual stop in a train's schedule
- **Train**: Collection of schedule entries
- **Timetable**: Manager for all trains with query capabilities

## License

This project is open source and available for educational and commercial use.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
