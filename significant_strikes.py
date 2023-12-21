from dateutil.relativedelta import relativedelta
import swifter
import pandas as pd

class SignificantStrikes():
    """
    This class provides functionalities to calculate various significant strike statistics for UFC fighters.
    """

    def __init__(self) -> None: 
        """
        Initializes the SignificantStrikes class
        """

        self.default_val = 0

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
        fighter_a_last_3_fights, fighter_a_last_5_fights, fighter_a_prev_fights = self.get_fighter_fights_significant_strikes(df, fighter_a_id, index)
        fighter_b_last_3_fights, fighter_b_last_5_fights, fighter_b_prev_fights = self.get_fighter_fights_significant_strikes(df, fighter_b_id, index)

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
            if time_period == 'last-3-fights':
                
                prev_fights = last_3_fights

            if time_period == 'last-5-fights':
                prev_fights = last_5_fights

            if time_period == 'alltime':
                prev_fights = all_prev_fights

            # if no fights 
            if prev_fights.empty:
                    res.append(self.default_val)
                    continue
            
            # filter and get the stats for the specific round
            raw_significant_strike_stats = self.get_raw_significant_strikes_stats(prev_fights, round)

            if raw_significant_strike_stats.empty:
                res.append(self.default_val)
                continue
        
            if stat == "significant-strikes-landed":
                res.append(self.calculate_significant_strikes_landed(raw_significant_strike_stats, fighter_id))
            if stat == "significant-strikes-accuracy":
                res.append(self.calculate_significant_strikes_accuracy(raw_significant_strike_stats, fighter_id))
            if stat == "significant-strikes-defense":
                res.append(self.calculate_significant_strikes_defense(raw_significant_strike_stats, fighter_id))
            if stat == "significant-strikes-absorbed":
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
        significant_strike_stats = ['significant-strikes-landed', 'significant-strikes-accuracy', 'significant-strikes-defense', 'significant-strikes-absorbed']
        rounds = ['R1', 'R2', 'R3', 'R4', 'R5', 'overall']
        time_periods = ['last-3-fights', 'last-5-fights', 'alltime']

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
        significant_strike_stats = ['significant-strikes-landed-differential', 'significant-strikes-accuracy-differential', 'significant-strikes-defense-differential', 'significant-strikes-absorbed-differential']
        rounds = ['R1', 'R2', 'R3', 'R4', 'R5', 'overall']
        time_periods = ['last-3-fights', 'last-5-fights', 'alltime']

        # Iterate through all combinations to create column names
        for fighter in fighters:
            for significant_strike_stat in significant_strike_stats:
                for round in rounds:
                    for time_period in time_periods:
                        col_name = f"{fighter.replace(' ', '_')}_{significant_strike_stat.replace(' ', '_')}_{round}_{time_period.replace(' ', '_')}"
                        col_names.append(col_name)
        return col_names
    
    def get_fighter_fights_significant_strikes(self, df, fighter_id, index):
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

        if not all_prev_fights.empty:
            # Filter fights involving the specified fighter
            fighter_a_id_vals = all_prev_fights.fighter_a_id.values
            fighter_b_id_vals = all_prev_fights.fighter_b_id.values

            prev_fights = all_prev_fights[((fighter_a_id_vals == fighter_id) | (fighter_b_id_vals == fighter_id))]
            num_fights = len(prev_fights)

            # Initialize empty DataFrames for the scenarios where there are fewer than 3 or 5 fights
            last_3_fights = pd.DataFrame()
            last_5_fights = pd.DataFrame()

            # Check if the fighter has at least 3 fights
            if num_fights >= 3:
                last_3_fights = prev_fights.tail(3)
                
            else:
                # If fewer than 3 fights, return all available fights
                last_3_fights = prev_fights

            # Check if the fighter has at least 5 fights
            if num_fights >= 5:
                last_5_fights = prev_fights.tail(5)
                
            else:
                # If fewer than 5 fights, return all available fights
                last_5_fights = prev_fights
                
            return last_3_fights, last_5_fights, prev_fights

        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        

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
        if round == "overall":
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
                f'fighter_a_round_{round[1]}_sig_str_landed',
                f'fighter_a_round_{round[1]}_sig_str_attempted',
                f'fighter_b_round_{round[1]}_sig_str_landed',
                f'fighter_b_round_{round[1]}_sig_str_attempted'
            ]

        # Initialize an empty DataFrame with the specified columns
        stats_df = pd.DataFrame(columns=[
            'total_fight_time', 'fighter_a_id', 'fighter_b_id',
            'fighter_a_sig_str_landed', 'fighter_a_sig_str_attempted',
            'fighter_b_sig_str_landed', 'fighter_b_sig_str_attempted'
        ])

        # Iterate through each fight in the DataFrame
        for index, fight in df.iterrows():
            # Calculate the total fight time
            total_fight_time = self.get_round_time(fight['outcome_round'], fight['outcome_time'], round)

            # Extract relevant columns for the round
            sig_str_stats = [fight[col] for col in sig_str_cols]

            # Create a list of stats for the current fight
            fight_stats = [
                total_fight_time, fight['fighter_a_id'], fight['fighter_b_id']
            ] + sig_str_stats

            # Append the stats to the DataFrame
            stats_df.loc[index] = fight_stats

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

        # Initialize variables to store totals
        sig_str_landed = 0
        total_fight_time = 0

        # Iterate through each fight in the DataFrame
        for index, fight in stats_by_fight_df.iterrows():
            if fight['fighter_a_id'] == fighter_id:
                # Fighter is Fighter A
                sig_str_landed += fight['fighter_a_sig_str_landed']

            elif fight['fighter_b_id'] == fighter_id:
                # Fighter is Fighter B
                sig_str_landed += fight['fighter_b_sig_str_landed']

            # Sum the total fight time
            total_fight_time += fight['total_fight_time']

        # If no fights, return default value
        if total_fight_time == 0:
            return self.default_val
        
        return sig_str_landed / total_fight_time


    def calculate_significant_strikes_accuracy(self, stats_df, fighter_id):
        """
        Calculates the accuracy of significant strikes for a fighter.

        Args:
            stats_df (pd.DataFrame): The dataframe containing aggregated fight stats.
            fighter_id (str): The ID of the fighter.

        Returns:
            float: The accuracy of significant strikes as a percentage in the given fights.
        """

        # Initialize variables to store totals
        sig_str_landed = 0
        sig_str_attempted = 0

        # Iterate through each fight in the DataFrame
        for index, fight in stats_df.iterrows():
            if fight['fighter_a_id'] == fighter_id:
                # Fighter is Fighter A
                sig_str_landed += fight['fighter_a_sig_str_landed']
                sig_str_attempted += fight['fighter_a_sig_str_attempted']

            elif fight['fighter_b_id'] == fighter_id:
                # Fighter is Fighter B
                sig_str_landed += fight['fighter_b_sig_str_landed']
                sig_str_attempted += fight['fighter_b_sig_str_attempted']

        # If no fights, return default value
        if sig_str_attempted == 0:
            return self.default_val
        
        return sig_str_landed / sig_str_attempted


    def calculate_significant_strikes_defense(self, stats_df, fighter_id):
        """
        Calculates the defense rate against significant strikes for a fighter.

        Args:
            stats_df (pd.DataFrame): The dataframe containing aggregated fight stats.
            fighter_id (str): The ID of the fighter.

        Returns:
            float: The defense rate against significant strikes as a percentage in the given fights.
        """

        # Initialize variables to store totals
        sig_str_landed_op = 0
        sig_str_attempted_op = 0

        # Iterate through each fight in the DataFrame
        for index, fight in stats_df.iterrows():
            if fight['fighter_a_id'] == fighter_id:
                # Fighter is Fighter A
                sig_str_landed_op += fight['fighter_b_sig_str_landed']
                sig_str_attempted_op += fight['fighter_b_sig_str_attempted']

            elif fight['fighter_b_id'] == fighter_id:
                # Fighter is Fighter B
                sig_str_landed_op += fight['fighter_a_sig_str_landed']
                sig_str_attempted_op += fight['fighter_a_sig_str_attempted']

        # If no fights, return default value
        if sig_str_attempted_op == 0:
            return self.default_val
        
        return 1 - (sig_str_landed_op / sig_str_attempted_op)


    def calculate_significant_strikes_absorbed(self, stats_df, fighter_id):
        """
        Calculates the rate of significant strikes absorbed per minute by a fighter.

        Args:
            stats_df (pd.DataFrame): The dataframe containing aggregated fight stats.
            fighter_id (str): The ID of the fighter.

        Returns:
            float: The rate of significant strikes absorbed per minute in the given fights.
        """

        # Initialize variables to store totals
        sig_str_landed_op = 0
        sig_str_attempted_op = 0
        total_fight_time = 0

        # Iterate through each fight in the DataFrame
        for index, fight in stats_df.iterrows():
            if fight['fighter_a_id'] == fighter_id:
                # Fighter is Fighter A
                sig_str_landed_op += fight['fighter_b_sig_str_landed']
                sig_str_attempted_op += fight['fighter_b_sig_str_attempted']
            elif fight['fighter_b_id'] == fighter_id:
                # Fighter is Fighter B
                sig_str_landed_op += fight['fighter_a_sig_str_landed']
                sig_str_attempted_op += fight['fighter_a_sig_str_attempted']
            
            # Sum the total fight time
            total_fight_time += fight['total_fight_time']
        
        # If no fights, return default value
        if total_fight_time == 0:
            return self.default_val

        return (sig_str_attempted_op - sig_str_landed_op) / total_fight_time
    

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
        if round == "overall":
            # Calculate total fight time up to the outcome round
            total_time = 0

            for r in range(1, outcome_round):
                total_time += 300  # Add full time for each completed round

            total_time += outcome_time  # Add the time of the last (outcome) round

            return total_time / 60  # Convert to minutes
        
        round_num = int(round[1])  # Extract the round number from the string

        # Handle specific rounds
        if outcome_round == round_num:
            return outcome_time/60  # Convert to minutes
        
        elif outcome_round > round_num:
            return 300/60  # Full round time
        
        else:
            return 0  # Round did not occur