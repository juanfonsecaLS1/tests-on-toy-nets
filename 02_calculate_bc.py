import osmnx as ox
import networkx as nx
import os
import numpy as np
import geopandas as gpd
import momepy as mp
import pandas as pd
import sys
sys.path.insert(0, 'spatial-centrality-pub/algo')
import centrality as sbc
import net_helper as nh
from superblockify.metrics.measures import betweenness_centrality as sb_betweenness_centrality
from superblockify.metrics.distances import calculate_path_distance_matrix as sb_calculate_path_distance_matrix

# list of graph files in the "graphs" folder
graph_files = [f for f in os.listdir("graphs") if f.endswith(".graphml")]

for graph_file in graph_files:
    city_name = graph_file.split(".")[0]
    print(f"Processing {city_name}...")
    graph_file_path = f"graphs/{graph_file}"
    net_file_path = f"raw_nets_gpkg/{city_name}.gpkg"
    results_path = f"raw_nets_gpkg/bc_{city_name}.gpkg"
    
     # Load the graph
    graph = ox.load_graphml(graph_file_path)
    # Load the tessellation nodes
    tessellation_nodes = gpd.read_file(net_file_path, layer="tessellation")
    edges_proj = gpd.read_file(net_file_path, layer="edges")
    c_standard = nx.edge_betweenness_centrality(graph, normalized=True, weight='travel_time')
    c_spatial = sbc.spatial_betweenness_centrality(graph, tessellation_nodes, tessellation_nodes, normalized=True, weight='travel_time')
    node_order = list(graph.nodes)
    matrix, predecessors = sb_calculate_path_distance_matrix(graph, weight = "travel_time", node_order = node_order)
    sb_betweenness_centrality(graph, node_order, matrix, predecessors, weight="travel_time")
    tdf = pd.DataFrame({
        'u': [u for u, v, k in graph.edges(keys=True)],
        'v': [v for u, v, k in graph.edges(keys=True)],
        'key': [k for u, v, k in graph.edges(keys=True)],
        'edge_betweenness_normal': [data.get('edge_betweenness_normal', 0) for u, v, k, data in graph.edges(keys=True, data=True)],
        'edge_betweenness_length': [data.get('edge_betweenness_length', 0) for u, v, k, data in graph.edges(keys=True, data=True)],
        'edge_betweenness_linear': [data.get('edge_betweenness_linear', 0) for u, v, k, data in graph.edges(keys=True, data=True)],
        'c_standard': [c_standard.get((u, v, k), 0) for u, v, k in graph.edges(keys=True)],
        'c_spatial': [c_spatial.get((u, v, k), 0) for u, v, k in graph.edges(keys=True)]
        })
    edges_with_centrality = edges_proj.merge(
        tdf, 
        on=['u', 'v', 'key'], 
        how='left'
        )
    edges_with_centrality.to_file(results_path, layer='edges_bc', driver='GPKG')