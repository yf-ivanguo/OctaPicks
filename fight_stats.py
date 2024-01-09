import pandas as pd
import numpy as np


class FightStats:
    def __init__(self, df):
        self.df = df

    def get_fight_stats(self):
        self.df = self.create_knockdown_feats(self.df)
        self.df = self.create_significant_strikes_feats(self.df)
        self.df = self.create_takedown_feats(self.df)

        return self.df
    
    def create_knockdown_feats(self, df, include_progress=False):
        """
        Creates the knockdowns features for each fighter in the dataset

        Parameters:
            df (pd.DataFrame): DataFrame containing all the fights in the dataset

        Returns:
            pd.DataFrame: DataFrame containing the knockdowns features for each fighter in the dataset
        """

        col_names = ['fighter_a_kd_per_sigs_l3', 'fighter_b_kd_per_sigs_l3', \
                     'fighter_a_kd_per_sigs_l5', 'fighter_b_kd_per_sigs_l5', \
                     'fighter_a_kd_per_sigs_alltime', 'fighter_b_kd_per_sigs_alltime', \
                     'fighter_a_kd_per_sigs_l3_diff', 'fighter_b_kd_per_sigs_l3_diff', \
                     'fighter_a_kd_per_sigs_l5_diff', 'fighter_b_kd_per_sigs_l5_diff', \
                     'fighter_a_kd_per_sigs_alltime_diff', 'fighter_b_kd_per_sigs_alltime_diff']

        target_df = df.copy()
        result_features = pd.DataFrame(columns=col_names)

        result_features[['fighter_a_kd_per_sigs_l3', 'fighter_b_kd_per_sigs_l3']] = target_df.swifter.progress_bar(include_progress).apply(lambda row: self.compute_knockdowns(df, row['fighter_a_id'], row['fighter_b_id'], row.name, last_fights=3), axis=1)
        result_features[['fighter_a_kd_per_sigs_l5', 'fighter_b_kd_per_sigs_l5']] = target_df.swifter.progress_bar(include_progress).apply(lambda row: self.compute_knockdowns(df, row['fighter_a_id'], row['fighter_b_id'], row.name, last_fights=5), axis=1)
        result_features[['fighter_a_kd_per_sigs_alltime', 'fighter_b_kd_per_sigs_alltime']] = target_df.swifter.progress_bar(include_progress).apply(lambda row: self.compute_knockdowns(df, row['fighter_a_id'], row['fighter_b_id'], row.name), axis=1)
        result_features[['fighter_a_kd_per_sigs_l3_diff', 'fighter_b_kd_per_sigs_l3_diff']] = target_df.swifter.progress_bar(include_progress).apply(lambda row: self.compute_knockdowns(df, row['fighter_a_id'], row['fighter_b_id'], row.name, last_fights=3, differential=True), axis=1)
        result_features[['fighter_a_kd_per_sigs_l5_diff', 'fighter_b_kd_per_sigs_l5_diff']] = target_df.swifter.progress_bar(include_progress).apply(lambda row: self.compute_knockdowns(df, row['fighter_a_id'], row['fighter_b_id'], row.name, last_fights=5, differential=True), axis=1)
        result_features[['fighter_a_kd_per_sigs_alltime_diff', 'fighter_b_kd_per_sigs_alltime_diff']] = target_df.swifter.progress_bar(include_progress).apply(lambda row: self.compute_knockdowns(df, row['fighter_a_id'], row['fighter_b_id'], row.name, differential=True), axis=1)

        return pd.concat([target_df, result_features], axis=1)
    
    def compute_knockdowns(self, df, fighter_a_id, fighter_b_id, index, last_fights=0, differential=False):
        """
        Computes the knockdowns features for a single example in the dataset

        Parameters:
            df (pd.DataFrame): DataFrame containing all the fights in the dataset
            fighter_a_id (str): ID of fighter A
            fighter_b_id (str): ID of fighter B
            index (int): Index of the current fight in the dataset
            last_fights (int): Number of last fights to consider
            differential (bool): Whether to compute the differential of the knockdowns features

        Returns:
            pd.Series: Series containing the knockdowns features for both fighters
        """

        all_prev_fights = df.loc[:index-1]
        if not all_prev_fights.empty:
            fighter_a_id_vals = all_prev_fights.fighter_a_id.values
            fighter_b_id_vals = all_prev_fights.fighter_b_id.values

            fighter_a_fights = all_prev_fights[(fighter_a_id_vals == fighter_a_id) | (fighter_b_id_vals == fighter_a_id)][-last_fights:]
            fighter_b_fights = all_prev_fights[(fighter_a_id_vals == fighter_b_id) | (fighter_b_id_vals == fighter_b_id)][-last_fights:]

            fighter_a_kd_per_sigs = self.get_fighter_kd_per_sigs(fighter_a_fights, fighter_a_id)
            fighter_b_kd_per_sigs = self.get_fighter_kd_per_sigs(fighter_b_fights, fighter_b_id)

            if differential:
                return pd.Series([fighter_a_kd_per_sigs - fighter_b_kd_per_sigs, fighter_b_kd_per_sigs - fighter_a_kd_per_sigs])
            else:
                return pd.Series([fighter_a_kd_per_sigs, fighter_b_kd_per_sigs])
            
        return pd.Series([0, 0])
    
    def get_fighter_kd_per_sigs(self, fighter_past_fights, fighter_id):
        """
        Given a fighter's past fights, returns the number of knockdowns per significant strikes landed

        Parameters:
            fighter_past_fights (pd.DataFrame): DataFrame containing the fighter's past fights
            fighter_id (str): ID of the fighter

        Returns:
            float: Number of knockdowns per significant strikes landed
        """
        
        if fighter_past_fights.empty:
            return 0
        
        fighter_a_id_vals = fighter_past_fights.fighter_a_id.values
        fighter_b_id_vals = fighter_past_fights.fighter_b_id.values
        
        fighter_knockdowns = fighter_past_fights[fighter_a_id_vals == fighter_id]['fighter_a_total_kd'].sum() + \
                             fighter_past_fights[fighter_b_id_vals == fighter_id]['fighter_b_total_kd'].sum()
        
        fighter_sig_strikes = fighter_past_fights[fighter_a_id_vals == fighter_id]['fighter_a_total_sig_str_landed'].sum() + \
                              fighter_past_fights[fighter_b_id_vals == fighter_id]['fighter_b_total_sig_str_landed'].sum()

        return fighter_knockdowns / fighter_sig_strikes if fighter_sig_strikes > 0 else 0
    
    def test_knockdown_feature(self, df):
        """
        Tests the knockdowns feature

        Parameters:
            df (pd.DataFrame): DataFrame containing all the fights in the dataset

        Returns:
            pd.DataFrame: DataFrame containing the knockdowns features for each fighter in the dataset
        """

        test_df = self.create_knockdown_feats(df[((df['fighter_a_id'] == 'f1fac969a1d70b08') | (df['fighter_b_id'] == 'f1fac969a1d70b08'))]).reset_index(drop=True)

        fighter_a_cols = ['fighter_a_id', 'fighter_a_total_kd', 'fighter_a_total_sig_str_landed', \
                          'fighter_a_kd_per_sigs_l3', 'fighter_a_kd_per_sigs_l5', 'fighter_a_kd_per_sigs_alltime', \
                          'fighter_a_kd_per_sigs_l3_diff', 'fighter_a_kd_per_sigs_l5_diff', 'fighter_a_kd_per_sigs_alltime_diff']
        
        fighter_b_cols = ['fighter_b_id', 'fighter_b_total_kd', 'fighter_b_total_sig_str_landed', \
                          'fighter_b_kd_per_sigs_l3', 'fighter_b_kd_per_sigs_l5', 'fighter_b_kd_per_sigs_alltime', \
                          'fighter_b_kd_per_sigs_l3_diff', 'fighter_b_kd_per_sigs_l5_diff', 'fighter_b_kd_per_sigs_alltime_diff']
        
        combined_cols = np.concatenate((fighter_a_cols[3:], fighter_b_cols[3:]), axis=0)

        assert all(test_df[col].values[0] == 0.0 for col in combined_cols)

        formatted_test_df = test_df.apply(lambda row: self.swap_ids_and_columns(row, fighter_a_cols, fighter_b_cols), axis=1)
        
        test_methods = ['test_knockdown_feature_l3', 'test_knockdown_feature_l5', 'test_knockdown_feature_alltime']
        
        for method in test_methods:
            getattr(self, method)(formatted_test_df)

        print("Knockdown feature tests passed")

    def swap_ids_and_columns(self, row, fighter_a_cols, fighter_b_cols):
        """
        Swaps the fighter_a and fighter_b columns if the fighter_a_id is not the fighter we are interested in

        Parameters:
            row (Series): Row of the DataFrame
            fighter_a_cols (list): List of fighter_a columns
            fighter_b_cols (list): List of fighter_b columns
        
        Returns:
            Series: Row of the DataFrame with the fighter_a and fighter_b columns swapped if necessary
        """

        if row['fighter_b_id'] == 'f1fac969a1d70b08':
            for i in range(len(fighter_a_cols)):
                row[fighter_a_cols[i]], row[fighter_b_cols[i]] = row[fighter_b_cols[i]], row[fighter_a_cols[i]]
        
        return row

    def test_knockdown_feature_l3(self, df):
        """
        Tests the knockdowns feature for the last 3 fights

        Parameters:
            df (pd.DataFrame): DataFrame containing all the fights in the dataset
        """

        test_df = df.copy().reset_index(drop=True)
        columns_to_select = ['fighter_a_total_kd', 'fighter_a_total_sig_str_landed', 'fighter_b_total_kd', 'fighter_b_total_sig_str_landed']
        res_df = df[columns_to_select].rolling(3, min_periods=1).sum().reset_index(drop=True)

        for index, row in enumerate(test_df.itertuples()):
            if index > 0:
                expected = res_df.loc[index-1, 'fighter_a_total_kd'] / res_df.loc[index-1, 'fighter_a_total_sig_str_landed']
                actual = row.fighter_a_kd_per_sigs_l3
                assert expected == actual, f"Expected {expected}, but got {actual} on row {row.Index}"

    def test_knockdown_feature_l5(self, df):
        test_df = df.copy().reset_index(drop=True)
        columns_to_select = ['fighter_a_total_kd', 'fighter_a_total_sig_str_landed', 'fighter_b_total_kd', 'fighter_b_total_sig_str_landed']
        res_df = df[columns_to_select].rolling(5, min_periods=1).sum().reset_index(drop=True)

        for index, row in enumerate(test_df.itertuples()):
            if index > 0:
                expected = res_df.loc[index-1, 'fighter_a_total_kd'] / res_df.loc[index-1, 'fighter_a_total_sig_str_landed']
                actual = row.fighter_a_kd_per_sigs_l5
                assert expected == actual, f"Expected {expected}, but got {actual} on row {row.Index}"

    def test_knockdown_feature_alltime(self, df):
        test_df = df.copy().reset_index(drop=True)
        columns_to_select = ['fighter_a_total_kd', 'fighter_a_total_sig_str_landed', 'fighter_b_total_kd', 'fighter_b_total_sig_str_landed']
        res_df = df[columns_to_select].expanding().sum().reset_index(drop=True)

        for index, row in enumerate(test_df.itertuples()):
            if index > 0:
                expected = res_df.loc[index-1, 'fighter_a_total_kd'] / res_df.loc[index-1, 'fighter_a_total_sig_str_landed']
                actual = row.fighter_a_kd_per_sigs_alltime
                assert expected == actual, f"Expected {expected}, but got {actual} on row {row.Index}"

    def create_significant_strikes_feats(self, df):
        """
        Creates a dataframe with added features for significant strikes and their differentials.

        Args:
            df (pd.DataFrame): The original dataframe containing fight data.

        Returns:
            pd.DataFrame: A dataframe with additional columns for significant strike features and differentials.
        """
        # Generate column names for significant strikes and differentials
        col_names = self.create_col_names_significant_strikes()
        col_names_differential = self.create_col_names_differential_significant_strikes()

        # Copy the input dataframe and calculate significant strike features
        input_df = df.copy()
        result_features = pd.DataFrame(columns=col_names)
        result_features[col_names] = input_df.swifter.progress_bar(True).apply(lambda row: self.calculate_significant_strikes(input_df, row['fighter_a_id'], row['fighter_b_id'], row.name, col_names), axis=1)

        # Combine the input dataframe with the calculated features
        result_df = pd.concat([input_df, result_features], axis=1)

        # Calculate and add differential features to the dataframe
        result_df = self.calculate_significant_strikes_differential(result_df, col_names_differential)

        return result_df

    def calculate_significant_strikes(self, df, fighter_a_id, fighter_b_id, index, col_names):
        """
        Calculates significant strike features for both fighters in a match.

        Args:
            df (pd.DataFrame): The dataframe containing fight data.
            fighter_a_id (str): The ID of fighter A.
            fighter_b_id (str): The ID of fighter B.
            index (int): The index of the current row in the dataframe.
            col_names (list): List of column names to calculate.

        Returns:
            pd.Series: A series with calculated significant strike features.
        """
        # Initialize result list
        res = []
        fighter_a_last_3_fights, fighter_a_last_5_fights, fighter_a_prev_fights = self.get_fighter_fights(df, fighter_a_id, index)
        fighter_b_last_3_fights, fighter_b_last_5_fights, fighter_b_prev_fights = self.get_fighter_fights(df, fighter_b_id, index)

        for i in range(len(col_names)):
            split = col_names[i].split('_')
            fighter = split[0] # fighter-a, fighter-b
            stat = split[1] # significant-strikes-landed, significant-strikes-accuracy, significant-strikes-defense, significant-strikes-absorbed
            round = split[2]  # R1, R2, R3, R4, R5, overall
            time_period = split[3] # last-3-fights, last-5-fights, alltime

            # Get fights for the fighter
            all_prev_fights = fighter_a_prev_fights if fighter == 'fighter-a' else fighter_b_prev_fights
            last_3_fights = fighter_a_last_3_fights if fighter == 'fighter-a' else fighter_b_last_3_fights
            last_5_fights = fighter_a_last_5_fights if fighter == 'fighter-a' else fighter_b_last_5_fights
            
            prev_fights = pd.DataFrame()

            if fighter == 'fighter-a':
                fighter_id = fighter_a_id
            else:
                fighter_id = fighter_b_id

            # filter based on time period
            if time_period == 'l3':
                
                prev_fights = last_3_fights

            if time_period == 'l5':
                prev_fights = last_5_fights

            if time_period == 'alltime':
                prev_fights = all_prev_fights

            # if no fights 
            if prev_fights.empty:
                    res.append(0)
                    continue
            if round == 'overall':
                round = 0
            else:
                round = int(round[1])

            # filter and get the stats for the specific round
            raw_significant_strike_stats = self.get_raw_significant_strikes_stats(prev_fights, round)

            if raw_significant_strike_stats.empty:
                res.append(0)
                continue
        
            if stat == "significant-strikes-landed-per-minute":
                res.append(self.calculate_significant_strikes_landed(raw_significant_strike_stats, fighter_id))
            if stat == "significant-strikes-accuracy-percentage":
                res.append(self.calculate_significant_strikes_accuracy(raw_significant_strike_stats, fighter_id))
            if stat == "significant-strikes-defense-percentage":
                res.append(self.calculate_significant_strikes_defense(raw_significant_strike_stats, fighter_id))
            if stat == "significant-strikes-absorbed-per-minute":
                res.append(self.calculate_significant_strikes_absorbed(raw_significant_strike_stats, fighter_id))

        return pd.Series(res)

    def calculate_significant_strikes_differential(self, df, col_names_differential):
        """
        Calculates the differential of significant strikes statistics between two fighters.

        Args:
            df (pd.DataFrame): The dataframe containing significant strike statistics data for fighters.
            col_names_differential (list): List of column names for differential calculations.

        Returns:
            pd.DataFrame: A dataframe with added columns for differential significant strike features.
        """

        input_df = df.copy()
        differential_features = pd.DataFrame(columns=col_names_differential)
        for col_name in col_names_differential:
            # Split the column name to identify the fighter, type of strike, round, and time period
            split_name = col_name.split('_') # fighter-a_significant-strikes-landed-differential_R1_last-3-fights
            fighter, stat_type, round, time_period = split_name[0], split_name[1], split_name[2], split_name[3]

            if fighter == "fighter-a":
                # Calculate differential for fighter A
                fighter_a_col = '_'.join(['fighter-a', '-'.join(stat_type.split('-')[:-1]), round, time_period])
                fighter_b_col = '_'.join(['fighter-b', '-'.join(stat_type.split('-')[:-1]), round, time_period])

                differential_features[col_name] = input_df[fighter_a_col] - input_df[fighter_b_col]

                # Calculate and set the corresponding differential for fighter B
                fighter_b_diff_col = '_'.join(['fighter-b', stat_type, round, time_period])
                differential_features[fighter_b_diff_col] = -differential_features[col_name]

        result_df = pd.concat([input_df, differential_features], axis=1)

        return result_df

    def create_col_names_significant_strikes(self):
        """
        Generates column names for significant strike statistics.

        Returns:
            list: A list of strings, each representing a column name for a specific significant strike statistic.
        """
        col_names = []
        fighters = ['fighter-a', 'fighter-b']
        significant_strike_stats = ['significant-strikes-landed-per-minute', 'significant-strikes-accuracy-percentage', 'significant-strikes-defense-percentage', 'significant-strikes-absorbed-per-minute']
        rounds = ['R1', 'R2', 'R3', 'R4', 'R5', 'overall']
        time_periods = ['l3', 'l5', 'alltime']

        # Iterate through all combinations to create column names
        for fighter in fighters:
            for significant_strike_stat in significant_strike_stats:
                for round in rounds:
                    for time_period in time_periods:
                        col_name = f"{fighter.replace(' ', '_')}_{significant_strike_stat.replace(' ', '_')}_{round}_{time_period.replace(' ', '_')}"
                        col_names.append(col_name)
        return col_names

    def create_col_names_differential_significant_strikes(self):
        """
        Generates column names for differential significant strike statistics.

        Returns:
            list: A list of strings, each representing a column name for a specific significant strike statistic.
        """

        col_names = []
        fighters = ['fighter-a', 'fighter-b']
        significant_strike_stats = ['significant-strikes-landed-per-minute-diff', 'significant-strikes-accuracy-percentage-diff', 'significant-strikes-defense-percentage-diff', 'significant-strikes-absorbed-per-minute-diff']
        rounds = ['R1', 'R2', 'R3', 'R4', 'R5', 'overall']
        time_periods = ['l3', 'l5', 'alltime']

        # Iterate through all combinations to create column names
        for fighter in fighters:
            for significant_strike_stat in significant_strike_stats:
                for round in rounds:
                    for time_period in time_periods:
                        col_name = f"{fighter.replace(' ', '_')}_{significant_strike_stat.replace(' ', '_')}_{round}_{time_period.replace(' ', '_')}"
                        col_names.append(col_name)
        return col_names
        
    def get_raw_significant_strikes_stats(self, df, round):
        """
        Extracts raw significant strike stats from the dataframe for a specific round.

        Args:
            df (pd.DataFrame): The dataframe containing fight records.
            round (str): The round for which the statistics are required.

        Returns:
            pd.DataFrame: A dataframe with raw stats for the specified round for fighters a and b.
        """

        # Define column names based on the round
        if round == 0:
            # Use overall stats columns
            sig_str_cols = [
                'fighter_a_total_sig_str_landed',
                'fighter_a_total_sig_str_attempted',
                'fighter_b_total_sig_str_landed',
                'fighter_b_total_sig_str_attempted'
            ]
        else:
            # Use specific round stats columns
            sig_str_cols = [
                f'fighter_a_round_{round}_sig_str_landed',
                f'fighter_a_round_{round}_sig_str_attempted',
                f'fighter_b_round_{round}_sig_str_landed',
                f'fighter_b_round_{round}_sig_str_attempted'
            ]

        # Apply vectorization for calculating total fight time
        total_fight_times = df.apply(lambda row: self.get_round_time(row['outcome_round'], row['outcome_time'], round), axis=1)

        # Select and rename the significant strike stats columns in the DataFrame to match the target structure
        sig_str_stats_df = df[sig_str_cols].rename(columns={
            sig_str_cols[0]: 'fighter_a_sig_str_landed',
            sig_str_cols[1]: 'fighter_a_sig_str_attempted',
            sig_str_cols[2]: 'fighter_b_sig_str_landed',
            sig_str_cols[3]: 'fighter_b_sig_str_attempted'
        })

        # Concatenate the total fight times with the significant strike stats
        stats_df = pd.concat([total_fight_times.rename('total_fight_time'), df[['fighter_a_id', 'fighter_b_id']], sig_str_stats_df], axis=1)

        return stats_df

    def calculate_significant_strikes_landed(self, stats_by_fight_df, fighter_id):
        """
        Calculates the rate of significant strikes landed per minute by a fighter.

        Args:
            stats_by_fight_df (pd.DataFrame): The dataframe containing aggregated fight stats.
            fighter_id (str): The ID of the fighter.

        Returns:
            float: The rate of significant strikes landed per minute in the given fights.
        """

        return self.get_significant_strikes_return_values(stats_by_fight_df, fighter_id, is_percentage=False, is_defence=False)

    def calculate_significant_strikes_accuracy(self, stats_by_fight_df, fighter_id):
        """
        Calculates the accuracy of significant strikes for a fighter.

        Args:
            stats_df (pd.DataFrame): The dataframe containing aggregated fight stats.
            fighter_id (str): The ID of the fighter.

        Returns:
            float: The accuracy of significant strikes as a percentage in the given fights.
        """

        return self.get_significant_strikes_return_values(self, stats_by_fight_df, fighter_id, is_percentage=True, is_defence=False)

    def calculate_significant_strikes_defense(self, stats_by_fight_df, fighter_id):
        """
        Calculates the defense rate against significant strikes for a fighter.

        Args:
            stats_df (pd.DataFrame): The dataframe containing aggregated fight stats.
            fighter_id (str): The ID of the fighter.

        Returns:
            float: The defense rate against significant strikes as a percentage in the given fights.
        """

        return 1 - self.get_significant_strikes_return_values(stats_by_fight_df, fighter_id, is_percentage=True, is_defence= True)

    def calculate_significant_strikes_absorbed(self, stats_by_fight_df, fighter_id):
        """
        Calculates the rate of significant strikes absorbed per minute by a fighter.

        Args:
            stats_df (pd.DataFrame): The dataframe containing aggregated fight stats.
            fighter_id (str): The ID of the fighter.

        Returns:
            float: The rate of significant strikes absorbed per minute in the given fights.
        """

        return self.get_significant_strikes_return_values(self, stats_by_fight_df, fighter_id, is_percentage=False, is_defence=True)

    def convert_time_to_seconds(self, time_str):
        """
        Converts a time string in MM:SS format to total seconds.

        Args:
            time_str (str): The time string to convert.

        Returns:
            int: The time in total seconds.
        """

        if ':' in time_str:
            minutes, seconds = time_str.split(':')
            return int(minutes) * 60 + int(seconds)
        else:
            return int(time_str)
        
    def get_round_time(self, outcome_round, outcome_time, round):
        """
        Calculates the total fight time in a specific round.

        Args:
            outcome_round (int): The round number at the end of the fight.
            outcome_time (str): The time at which the fight ended in the outcome round.
            round (str): The round for which the time is to be calculated.

        Returns:
            float: The total fight time in the specified round in minutes.
        """

        # Convert outcome_time to seconds
        outcome_time = self.convert_time_to_seconds(outcome_time)
        
        # Handle the "overall" case
        if round == 0:
            # Calculate total fight time up to the outcome round
            total_time = 0

            for r in range(1, outcome_round):
                total_time += 300  # Add full time for each completed round

            total_time += outcome_time  # Add the time of the last (outcome) round

            return total_time / 60  # Convert to minutes

        # Handle specific rounds
        if outcome_round == round:
            return outcome_time/60  # Convert to minutes
        
        elif outcome_round > round:
            return 300/60  # Full round time
        
        else:
            return 0  # Round did not occur

    def get_significant_strikes_return_values(self, stats_by_fight_df, fighter_id, is_percentage, is_defence):

        """
        Calculates either the rate or the percentage of significant strikes for a fighter.

        Args:
            stats_by_fight_df (pd.DataFrame): DataFrame containing the statistics of the fights.
            fighter_id (str): ID of the fighter whose statistics are being calculated.
            is_percentage (bool): Flag to indicate whether to calculate the percentage (True) or rate (False).
            is_defence (bool): Flag to indicate whether to calculate for defence (True) or offence (False).

        Returns:
            float: Calculated rate or percentage of significant strikes.
        """

        # Get the IDs of the fighters in the fights
        fighter_a_id_vals = stats_by_fight_df.fighter_a_id.values
        fighter_b_id_vals = stats_by_fight_df.fighter_b_id.values


        # Sum up significant strikes landed based on whether it's for defence or offence
        sig_str_landed = stats_by_fight_df[fighter_a_id_vals == fighter_id][f'fighter_a_sig_str_landed' if not is_defence else f'fighter_b_sig_str_landed'].sum() + stats_by_fight_df[fighter_b_id_vals == fighter_id][f'fighter_b_sig_str_landed' if not is_defence else f'fighter_a_sig_str_landed'].sum()

        if not is_percentage:
            # Sum total fight time and calculate rate of significant strikes landed per minute
            total_fight_time = stats_by_fight_df['total_fight_time'].sum()
            if total_fight_time == 0:
                return 0
            return sig_str_landed / total_fight_time
        else:
            # Sum up significant strikes attempted and calculate the accuracy percentage
            sig_str_attempted = stats_by_fight_df[fighter_a_id_vals == fighter_id]['fighter_a_sig_str_attempted'].sum() + stats_by_fight_df[fighter_b_id_vals == fighter_id]['fighter_b_sig_str_attempted'].sum()
            if sig_str_attempted == 0:
                return 0
            return sig_str_landed / sig_str_attempted
        
    def create_takedown_feats(self, df):
            """
            Creates a dataframe with added features for takedowns and their differentials.

            Args:
                df (pd.DataFrame): The original dataframe containing fight data.

            Returns:
                pd.DataFrame: A dataframe with additional columns for significant strike features and differentials.
            """
            # Generate column names for takedowns and differentials
            col_names = self.create_col_names_takedowns()
            col_names_differential = self.create_col_names_differential_takedowns()

            # Copy the input dataframe and calculate significant strike features
            input_df = df.copy()
            result_features = pd.DataFrame(columns=col_names)
            result_features[col_names] = input_df.swifter.progress_bar(True).apply(lambda row: self.calculate_takedowns(input_df, row['fighter_a_id'], row['fighter_b_id'], row.name, col_names), axis=1)

            # Combine the input dataframe with the calculated features
            result_df = pd.concat([input_df, result_features], axis=1)

            # Calculate and add differential features to the dataframe
            result_df = self.calculate_takedowns_differential(result_df, col_names_differential)

            return result_df

    def calculate_takedowns(self, df, fighter_a_id, fighter_b_id, index, col_names):
        """
        Calculates significant strike features for both fighters in a match.

        Args:
            df (pd.DataFrame): The dataframe containing fight data.
            fighter_a_id (str): The ID of fighter A.
            fighter_b_id (str): The ID of fighter B.
            index (int): The index of the current row in the dataframe.
            col_names (list): List of column names to calculate.

        Returns:
            pd.Series: A series with calculated significant strike features.
        """
        # Initialize result list
        res = []
        fighter_a_last_3_fights, fighter_a_last_5_fights, fighter_a_prev_fights = self.get_fighter_fights(df, fighter_a_id, index)
        fighter_b_last_3_fights, fighter_b_last_5_fights, fighter_b_prev_fights = self.get_fighter_fights(df, fighter_b_id, index)

        for i in range(len(col_names)):
            split = col_names[i].split('_')
            fighter = split[0] # fighter-a, fighter-b
            stat = split[1] # takedown-landed, takedown-accuracy, takedown-defense, takedown-absorbed
            round = split[2]  # R1, R2, R3, R4, R5, overall
            time_period = split[3] # last-3-fights, last-5-fights, alltime

            # Get fights for the fighter
            all_prev_fights = fighter_a_prev_fights if fighter == 'fighter-a' else fighter_b_prev_fights
            last_3_fights = fighter_a_last_3_fights if fighter == 'fighter-a' else fighter_b_last_3_fights
            last_5_fights = fighter_a_last_5_fights if fighter == 'fighter-a' else fighter_b_last_5_fights
            
            prev_fights = pd.DataFrame()

            if fighter == 'fighter-a':
                fighter_id = fighter_a_id
            else:
                fighter_id = fighter_b_id

            # filter based on time period
            if time_period == 'l3':
                
                prev_fights = last_3_fights

            if time_period == 'l5':
                prev_fights = last_5_fights

            if time_period == 'alltime':
                prev_fights = all_prev_fights

            # if no fights 
            if prev_fights.empty:
                    res.append(np.nan)
                    continue
            if round == 'overall':
                round = 0
            else:
                round = int(round[1])

            # filter and get the stats for the specific round
            raw_significant_strike_stats = self.get_raw_takedowns_stats(prev_fights, round)

            if raw_significant_strike_stats.empty:
                res.append(np.nan)
                continue
        
            if stat == "takedown-landed-per-minute":
                res.append(self.calculate_takedowns_landed(raw_significant_strike_stats, fighter_id))
            if stat == "takedown-accuracy-percentage":
                res.append(self.calculate_takedowns_accuracy(raw_significant_strike_stats, fighter_id))
            if stat == "takedown-defense-percentage":
                res.append(self.calculate_takedowns_defense(raw_significant_strike_stats, fighter_id))
            if stat == "takedown-absorbed-per-minute":
                res.append(self.calculate_takedowns_absorbed(raw_significant_strike_stats, fighter_id))

        return pd.Series(res)

    def calculate_takedowns_differential(self, df, col_names_differential):
        """
        Calculates the differential of takedowns statistics between two fighters.

        Args:
            df (pd.DataFrame): The dataframe containing significant strike statistics data for fighters.
            col_names_differential (list): List of column names for differential calculations.

        Returns:
            pd.DataFrame: A dataframe with added columns for differential significant strike features.
        """

        input_df = df.copy()
        differential_features = pd.DataFrame(columns=col_names_differential)
        for col_name in col_names_differential:
            # Split the column name to identify the fighter, type of strike, round, and time period
            split_name = col_name.split('_') # fighter-a_takedown-landed-differential_R1_last-3-fights
            fighter, stat_type, round, time_period = split_name[0], split_name[1], split_name[2], split_name[3]

            if fighter == "fighter-a":
                # Calculate differential for fighter A
                fighter_a_col = '_'.join(['fighter-a', '-'.join(stat_type.split('-')[:-1]), round, time_period])
                fighter_b_col = '_'.join(['fighter-b', '-'.join(stat_type.split('-')[:-1]), round, time_period])

                differential_features[col_name] = input_df[fighter_a_col] - input_df[fighter_b_col]

                # Calculate and set the corresponding differential for fighter B
                fighter_b_diff_col = '_'.join(['fighter-b', stat_type, round, time_period])
                differential_features[fighter_b_diff_col] = -differential_features[col_name]

        result_df = pd.concat([input_df, differential_features], axis=1)

        return result_df

    def create_col_names_takedowns(self):
        """
        Generates column names for significant strike statistics.

        Returns:
            list: A list of strings, each representing a column name for a specific significant strike statistic.
        """
        col_names = []
        fighters = ['fighter-a', 'fighter-b']
        significant_strike_stats = ['takedown-landed-per-minute', 'takedown-accuracy-percentage', 'takedown-defense-percentage', 'takedown-absorbed-per-minute']
        rounds = ['R1', 'R2', 'R3', 'R4', 'R5', 'overall']
        time_periods = ['l3', 'l5', 'alltime']

        # Iterate through all combinations to create column names
        for fighter in fighters:
            for significant_strike_stat in significant_strike_stats:
                for round in rounds:
                    for time_period in time_periods:
                        col_name = f"{fighter.replace(' ', '_')}_{significant_strike_stat.replace(' ', '_')}_{round}_{time_period.replace(' ', '_')}"
                        col_names.append(col_name)
        return col_names

    def create_col_names_differential_takedowns(self):
        """
        Generates column names for differential significant strike statistics.

        Returns:
            list: A list of strings, each representing a column name for a specific significant strike statistic.
        """

        col_names = []
        fighters = ['fighter-a', 'fighter-b']
        significant_strike_stats = ['takedown-landed-per-minute-diff', 'takedown-accuracy-percentage-diff', 'takedown-defense-percentage-diff', 'takedown-absorbed-per-minute-diff']
        rounds = ['R1', 'R2', 'R3', 'R4', 'R5', 'overall']
        time_periods = ['l3', 'l5', 'alltime']

        # Iterate through all combinations to create column names
        for fighter in fighters:
            for significant_strike_stat in significant_strike_stats:
                for round in rounds:
                    for time_period in time_periods:
                        col_name = f"{fighter.replace(' ', '_')}_{significant_strike_stat.replace(' ', '_')}_{round}_{time_period.replace(' ', '_')}"
                        col_names.append(col_name)
        return col_names

    def get_fighter_fights(self, df, fighter_id, index):
        """
        Retrieves the most recent fights of a fighter before a given index in the dataframe.

        Args:
            df (pd.DataFrame): The dataframe containing fight records.
            fighter_id (str): The ID of the fighter.
            index (int): The index in the dataframe up to which fights should be considered.

        Returns:
            tuple: Contains three dataframes - the last 3 fights, the last 5 fights, and all previous fights.
        """

        all_prev_fights = df.loc[:index-1]
        col_names = df.columns
        all_prev_fights_default = pd.DataFrame(columns=col_names)

        if not all_prev_fights.empty:
            # Filter fights involving the specified fighter
            fighter_a_id_vals = all_prev_fights.fighter_a_id.values
            fighter_b_id_vals = all_prev_fights.fighter_b_id.values

            prev_fights = all_prev_fights[((fighter_a_id_vals == fighter_id) | (fighter_b_id_vals == fighter_id))]

            return prev_fights[-3:], prev_fights[-5:], prev_fights

        return all_prev_fights_default(), all_prev_fights_default(), all_prev_fights_default()
        
    def get_raw_takedowns_stats(self, df, round):
        """
        Extracts raw significant strike stats from the dataframe for a specific round.

        Args:
            df (pd.DataFrame): The dataframe containing fight records.
            round (str): The round for which the statistics are required.

        Returns:
            pd.DataFrame: A dataframe with raw stats for the specified round for fighters a and b.
        """

        # Define column names based on the round
        if round == 0:
            # Use overall stats columns
            td_cols = [
                'fighter_a_total_td_landed',
                'fighter_a_total_td_attempted',
                'fighter_b_total_td_landed',
                'fighter_b_total_td_attempted'
            ]
        else:
            # Use specific round stats columns
            td_cols = [
                f'fighter_a_round_{round}_td_landed',
                f'fighter_a_round_{round}_td_attempted',
                f'fighter_b_round_{round}_td_landed',
                f'fighter_b_round_{round}_td_attempted'
            ]

        # Apply vectorization for calculating total fight time
        total_fight_times = df.apply(lambda row: self.get_round_time(row['outcome_round'], row['outcome_time'], round), axis=1)

        # Select and rename the significant strike stats columns in the DataFrame to match the target structure
        td_stats_df = df[td_cols].rename(columns={
            td_cols[0]: 'fighter_a_td_landed',
            td_cols[1]: 'fighter_a_td_attempted',
            td_cols[2]: 'fighter_b_td_landed',
            td_cols[3]: 'fighter_b_td_attempted'
        })

        # Concatenate the total fight times with the significant strike stats
        stats_df = pd.concat([total_fight_times.rename('total_fight_time'), df[['fighter_a_id', 'fighter_b_id']], td_stats_df], axis=1)

        return stats_df

    def calculate_takedowns_landed(self, stats_by_fight_df, fighter_id):
        """
        Calculates the rate of takedowns landed per minute by a fighter.

        Args:
            stats_by_fight_df (pd.DataFrame): The dataframe containing aggregated fight stats.
            fighter_id (str): The ID of the fighter.

        Returns:
            float: The rate of takedowns landed per minute in the given fights.
        """

        return self.get_takedowns_return_values(stats_by_fight_df, fighter_id, is_percentage=False, is_defence=False)

    def calculate_takedowns_accuracy(self, stats_by_fight_df, fighter_id):
        """
        Calculates the accuracy of takedowns for a fighter.

        Args:
            stats_df (pd.DataFrame): The dataframe containing aggregated fight stats.
            fighter_id (str): The ID of the fighter.

        Returns:
            float: The accuracy of takedowns as a percentage in the given fights.
        """

        return self.get_takedowns_return_values(stats_by_fight_df, fighter_id, is_percentage=True, is_defence=False)

    def calculate_takedowns_defense(self, stats_by_fight_df, fighter_id):
        """
        Calculates the defense rate against takedowns for a fighter.

        Args:
            stats_df (pd.DataFrame): The dataframe containing aggregated fight stats.
            fighter_id (str): The ID of the fighter.

        Returns:
            float: The defense rate against takedowns as a percentage in the given fights.
        """

        return 1 - self.get_takedowns_return_values(stats_by_fight_df, fighter_id, is_percentage=True, is_defence= True)

    def calculate_takedowns_absorbed(self, stats_by_fight_df, fighter_id):
        """
        Calculates the rate of takedowns absorbed per minute by a fighter.

        Args:
            stats_df (pd.DataFrame): The dataframe containing aggregated fight stats.
            fighter_id (str): The ID of the fighter.

        Returns:
            float: The rate of takedowns absorbed per minute in the given fights.
        """

        return self.get_takedowns_return_values(stats_by_fight_df, fighter_id, is_percentage=False, is_defence=True)

    def convert_time_to_seconds(self, time_str):
        """
        Converts a time string in MM:SS format to total seconds.

        Args:
            time_str (str): The time string to convert.

        Returns:
            int: The time in total seconds.
        """

        if ':' in time_str:
            minutes, seconds = time_str.split(':')
            return int(minutes) * 60 + int(seconds)
        else:
            return int(time_str)
        
    def get_round_time(self, outcome_round, outcome_time, round):
        """
        Calculates the total fight time in a specific round.

        Args:
            outcome_round (int): The round number at the end of the fight.
            outcome_time (str): The time at which the fight ended in the outcome round.
            round (str): The round for which the time is to be calculated.

        Returns:
            float: The total fight time in the specified round in minutes.
        """

        # Convert outcome_time to seconds
        outcome_time = self.convert_time_to_seconds(outcome_time)
        
        # Handle the "overall" case
        if round == 0:
            # Calculate total fight time up to the outcome round
            total_time = 0

            for r in range(1, outcome_round):
                total_time += 300  # Add full time for each completed round

            total_time += outcome_time  # Add the time of the last (outcome) round

            return total_time / 60  # Convert to minutes

        # Handle specific rounds
        if outcome_round == round:
            return outcome_time/60  # Convert to minutes
        
        elif outcome_round > round:
            return 300/60  # Full round time
        
        else:
            return 0  # Round did not occur

    def get_takedowns_return_values(self, stats_by_fight_df, fighter_id, is_percentage, is_defence):
        """
        Calculates either the rate or the percentage of takedowns for a fighter.

        Args:
            stats_by_fight_df (pd.DataFrame): DataFrame containing the statistics of the fights.
            fighter_id (str): ID of the fighter whose statistics are being calculated.
            is_percentage (bool): Flag to indicate whether to calculate the percentage (True) or rate (False).
            is_defence (bool): Flag to indicate whether to calculate for defence (True) or offence (False).

        Returns:
            float: Calculated rate or percentage of takedowns.
        """

        # Get the IDs of the fighters in the fights
        fighter_a_id_vals = stats_by_fight_df.fighter_a_id.values
        fighter_b_id_vals = stats_by_fight_df.fighter_b_id.values


        # Sum up takedowns landed based on whether it's for defence or offence
        td_landed = stats_by_fight_df[fighter_a_id_vals == fighter_id][f'fighter_a_td_landed' if not is_defence else f'fighter_b_td_landed'].sum() + stats_by_fight_df[fighter_b_id_vals == fighter_id][f'fighter_b_td_landed' if not is_defence else f'fighter_a_td_landed'].sum()

        if not is_percentage:
            # Sum total fight time and calculate rate of takedowns landed per minute
            total_fight_time = stats_by_fight_df['total_fight_time'].sum()
            if total_fight_time == 0:
                return 0
            return td_landed / total_fight_time
        else:
            # Sum up takedowns attempted and calculate the accuracy percentage
            td_attempted = stats_by_fight_df[fighter_a_id_vals == fighter_id]['fighter_a_td_attempted'].sum() + stats_by_fight_df[fighter_b_id_vals == fighter_id]['fighter_b_td_attempted'].sum()
            if td_attempted == 0:
                return 0
            return td_landed / td_attempted