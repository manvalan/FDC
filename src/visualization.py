"""
Visualization utilities for the Railway Network Project.

Provides a timetable / time-distance plot (train diagram) where the
vertical axis is distance along a route (km) and the horizontal axis is time.
"""
from typing import List, Dict, Optional
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from schedule import TrainSchedule


def compute_node_km_mapping(route: List[str], network) -> Dict[str, float]:
    """Compute cumulative km positions for nodes along a given route.

    Args:
        route: ordered list of node IDs along the route
        network: RailwayNetwork instance

    Returns:
        dict mapping node_id -> km (float)
    """
    km_map = {route[0]: 0.0}
    cum = 0.0
    for i in range(len(route) - 1):
        a = route[i]
        b = route[i + 1]
        # find edge distance
        dist = None
        for e in network.edges:
            if e.from_node == a and e.to_node == b:
                dist = e.distance
                break
            if e.bidirectional and e.from_node == b and e.to_node == a:
                dist = e.distance
                break
        if dist is None:
            raise ValueError(f"No edge between {a} and {b} to compute km positions")
        cum += dist
        km_map[b] = cum
    return km_map


def plot_timetable(
    route: List[str],
    schedules: List[TrainSchedule],
    network,
    filename: Optional[str] = None,
    figsize: Optional[tuple] = None,
    show_conflicts: bool = True
):
    """Plot a time-distance diagram for the given route and schedules.

    Args:
        route: ordered list of node IDs for the line to plot
        schedules: list of TrainSchedule objects (services to draw)
        network: RailwayNetwork instance
        filename: optional path to save the figure (PNG)
        figsize: matplotlib figure size. If None, auto-calculated from data
        show_conflicts: if True, highlight single-track conflicts
    """
    # Compute km mapping for nodes
    km_map = compute_node_km_mapping(route, network)
    
    # Auto-calculate figsize if not specified
    if figsize is None:
        max_km = max(km_map.values()) if km_map else 100
        num_trains = len(schedules)
        
        # Calculate width based on time span
        if schedules:
            all_times = []
            for sched in schedules:
                for stop in sched.stops:
                    if stop.arrival_time:
                        all_times.append(stop.arrival_time)
                    if stop.departure_time:
                        all_times.append(stop.departure_time)
            
            if all_times:
                time_span_hours = (max(all_times) - min(all_times)).total_seconds() / 3600
                width = min(max(12, time_span_hours * 2), 24)
            else:
                width = 14
        else:
            width = 14
        
        # Calculate height based on route length
        height = min(max(8, max_km / 20), 16)
        
        figsize = (width, height)

    # Prepare plot
    fig, ax = plt.subplots(figsize=figsize)

    # Date formatter for x axis
    ax.xaxis_date()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.grid(True, which='both', axis='x', linestyle='--', alpha=0.5)

    colors = plt.cm.tab10
    
    # Identify single-track sections for conflict visualization
    single_track_sections = []
    if show_conflicts:
        for i in range(len(route) - 1):
            a, b = route[i], route[i+1]
            for e in network.edges:
                if ((e.from_node == a and e.to_node == b) or 
                    (e.bidirectional and e.from_node == b and e.to_node == a)):
                    if e.track_type.value == 'single' or e.capacity == 1:
                        single_track_sections.append((km_map[a], km_map[b]))
                    break
    
    # Draw shaded regions for single-track sections
    for km_start, km_end in single_track_sections:
        ax.axhspan(km_start, km_end, alpha=0.1, color='red', 
                   label='Single Track' if (km_start, km_end) == single_track_sections[0] else '')

    for idx, sched in enumerate(schedules):
        times = []
        kms = []
        stops_data = []  # (time, km, stop_obj)
        
        # Only use stops that belong to the route
        for stop in sched.stops:
            if stop.node_id in km_map:
                # Add arrival time
                if stop.arrival_time:
                    times.append(mdates.date2num(stop.arrival_time))
                    kms.append(km_map[stop.node_id])
                    stops_data.append((mdates.date2num(stop.arrival_time), km_map[stop.node_id], stop))
                
                # Add departure time (creates horizontal line for stop duration)
                if stop.departure_time and stop.arrival_time != stop.departure_time:
                    times.append(mdates.date2num(stop.departure_time))
                    kms.append(km_map[stop.node_id])
                    stops_data.append((mdates.date2num(stop.departure_time), km_map[stop.node_id], stop))
                elif stop.departure_time and not stop.arrival_time:
                    # First stop (departure only)
                    times.append(mdates.date2num(stop.departure_time))
                    kms.append(km_map[stop.node_id])
                    stops_data.append((mdates.date2num(stop.departure_time), km_map[stop.node_id], stop))

        if len(times) >= 2:
            color = colors(idx % 10)
            ax.plot_date(times, kms, '-', label=f"{sched.train.name}",
                         color=color, linewidth=2.5, alpha=0.8)
            # Mark stops with circles
            ax.plot_date(times, kms, 'o', color=color, markersize=6)
            
            # Add train name label at midpoint of journey
            mid_idx = len(times) // 2
            ax.annotate(sched.train.name, 
                       xy=(times[mid_idx], kms[mid_idx]),
                       xytext=(10, 0), textcoords='offset points',
                       fontsize=9, color=color, fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                                edgecolor=color, alpha=0.7))
            
            # Show delays if any
            if sched.total_delay > 0:
                ax.annotate(f'+{sched.total_delay}m', 
                           xy=(times[-1], kms[-1]),
                           xytext=(5, -15), textcoords='offset points',
                           fontsize=8, color='red', style='italic')
            
            # Annotate stop durations on horizontal segments
            for stop in sched.stops:
                if stop.node_id in km_map and stop.arrival_time and stop.departure_time:
                    if stop.arrival_time != stop.departure_time:
                        stop_duration_mins = (stop.departure_time - stop.arrival_time).total_seconds() / 60
                        if stop_duration_mins > 1:  # Only show if > 1 minute
                            mid_time = mdates.date2num(stop.arrival_time) + (mdates.date2num(stop.departure_time) - mdates.date2num(stop.arrival_time)) / 2
                            ax.annotate(f'{int(stop_duration_mins)}min', 
                                       xy=(mid_time, km_map[stop.node_id]),
                                       xytext=(0, -8), textcoords='offset points',
                                       fontsize=7, color=color, style='italic',
                                       ha='center', alpha=0.7)
        elif len(times) == 1:
            ax.plot_date(times, kms, 'o', color=colors(idx % 10), markersize=6)

    # Detect and mark conflicts on single-track sections
    if show_conflicts and len(schedules) > 1:
        conflicts_found = _detect_track_conflicts(schedules, route, km_map, network)
        for conflict in conflicts_found:
            # Draw a red 'X' or warning marker at conflict location
            ax.plot_date([conflict['time']], [conflict['km']], 'rx', 
                        markersize=15, markeredgewidth=3, label='Conflict' if conflict == conflicts_found[0] else '')
            ax.annotate(f"⚠️ Conflict\n{conflict['trains']}", 
                       xy=(conflict['time'], conflict['km']),
                       xytext=(15, 15), textcoords='offset points',
                       fontsize=8, color='red', fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.4', facecolor='yellow', 
                                edgecolor='red', alpha=0.9),
                       arrowprops=dict(arrowstyle='->', color='red', lw=1.5))

    # Y axis: station labels and km
    y_ticks = [km_map[n] for n in route]
    y_labels = []
    for n in route:
        node = network.get_node(n)
        name = node.name if node else n
        y_labels.append(f"{name} ({km_map[n]:.0f} km)")

    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_labels)
    ax.invert_yaxis()  # top station at top (optional - depends on preference)

    ax.set_xlabel('Time', fontsize=12, fontweight='bold')
    ax.set_ylabel('Station (km)', fontsize=12, fontweight='bold')
    ax.set_title('Time-Distance Diagram (Train Graph)', fontsize=14, fontweight='bold')
    # ax.legend(loc='upper left', fontsize=9, framealpha=0.9)  # Legend removed - train labels are sufficient
    fig.autofmt_xdate()

    # Optimize layout to fit visible window
    plt.tight_layout(pad=0.5)
    
    if filename:
        plt.savefig(filename, dpi=300, bbox_inches='tight', pad_inches=0.1)
        plt.close()  # Close the figure to avoid opening a window
    else:
        plt.show()  # Only show if no filename (for standalone use)


def _detect_track_conflicts(schedules: List[TrainSchedule], route: List[str], 
                            km_map: Dict[str, float], network) -> List[Dict]:
    """Detect conflicts where two trains overlap on single-track sections or same platform.
    
    Returns:
        List of conflict dicts with 'time', 'km', 'trains' keys
    """
    conflicts = []
    
    # 1. Check track conflicts (single-track sections only)
    for i in range(len(route) - 1):
        node_a, node_b = route[i], route[i+1]
        
        # Check if this is a single-track section
        # A section is single-track ONLY if track_type is explicitly SINGLE
        is_single_track = False
        for e in network.edges:
            if ((e.from_node == node_a and e.to_node == node_b) or
                (e.bidirectional and e.from_node == node_b and e.to_node == node_a)):
                # Only consider it single-track if explicitly set as SINGLE
                # DOUBLE, HIGH_SPEED, etc. are NOT single-track
                if e.track_type.value == 'single':
                    is_single_track = True
                break
        
        if not is_single_track:
            continue
        
        # Find all trains using this section and their time windows
        train_windows = []
        for sched in schedules:
            # Find if this train uses this segment
            for j in range(len(sched.stops) - 1):
                stop_from = sched.stops[j]
                stop_to = sched.stops[j+1]
                
                # Check if this segment matches (in either direction)
                if ((stop_from.node_id == node_a and stop_to.node_id == node_b) or
                    (stop_from.node_id == node_b and stop_to.node_id == node_a)):
                    
                    dep_time = stop_from.departure_time
                    arr_time = stop_to.arrival_time
                    
                    if dep_time and arr_time:
                        train_windows.append({
                            'train': sched.train.name,
                            'start': mdates.date2num(dep_time),
                            'end': mdates.date2num(arr_time),
                            'direction': 'forward' if stop_from.node_id == node_a else 'backward'
                        })
        
        # Check for overlaps
        for idx1, w1 in enumerate(train_windows):
            for w2 in train_windows[idx1+1:]:
                # Check if time windows overlap
                if not (w1['end'] <= w2['start'] or w2['end'] <= w1['start']):
                    # Conflict detected
                    conflict_time = max(w1['start'], w2['start'])
                    conflict_km = (km_map[node_a] + km_map[node_b]) / 2
                    conflicts.append({
                        'time': conflict_time,
                        'km': conflict_km,
                        'trains': f"{w1['train']} vs {w2['train']}"
                    })
    
    # 2. Check platform conflicts at stations
    # Build platform usage: {node_id: {platform: [(train_name, arrival, departure)]}}
    platform_usage = {}
    
    for sched in schedules:
        for stop in sched.stops:
            if not stop.platform or stop.node_id not in route:
                continue
            
            arrival = stop.arrival_time or stop.departure_time
            departure = stop.departure_time or stop.arrival_time
            
            if not arrival or not departure:
                continue
            
            node_id = stop.node_id
            platform = stop.platform
            
            if node_id not in platform_usage:
                platform_usage[node_id] = {}
            if platform not in platform_usage[node_id]:
                platform_usage[node_id][platform] = []
            
            platform_usage[node_id][platform].append({
                'train': sched.train.name,
                'arrival': arrival,
                'departure': departure
            })
    
    # Check for platform overlaps
    for node_id, platforms in platform_usage.items():
        if node_id not in km_map:
            continue
        
        for platform, usages in platforms.items():
            # Sort by arrival
            usages.sort(key=lambda x: x['arrival'])
            
            # Check consecutive pairs
            for i in range(len(usages) - 1):
                u1 = usages[i]
                u2 = usages[i + 1]
                
                # Check if time windows overlap on same platform
                if u1['departure'] > u2['arrival']:
                    conflict_time = mdates.date2num(max(u1['arrival'], u2['arrival']))
                    conflict_km = km_map[node_id]
                    conflicts.append({
                        'time': conflict_time,
                        'km': conflict_km,
                        'trains': f"{u1['train']} vs {u2['train']} (Platform {platform})"
                    })
    
    return conflicts
