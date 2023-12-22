import pandas as pd
import numpy as np
import swifter

class Knockdowns():
    def __init__(self):
        pass

    """
    Creates the knockdowns features for each fighter in the dataset

    Parameters:
        - df (DataFrame): DataFrame containing all the fights in the dataset

    Returns:
        - pd.DataFrame: DataFrame containing the knockdowns features for each fighter in the dataset
    """
    def create_knockdown_feats(self, df, include_progress=False):
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
    
    """
    Computes the knockdowns features for a single example in the dataset

    Parameters:
        - df (DataFrame): DataFrame containing all the fights in the dataset
        - fighter_a_id (str): ID of fighter A
        - fighter_b_id (str): ID of fighter B
        - index (int): Index of the current fight in the dataset
        - last_fights (int): Number of last fights to consider
        - differential (bool): Whether to compute the differential of the knockdowns features

    Returns:
        - pd.Series: Series containing the knockdowns features for both fighters
    """
    def compute_knockdowns(self, df, fighter_a_id, fighter_b_id, index, last_fights=0, differential=False):
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
    
    """
    Given a fighter's past fights, returns the number of knockdowns per significant strikes landed

    Parameters:
        - fighter_past_fights (DataFrame): DataFrame containing the fighter's past fights
        - fighter_id (str): ID of the fighter

    Returns:
        - float: Number of knockdowns per significant strikes landed
    """
    def get_fighter_kd_per_sigs(self, fighter_past_fights, fighter_id):
        if fighter_past_fights.empty:
            return 0
        
        
        fighter_a_id_vals = fighter_past_fights.fighter_a_id.values
        fighter_b_id_vals = fighter_past_fights.fighter_b_id.values
        
        fighter_knockdowns = fighter_past_fights[fighter_a_id_vals == fighter_id]['fighter_a_total_kd'].sum() + \
                             fighter_past_fights[fighter_b_id_vals == fighter_id]['fighter_b_total_kd'].sum()
        
        fighter_sig_strikes = fighter_past_fights[fighter_a_id_vals == fighter_id]['fighter_a_total_sig_str_landed'].sum() + \
                              fighter_past_fights[fighter_b_id_vals == fighter_id]['fighter_b_total_sig_str_landed'].sum()

        return fighter_knockdowns / fighter_sig_strikes if fighter_sig_strikes > 0 else 0
    
    """
    Tests the knockdowns feature

    Parameters:
        - df (DataFrame): DataFrame containing all the fights in the dataset

    Returns:
        - pd.DataFrame: DataFrame containing the knockdowns features for each fighter in the dataset
    """
    def test_knockdown_feature(self, df):
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

    """
    Swaps the fighter_a and fighter_b columns if the fighter_a_id is not the fighter we are interested in

    Parameters:
        - row (Series): Row of the DataFrame
        - fighter_a_cols (list): List of fighter_a columns
        - fighter_b_cols (list): List of fighter_b columns
    
    Returns:
        - Series: Row of the DataFrame with the fighter_a and fighter_b columns swapped if necessary
    """
    def swap_ids_and_columns(self, row, fighter_a_cols, fighter_b_cols):
        if row['fighter_b_id'] == 'f1fac969a1d70b08':
            for i in range(len(fighter_a_cols)):
                row[fighter_a_cols[i]], row[fighter_b_cols[i]] = row[fighter_b_cols[i]], row[fighter_a_cols[i]]
        
        return row

    def test_knockdown_feature_l3(self, df):
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

    # def test_knockdown_feature_l3_diff(self, df):
    #     test_df = df.copy().reset_index(drop=True)
    #     columns_to_select = ['fighter_a_total_kd', 'fighter_a_total_sig_str_landed', 'fighter_b_total_kd', 'fighter_b_total_sig_str_landed']
    #     res_df = df[columns_to_select].rolling(3, min_periods=1).sum().reset_index(drop=True)

    #     for index, row in enumerate(test_df.itertuples()):
    #         if index > 0:
    #             expected = (res_df.loc[index-1, 'fighter_a_total_kd'] / res_df.loc[index-1, 'fighter_a_total_sig_str_landed']) - (res_df.loc[index-1, 'fighter_b_total_kd'] / res_df.loc[index-1, 'fighter_b_total_sig_str_landed'])
    #             actual = row.fighter_a_kd_per_sigs_l3_diff
    #             assert expected == actual, f"Expected {expected}, but got {actual} on row {row.Index}"
                
    # def test_knockdown_feature_l5_diff(self, df):
    #     test_df = df.copy().reset_index(drop=True)
    #     columns_to_select = ['fighter_a_total_kd', 'fighter_a_total_sig_str_landed', 'fighter_b_total_kd', 'fighter_b_total_sig_str_landed']
    #     res_df = df[columns_to_select].rolling(5, min_periods=1).sum().reset_index(drop=True)

    #     for index, row in enumerate(test_df.itertuples()):
    #         if index > 0:
    #             expected = (res_df.loc[index-1, 'fighter_a_total_kd'] / res_df.loc[index-1, 'fighter_a_total_sig_str_landed']) - (res_df.loc[index-1, 'fighter_b_total_kd'] / res_df.loc[index-1, 'fighter_b_total_sig_str_landed'])
    #             actual = row.fighter_a_kd_per_sigs_l5_diff
    #             assert expected == actual, f"Expected {expected}, but got {actual} on row {row.Index}"
    #             
    # def test_knockdown_feature_alltime_diff(self, df):
    #     test_df = df.copy().reset_index(drop=True)
    #     columns_to_select = ['fighter_a_total_kd', 'fighter_a_total_sig_str_landed', 'fighter_b_total_kd', 'fighter_b_total_sig_str_landed']
    #     res_df = df[columns_to_select].expanding().sum().reset_index(drop=True)

    #     for index, row in enumerate(test_df.itertuples()):
    #         if index > 0:
    #             expected = (res_df.loc[index-1, 'fighter_a_total_kd'] / res_df.loc[index-1, 'fighter_a_total_sig_str_landed']) - (res_df.loc[index-1, 'fighter_b_total_kd'] / res_df.loc[index-1, 'fighter_b_total_sig_str_landed'])
    #             actual = row.fighter_a_kd_per_sigs_alltime_diff
    #             assert expected == actual, f"Expected {expected}, but got {actual} on row {row.Index}"