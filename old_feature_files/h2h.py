import pandas as pd
import swifter

class HeadToHead():
    def __init__(self):
        pass

    """
    Creates the head to head features for each fighter in the dataset

    Usage:
        df = HeadToHead().create_h2h_feats(df)
    """
    def create_h2h_feats(self, df):
        target_df = df.copy()
        col_names = ['fighter_a_h2h_wins', 'fighter_b_h2h_wins']
        result_features = pd.DataFrame(columns=col_names)

        result_features[col_names] = target_df.swifter.progress_bar(True).apply(lambda row: self.compute_h2h(target_df, row['fighter_a_id'], row['fighter_b_id'], row.name), axis=1)

        result_df = pd.concat([target_df, result_features], axis=1)
        return result_df

    """
    Computes the head to head features for a single example in the dataset
    """
    def compute_h2h(self, df, fighter_a_id, fighter_b_id, index):
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