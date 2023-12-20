import pandas as pd
import swifter

class Knockdowns():
    def __init__(self):
        pass

    """
    Creates the knockdowns features for each fighter in the dataset
    """
    def create_knockdown_feats(self, df):
        target_df = df

        target_df[['fighter_a_knockdowns_per_sigs_l3', 'fighter_b_knockdowns_per_sigs_l3']] = target_df.swifter.progress_bar(True).apply(lambda row: self.compute_knockdowns_l3(df, row['fighter_a_id'], row['fighter_b_id'], row.name), axis=1)
        target_df[['fighter_a_knockdowns_per_sigs_l5', 'fighter_b_knockdowns_per_sigs_l5']] = target_df.swifter.progress_bar(True).apply(lambda row: self.compute_knockdowns_l5(df, row['fighter_a_id'], row['fighter_b_id'], row.name), axis=1)
        target_df[['fighter_a_knockdowns_per_sigs_alltime', 'fighter_b_knockdowns_per_sigs_alltime']] = target_df.swifter.progress_bar(True).apply(lambda row: self.compute_knockdowns(df, row['fighter_a_id'], row['fighter_b_id'], row.name, False), axis=1)
        target_df[['fighter_a_knockdowns_per_sigs_diff', 'fighter_b_knockdowns_per_sigs_diff']] = target_df.swifter.progress_bar(True).apply(lambda row: self.compute_knockdowns(df, row['fighter_a_id'], row['fighter_b_id'], row.name, True), axis=1)

        return target_df
    
    """
    Computes the knockdowns features for a single example in the dataset
    """
    def compute_knockdowns_l3(self, df, fighter_a_id, fighter_b_id, index):
        all_prev_fights = df.loc[:index-1]
        if not all_prev_fights.empty:
            fighter_a_id_vals = all_prev_fights.fighter_a_id.values
            fighter_b_id_vals = all_prev_fights.fighter_b_id.values

            fighter_a_l3_fights = all_prev_fights[(fighter_a_id_vals == fighter_a_id)][-3:]
            fighter_b_l3_fights = all_prev_fights[(fighter_b_id_vals == fighter_b_id)][-3:]

            fighter_a_knockdowns_per_sigs = 0
            fighter_b_knockdowns_per_sigs = 0

            if not fighter_a_l3_fights.empty:
                fighter_a_knockdowns = fighter_a_l3_fights[fighter_a_l3_fights['fighter_a_id'] == fighter_a_id]['fighter_a_total_kd'].sum() + \
                                        fighter_a_l3_fights[fighter_a_l3_fights['fighter_b_id'] == fighter_a_id]['fighter_b_total_kd'].sum()
                
                fighter_a_sig_strikes = fighter_a_l3_fights[fighter_a_l3_fights['fighter_a_id'] == fighter_a_id]['fighter_a_total_sig_str_landed'].sum() + \
                                        fighter_a_l3_fights[fighter_a_l3_fights['fighter_b_id'] == fighter_a_id]['fighter_b_total_sig_str_landed'].sum()

                fighter_a_knockdowns_per_sigs = fighter_a_knockdowns / fighter_a_sig_strikes if fighter_a_sig_strikes > 0 else 0

            if not fighter_b_l3_fights.empty:
                fighter_b_knockdowns = fighter_b_l3_fights[fighter_b_l3_fights['fighter_a_id'] == fighter_b_id]['fighter_a_total_kd'].sum() + \
                                        fighter_b_l3_fights[fighter_b_l3_fights['fighter_b_id'] == fighter_b_id]['fighter_b_total_kd'].sum()
                
                fighter_b_sig_strikes = fighter_b_l3_fights[fighter_b_l3_fights['fighter_a_id'] == fighter_b_id]['fighter_a_total_sig_str_landed'].sum() + \
                                        fighter_b_l3_fights[fighter_b_l3_fights['fighter_b_id'] == fighter_b_id]['fighter_b_total_sig_str_landed'].sum()

                fighter_b_knockdowns_per_sigs = fighter_b_knockdowns / fighter_b_sig_strikes if fighter_b_sig_strikes > 0 else 0

            return pd.Series([fighter_a_knockdowns_per_sigs, fighter_b_knockdowns_per_sigs])
        return pd.Series([0, 0])
    
    def compute_knockdowns_l5(self, df, fighter_a_id, fighter_b_id, index):
        all_prev_fights = df.loc[:index-1]
        if not all_prev_fights.empty:
            fighter_a_id_vals = all_prev_fights.fighter_a_id.values
            fighter_b_id_vals = all_prev_fights.fighter_b_id.values

            fighter_a_l5_fights = all_prev_fights[(fighter_a_id_vals == fighter_a_id)][-5:]
            fighter_b_l5_fights = all_prev_fights[(fighter_b_id_vals == fighter_b_id)][-5:]

            fighter_a_knockdowns_per_sigs = 0
            fighter_b_knockdowns_per_sigs = 0

            if not fighter_a_l5_fights.empty:
                fighter_a_knockdowns = fighter_a_l5_fights[fighter_a_l5_fights['fighter_a_id'] == fighter_a_id]['fighter_a_total_kd'].sum() + \
                                        fighter_a_l5_fights[fighter_a_l5_fights['fighter_b_id'] == fighter_a_id]['fighter_b_total_kd'].sum()
                
                fighter_a_sig_strikes = fighter_a_l5_fights[fighter_a_l5_fights['fighter_a_id'] == fighter_a_id]['fighter_a_total_sig_str_landed'].sum() + \
                                        fighter_a_l5_fights[fighter_a_l5_fights['fighter_b_id'] == fighter_a_id]['fighter_b_total_sig_str_landed'].sum()

                fighter_a_knockdowns_per_sigs = fighter_a_knockdowns / fighter_a_sig_strikes if fighter_a_sig_strikes > 0 else 0

            if not fighter_b_l5_fights.empty:
                fighter_b_knockdowns = fighter_b_l5_fights[fighter_b_l5_fights['fighter_a_id'] == fighter_b_id]['fighter_a_total_kd'].sum() + \
                                        fighter_b_l5_fights[fighter_b_l5_fights['fighter_b_id'] == fighter_b_id]['fighter_b_total_kd'].sum()
                
                fighter_b_sig_strikes = fighter_b_l5_fights[fighter_b_l5_fights['fighter_a_id'] == fighter_b_id]['fighter_a_total_sig_str_landed'].sum() + \
                                        fighter_b_l5_fights[fighter_b_l5_fights['fighter_b_id'] == fighter_b_id]['fighter_b_total_sig_str_landed'].sum()

                fighter_b_knockdowns_per_sigs = fighter_b_knockdowns / fighter_b_sig_strikes if fighter_b_sig_strikes > 0 else 0

            return pd.Series([fighter_a_knockdowns_per_sigs, fighter_b_knockdowns_per_sigs])
        return pd.Series([0, 0])
    
    def compute_knockdowns(self, df, fighter_a_id, fighter_b_id, index, differential):
        all_prev_fights = df.loc[:index-1]
        if not all_prev_fights.empty:
            fighter_a_id_vals = all_prev_fights.fighter_a_id.values
            fighter_b_id_vals = all_prev_fights.fighter_b_id.values

            fighter_a_fights = all_prev_fights[(fighter_a_id_vals == fighter_a_id)][-5:]
            fighter_b_fights = all_prev_fights[(fighter_b_id_vals == fighter_b_id)][-5:]

            fighter_a_knockdowns_per_sigs = 0
            fighter_b_knockdowns_per_sigs = 0

            if not fighter_a_fights.empty:
                fighter_a_knockdowns = fighter_a_fights[fighter_a_fights['fighter_a_id'] == fighter_a_id]['fighter_a_total_kd'].sum() + \
                                        fighter_a_fights[fighter_a_fights['fighter_b_id'] == fighter_a_id]['fighter_b_total_kd'].sum()
                
                fighter_a_sig_strikes = fighter_a_fights[fighter_a_fights['fighter_a_id'] == fighter_a_id]['fighter_a_total_sig_str_landed'].sum() + \
                                        fighter_a_fights[fighter_a_fights['fighter_b_id'] == fighter_a_id]['fighter_b_total_sig_str_landed'].sum()

                fighter_a_knockdowns_per_sigs = fighter_a_knockdowns / fighter_a_sig_strikes if fighter_a_sig_strikes > 0 else 0

            if not fighter_b_fights.empty:
                fighter_b_knockdowns = fighter_b_fights[fighter_b_fights['fighter_a_id'] == fighter_b_id]['fighter_a_total_kd'].sum() + \
                                        fighter_b_fights[fighter_b_fights['fighter_b_id'] == fighter_b_id]['fighter_b_total_kd'].sum()
                
                fighter_b_sig_strikes = fighter_b_fights[fighter_b_fights['fighter_a_id'] == fighter_b_id]['fighter_a_total_sig_str_landed'].sum() + \
                                        fighter_b_fights[fighter_b_fights['fighter_b_id'] == fighter_b_id]['fighter_b_total_sig_str_landed'].sum()
                
                fighter_b_knockdowns_per_sigs = fighter_b_knockdowns / fighter_b_sig_strikes if fighter_b_sig_strikes > 0 else 0

            if differential:
                return pd.Series([fighter_a_knockdowns_per_sigs - fighter_b_knockdowns_per_sigs, fighter_b_knockdowns_per_sigs - fighter_a_knockdowns_per_sigs])
            else:
                return pd.Series([fighter_a_knockdowns_per_sigs, fighter_b_knockdowns_per_sigs])
        return pd.Series([0, 0])