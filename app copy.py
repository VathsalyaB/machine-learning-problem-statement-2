from flask import Flask, jsonify, request, render_template
import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns

app = Flask(__name__)

# Load datasets with error handling
def load_data():
    try:
        base_dir = os.path.abspath(os.path.dirname(__file__))
        file_path1 = os.path.join(base_dir, 'Demand.csv')
        demand_df = pd.read_csv(file_path1, encoding='ISO-8859-1')

        file_path2 = os.path.join(base_dir, 'Routes.csv')
        routes_df = pd.read_csv(file_path2, encoding='ISO-8859-1')

        file_path3 = os.path.join(base_dir, 'RouteTraffic.csv')
        traffic_df = pd.read_csv(file_path3, encoding='ISO-8859-1')

        # Convert column names to lowercase
        demand_df.columns = [col.lower() for col in demand_df.columns]
        routes_df.columns = [col.lower() for col in routes_df.columns]
        traffic_df.columns = [col.lower() for col in traffic_df.columns]

    except FileNotFoundError as e:
        return None, None, None, str(e)

    return demand_df, routes_df, traffic_df, None

# Optimize routes based on demand and traffic conditions
def optimize_routes(demand_df, routes_df, traffic_df, origin, destination):
    optimized_routes = []

    # Check for valid routes
    valid_routes = routes_df[(routes_df['starting point'] == origin) & (routes_df['destination'] == destination)]
    
    if valid_routes.empty:
        print("No valid routes found for the given origin and destination.")
        return optimized_routes

    for _, route in valid_routes.iterrows():
        route_number = route['route number']
        starting_point = route['starting point']
        destination = route['destination']
        
        # Get demand for this route
        route_demand = demand_df[demand_df['route number'] == route_number]
        
        # Sum average passengers for all stops and time slots
        total_average_passengers = route_demand['average passengers'].sum()
        
        # Get traffic conditions for this route
        traffic_for_route = traffic_df[traffic_df['route number'] == route_number]

        # Initialize average traffic score
        traffic_score = None

        if not traffic_for_route.empty:
            # Map traffic conditions to numerical values
            traffic_condition_mapping = {'light': 1, 'moderate': 2, 'heavy': 3}
            traffic_score = traffic_for_route['current traffic condition'].map(traffic_condition_mapping).mean()

        # Create optimized route entry
        optimized_route = {
            'route number': route_number,
            'starting point': starting_point,
            'destination': destination,
            'total average passengers': total_average_passengers,
            'average traffic score': traffic_score if traffic_score is not None else 0,
            'key stops': route['key stops'].split(','),
            'optimal schedule': 'Adjusted based on demand and traffic'
        }
        optimized_routes.append(optimized_route)

    return optimized_routes

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/optimize', methods=['POST'])
def optimize():
    demand_df, routes_df, traffic_df, error = load_data()
    if error:
        return jsonify({"error": error}), 500

    origin = request.form['origin'].strip().lower()
    destination = request.form['destination'].strip().lower()
    
    print(f"Received request to optimize route from {origin} to {destination}")

    optimized_routes = optimize_routes(demand_df, routes_df, traffic_df, origin, destination)
    
    if not optimized_routes:
        return jsonify({"error": "No routes found for the given origin and destination."}), 404
    
    return jsonify(optimized_routes)

@app.route('/passenger_graph', methods=['POST'])
def passenger_graph():
    demand_df, routes_df, traffic_df, error = load_data()
    if error:
        return jsonify({"error": error}), 500

    destination = request.form['destination'].strip().lower()
    
    # Filter demand data for the given destination
    filtered_data = demand_df[demand_df['stop name'] == destination]

    # If no data found for the destination
    if filtered_data.empty:
        return jsonify({"error": "No data found for the specified destination."}), 404

    # Group by Time Slot and calculate the average number of passengers
    average_passengers = filtered_data.groupby('time slot')['average passengers'].mean()

    # Create the graph
    plt.figure(figsize=(10, 5))
    average_passengers.plot(kind='bar', color='skyblue')
    plt.title(f'Average Passengers at {destination} by Time Slot')
    plt.xlabel('Time Slot')
    plt.ylabel('Average Passengers')
    
    # Save the graph to a file
    graph_file_path = os.path.join(os.getcwd(), 'static', 'passenger_graph.png')
    plt.savefig(graph_file_path)
    plt.close()  # Close the figure

    return render_template('passenger_graph.html', destination=destination)

@app.route('/heatmap', methods=['GET'])
def heatmap():
    demand_df, routes_df, traffic_df, error = load_data()
    if error:
        return jsonify({"error": error}), 500

    # Create a heatmap of traffic conditions
    plt.figure(figsize=(12, 8))
    heatmap_data = traffic_df.pivot_table(values='current traffic condition', 
                                           index='route number', 
                                           columns='starting point', 
                                           aggfunc='mean')
    sns.heatmap(heatmap_data, cmap='YlGnBu', annot=True, fmt=".1f")
    plt.title('Traffic Heatmap by Route and Starting Point')
    plt.xlabel('Starting Point')
    plt.ylabel('Route Number')
    
    # Save the heatmap to a file
    heatmap_file_path = os.path.join(os.getcwd(), 'static', 'traffic_heatmap.png')
    plt.savefig(heatmap_file_path)
    plt.close()  # Close the figure

    return render_template('heatmap.html')

if __name__ == '__main__':
    app.run(debug=True)
