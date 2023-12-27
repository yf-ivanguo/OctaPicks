import pandas as pd
import numpy as np
import requests
import swifter

class WinLossRoundFeats:

    def __init__(self):
        pass

    def create_col_names_win_loss_round(self):
        """
        Generates column names for significant strike statistics.

        Returns:
            list: A list of strings, each representing a column name for a specific significant strike statistic.
        """
        col_names = []
        fighters = ['fighter-a', 'fighter-b']
        fight_rounds = ['3R', '5R']
        win_loss = ['wins', 'losses']
        rounds = ['R1', 'R2', 'R3', 'R4', 'R5', 'decision', 'overall']
        time_periods = ['alltime', '1y']
        for fighter in fighters:
            for num_rounds in fight_rounds:
                for wl in win_loss:
                    for dec_round in rounds:
                        for time_period in time_periods:
                            if num_rounds == '3R' and (dec_round == 'R4' or dec_round == 'R5'):
                                continue
                            col_name = f"{fighter.replace(' ', '_')}_{num_rounds.replace(' ', '_')}_{dec_round}_{wl}_{time_period.replace(' ', '_')}"
                            col_names.append(col_name)
        return col_names
    def compute_year_ago(self, df):
        """
        Calculates the date one year ago from each date in the dataframe's 'date' column.

        Args:
            df (pd.DataFrame): The dataframe containing a 'date' column.

        Returns:
            pd.Series: A Series object with dates that are one year before the corresponding dates in df's 'date' column.
        """

        temp_year_ago_df = pd.to_datetime(df['date'])
        temp_year_ago_df = temp_year_ago_df - pd.DateOffset(years=1)
        return temp_year_ago_df


    def get_fighter_fights_win_loss_round(self, df, fighter_id, index):
            """
            Retrieves the most recent fights of a fighter before a given index in the dataframe.

            Args:
                df (pd.DataFrame): The dataframe containing fight records.
                fighter_id (str): The ID of the fighter.
                index (int): The index in the dataframe up to which fights should be considered.

            Returns:
                tuple: Contains three dataframes - the last 3 fights, the last 5 fights, and all previous fights.
            """
            year_ago = self.compute_year_ago(df)
            all_prev_fights = df.loc[:index-1]
            col_names = df.columns

            all_prev_fights_3R = pd.DataFrame(columns=col_names)
            all_prev_fights_5R = pd.DataFrame(columns=col_names)

            if not all_prev_fights.empty:
                # Filter fights involving the specified fighter
                fighter_a_id_vals = all_prev_fights.fighter_a_id.values
                fighter_b_id_vals = all_prev_fights.fighter_b_id.values

                prev_fights = all_prev_fights[((fighter_a_id_vals == fighter_id) | (fighter_b_id_vals == fighter_id))]

                if not prev_fights.empty:
                    outcome_format_values = prev_fights.outcome_format.values

                    # Filter fights that are 3R or 5R
                    all_prev_fights_3R[col_names] = prev_fights[outcome_format_values == "(5-5-5)"]
                    all_prev_fights_5R[col_names] = prev_fights[outcome_format_values == "(5-5-5-5-5)"]
                    
                    return all_prev_fights_3R, all_prev_fights_5R, year_ago[index]
                    
                else:
                    return all_prev_fights_3R, all_prev_fights_5R, year_ago[index]
                
            return all_prev_fights_3R, all_prev_fights_5R, year_ago[index]


    def get_wins_losses(self, df, fighter_id):
        """
        Retrieves the wins and losses of a fighter.

        Args:
            df (pd.DataFrame): The dataframe containing fight records.
            fighter_id (str): The ID of the fighter.
            colnames (list): A list of column names to be used for the dataframe.

        Returns:
            tuple: Contains two dataframes - one containing the wins of the fighter, and the other containing the losses of the fighter.
        """
        col_names = df.columns
        fighter_wins = pd.DataFrame(columns=col_names)
        fighter_losses = pd.DataFrame(columns=col_names)
        
        if df.empty:
            return fighter_wins, fighter_losses
        
        fighter_wins[col_names] = df[(df['winner_id'] == fighter_id)]
        fighter_losses[col_names] = df[(df['winner_id'] != fighter_id)]

        assert len(fighter_wins) + len(fighter_losses) == len(df)

        return fighter_wins, fighter_losses
        
    def isDecision(self, outcome_methods):
        """
        Checks if the fight outcome method involves a decision.

        Args:
            outcome_methods (pd.Series): A pandas Series containing fight outcome methods.

        Returns:
            pd.Series: A boolean Series where True indicates the outcome method is a decision.
        """
        return outcome_methods.str.contains("Decision", case=False, na=False)

    def compute_win_loss_round_details_alltime(self, fights_df, round_num):
        """
        Filters fights based on the specified round number and whether the outcome was not by decision.

        Args:
            fights_df (pd.DataFrame): The dataframe containing fight records.
            round_num (int): The specific round number to filter fights on.

        Returns:
            pd.DataFrame: A filtered DataFrame containing fights that match the specified criteria.
        """
        col_names = fights_df.columns
        round_outcome_fights = pd.DataFrame(columns=col_names)

        if fights_df.empty:
            return round_outcome_fights
        
        round_outcome_fights[col_names] = fights_df[(fights_df['outcome_round'] == round_num) & (~self.isDecision(fights_df['outcome_method']))]
        return round_outcome_fights

    def get_win_loss_round_details(self, fights_won, fights_lost, fighter_id, colnames, year_ago):
        """
        Calculates win/loss statistics for each fighter based on specific criteria defined in colnames.

        Args:
            fights_won (pd.DataFrame): DataFrame containing fights that the fighter won.
            fights_lost (pd.DataFrame): DataFrame containing fights that the fighter lost.
            fighter_id (str): The ID of the fighter.
            colnames (list): List of column names defining specific criteria for win/loss calculation.
            year_ago (pd.Series): Series object with dates that are one year before the corresponding dates in fights' date column.

        Returns:
            list: A list containing calculated win/loss statistics based on the specified criteria.
        """
        
        res = []
        for i in range(0, len(colnames), 2):

            split = colnames[i].split('_')
            round_num = split[2]
            outcome = split[3]

            if round_num[0] == 'R':
                round_num = int(round_num[1:])
            
            if outcome == 'wins':
                outcome = 1
            else:
                outcome = 0

            # print(index)
            if round_num == 'overall':
                if outcome:
                    res.append(len(fights_won))
                    res.append(len(fights_won[(pd.to_datetime(fights_won['date'])> year_ago)]))
                else:
                    res.append(len(fights_lost))
                    res.append(len(fights_lost[(pd.to_datetime(fights_lost['date']) > year_ago)]))
                continue
                

            if round_num == 'decision':
                if outcome:
                    res.append(len(fights_won[self.isDecision(fights_won['outcome_method'])]))
                    res.append(len(fights_won[self.isDecision(fights_won['outcome_method']) & (pd.to_datetime(fights_won['date']) > year_ago)]))
                    
                else:
                    res.append(len(fights_lost[self.isDecision(fights_lost['outcome_method'])]))
                    res.append(len(fights_lost[self.isDecision(fights_lost['outcome_method']) & (pd.to_datetime(fights_lost['date']) > year_ago)]))

                continue
                
            elif outcome:
                round_outcome_fights = self.compute_win_loss_round_details_alltime(fights_won, round_num)

                res.append(len(round_outcome_fights))
                res.append(len(round_outcome_fights[(pd.to_datetime(round_outcome_fights['date']) > year_ago)]))

                continue
            else:
                round_outcome_fights = self.compute_win_loss_round_details_alltime(fights_lost, round_num) 

                res.append(len(round_outcome_fights))
                res.append(len(round_outcome_fights[(pd.to_datetime(round_outcome_fights['date']) > year_ago)]))

                continue

        return res

    def get_win_loss_round_feats(self, df, fighter_id, index, colnames):
        """
        Generates win/loss statistics for a fighter at a specific index in the dataframe.

        Args:
            df (pd.DataFrame): The dataframe containing fight records.
            fighter_id (str): The ID of the fighter.
            index (int): The index in the dataframe to consider for generating statistics.
            colnames (list): List of column names for generating statistics.

        Returns:
            list: A list of calculated win/loss statistics for the specified fighter.
        """
        res = []
        all_prev_fights_3R, all_prev_fights_5R, year_ago= self.get_fighter_fights_win_loss_round(df, fighter_id, index)

        fights_won_3R, fights_lost_3R = self.get_wins_losses(all_prev_fights_3R, fighter_id)
        fights_won_5R, fights_lost_5R = self.get_wins_losses(all_prev_fights_5R, fighter_id)

        res += self.get_win_loss_round_details(fights_won_3R, fights_lost_3R, fighter_id, colnames[:20], year_ago)
        res += self.get_win_loss_round_details(fights_won_5R, fights_lost_5R, fighter_id, colnames[20:], year_ago)

        return res


    def calculate_win_loss_round(self, df, fighter_a_id, fighter_b_id, index, colnames):
        """
        Computes win/loss round features for two fighters in a match.

        Args:
            df (pd.DataFrame): The dataframe containing fight data.
            fighter_a_id (str): The ID of fighter A.
            fighter_b_id (str): The ID of fighter B.
            index (int): The index of the current row in the dataframe.
            colnames (list): List of column names for feature calculation.

        Returns:
            pd.Series: A series containing calculated win/loss round features for both fighters.
        """
        res = []
        
        res += self.get_win_loss_round_feats(df, fighter_a_id, index, colnames[:48]) # has all of fighter_a's cols
        res += self.get_win_loss_round_feats(df, fighter_b_id, index, colnames[48:]) # has all of fighter_b's cols

        return pd.Series(res)

    def create_win_loss_round_feats(self, df):
        """
        Creates a dataframe with added features for significant strikes and their differentials.

        Args:
            df (pd.DataFrame): The original dataframe containing fight data.

        Returns:
            pd.DataFrame: A dataframe with additional columns for significant strike features and differentials.
        """
        
        # Generate column names for significant strikes and differentials
        col_names = self.create_col_names_win_loss_round()

        df['date'] = pd.to_datetime(df['date'])

        # Copy the input dataframe and calculate significant strike features
        input_df = df.copy()
        result_features = pd.DataFrame(columns=col_names)
        result_features[col_names] = input_df.swifter.progress_bar(True).apply(lambda row: self.calculate_win_loss_round(input_df, row['fighter_a_id'], row['fighter_b_id'], row.name, col_names), axis=1)

        # Combine the input dataframe with the calculated features
        result_df = pd.concat([input_df, result_features], axis=1)

        return result_df