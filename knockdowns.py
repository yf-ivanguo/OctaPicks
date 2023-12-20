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

        target_df[['fighter_a_knockdowns_per_sigs_l3', 'fighter_b_knockdowns_per_sigs_l3']] = target_df.swifter.progress_bar(True).apply(lambda row: self.compute_knockdowns(df, row['fighter_a_id'], row['fighter_b_id'], row.name, last_fights=3), axis=1)
        target_df[['fighter_a_knockdowns_per_sigs_l5', 'fighter_b_knockdowns_per_sigs_l5']] = target_df.swifter.progress_bar(True).apply(lambda row: self.compute_knockdowns(df, row['fighter_a_id'], row['fighter_b_id'], row.name, last_fights=5), axis=1)
        target_df[['fighter_a_knockdowns_per_sigs_alltime', 'fighter_b_knockdowns_per_sigs_alltime']] = target_df.swifter.progress_bar(True).apply(lambda row: self.compute_knockdowns(df, row['fighter_a_id'], row['fighter_b_id'], row.name), axis=1)
        target_df[['fighter_a_knockdowns_per_sigs_l3_diff', 'fighter_b_knockdowns_per_sigs_l3_diff']] = target_df.swifter.progress_bar(True).apply(lambda row: self.compute_knockdowns(df, row['fighter_a_id'], row['fighter_b_id'], row.name, last_fights=3, differential=True), axis=1)
        target_df[['fighter_a_knockdowns_per_sigs_l5_diff', 'fighter_b_knockdowns_per_sigs_l5_diff']] = target_df.swifter.progress_bar(True).apply(lambda row: self.compute_knockdowns(df, row['fighter_a_id'], row['fighter_b_id'], row.name, last_fights=5, differential=True), axis=1)
        target_df[['fighter_a_knockdowns_per_sigs_alltime_diff', 'fighter_b_knockdowns_per_sigs_alltime_diff']] = target_df.swifter.progress_bar(True).apply(lambda row: self.compute_knockdowns(df, row['fighter_a_id'], row['fighter_b_id'], row.name, differential=True), axis=1)

        return target_df
    
    """
    Computes the knockdowns features for a single example in the dataset
    """
    def compute_knockdowns(self, df, fighter_a_id, fighter_b_id, index, last_fights=0, differential=False):
        all_prev_fights = df.loc[:index-1]
        if not all_prev_fights.empty:
            fighter_a_id_vals = all_prev_fights.fighter_a_id.values
            fighter_b_id_vals = all_prev_fights.fighter_b_id.values

            fighter_a_fights = all_prev_fights[(fighter_a_id_vals == fighter_a_id)][-last_fights:]
            fighter_b_fights = all_prev_fights[(fighter_b_id_vals == fighter_b_id)][-last_fights:]

            fighter_a_knockdowns_per_sigs = self.get_fighter_knockdowns_per_sigs(fighter_a_fights, fighter_a_id)
            fighter_b_knockdowns_per_sigs = self.get_fighter_knockdowns_per_sigs(fighter_b_fights, fighter_b_id)

            if differential:
                return pd.Series([fighter_a_knockdowns_per_sigs - fighter_b_knockdowns_per_sigs, fighter_b_knockdowns_per_sigs - fighter_a_knockdowns_per_sigs])
            else:
                return pd.Series([fighter_a_knockdowns_per_sigs, fighter_b_knockdowns_per_sigs])
            
        return pd.Series([0, 0])
    
    """
    Given a fighter's past fights, returns the number of knockdowns per significant strikes landed
    """
    def get_fighter_knockdowns_per_sigs(self, fighter_past_fights, fighter_id):
        if fighter_past_fights.empty:
            return 0
        
        # Necessary as the fighter's past fights may be in either the fighter_a or fighter_b columns
        fighter_knockdowns = fighter_past_fights[fighter_past_fights['fighter_a_id'] == fighter_id]['fighter_a_total_kd'].sum() + \
                                fighter_past_fights[fighter_past_fights['fighter_b_id'] == fighter_id]['fighter_b_total_kd'].sum()
        
        fighter_sig_strikes = fighter_past_fights[fighter_past_fights['fighter_a_id'] == fighter_id]['fighter_a_total_sig_str_landed'].sum() + \
                                fighter_past_fights[fighter_past_fights['fighter_b_id'] == fighter_id]['fighter_b_total_sig_str_landed'].sum()

        return fighter_knockdowns / fighter_sig_strikes if fighter_sig_strikes > 0 else 0