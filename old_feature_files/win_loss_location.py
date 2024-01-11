import pandas as pd
import numpy as np
import swifter

class WinLossLocation():
    """
    This class is used to create the win/loss location features for each fighter in the dataset.
    """

    def __init__(self):
        """
        Initializes the WinLossLocation class
        """
        pass

    def create_win_loss_location_feats(self, df, include_progress=False):
        """
        Creates the win/loss location features for each fighter in the dataset

        Parameters:
            df (pd.DataFrame): DataFrame containing all the fights in the dataset

        Returns:
            pd.DataFrame: DataFrame containing the win/loss location features for each fighter in the dataset
        """

        col_names = ['fighter_a_wins_in_location', 'fighter_a_losses_in_location', \
                     'fighter_b_wins_in_location', 'fighter_b_losses_in_location']

        target_df = df.copy()
        result_features = pd.DataFrame(columns=col_names)

        result_features[col_names] = target_df.swifter.progress_bar(include_progress).apply(lambda row: self.compute_win_loss_location(df, row['fighter_a_id'], row['fighter_b_id'], row['location'], row.name), axis=1)

        return pd.concat([target_df, result_features], axis=1)
    
    def compute_win_loss_location(self, df, fighter_a_id, fighter_b_id, location, index):
        """
        Computes the win/loss location features for a single example in the dataset

        Parameters:
            df (pd.DataFrame): The dataframe containing the fighter data
            fighter_a_id (int): The id of fighter a
            fighter_b_id (int): The id of fighter b
            location (str): The location of the fight
            index (int): The index of the example in the dataset

        Returns:
            pd.Series: The win/loss location features for the example
        """

        all_prev_fights = df.loc[:index-1]
        if not all_prev_fights.empty:
            fighter_a_id_vals = all_prev_fights.fighter_a_id.values
            fighter_b_id_vals = all_prev_fights.fighter_b_id.values
            location_vals = all_prev_fights.location.values

            fighter_a_fights = all_prev_fights[((fighter_a_id_vals == fighter_a_id) | (fighter_b_id_vals == fighter_a_id)) & (location_vals == location)]
            fighter_b_fights = all_prev_fights[((fighter_a_id_vals == fighter_b_id) | (fighter_b_id_vals == fighter_b_id)) & (location_vals == location)]

            winner_id_vals = fighter_a_fights.winner_id.values
            fighter_a_wins_in_location = len(fighter_a_fights[winner_id_vals == fighter_a_id])
            fighter_a_losses_in_location = len(fighter_a_fights) - fighter_a_wins_in_location

            winner_id_vals = fighter_b_fights.winner_id.values
            fighter_b_wins_in_location = len(fighter_b_fights[winner_id_vals == fighter_b_id])
            fighter_b_losses_in_location = len(fighter_b_fights) - fighter_b_wins_in_location

            return pd.Series([fighter_a_wins_in_location, fighter_a_losses_in_location, fighter_b_wins_in_location, fighter_b_losses_in_location])
            
        return pd.Series([0, 0, 0, 0])
