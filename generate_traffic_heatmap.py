import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os

def load_data():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    
    # Load datasets
    demand_df = pd.read_csv(os.path.join(base_dir, 'Demand.csv'), encoding='ISO-8859-1')
    routes_df = pd.read_csv(os.path.join(base_dir, 'Routes.csv'), encoding='ISO-8859-1')
    traffic_df = pd.read_csv(os.path.join(base_dir, 'RouteTraffic.csv'), encoding='ISO-8859-1')
    
    return demand_df, routes_df, traffic_df

def create_traffic_heatmap(traffic_df):
    # Assuming the traffic_df has columns: 'route_number', 'current_traffic_condition', 'time_slot'

    # Map traffic conditions to numerical values for heatmap visualization
    traffic_condition_mapping = {
        'light': 1,
        'moderate': 2,
        'heavy': 3
    }
    
    traffic_df['traffic_score'] = traffic_df['current_traffic_condition'].map(traffic_condition_mapping)

    # Create a pivot table for heatmap
    heatmap_data = traffic_df.pivot_table(index='route_number', columns='time_slot', values='traffic_score', fill_value=0)

    # Generate the heatmap
    plt.figure(figsize=(12, 8))
    sns.heatmap(heatmap_data, annot=True, cmap='YlGnBu', cbar_kws={'label': 'Traffic Condition Score'})
    
    plt.title('Traffic Heatmap')
    plt.xlabel('Time Slot')
    plt.ylabel('Route Number')
    
    # Save the heatmap to a file
    plt.savefig('traffic_heatmap.png')
    plt.show()

if __name__ == "__main__":
    demand_df, routes_df, traffic_df = load_data()
    create_traffic_heatmap(traffic_df)
