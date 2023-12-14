import pandas as pd
import googlemaps
from geopy.distance import geodesic
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

class HometownAdvatage():

    def __init__(self) -> None: 
        pass

    def calculate_distance(self, fighter_hometown_coords, fight_location_coords):
        """
        Calculate the distance between two locations. take in coordinates as tuples
        """
        if fighter_hometown_coords and fight_location_coords:
            return geodesic(fighter_hometown_coords, fight_location_coords).kilometers
        return float('inf') 
    # Function to get coordinates from location name
    def get_coords(location, gmaps):
        """
        Retrieves the coordinates of a given location.

        Args:
        location (str): The location to get coordinates for.
        gmaps (googlemaps.Client): Google Maps client instance.

        Returns:
        tuple: A tuple containing the latitude and longitude of the location.
        """
        geocode_result = gmaps.geocode(location)
        if geocode_result:
            return (geocode_result[0]['geometry']['location']['lat'], 
                    geocode_result[0]['geometry']['location']['lng'])
        return None

    # Modified function to calculate home advantage
    def calculate_home_advantage(self, fighter_name, fighter_id, fight_location, fighter_df, gmaps, log_csv_path='missing_data_log.csv'):
        # Check if fighter_id exists in fighter_df
        if fighter_id not in fighter_df['ID'].values:
            return 0

        filtered_df = fighter_df.loc[fighter_df['ID'] == fighter_id, 'Hometown']

        # Check if hometown exists for the fighter
        if filtered_df.empty or pd.isna(filtered_df.iloc[0]):
            return 0
        fighter_hometown = filtered_df.iloc[0]
        # Get coordinates for fighter's hometown and fight location
        hometown_coords = self.get_coords(fighter_hometown, gmaps)
        location_coords = self.get_coords(fight_location, gmaps)

        # Calculate distance and check if it's within 20 km
        ht_adv = 0
        if self.calculate_distance(hometown_coords, location_coords) <= 20:
            ht_adv = 1
            
        return ht_adv

    def home_adv_feat(self, fighter_df, fights_df, gmaps_key, include_progress_bar=True):
        """
        Adds 'fighter_A_home_advantage' and 'fighter_B_home_advantage' features to the fights_df.
        These features indicate whether the fight location is within 20 km of the fighter's hometown.
        """
        # Initialize Google Maps client
        gmaps = googlemaps.Client(key=gmaps_key)

        # Enable progress bar if required
        if include_progress_bar:
            tqdm.pandas(desc="Calculating home advantage")

        # Apply the function to calculate home advantage for fighter A
        if include_progress_bar:
            
            fights_df['fighter_a_home_advantage'] = fights_df.progress_apply(lambda row: self.calculate_home_advantage(row['fighter_a'], row['fighter_a_id'], row['location'], fighter_df, gmaps), axis=1)
        else:
            fights_df['fighter_A_home_advantage'] = fights_df.apply(lambda row: self.calculate_home_advantage(row['fighter_a'],row['fighter_a_id'], row['location'], fighter_df, gmaps), axis=1)

        # Apply the function to calculate home advantage for fighter B
        if include_progress_bar:
            fights_df['fighter_B_home_advantage'] = fights_df.progress_apply(lambda row: self.calculate_home_advantage(row['fighter_b'], row['fighter_b_id'], row['location'], fighter_df, gmaps), axis=1)
        else:
            fights_df['fighter_B_home_advantage'] = fights_df.apply(lambda row: self.calculate_home_advantage(row['fighter_b'], row['fighter_b_id'], row['location'], fighter_df, gmaps), axis=1)

        return fights_df
