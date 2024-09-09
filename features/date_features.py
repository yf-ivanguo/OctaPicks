import pandas as pd
import numpy as np
import googlemaps
from geopy.distance import geodesic
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import swifter

class DateFeatures():
    def __init__(self) -> None:
        pass

    def create_date_features(self, df):
        """
        Creates the date features for each fight in the dataset.

        Parameters:
            df (pd.DataFrame): DataFrame containing all the fights in the dataset

        Returns:
            pd.DataFrame: DataFrame containing the date features for each fight in the dataset
        """

        df['date'] = pd.to_datetime(df['date'])

        df['year'] = df['date'].dt.year
        temp_col = df['date'].dt.day_of_year

        df['day_cos'] = temp_col.apply(lambda x: np.cos(x * 2 * np.pi / 365.25))
        df['day_sin'] = temp_col.apply(lambda x: np.sin(x * 2 * np.pi / 365.25))

        return df

    # def create_home_adv_features(self, fighter_df, fights_df, include_progress_bar=True):
    #     """
    #     Adds 'fighter_A_home_advantage' and 'fighter_B_home_advantage' features to the fights_df.
    #     These features indicate whether the fight location is within 20 km of the fighter's hometown.

    #     Parameters:
    #         fighter_df (pd.DataFrame): DataFrame containing all the fighters in the dataset
    #         fights_df (pd.DataFrame): DataFrame containing all the fights in the dataset
    #         include_progress_bar (bool): Whether or not to include a progress bar

    #     Returns:
    #         pd.DataFrame: DataFrame containing the home advantage features for each fight in the dataset
    #     """

    #     # Initialize Google Maps client
    #     gmaps = googlemaps.Client(key=self.gmaps_key)

    #     # Enable progress bar if required
    #     if include_progress_bar:
    #         tqdm.pandas(desc="Calculating home advantage")

    #     # Apply the function to calculate home advantage for fighter A
    #     if include_progress_bar:

    #         fights_df['fighter_a_home_advantage'] = fights_df.progress_apply(lambda row: self.calculate_home_advantage(row['fighter_a_id'], row['location'], fighter_df, gmaps), axis=1)
    #     else:
    #         fights_df['fighter_A_home_advantage'] = fights_df.apply(lambda row: self.calculate_home_advantage(row['fighter_a_id'], row['location'], fighter_df, gmaps), axis=1)

    #     # Apply the function to calculate home advantage for fighter B
    #     if include_progress_bar:
    #         fights_df['fighter_B_home_advantage'] = fights_df.progress_apply(lambda row: self.calculate_home_advantage(row['fighter_b_id'], row['location'], fighter_df, gmaps), axis=1)
    #     else:
    #         fights_df['fighter_B_home_advantage'] = fights_df.apply(lambda row: self.calculate_home_advantage(row['fighter_b_id'], row['location'], fighter_df, gmaps), axis=1)

    #     return fights_df

    # def calculate_home_advantage(self, fighter_id, fight_location, fighter_df, gmaps, log_csv_path='missing_data_log.csv'):
    #     """
    #     Calculates the home advantage for a given fighter in a given fight.

    #     Parameters:
    #         fighter_id (str): ID of the fighter
    #         fight_location (str): Location of the fight
    #         fighter_df (pd.DataFrame): DataFrame containing all the fighters in the dataset
    #         gmaps (googlemaps.Client): Google Maps client instance
    #         log_csv_path (str): Path to the CSV file containing the names of the fighters whose hometowns could not be found

    #     Returns:
    #         int: 1 if the fighter has home advantage, 0 otherwise
    #     """

    #     if fighter_id not in fighter_df['ID'].values:
    #         return 0

    #     filtered_df = fighter_df.loc[fighter_df['ID'] == fighter_id, 'Hometown']

    #     # Check if hometown exists for the fighter
    #     if filtered_df.empty or pd.isna(filtered_df.iloc[0]):
    #         return 0
    #     fighter_hometown = filtered_df.iloc[0]
    #     # Get coordinates for fighter's hometown and fight location
    #     hometown_coords = self.get_coords(fighter_hometown, gmaps)
    #     location_coords = self.get_coords(fight_location, gmaps)

    #     # Calculate distance and check if it's within 20 km
    #     ht_adv = 0
    #     if self.calculate_distance(hometown_coords, location_coords) <= 20:
    #         ht_adv = 1

    #     return ht_adv

    # def get_coords(location, gmaps):
    #     """
    #     Retrieves the coordinates of a given location.

    #     Parameters:
    #         location (str): The location to get coordinates for.
    #         gmaps (googlemaps.Client): Google Maps client instance.

    #     Returns:
    #         tuple: A tuple containing the latitude and longitude of the location.
    #     """

    #     geocode_result = gmaps.geocode(location)
    #     if geocode_result:
    #         return (geocode_result[0]['geometry']['location']['lat'],
    #                 geocode_result[0]['geometry']['location']['lng'])
    #     return None

    # def calculate_distance(self, fighter_hometown_coords, fight_location_coords):
    #     """
    #     Calculate the distance between two locations. take in coordinates as tuples

    #     Parameters:
    #         fighter_hometown_coords (tuple): Coordinates of the fighter's hometown
    #         fight_location_coords (tuple): Coordinates of the fight location

    #     Returns:
    #         float: Distance between the two locations in kilometers
    #     """

    #     if fighter_hometown_coords and fight_location_coords:
    #         return geodesic(fighter_hometown_coords, fight_location_coords).kilometers
    #     return float('inf')