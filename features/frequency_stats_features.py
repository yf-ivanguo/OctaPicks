import pandas as pd
import numpy as np
import swifter

class FrequencyStats():
    """
    This class is used to create the total rounds fought features for each fighter in the dataset.
    """

    def __init__(self) -> None:
        """
        Initializes the TotalRounds class
        """
        pass

    def create_frequency_feats(self, df, include_progress=False):
        """
        Creates the frequency features for each fighter in the dataset

        Parameters:
            df (pd.DataFrame): DataFrame containing all the fights in the dataset

        Returns:
            pd.DataFrame: DataFrame containing the frequency features for each fighter in the dataset
        """

        col_names = ['fighter_a_fights_l6_months', 'fighter_b_fights_l6_months', \
                     'fighter_a_weeks_inactive', 'fighter_b_weeks_inactive']

        target_df = df.copy()
        result_features = pd.DataFrame(columns=col_names)

        result_features[col_names[:2]] = target_df.swifter.progress_bar(include_progress).apply(lambda row: self.__compute_fights_last_6_months(df, row['fighter_a_id'], row['fighter_b_id'], row.name), axis=1)
        result_features[col_names[2:]] = target_df.swifter.progress_bar(include_progress).apply(lambda row: self.__compute_weeks_inactive(df, row['fighter_a_id'], row['fighter_b_id'], row.name), axis=1)

        return pd.concat([target_df, result_features], axis=1)

    def create_total_rounds_fought_feats(self, df, include_progress=False):
            """
            Creates the total rounds fought features for each fighter in the dataset

            Parameters:
                df (pd.DataFrame): DataFrame containing all the fights in the dataset

            Returns:
                pd.DataFrame: DataFrame containing the total rounds fought features for each fighter in the dataset
            """

            col_names = ['fighter_a_total_rounds_fought_last_year', 'fighter_a_total_rounds_fought_alltime', \
                        'fighter_b_total_rounds_fought_last_year', 'fighter_b_total_rounds_fought_alltime']

            target_df = df.copy()
            result_features = pd.DataFrame(columns=col_names)

            result_features[col_names] = target_df.swifter.progress_bar(include_progress).apply(lambda row: self.__compute_total_rounds_fought(df, row['fighter_a_id'], row['fighter_b_id'], row.name), axis=1)

            return pd.concat([target_df, result_features], axis=1)

    def __compute_fights_last_6_months(self, df, fighter_a_id, fighter_b_id, index):
        """
        Computes the number of fights each fighter has had in the last 6 months

        Parameters:
            df (pd.DataFrame): DataFrame containing all the fights in the dataset
            fighter_a_id (str): ID of Fighter A
            fighter_b_id (str): ID of Fighter B
            index (int): Index of the current fight in the dataset

        Returns:
            pd.Series: Number of fights each fighter has had in the last 6 months
        """

        all_prev_fights = df.loc[:index-1]

        if not all_prev_fights.empty:
            fighter_a_id_vals = all_prev_fights.fighter_a_id.values
            fighter_b_id_vals = all_prev_fights.fighter_b_id.values
            # Assume dates are in datetime format
            date_vals = pd.DatetimeIndex(all_prev_fights.date)
            half_year_ago_vals = (all_prev_fights.date.max() - pd.DateOffset(months=6))

            fighter_a_fights = all_prev_fights[((fighter_a_id_vals == fighter_a_id) | (fighter_b_id_vals == fighter_a_id)) & (date_vals >= half_year_ago_vals)]
            fighter_b_fights = all_prev_fights[((fighter_a_id_vals == fighter_b_id) | (fighter_b_id_vals == fighter_b_id)) & (date_vals >= half_year_ago_vals)]

            return pd.Series([len(fighter_a_fights), len(fighter_b_fights)])

        return pd.Series([0, 0])

    def __compute_weeks_inactive(self, df, fighter_a_id, fighter_b_id, index):
        """
        Computes the number of weeks a fighter has been inactive

        Parameters:
            df (pd.DataFrame): DataFrame containing all the fights in the dataset
            fighter_id (str): ID of the fighter
            index (int): Index of the current fight in the dataset

        Returns:
            int: Number of weeks the fighter has been inactive
        """

        all_prev_fights = df.loc[:index-1]

        if not all_prev_fights.empty:
            fighter_a_id_vals = all_prev_fights.fighter_a_id.values
            fighter_b_id_vals = all_prev_fights.fighter_b_id.values

            fighter_a_fights = all_prev_fights[(fighter_a_id_vals == fighter_a_id) | (fighter_b_id_vals == fighter_a_id)]
            fighter_b_fights = all_prev_fights[(fighter_a_id_vals == fighter_b_id) | (fighter_b_id_vals == fighter_b_id)]

            fighter_a_weeks_inactive = self.__get_weeks_inactive(df.loc[index], fighter_a_fights)
            fighter_b_weeks_inactive = self.__get_weeks_inactive(df.loc[index], fighter_b_fights)

            return pd.Series([fighter_a_weeks_inactive, fighter_b_weeks_inactive])

        return pd.Series([0, 0])

    def __get_weeks_inactive(self, current_fight, fighter_prev_fights):
        """
        Computes the number of weeks since a fighter's last fight

        Parameters:
            current_fight (pd.Series): Series containing the current fight
            fighter_prev_fights (pd.DataFrame): DataFrame containing all the previous fights of the fighter

        Returns:
            int: Number of weeks the fighter has been inactive
        """

        if fighter_prev_fights.empty:
            return 0

        last_fight = fighter_prev_fights.iloc[-1]
        return (current_fight.date - last_fight.date).days // 7

    def __compute_total_rounds_fought(self, df, fighter_a_id, fighter_b_id, index):
        """
        Computes the total rounds fought features for a single example in the dataset

        Parameters:
            df (pd.DataFrame): Dataframe containing the fighter data
            fighter_a_id (int): The id of fighter a
            fighter_b_id (int): The id of fighter b
            index (int): The index of the example in the dataset

        Returns:
            pd.Series: The total rounds fought features for the example
        """

        all_prev_fights = df.loc[:index-1]
        if not all_prev_fights.empty:
            fighter_a_id_vals = all_prev_fights.fighter_a_id.values
            fighter_b_id_vals = all_prev_fights.fighter_b_id.values

            fighter_a_fights = all_prev_fights[(fighter_a_id_vals == fighter_a_id) | (fighter_b_id_vals == fighter_a_id)]
            fighter_b_fights = all_prev_fights[(fighter_a_id_vals == fighter_b_id) | (fighter_b_id_vals == fighter_b_id)]

            fighter_a_fight_dates_vals = pd.DatetimeIndex(fighter_a_fights.date)
            fighter_b_fight_dates_vals = pd.DatetimeIndex(fighter_b_fights.date)

            fighter_a_fights_last_year = fighter_a_fights[fighter_a_fight_dates_vals >= (fighter_a_fight_dates_vals.max() - pd.DateOffset(years=1))]
            fighter_b_fights_last_year = fighter_b_fights[fighter_b_fight_dates_vals >= (fighter_b_fight_dates_vals.max() - pd.DateOffset(years=1))]

            fighter_a_rounds_fought_alltime = fighter_a_fights['outcome_round'].sum()
            fighter_b_rounds_fought_alltime = fighter_b_fights['outcome_round'].sum()

            fighter_a_rounds_fought_last_year = fighter_a_fights_last_year['outcome_round'].sum()
            fighter_b_rounds_fought_last_year = fighter_b_fights_last_year['outcome_round'].sum()

            return pd.Series([fighter_a_rounds_fought_last_year, fighter_a_rounds_fought_alltime, fighter_b_rounds_fought_last_year, fighter_b_rounds_fought_alltime])

        return pd.Series([0, 0, 0, 0])

