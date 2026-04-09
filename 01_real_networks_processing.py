import osmnx as ox
import os
import numpy as np
import geopandas as gpd
import momepy as mp


cities = [
    {"name": "Lima","long_name": "Lima Metropolitan Area", "lat": -12.077948042115647, "lon": -77.05096688507561},
    {"name": "Brussels","long_name": "Brussels, Belgium", "lat": 50.856117793777145, "lon": 4.381718424984715},
    # {"name": "Rome","long_name": "Rome, Italy", "lat": 41.89900799198937, "lon": 12.512797548177907},
    # {"name": "Cairo","long_name": "Cairo, Egypt", "lat": 30.036716997454857, "lon": 31.23947439245143},
    {"name": "Salt Lake City","long_name": "Salt Lake City, US", "lat": 40.75984495218752, "lon": -111.88769690322184},
    {"name": "Bogota","long_name": "Bogota, Colombia", "lat": 4.646242884611647, "lon": -74.08436455625211},
    {"name": "Leeds","long_name": "Leeds, UK", "lat": 53.81303429075668,  "lon": -1.508881353201933},
    {"name": "Milton Keynes","long_name": "Milton Keynes, UK", "lat": 52.0367171540023, "lon": -0.7324001661371712},
    {"name": "Lisbon","long_name": "Lisbon, Portugal", "lat": 38.72778849555562, "lon": -9.162267565552924},
    # {"name": "New York","long_name": "New York, US", "lat": 40.7589664816669, "lon": -73.96121069380527},
    # {"name": "Brasilia","long_name": "Brasilia, Brasil", "lat": -15.76133509896713, "lon": -47.88377302616466},
    # {"name": "Sao Paulo","long_name": "Sao Paulo, Brasil", "lat": -23.54468352821393, "lon": -46.67047368527096},

]

# Extracting the graph for each city and saving it as a GraphML file

for city_info in cities:
    # city_info = cities[0]
    city_name = city_info["name"]
    net_file = f"raw_nets_gpkg/{city_name}.gpkg"
    graph_file = f"graphs/{city_name}.graphml"
    print(f"Processing {city_name}...")
    if not os.path.exists(graph_file):
        graph = ox.graph_from_place(city_info["name"], network_type="drive", simplify=True)
        graph = ox.add_edge_speeds(graph)
        graph = ox.add_edge_travel_times(graph)
        ox.save_graphml(graph, graph_file)

# Producing GPKG files for each city
for city_info in cities:
    
    city_name = city_info["name"]
    graph_file = f"graphs/{city_name}.graphml"
    net_file = f"raw_nets_gpkg/{city_name}.gpkg"
    print(f"Processing {city_name}...")
     
    if not os.path.exists(net_file):
        # loading graph
        graph = ox.load_graphml(graph_file)

        # simplifying graphg for spatial operations and visualisation
        graph_undirected = graph.to_undirected()
        # Extracting nodes and simplified edges as GeoDataFrames
        nodes_gdf, edges_filtered = ox.graph_to_gdfs(graph_undirected)
        
        edges_filtered = edges_filtered.reset_index()

        # Reprojecting to UTM for tesselation and spatial operations
        nodes_proj = nodes_gdf.to_crs(nodes_gdf.estimate_utm_crs())
        edges_proj = edges_filtered.to_crs(nodes_proj.crs)

        # Producing a hull
        hull = edges_proj.union_all().convex_hull    
        # Buffering the hull for tesselation
        buffer = hull.buffer(0.01*(hull.area/np.pi)**0.5) # Buffering 1% of the equivalent radius of the hull
        
        # Performing morphological tessellation
        tessellation_nodes = mp.morphological_tessellation(nodes_proj, clip= buffer)
        tessellation_nodes.index = nodes_proj.index

        # Assigning areas as weights to nodes for spatial BC
        tessellation_nodes['weight'] = tessellation_nodes.geometry.area

        # Saving the spatial data to a GPKG
        nodes_proj.to_file(net_file, layer="nodes", driver="GPKG")
        edges_proj.to_file(net_file, layer="edges", driver="GPKG")
        tessellation_nodes.to_file(net_file, layer="tessellation", driver="GPKG")
        # Save the hull as a layer of the GPKG for visualisation purposes
        gpd.GeoDataFrame(geometry=[hull], crs=nodes_proj.crs).to_file(net_file, layer="hull", driver="GPKG")

