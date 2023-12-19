# msa_functions.py

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN
import folium
from folium.plugins import MarkerCluster

def load_data(file_path):
    df = pd.read_csv(file_path)
    df = df.drop(df.columns[0], axis=1)
    return df

def filter_cities_by_country(df, country='united states'):
    return df[df['country'] == country]

def filter_high_population_cities(df, population_threshold=50000):
    return df[df['population'] > population_threshold]

def plot_population_distribution(df_high_pop, df_all):
    fig, ax = plt.subplots()
    bars = ax.bar(['Cities with >50k Population', 'Cities with <=50k Population'],
                  [len(df_high_pop), len(df_all) - len(df_high_pop)])
    
    plt.ylabel('Number of Cities')
    plt.title('Cities Population Distribution')
    
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 0.1, round(yval), ha='center', va='bottom')
    
    plt.show()

def dbscan_clustering(df, dist_threshold=15.0, min_samples=1):
    dbscan = DBSCAN(eps=(dist_threshold/6371), min_samples=min_samples, metric='haversine', algorithm='ball_tree')
    labels = dbscan.fit_predict(np.radians([x for x in zip(df['latitude'], df['longitude'])]))
    df['cluster'] = labels
    df_filtered = df[df['cluster'] != -1]
    df_filtered = df_filtered[df_filtered.groupby('cluster')['population'].transform('max') > 50000]
    return df_filtered

def label_msas(df_filtered):
    df_sorted = df_filtered.sort_values(by='population', ascending=False).groupby('cluster').head(3)
    df_sorted = df_sorted[df_sorted['population'] > 50000]
    
    msa_names_city = df_sorted.groupby('cluster')['city'].apply(lambda x: '-'.join(x)).reset_index(name='city_names')
    #some entries do not have "states"
    msa_names_state = df_sorted.groupby('cluster')['state'].apply(lambda x: '-'.join(str(i) for i in x.unique() if pd.notna(i))).reset_index(name='state_names')
    #msa_names_state = df_sorted.groupby('cluster')['state'].apply(lambda x: '-'.join(x.unique())).reset_index(name='state_names')
    
    df_with_pred_msa = pd.merge(df_filtered, msa_names_city, on='cluster', how='left')
    df_with_pred_msa = pd.merge(df_with_pred_msa, msa_names_state, on='cluster', how='left')
    
    df_with_pred_msa['pred-MSA'] = df_with_pred_msa.apply(lambda row: f"{row['city_names']} {' '.join(row['state_names'].split())} msa", axis=1)
    df_with_pred_msa['pred-MSA'] = df_with_pred_msa['pred-MSA'].fillna('')
    df_with_pred_msa = df_with_pred_msa.drop(['city_names', 'state_names'], axis=1)
    
    return df_with_pred_msa

def save_to_csv(df, file_path='df_with_pred_msa.csv'):
    df.to_csv(file_path, index=False)

def create_folium_map(df):
    map_usa = folium.Map(location=[37.0902, -95.7129], zoom_start=4)
    marker_cluster = MarkerCluster().add_to(map_usa)

    for index, row in df.iterrows():
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=f"Pred-MSA: {row['pred-MSA']}",
            icon=None
        ).add_to(marker_cluster)

    return map_usa
