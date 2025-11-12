"""
Plotter module for Railway Network System.
Creates time-distance diagrams (train graph) showing station positions on the vertical
axis (km) and time on the horizontal axis.
"""
from typing import List, Optional
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from schedule import TrainSchedule
from railway_network import RailwayNetwork


def _compute_cumulative_distances(route: List[str], network: RailwayNetwork) -> dict:
    """Compute cumulative distances (km) for each node along the route."""
    cum = {route[0]: 0.0}
    total = 0.0
    for i in range(len(route) - 1):
        a = route[i]
        b = route[i+1]
        # find edge
        dist = None
        for e in network.edges:
            if e.from_node == a and e.to_node == b:
                dist = e.distance
                break
            if e.bidirectional and e.from_node == b and e.to_node == a:
                dist = e.distance
                break
        if dist is None:
            raise ValueError(f"Edge not found between {a} and {b}")
        total += dist
        cum[b] = total
    return cum


def plot_time_distance(
    schedules: List[TrainSchedule],
    network: RailwayNetwork,
    route: Optional[List[str]] = None,
    figsize: tuple = (12, 8),
    show: bool = True,
    save_path: Optional[str] = None
):
    """
    Plot time-distance diagram for the given schedules on a specific route.

    Args:
        schedules: list of TrainSchedule objects
        network: RailwayNetwork instance
        route: sequence of node IDs defining the line; if None, inferred from first schedule
        figsize: figure size
        show: whether to call plt.show()
        save_path: optional file path to save the figure
    """
    if not schedules:
        raise ValueError("No schedules provided")

    if route is None:
        # infer route from first schedule
        route = schedules[0].route

    # compute distances for nodes on the route
    cum_dist = _compute_cumulative_distances(route, network)

    plt.figure(figsize=figsize)

    ax = plt.gca()

    # Colors for trains
    cmap = plt.get_cmap('tab10')

    for idx, sched in enumerate(sorted(schedules, key=lambda s: s.get_departure_time() or datetime.min)):
        # build x (times) and y (distances)
        times = []
        dists = []
        for stop in sched.stops:
            if stop.node_id not in cum_dist:
                # skip stops not on this route
                continue
            # choose arrival if available, else departure
            if stop.arrival_time:
                t = stop.arrival_time
            elif stop.departure_time:
                t = stop.departure_time
            else:
                continue
            times.append(mdates.date2num(t))
            dists.append(cum_dist[stop.node_id])
            # also add departure time as separate point if exists and different
            if stop.departure_time and stop.arrival_time and stop.departure_time != stop.arrival_time:
                times.append(mdates.date2num(stop.departure_time))
                dists.append(cum_dist[stop.node_id])
        if not times:
            continue
        # sort by time
        pairs = sorted(zip(times, dists))
        times_sorted = [p[0] for p in pairs]
        dists_sorted = [p[1] for p in pairs]

        ax.plot_date(times_sorted, dists_sorted, '-o', label=f"{sched.train.name} ({sched.schedule_id})",
                     color=cmap(idx % 10))
        # annotate train name at first point
        ax.annotate(sched.train.name, (times_sorted[0], dists_sorted[0]), xytext=(5, 5), textcoords='offset points', fontsize=8)

    # draw horizontal lines for stations with labels
    yticks = []
    ylabels = []
    for node in route:
        y = cum_dist[node]
        yticks.append(y)
        node_obj = network.get_node(node)
        label = node if node_obj is None else f"{node_obj.name} ({node})"
        ylabels.append(label)
        ax.hlines(y, xmin=mdates.date2num(datetime(1970,1,1)), xmax=mdates.date2num(datetime(3000,1,1)), colors='lightgray', linestyles='dashed', linewidth=0.5)

    ax.set_yticks(yticks)
    ax.set_yticklabels(ylabels)
    ax.invert_yaxis()  # so origin/top is at top like typical diagrams (optional)

    # format x-axis as time
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.xlabel('Time')
    plt.ylabel('Station (cumulative km)')
    plt.title('Time-Distance Diagram')
    plt.legend(loc='best', fontsize=8)
    plt.grid(True, which='both', axis='x', linestyle='--', alpha=0.3)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300)

    if show:
        plt.show()

    return ax
