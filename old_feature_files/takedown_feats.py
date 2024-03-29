from dateutil.relativedelta import relativedelta
import swifter
import pandas as pd
default_val = 0

class TakeDown():
    """
    This class provides functionalities to calculate various takedown statistics for UFC fighters.
    """

    def __init__(self) -> None: 
        """
        Initializes the TakeDown class
        """

        self.default_val = 0

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

            fighter_id = fighter_a_id if fighter == 'fighter-a' else fighter_b_id

            # filter based on time period
            if time_period == 'l3':
                
                prev_fights = last_3_fights

            if time_period == 'l5':
                prev_fights = last_5_fights

            if time_period == 'alltime':
                prev_fights = all_prev_fights

            # if no fights 
            if prev_fights.empty:
                    res.append(default_val)
                    continue
            if round == 'overall':
                round = 0
            else:
                round = int(round[1])

            # filter and get the stats for the specific round
            raw_significant_strike_stats = self.get_raw_takedowns_stats(prev_fights, round)

            if raw_significant_strike_stats.empty:
                res.append(default_val)
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
        for significant_strike_stat in significant_strike_stats:
            for round in rounds:
                for time_period in time_periods:
                    for fighter in fighters:
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
        for significant_strike_stat in significant_strike_stats:
            for round in rounds:
                for time_period in time_periods:
                    for fighter in fighters:
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

        # Filter rows where the fighter is fighter_a and sum up their takedowns
        td_landed_a = stats_by_fight_df[fighter_a_id_vals == fighter_id][f'fighter_a_td_landed' if not is_defence else f'fighter_b_td_landed'].sum()

        # Filter rows where the fighter is fighter_b and sum up their takedowns
        td_landed_b = stats_by_fight_df[fighter_b_id_vals == fighter_id][f'fighter_b_td_landed' if not is_defence else f'fighter_a_td_landed'].sum()

        # Sum up takedowns landed from both calculations
        td_landed = td_landed_a + td_landed_b

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
        
