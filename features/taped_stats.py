import pandas as pd
from datetime import datetime
import swifter

class TapedStats:
    def __init__(self):
        pass

    def create_taped_stats_feats(self, df, static_stats_df):
        """
        Creates a dataframe with added features for taped stats and their differentials.

        Args:
            df (pd.DataFrame): The original dataframe containing fight data.
            static_stats_df (pd.DataFrame): The dataframe containing static fighter statistics.

        Returns:
            pd.DataFrame: A dataframe for the additional columns for the taped stats features and thier differentials.
        """

        # Generate column names for significant strikes and differentials
        col_names = self.create_col_names_taped()
        # print(len(col_names))
        # df['date'] = pd.to_datetime(df['date'])
        # Copy the input dataframe and calculate significant strike features
        input_df = df.copy()
        result_features = pd.DataFrame(columns=col_names)
        result_features[col_names] = input_df.swifter.progress_bar(True).apply(lambda row: self.calculate_taped_stats(input_df, static_stats_df, row['fighter_a_id'], row['fighter_b_id'], row.name), axis=1)

        # Combine the input dataframe with the calculated features
        result_df = pd.concat([input_df, result_features], axis=1)

        result_df = self.calculate_taped_stats_differentials(result_df)

        return result_df

    def calculate_taped_stats_differentials(self, df):
        """
        Calculates the differential of taped stats (height, reach, age) between two fighters.

        Args:
            df (pd.DataFrame): The dataframe containing taped stats data for fighters.

        Returns:
            pd.DataFrame: A dataframe with added columns for differential taped stats features.
        """

        input_df = df.copy()

        # Calculate differentials for height, reach, and age
        input_df['fighter-a_height-diff'] = input_df['fighter-a_height'] - input_df['fighter-b_height']
        input_df['fighter-b_height-diff'] = -input_df['fighter-a_height-diff']

        input_df['fighter-a_reach-diff'] = input_df['fighter-a_reach'] - input_df['fighter-b_reach']
        input_df['fighter-b_reach-diff'] = -input_df['fighter-a_reach-diff']

        input_df['fighter-a_age-diff'] = input_df['fighter-a_age'] - input_df['fighter-b_age']
        input_df['fighter-b_age-diff'] = -input_df['fighter-a_age-diff']

        return input_df

    def calculate_taped_stats(self, df, static_stats_df, fighter_a_id, fighter_b_id, index):
        res = []

        res += self.get_taped_stats(df, static_stats_df, fighter_a_id, index)
        res += self.get_taped_stats(df, static_stats_df, fighter_b_id, index)

        return pd.Series(res)

    def get_taped_stats(self, df, static_stats_df, fighter_id, index):

        res = []

        fighter_stats = static_stats_df.loc[static_stats_df['ID'] == fighter_id]

        fighter_stats = fighter_stats.iloc[0]

        fighter_stats = fighter_stats[['Height', 'Reach', 'DOB']]

        for i in range(0, 3):
            if i == 0:
                res.append(self.convert_to_cm(fighter_stats[i], 'height'))
                continue
            elif i == 1:
                res.append(self.convert_to_cm(fighter_stats[i], 'reach'))
                continue
            elif i == 2:
                res.append(self.get_age(fighter_stats[i]))
                continue

        res.append(self.get_avg_fight_time(df, fighter_id, index))

        return res


    def get_avg_fight_time(self, df, fighter_id, index):
        all_prev_fights = df.loc[:index-1]
        if not all_prev_fights.empty:
            # Filter fights involving the specified fighter
            fighter_a_id_vals = all_prev_fights.fighter_a_id.values
            fighter_b_id_vals = all_prev_fights.fighter_b_id.values

            prev_fights = all_prev_fights[((fighter_a_id_vals == fighter_id) | (fighter_b_id_vals == fighter_id))]
            round_time = (prev_fights['outcome_round'] - 1).sum() * 60
            min_time = prev_fights['outcome_time'].apply(lambda x: self.convert_time_to_seconds(x)).sum()
            total_fight_time = round_time + min_time

            fight_count = prev_fights.shape[0]
            if fight_count > 0:
                return total_fight_time / fight_count
            return 0
        else:
            return 0

    def get_round_time(self, outcome_round, outcome_time):
        """
        Calculates the total fight time in a specific round.

        Args:
            outcome_round (int): The round number at the end of the fight.
            outcome_time (str): The time at which the fight ended in the outcome round.

        Returns:
            float: The total fight time in the specified round in minutes.
        """

        # Convert outcome_time to seconds
        outcome_time = self.convert_time_to_seconds(outcome_time)

        # Calculate total fight time up to the outcome round
        total_time = 0

        for r in range(1, outcome_round):
            total_time += 300  # Add full time for each completed round

        total_time += outcome_time  # Add the time of the last (outcome) round

        total_time /= 60  # Convert to minutes

        return total_time

    def convert_time_to_seconds(self, time_str):
        """
        Converts a time string in MM:SS format to total seconds.

        Args:
            time_str (str): The time string to convert.

        Returns:
            int: The time in total seconds.
        """

        minutes, seconds = map(int, time_str.split(':'))
        total_seconds = minutes * 60 + seconds
        return total_seconds

    def create_col_names_taped(self):
        """
        Generates column names for significant strike statistics.

        Returns:
            list: A list of strings, each representing a column name for a specific significant strike statistic.
        """
        col_names = []
        fighters = ['fighter-a', 'fighter-b']
        stats = ['height', 'reach', 'age', 'avg-fight-time']

        for fighter in fighters:
            for stat in stats:
                col_name = f"{fighter.replace(' ', '_')}_{stat.replace(' ', '_')}"
                col_names.append(col_name)
        return col_names

    def get_age(self, dob_str):
        if dob_str == "--":
            return 0
        dob = pd.to_datetime(dob_str)
        today = datetime.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return age


    def convert_to_cm(self, input_str, measurement_type):
        """
        Converts height or reach measurements to centimeters.

        Args:
            input_str (str): The string representation of the measurement (height or reach).
            measurement_type (str): Specifies the type of measurement ('height' or 'reach').

        Returns:
            float: The measurement in centimeters.
        """

        # Conversion factors
        inch_to_cm = 2.54
        foot_to_cm = 30.48

        if input_str == '--':
            return 0

        if measurement_type == 'height':
            # Height format expected: "6' 3"" (feet and inches)
            feet, inches = input_str.split("' ")
            return (int(feet) * foot_to_cm) + (int(inches.replace('"', '')) * inch_to_cm)

        elif measurement_type == 'reach':
            # Reach format expected: "74"" (inches)
            inches = input_str.replace('"', '')
            return int(inches) * inch_to_cm

        else:
            raise ValueError("Invalid measurement type. Please specify 'height' or 'reach'.")