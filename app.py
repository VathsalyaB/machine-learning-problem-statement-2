from flask import Flask, jsonify, request, render_template, send_file
import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load datasets with error handling
def load_data():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    files = {
        'Demand': 'Demand.csv',
        'Routes': 'Routes.csv',
        'Traffic': 'RouteTraffic.csv',
        'Live': 'Live.csv'
    }
    datasets = {}
    for name, filename in files.items():
        try:
            file_path = os.path.join(base_dir, filename)
            datasets[name] = pd.read_csv(file_path, encoding='ISO-8859-1')
            datasets[name].columns = [col.lower() for col in datasets[name].columns]
        except FileNotFoundError as e:
            logging.error(f"File {filename} not found: {e}")
            return None, f"{filename} not found."
        except pd.errors.EmptyDataError as e:
            logging.error(f"File {filename} is empty: {e}")
            return None, f"{filename} is empty."

    return datasets, None

# Optimize routes based on demand and traffic conditions
def optimize_routes(demand_df, routes_df, traffic_df, origin, destination):
    logging.info(f"Finding routes from '{origin}' to '{destination}'")

    # Ensure origin and destination values are stripped and lowercase for comparison
    origin = origin.strip().lower()
    destination = destination.strip().lower()
    
    # Print the unique starting points and destinations for debugging
    logging.info(f"Unique starting points in Routes dataset: {routes_df['starting point'].unique()}")
    logging.info(f"Unique destinations in Routes dataset: {routes_df['destination'].unique()}")

    # Check for valid routes
    valid_routes = routes_df[
        (routes_df['starting point'].str.strip().str.lower() == origin) &
        (routes_df['destination'].str.strip().str.lower() == destination)
    ]
    
    if valid_routes.empty:
        logging.warning("No valid routes found for the given origin and destination.")
        return []

    optimized_routes = []
    for _, route in valid_routes.iterrows():
        print(route)
        route_number = route['ï»¿route number']
        starting_point = route['starting point']
        destination = route['destination']
        
        # Get demand for this route
        route_demand = demand_df[demand_df['ï»¿route number'] == route_number]
        
        # Sum average passengers for all stops and time slots
        total_average_passengers = route_demand['average passengers'].sum()
        
        # Get traffic conditions for this route
        traffic_for_route = traffic_df[traffic_df['ï»¿route number'] == route_number]

        # Initialize average traffic score
        traffic_score = None
        if not traffic_for_route.empty:
            traffic_condition_mapping = {'light': 1, 'moderate': 2, 'heavy': 3}
            traffic_score = traffic_for_route['current traffic condition'].map(traffic_condition_mapping).mean()

        optimized_route = {
            # 'route number': route_number,
            # 'starting point': starting_point,
            # 'destination': destination,
            # 'total average passengers': str(total_average_passengers),
            # 'average traffic score': traffic_score if traffic_score is not None else 0,
            # 'key stops': route['key stops'].split(','),
            # 'optimal schedule': 'Adjusted based on demand and traffic',
            'route': "Route# : " + route_number + " : " + starting_point + " : " + destination,
            'details': "Via : " + route['key stops']
        }
        return optimized_route
    #     optimized_routes.append(optimized_route)
    # logging.info(f"Found {len(optimized_routes)} optimized routes.")
    # return optimized_routes

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/optimize', methods=['POST'])
def optimize():
    datasets, error = load_data()
    if error:
        return jsonify({"error": error}), 500

    demand_df = datasets['Demand']
    routes_df = datasets['Routes']
    traffic_df = datasets['Traffic']

    origin = request.form['origin'].strip().lower()
    destination = request.form['destination'].strip().lower()
    
    logging.info(f"Received request to optimize route from {origin} to {destination}")

    optimized_routes = optimize_routes(demand_df, routes_df, traffic_df, origin, destination)
    
    if not optimized_routes:
        return jsonify({"error": "No routes found for the given origin and destination."}), 404
    
    return jsonify(optimized_routes)

@app.route('/passenger_graph', methods=['POST'])
def passenger_graph():
    datasets, error = load_data()
    if error:
        return jsonify({"error": error}), 500

    demand_df = datasets['Demand']
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

    # Save the graph to a BytesIO object
    img = BytesIO()
    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)

    return send_file(img, mimetype='image/png')

@app.route('/heatmap', methods=['GET'])
def heatmap():
    datasets, error = load_data()
    if error:
        return jsonify({"error": error}), 500

    traffic_df = datasets['Traffic']

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

    # Save the heatmap to a BytesIO object
    img = BytesIO()
    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)

    return send_file(img, mimetype='image/png')

@app.route('/calculate_buses', methods=['GET'])
def calculate_buses():
    route_number = request.args.get('route')
    
    if not route_number:
        return jsonify({"error": "Route number is required"}), 400

    # Load demand data
    datasets, error = load_data()
    if error:
        return jsonify({"error": error}), 500

    demand_df = datasets['Demand']

    # Convert route_number to lowercase and strip whitespace for comparison
    route_number = route_number.strip().lower()
    
    # Filter demand data by route number
    route_data = demand_df[demand_df['ï»¿route number'].str.strip().str.lower() == route_number]

    # Check if route data is empty
    if route_data.empty:
        logging.warning(f"No data found for route number: {route_number}")
        return jsonify({"error": "No data found for the specified route"}), 404

    # Calculate the total average passengers for the route
    total_passengers = route_data['average passengers'].sum()

    # Assuming each bus can accommodate 50 passengers
    buses_required = total_passengers // 50
    if total_passengers % 50 != 0:
        buses_required += 1  # Add one more bus if there are remaining passengers

    return jsonify({'buses_required': str(buses_required)})


@app.route('/calculate_live_buses', methods=['GET'])
def calculate_live_buses():
    route_number = request.args.get('route')
    
    if not route_number:
        return jsonify({"error": "Route number is required"}), 400

    # Load demand data and live data
    datasets, error = load_data()
    if error:
        return jsonify({"error": error}), 500

    live_df = datasets['Live']

    # Convert route_number to lowercase and strip whitespace for comparison
    route_number = route_number.strip().lower()
    
    # Filter live data by route number
    route_data = live_df[live_df['ï»¿route number'].str.strip().str.lower() == route_number]

    # Check if route data is empty
    if route_data.empty:
        logging.warning(f"No live data found for route number: {route_number}")
        return jsonify({"error": "No live data found for the specified route"}), 404

    # Calculate the total live count for the route
    total_live_count = route_data['live count'].sum()  # Adjust to match your column name in live.csv
    
    # Assuming each bus can accommodate 50 passengers
    buses_required = total_live_count // 50
    if total_live_count % 50 != 0:
        buses_required += 1  # Add one more bus if there are remaining passengers

    return jsonify({'buses_required': str(buses_required)})

if __name__ == '__main__':
    app.run(debug=True)
