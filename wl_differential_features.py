import pandas as pd
import swifter

class WLDifferential():
    def __init__(self):
        pass

    def create_wl_differential_feats(self, df):
        """
        Creates the w/l differential features for each fighter in the dataset

        Parameters:
        - df (pd.Dataframe): The original dataframe containing all the fights

        Returns:
        - pd.Dataframe: The dataframe containing the w/l differential features for each fighter
        """
        
        col_names = [
            'fighter-a_win-diff_l5',
            'fighter-a_loss-diff_l5',
            'fighter-b_win-diff_l5',
            'fighter-b_loss-diff_l5',
            'fighter-a_win-diff_alltime',
            'fighter-a_loss-diff_alltime',
            'fighter-b_win-diff_alltime',
            'fighter-b_loss-diff_alltime'
        ]
        input_df = df.copy()
        result_features = pd.DataFrame(columns=col_names)
        result_features[col_names] = input_df.swifter.progress_bar(True).apply(lambda row: self.calculate_wl_diff(input_df, row['fighter_a_id'], row['fighter_b_id'], row.name, col_names), axis=1)

        target_df = pd.concat([input_df, result_features], axis=1)

        return target_df
    
    def calculate_wl_diff(self, df, fighter_a_id, fighter_b_id, index, col_names):
        """
        Calculates all the w/l differential features for each fighter in the dataset

        Parameters:
        - df (pd.Dataframe): The original dataframe containing all the fights
        - fighter_a_id (int): The id of the first fighter
        - fighter_b_id (int): The id of the second fighter
        - index (int): The index of the current fight
        - col_names (list): The list of column names for the consecutive w/l features

        Returns:
        - pd.Series: The series containing the consecutive w/l features for each fighter
        """
        res = []
        for i in range(0, len(col_names), 4):
            time_period = col_names[i].split('_')[2]
            if time_period == 'l5':
                last_fights = 5
            else:
                last_fights = 0
                        
            fighter_a_cwins, fighter_a_closses, fighter_b_cwins, fighter_b_closses = self.compute_wl_diff_stats(df, fighter_a_id, fighter_b_id, index, last_fights)
            res.append(fighter_a_cwins)
            res.append(fighter_a_closses)
            res.append(fighter_b_cwins)
            res.append(fighter_b_closses)
                
        return pd.Series(res)

    def compute_wl_diff_stats(self, df, fighter_a_id, fighter_b_id, index, last_fights):
        """
        Computes the consecutive w/l stats for each fighter in the dataset

        Parameters:
        - df (pd.Dataframe): The original dataframe containing all the fights
        - fighter_a_id (int): The id of the first fighter
        - fighter_b_id (int): The id of the second fighter
        - index (int): The index of the row in the dataframe
        - col_names (list): The list of column names for the consecutive w/l stats

        Returns:
        - list: The list of consecutive w/l stats for each fighter
        """
        all_prev_fights = df.loc[:index-1]
        if not all_prev_fights.empty:
            fighter_a_id_vals = all_prev_fights.fighter_a_id.values
            fighter_b_id_vals = all_prev_fights.fighter_b_id.values

            fighter_a_fights = all_prev_fights[(fighter_a_id_vals == fighter_a_id) | (fighter_b_id_vals == fighter_a_id)][-last_fights:]
            fighter_b_fights = all_prev_fights[(fighter_b_id_vals == fighter_b_id) | (fighter_a_id_vals == fighter_b_id)][-last_fights:]
          
            winner_id_vals = fighter_a_fights.winner_id.values
            fighter_a_wins = len(fighter_a_fights[winner_id_vals == fighter_a_id])
            fighter_a_losses = len(fighter_a_fights) - fighter_a_wins

            winner_id_vals = fighter_b_fights.winner_id.values
            fighter_b_wins = len(fighter_b_fights[winner_id_vals == fighter_b_id])
            fighter_b_losses = len(fighter_b_fights) - fighter_b_wins

            return fighter_a_wins - fighter_b_wins, fighter_a_losses - fighter_b_losses, fighter_b_wins - fighter_a_wins, fighter_b_losses - fighter_a_losses

        return 0,0,0,0


