from dateutil.relativedelta import relativedelta
import swifter
import pandas as pd

class WinLoss():
    def __init__(self):
        pass

    """
    Creates the win/loss features for each fighter in the dataset

    Usage:
        win_loss = WinLoss()
        win_loss_feats = win_loss.create_win_loss_feats(df)
    """
    def create_win_loss_feats(self, df):
        col_names = self.create_col_names()
        target_df = df

        target_df[col_names] = target_df.swifter.progress_bar(True).apply(lambda row: self.compute_win_loss(target_df, row['fighter_a_id'], row['fighter_b_id'], row.name, col_names), axis=1)
        return target_df

    """
    Computes the win/loss features for a single example in the dataset
    """
    def compute_win_loss(self, df, fighter_a_id, fighter_b_id, index, col_names):
        res = []
        fighter_a_prev_fights, fighter_a_prev_fights_last_year = self.get_fighter_fights(df, fighter_a_id, index)
        fighter_b_prev_fights, fighter_b_prev_fights_last_year = self.get_fighter_fights(df, fighter_b_id, index)

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

            fight_outcomes = self.get_fighter_outcomes(prev_fights, fighter_a_id if fighter == 'fighter-a' else fighter_b_id)
            prev_fights = fight_outcomes[0] if outcome == 'wins' else fight_outcomes[1]

            if prev_fights.empty:
                res.append(0)
                continue

            fight_outcome_methods = self.get_fighter_outcome_methods(prev_fights)
            prev_fights = fight_outcome_methods[0] if method == 'KO/TKO' \
                else fight_outcome_methods[1] if method == 'submission' \
                else fight_outcome_methods[2] if method == 'decision' \
                else fight_outcome_methods[3]
            
            if prev_fights.empty:
                res.append(0)
                continue

            fight_division = self.get_fighter_division(prev_fights)
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
    
    """
    Filters the data by division
    """
    def get_fighter_division(self, df):
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

    """
    Filters the data by outcome method
    """
    def get_fighter_outcome_methods(self, df):
        fighter_ko = df[(df['outcome_method'] == 'KO/TKO') | (df['outcome_method'] == 'TKO - Doctor\'s Stoppage')]
        fighter_sub = df[df['outcome_method'] == 'Submission']
        fighter_decision = df[(df['outcome_method'] == 'Decision - Unanimous') | (df['outcome_method'] == 'Decision - Split') | (df['outcome_method'] == 'Decision - Majority')]
        fighter_total = df
        return fighter_ko, fighter_sub, fighter_decision, fighter_total

    """
    Filters the data by outcome
    """
    def get_fighter_outcomes(self, df, fighter_id):
        fighter_wins = df[df['winner_id'] == fighter_id]
        fighter_losses = df[df['winner_id'] != fighter_id]
        return fighter_wins, fighter_losses

    """
    Filters the data by a specific fighter
    """
    def get_fighter_fights(self, df, fighter_id, index):
        year_ago = self.compute_year_ago(df)
        all_prev_fights = df.loc[:index-1]
        if not all_prev_fights.empty:
            fighter_a_id_vals = all_prev_fights.fighter_a_id.values
            fighter_b_id_vals = all_prev_fights.fighter_b_id.values

            prev_fights = all_prev_fights[((fighter_a_id_vals == fighter_id) | (fighter_b_id_vals == fighter_id))]
            prev_fights_last_year = all_prev_fights[((fighter_a_id_vals == fighter_id) | (fighter_b_id_vals == fighter_id)) & (pd.to_datetime(all_prev_fights['date']) > year_ago[index])]

            return prev_fights, prev_fights_last_year
        return pd.DataFrame(), pd.DataFrame()
    
    """
    Creates the column names for the win/loss features
    """
    def create_col_names(self):
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
    
    """
    Gets the date a year ago from the current date
    """
    def compute_year_ago(self, df):
        temp_year_ago_df = pd.to_datetime(df['date'])
        temp_year_ago_df = temp_year_ago_df - pd.DateOffset(years=1)
        return temp_year_ago_df