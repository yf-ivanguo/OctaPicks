import pandas as pd
import numpy as np


class WinLossStats:
    def __init__(self, df):
        self.df = df

    def create_win_loss_stat_features(self):
        self.df = self.create_h2h_feats(self.df)
        self.df = self.create_win_loss_location_feats(self.df)
        self.df = self.create_win_loss_round_feats(self.df)
        self.df = self.create_win_loss_feats(self.df)

        return self.df
    
    """
    Creates the head to head features for each fighter in the dataset

    Usage:
        df = HeadToHead().create_h2h_feats(df)
    """
    def create_h2h_feats(self, df):
        target_df = df.copy()
        col_names = ['fighter_a_h2h_wins', 'fighter_b_h2h_wins']
        result_features = pd.DataFrame(columns=col_names)

        result_features[col_names] = target_df.swifter.progress_bar(True).apply(lambda row: self.__compute_h2h(target_df, row['fighter_a_id'], row['fighter_b_id'], row.name), axis=1)

        result_df = pd.concat([target_df, result_features], axis=1)
        return result_df
    
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

        result_features[col_names] = target_df.swifter.progress_bar(include_progress).apply(lambda row: self.__compute_win_loss_location(df, row['fighter_a_id'], row['fighter_b_id'], row['location'], row.name), axis=1)

        return pd.concat([target_df, result_features], axis=1)
    
    def create_win_loss_round_feats(self, df):
        """
        Creates a dataframe with added features for significant strikes and their differentials.

        Args:
            df (pd.DataFrame): The original dataframe containing fight data.

        Returns:
            pd.DataFrame: A dataframe with additional columns for significant strike features and differentials.
        """
        
        # Generate column names for significant strikes and differentials
        col_names = self.__create_col_names_win_loss_round()

        df['date'] = pd.to_datetime(df['date'])

        # Copy the input dataframe and calculate significant strike features
        input_df = df.copy()
        result_features = pd.DataFrame(columns=col_names)
        result_features[col_names] = input_df.swifter.progress_bar(True).apply(lambda row: self.__calculate_win_loss_round(input_df, row['fighter_a_id'], row['fighter_b_id'], row.name, col_names), axis=1)

        # Combine the input dataframe with the calculated features
        result_df = pd.concat([input_df, result_features], axis=1)

        return result_df
    
    def create_win_loss_feats(self, df):
        """
        Creates the win/loss features for each fighter in the dataset

        Args:
            df (pd.DataFrame): The dataframe containing the fighter data

        Returns:
            pd.DataFrame: The dataframe with the win/loss features appended
        """

        col_names = self.__create_col_names_win_loss()
        target_df = df

        target_df[col_names] = target_df.swifter.progress_bar(True).apply(lambda row: self.__compute_win_loss(target_df, row['fighter_a_id'], row['fighter_b_id'], row.name, col_names), axis=1)
        return target_df
    
    """
    Computes the head to head features for a single example in the dataset
    """
    def __compute_h2h(self, df, fighter_a_id, fighter_b_id, index):
        all_prev_fights = df.loc[:index-1]
        if not all_prev_fights.empty:
            fighter_a_id_vals = all_prev_fights.fighter_a_id.values
            fighter_b_id_vals = all_prev_fights.fighter_b_id.values

            prev_fights = all_prev_fights[((fighter_a_id_vals == fighter_a_id) & (fighter_b_id_vals == fighter_b_id)) | ((fighter_a_id_vals == fighter_b_id) & (fighter_b_id_vals == fighter_a_id))]
            if not prev_fights.empty:
                prev_fight_len = len(prev_fights)
                fighter_a_h2h_wins = (prev_fights['winner_id'] == fighter_a_id).sum()
                fighter_b_h2h_wins = prev_fight_len - fighter_a_h2h_wins
                return pd.Series([fighter_a_h2h_wins, fighter_b_h2h_wins])
        return pd.Series([0, 0])
    
    def __compute_win_loss_location(self, df, fighter_a_id, fighter_b_id, location, index):
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
    
    def __create_col_names_win_loss_round(self):
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
    
    def __compute_year_ago(self, df):
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

    def __get_fighter_fights_win_loss_round(self, df, fighter_id, index):
            """
            Retrieves the most recent fights of a fighter before a given index in the dataframe.

            Args:
                df (pd.DataFrame): The dataframe containing fight records.
                fighter_id (str): The ID of the fighter.
                index (int): The index in the dataframe up to which fights should be considered.

            Returns:
                tuple: Contains three dataframes - the last 3 fights, the last 5 fights, and all previous fights.
            """
            year_ago = self.__compute_year_ago(df)
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

    def __get_wins_losses(self, df, fighter_id):
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
        
    def __isDecision(self, outcome_methods):
        """
        Checks if the fight outcome method involves a decision.

        Args:
            outcome_methods (pd.Series): A pandas Series containing fight outcome methods.

        Returns:
            pd.Series: A boolean Series where True indicates the outcome method is a decision.
        """
        return outcome_methods.str.contains("Decision", case=False, na=False)

    def __compute_win_loss_round_details_alltime(self, fights_df, round_num):
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
        
        round_outcome_fights[col_names] = fights_df[(fights_df['outcome_round'] == round_num) & (~self.__isDecision(fights_df['outcome_method']))]
        return round_outcome_fights

    def __get_win_loss_round_details(self, fights_won, fights_lost, fighter_id, colnames, year_ago):
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
                    res.append(len(fights_won[self.__isDecision(fights_won['outcome_method'])]))
                    res.append(len(fights_won[self.__isDecision(fights_won['outcome_method']) & (pd.to_datetime(fights_won['date']) > year_ago)]))
                    
                else:
                    res.append(len(fights_lost[self.__isDecision(fights_lost['outcome_method'])]))
                    res.append(len(fights_lost[self.__isDecision(fights_lost['outcome_method']) & (pd.to_datetime(fights_lost['date']) > year_ago)]))

                continue
                
            elif outcome:
                round_outcome_fights = self.__compute_win_loss_round_details_alltime(fights_won, round_num)

                res.append(len(round_outcome_fights))
                res.append(len(round_outcome_fights[(pd.to_datetime(round_outcome_fights['date']) > year_ago)]))

                continue
            else:
                round_outcome_fights = self.__compute_win_loss_round_details_alltime(fights_lost, round_num) 

                res.append(len(round_outcome_fights))
                res.append(len(round_outcome_fights[(pd.to_datetime(round_outcome_fights['date']) > year_ago)]))

                continue

        return res

    def __get_win_loss_round_feats(self, df, fighter_id, index, colnames):
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
        all_prev_fights_3R, all_prev_fights_5R, year_ago= self.__get_fighter_fights_win_loss_round(df, fighter_id, index)

        fights_won_3R, fights_lost_3R = self.__get_wins_losses(all_prev_fights_3R, fighter_id)
        fights_won_5R, fights_lost_5R = self.__get_wins_losses(all_prev_fights_5R, fighter_id)

        res += self.__get_win_loss_round_details(fights_won_3R, fights_lost_3R, fighter_id, colnames[:20], year_ago)
        res += self.__get_win_loss_round_details(fights_won_5R, fights_lost_5R, fighter_id, colnames[20:], year_ago)

        return res

    def __calculate_win_loss_round(self, df, fighter_a_id, fighter_b_id, index, colnames):
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
        
        res += self.__get_win_loss_round_feats(df, fighter_a_id, index, colnames[:48]) # has all of fighter_a's cols
        res += self.__get_win_loss_round_feats(df, fighter_b_id, index, colnames[48:]) # has all of fighter_b's cols

        return pd.Series(res)

    def __compute_win_loss(self, df, fighter_a_id, fighter_b_id, index, col_names):
        """
        Computes the win/loss features for a single example in the dataset

        Args:
            df (pd.DataFrame): The dataframe containing the fighter data
            fighter_a_id (int): The id of fighter a
            fighter_b_id (int): The id of fighter b
            index (int): The index of the example in the dataset
            col_names (list): The list of column names for the win/loss features

        Returns:
            pd.Series: The win/loss features for the example
        """

        res = []
        fighter_a_prev_fights, fighter_a_prev_fights_last_year = self.__get_fighter_fights_win_loss(df, fighter_a_id, index)
        fighter_b_prev_fights, fighter_b_prev_fights_last_year = self.__get_fighter_fights_win_loss(df, fighter_b_id, index)

        for i in range(len(col_names)):
            split = col_names[i].split('_')
            fighter = split[0]
            outcome = split[1]
            method = split[2]
            weight_class = split[3]
            time_period = split[4]

            print(f'{fighter} {outcome} {method} {weight_class} {time_period}')

            prev_fights = fighter_a_prev_fights if fighter == 'fighter-a' else fighter_b_prev_fights
            prev_fights_last_year = fighter_a_prev_fights_last_year if fighter == 'fighter-a' else fighter_b_prev_fights_last_year

            prev_fights = prev_fights if time_period == 'all-time' else prev_fights_last_year

            if prev_fights.empty:
                res.append(0)
                continue

            fight_outcomes = self.__get_fighter_outcomes_win_loss(prev_fights, fighter_a_id if fighter == 'fighter-a' else fighter_b_id)
            prev_fights = fight_outcomes[0] if outcome == 'wins' else fight_outcomes[1]

            if prev_fights.empty:
                res.append(0)
                continue

            fight_outcome_methods = self.__get_fighter_outcome_methods(prev_fights)
            prev_fights = fight_outcome_methods[0] if method == 'KO/TKO' \
                else fight_outcome_methods[1] if method == 'submission' \
                else fight_outcome_methods[2] if method == 'decision' \
                else fight_outcome_methods[3]
            
            if prev_fights.empty:
                res.append(0)
                continue

            fight_division = self.__get_fighter_division(prev_fights)
            prev_fights = fight_division[0] if weight_class == 'flyweight' \
                else fight_division[1] if weight_class == 'bantamweight' \
                else fight_division[2] if weight_class == 'featherweight' \
                else fight_division[3] if weight_class == 'lightweight' \
                else fight_division[4] if weight_class == 'welterweight' \
                else fight_division[5] if weight_class == 'middleweight' \
                else fight_division[6] if weight_class == 'light-heavyweight' \
                else fight_division[7] if weight_class == 'heavyweight' \
                else fight_division[8] if weight_class == 'catchweight' \
                else fight_division[9]
            
            if not prev_fights.empty:
                res.append(len(prev_fights))
            else:
                res.append(0)
        return pd.Series(res)
    
    def __get_fighter_division(self, df):
        """
        Filters the data by division

        Args:
            df (pd.DataFrame): The dataframe containing the fighter data
        
        Returns:
            pd.DataFrame: The dataframe containing the fighter data filtered by division
        """

        fighter_flyweight = df[df['division'] == 'Flyweight']
        fighter_bantamweight = df[df['division'] == 'Bantamweight']
        fighter_featherweight = df[df['division'] == 'Featherweight']
        fighter_lightweight = df[df['division'] == 'Lightweight']
        fighter_welterweight = df[df['division'] == 'Welterweight']
        fighter_middleweight = df[df['division'] == 'Middleweight']
        fighter_light_heavyweight = df[df['division'] == 'Light Heavyweight']
        fighter_heavyweight = df[df['division'] == 'Heavyweight']
        fighter_catchweight = df[df['division'] == 'Catchweight']
        fighter_overall = df
        return fighter_flyweight, fighter_bantamweight, fighter_featherweight, fighter_lightweight, fighter_welterweight, fighter_middleweight, fighter_light_heavyweight, fighter_heavyweight, fighter_catchweight, fighter_overall

    def __get_fighter_outcome_methods(self, df):
        """
        Filters the data by outcome method

        Args:
            df (pd.DataFrame): The dataframe containing the fighter data

        Returns:
            pd.DataFrame: The dataframe containing the fighter data filtered by outcome method
        """

        fighter_ko = df[(df['outcome_method'] == 'KO/TKO') | (df['outcome_method'] == 'TKO - Doctor\'s Stoppage')]
        fighter_sub = df[df['outcome_method'] == 'Submission']
        fighter_decision = df[(df['outcome_method'] == 'Decision - Unanimous') | (df['outcome_method'] == 'Decision - Split') | (df['outcome_method'] == 'Decision - Majority')]
        fighter_total = df
        return fighter_ko, fighter_sub, fighter_decision, fighter_total

    def __get_fighter_outcomes_win_loss(self, df, fighter_id):
        """
        Filters the data by outcome

        Args:
            df (pd.DataFrame): The dataframe containing the fighter data
            fighter_id (int): The id of the fighter

        Returns:
            pd.DataFrame: The dataframe containing the fighter data filtered by outcome
        """

        fighter_wins = df[df['winner_id'] == fighter_id]
        fighter_losses = df[df['winner_id'] != fighter_id]
        return fighter_wins, fighter_losses

    def __get_fighter_fights_win_loss(self, df, fighter_id, index):
        """
        Filters the data by a specific fighter

        Args:
            df (pd.DataFrame): The dataframe containing the fighter data
            fighter_id (int): The id of the fighter
            index (int): The index of the example in the dataset

        Returns:
            pd.DataFrame: The dataframe containing the fighter data filtered by fighter
        """

        year_ago = self.__compute_year_ago(df)
        all_prev_fights = df.loc[:index-1]
        if not all_prev_fights.empty:
            fighter_a_id_vals = all_prev_fights.fighter_a_id.values
            fighter_b_id_vals = all_prev_fights.fighter_b_id.values

            prev_fights = all_prev_fights[((fighter_a_id_vals == fighter_id) | (fighter_b_id_vals == fighter_id))]
            prev_fights_last_year = all_prev_fights[((fighter_a_id_vals == fighter_id) | (fighter_b_id_vals == fighter_id)) & (pd.to_datetime(all_prev_fights['date']) > year_ago[index])]

            return prev_fights, prev_fights_last_year
        return pd.DataFrame(), pd.DataFrame()
    
    def __create_col_names_win_loss(self):
        """
        Creates the column names for the win/loss features

        Returns:
            list: The list of column names for the win/loss features
        """

        col_names = []
        fighters = ['fighter-a', 'fighter-b']
        outcomes = ['wins', 'losses']
        methods = ['KO/TKO', 'submission', 'decision', 'total']
        weight_classes = ['flyweight', 'bantamweight', 'featherweight', 'lightweight', 'welterweight', 'middleweight', 'light-heavyweight', 'heavyweight', 'catchweight', 'overall']
        time_periods = ['last-year', 'all-time']

        for fighter in fighters:
            for outcome in outcomes:
                for method in methods:
                    for weight_class in weight_classes:
                        for time_period in time_periods:
                            col_name = f"{fighter.replace(' ', '_')}_{outcome}_{method}_{weight_class.replace(' ', '_')}_{time_period}"
                            col_names.append(col_name)
        return col_names
