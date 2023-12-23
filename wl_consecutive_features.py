import pandas as pd
import swifter

class ConsecutiveWL():
    def __init__(self):
        pass

    def create_wl_consecutive_feats(self, df):
        """
        Creates the w/l consecutive features for each fighter in the dataset

        Parameters:
        - df (pd.Dataframe): The original dataframe containing all the fights

        Returns:
        - pd.Dataframe: The dataframe containing the w/l consecutive features for each fighter
        """
        
        col_names = [
            'fighter-a_cwins_l5', 
            'fighter-a_closses_l5',
            'fighter-b_cwins_l5',
            'fighter-b_closses_l5',
            'fighter-a_cwins_l5_diff',
            'fighter-a_closses_l5_diff',
            'fighter-b_cwins_l5_diff',
            'fighter-b_closses_l5_diff',
            'fighter-a_cwins_alltime',
            'fighter-a_closses_alltime',
            'fighter-b_cwins_alltime',
            'fighter-b_closses_alltime',
            'fighter-a_cwins_alltime_diff',
            'fighter-a_closses_alltime_diff',
            'fighter-b_cwins_alltime_diff',
            'fighter-b_closses_alltime_diff'
        ]
        input_df = df.copy()
        result_features = pd.DataFrame(columns=col_names)
        result_features[col_names] = input_df.swifter.progress_bar(True).apply(lambda row: self.calculate_consecutive_wl(input_df, row['fighter_a_id'], row['fighter_b_id'], row.name, col_names), axis=1)

        target_df = pd.concat([input_df, result_features], axis=1)

        return target_df
    
    def calculate_consecutive_wl(self, df, fighter_a_id, fighter_b_id, index, col_names):
        """
        Calculates all the consecutive w/l features for each fighter in the dataset

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
                        
            has_diff = 'diff' in col_names[i]
            fighter_a_cwins, fighter_a_closses, fighter_b_cwins, fighter_b_closses = self.compute_consecutive_wl_stats(df, fighter_a_id, fighter_b_id, index, last_fights, has_diff)
            res.append(fighter_a_cwins)
            res.append(fighter_a_closses)
            res.append(fighter_b_cwins)
            res.append(fighter_b_closses)
                
        return pd.Series(res)
    
    def compute_consecutive_wl_stats(self, df, fighter_a_id, fighter_b_id, index, last_fights, diff=False):
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
        all_prev_fights = df.iloc[:index]
        if not all_prev_fights.empty:
            fighter_a_id_vals = all_prev_fights.fighter_a_id.values
            fighter_b_id_vals = all_prev_fights.fighter_b_id.values

            fighter_a_fights = all_prev_fights[(fighter_a_id_vals == fighter_a_id) | (fighter_b_id_vals == fighter_a_id)][-last_fights:]
            fighter_b_fights = all_prev_fights[(fighter_b_id_vals == fighter_b_id) | (fighter_a_id_vals == fighter_b_id)][-last_fights:]

            fighter_a_cwins = 0
            fighter_a_closses = 0
            fighter_b_cwins = 0
            fighter_b_closses = 0
            
            if not fighter_a_fights.empty:
                most_recent_fight = fighter_a_fights[-1:]
                won_last_fight = most_recent_fight['winner_id'].iloc[0] == fighter_a_id
                fighter_a_cwins = 1 if won_last_fight else 0
                fighter_a_closses = 0 if won_last_fight else 1
                fighter_a_fights = fighter_a_fights[:-1]
                fighter_a_fights = fighter_a_fights[::-1]
                for _, fight in fighter_a_fights.iterrows():
                    if fight['winner_id'] == fighter_a_id and fighter_a_cwins > 0:
                        fighter_a_cwins += 1
                        fighter_a_closses = 0
                    elif fighter_a_cwins > 0:
                        break;
                    elif fight['winner_id'] != fighter_a_id and fighter_b_closses > 0:
                        fighter_a_closses += 1
                        fighter_a_cwins = 0
                    else:
                        break;
    
            if not fighter_b_fights.empty:
                most_recent_fight = fighter_b_fights[-1:]
                won_last_fight = most_recent_fight['winner_id'].iloc[0] == fighter_a_id
                fighter_b_cwins = 1 if won_last_fight else 0
                fighter_b_closses = 0 if won_last_fight else 1
                fighter_b_fights = fighter_b_fights[:-1]
                fighter_b_fights = fighter_b_fights[::-1]
                for _, fight in fighter_b_fights.iterrows():
                    if fight['winner_id'] == fighter_b_id and fighter_b_cwins > 0:
                        fighter_b_cwins += 1
                        fighter_b_closses = 0
                    elif fighter_b_cwins > 0:
                        break;
                    elif fight['winner_id'] != fighter_b_id and fighter_b_closses > 0:
                        fighter_b_closses += 1
                        fighter_b_cwins = 0
                    else: 
                        break;
        
            if diff:
                return fighter_a_cwins - fighter_b_cwins, fighter_a_closses - fighter_b_closses, fighter_b_cwins - fighter_a_cwins, fighter_b_closses - fighter_a_closses
            else:
                return fighter_a_cwins, fighter_a_closses, fighter_b_cwins, fighter_b_closses
        
        return 0, 0, 0, 0