import pandas as pd
import swifter

class GroundStrikes():
    def __init__(self):
        pass

    def create_ground_strike_feats(self, df):
        """
        Creates the ground strikes features for each fighter in the dataset

        Parameters:
        - df (pd.Dataframe): The original dataframe containing all the fights

        Returns:
        - pd.Dataframe: The dataframe containing the ground strikes features for each fighter
        """
        
        col_names = self.create_col_names_significant_ground_strikes()
        input_df = df.copy()
        result_features = pd.DataFrame(columns=col_names)
        result_features[col_names] = input_df.swifter.progress_bar(True).apply(lambda row: self.calculate_ground_strikes(input_df, row['fighter_a_id'], row['fighter_b_id'], row.name, col_names), axis=1)

        target_df = pd.concat([input_df, result_features], axis=1)

        return target_df

    def calculate_ground_strikes(self, df, fighter_a_id, fighter_b_id, index, col_names):
        """
        Calculates all the ground strikes features for each fighter in the dataset

        Parameters:
        - df (pd.Dataframe): The original dataframe containing all the fights
        - fighter_a_id (int): The id of the first fighter
        - fighter_b_id (int): The id of the second fighter
        - index (int): The index of the current fight
        - col_names (list): The list of column names for the ground strikes features

        Returns:
        - pd.Series: The series containing the ground strikes features for each fighter
        """

        res = []
        for i in range(0, len(col_names), 2):
            split_a = col_names[i].split('_')
            stat = split_a[1]
            round = split_a[2]
            time_period = split_a[3]

            if time_period == 'l3':
                last_fights = 3
            elif time_period == 'l5':
                last_fights = 5
            else:
                last_fights = 0
            
            if round == 'overall':
                round_number = 0
            else:
                round_number = int(round[1])
            
            has_diff = 'diff' in stat
            if stat in 'ground-strikes-attempted-per-minute-diff':
                fighter_a_ground_strikes_attempted, fighter_b_ground_strikes_attempted = self.compute_ground_strikes_attempted_per_minute(df, fighter_a_id, fighter_b_id, index, round_number, differential=has_diff, last_fights=last_fights)
                res.append(fighter_a_ground_strikes_attempted)
                res.append(fighter_b_ground_strikes_attempted)
            elif stat == 'ground-strikes-landed-per-minute-diff':
                fighter_a_ground_strikes_landed, fighter_b_ground_strikes_landed = self.compute_ground_strikes_landed_per_minute(df, fighter_a_id, fighter_b_id, index, round_number, differential=has_diff, last_fights=last_fights)
                res.append(fighter_a_ground_strikes_landed)
                res.append(fighter_b_ground_strikes_landed)
            elif stat == 'ground-strikes-accuracy-percentage-diff':
                fighter_a_ground_strikes_acurracy_percentage, fighter_b_ground_strikes_acurracy_percentage = self.compute_ground_strikes_acurracy_percentage(df, fighter_a_id, fighter_b_id, index, round_number, differential=has_diff, last_fights=last_fights)
                res.append(fighter_a_ground_strikes_acurracy_percentage)
                res.append(fighter_b_ground_strikes_acurracy_percentage)
            elif stat == 'ground-strikes-absorbed-per-minute-diff':
                fighter_a_ground_strikes_absorbed_per_minute, fighter_b_ground_strikes_absorbed_per_minute = self.compute_ground_strikes_absorbed_per_minute(df, fighter_a_id, fighter_b_id, index, round_number, differential=has_diff, last_fights=last_fights)
                res.append(fighter_a_ground_strikes_absorbed_per_minute)
                res.append(fighter_b_ground_strikes_absorbed_per_minute)
            elif stat == 'ground-strikes-recieved-per-minute-diff':
                fighter_a_ground_strikes_recieved_per_minute, fighter_b_ground_strikes_recieved_per_minute = self.compute_ground_strikes_recieved_per_minute(df, fighter_a_id, fighter_b_id, index, round_number, differential=has_diff, last_fights=last_fights)
                res.append(fighter_a_ground_strikes_recieved_per_minute)
                res.append(fighter_b_ground_strikes_recieved_per_minute)
            elif stat == 'ground-strikes-defended-percentage-diff':
                fighter_a_ground_strikes_defended_percentage, fighter_b_ground_strikes_defended_percentage = self.compute_ground_strikes_defended_percentage(df, fighter_a_id, fighter_b_id, index, round_number, differential=has_diff, last_fights=last_fights)
                res.append(fighter_a_ground_strikes_defended_percentage)
                res.append(fighter_b_ground_strikes_defended_percentage)
                
        return pd.Series(res)

    def compute_ground_strikes_attempted_per_minute(self, df, fighter_a_id, fighter_b_id, index, round_number=0, differential=False, last_fights=0):
        """
        Computes the ground strikes attempted per minute for each fighter in the dataset 

        Parameters:
        - df (pd.Dataframe): The original dataframe containing all the fights
        - fighter_a_id (int): The id of the first fighter
        - fighter_b_id (int): The id of the second fighter
        - index (int): The index of the current fight
        - round_number (int): The round number of the current fight
        - differential (bool): Whether to compute the differential or not
        - last_fights (int): The number of last fights to consider

        Returns:
        - (float, float): The ground strikes attempted per minute for each fighter as a tuple
        """
        return self.compute_ground_strikes(df, fighter_a_id, fighter_b_id, index, round_number, last_fights, column_name="ground_attempted", differential=differential)
   

    def compute_ground_strikes_landed_per_minute(self, df, fighter_a_id, fighter_b_id, index, round_number, differential=False, last_fights=0):
        """
        Computes the ground strikes landed per minute for each fighter in the dataset

        Parameters:
        - df (pd.Dataframe): The original dataframe containing all the fights
        - fighter_a_id (int): The id of the first fighter
        - fighter_b_id (int): The id of the second fighter
        - index (int): The index of the current fight
        - round_number (int): The round number of the current fight
        - differential (bool): Whether to compute the differential or not
        - last_fights (int): The number of last fights to consider

        Returns:
        - (float, float): The ground strikes landed per minute for each fighter as a tuple
        """
        return self.compute_ground_strikes(df, fighter_a_id, fighter_b_id, index, round_number, last_fights, column_name="ground_landed", differential=differential)

    def compute_ground_strikes_acurracy_percentage(self, df, fighter_a_id, fighter_b_id, index, round_number, differential=False, last_fights=0):
        """
        Computes the ground strikes accuracy percentage for each fighter in the dataset

        Parameters:
        - df (pd.Dataframe): The original dataframe containing all the fights
        - fighter_a_id (int): The id of the first fighter
        - fighter_b_id (int): The id of the second fighter
        - index (int): The index of the current fight
        - round_number (int): The round number of the current fight
        - differential (bool): Whether to compute the differential or not
        - last_fights (int): The number of last fights to consider

        Returns:
        - (float, float): The ground strikes accuracy percentage for each fighter as a tuple
        """
        fighter_a_ground_strikes_landed, fighter_b_ground_strikes_landed = self.compute_ground_strikes(df, fighter_a_id, fighter_b_id, index, round_number, last_fights, column_name="ground_landed", differential=differential, is_percentage=True)
        fighter_a_ground_strikes_attempted, fighter_b_ground_strikes_attempted = self.compute_ground_strikes(df, fighter_a_id, fighter_b_id, index, round_number, last_fights, column_name="ground_attempted", differential=differential, is_percentage=True)
        return self.compute_ground_strikes_percentages(fighter_a_ground_strikes_landed, fighter_a_ground_strikes_attempted, fighter_b_ground_strikes_landed, fighter_b_ground_strikes_attempted, differential=differential)

    '''
    Ground Strikes Absorbed Per Minute
    '''
    def compute_ground_strikes_absorbed_per_minute(self, df, fighter_a_id, fighter_b_id, index, round_number, differential=False, last_fights=0):
        """
        Computes the ground strikes absorbed per minute for each fighter in the dataset

        Parameters:
        - df (pd.Dataframe): The original dataframe containing all the fights
        - fighter_a_id (int): The id of the first fighter
        - fighter_b_id (int): The id of the second fighter
        - index (int): The index of the current fight
        - round_number (int): The round number of the current fight
        - differential (bool): Whether to compute the differential or not
        - last_fights (int): The number of last fights to consider

        Returns:
        - (float, float): The ground strikes absorbed per minute for each fighter as a tuple
        """
        return self.compute_ground_strikes(df, fighter_a_id, fighter_b_id, index, round_number, last_fights, column_name="ground_landed", differential=differential, is_defense=True)

    def compute_ground_strikes_recieved_per_minute(self, df, fighter_a_id, fighter_b_id, index, round_number, differential=False, last_fights=0):
        """
        Computes the ground strikes recieved per minute for each fighter in the dataset

        Parameters:
        - df (pd.Dataframe): The original dataframe containing all the fights
        - fighter_a_id (int): The id of the first fighter
        - fighter_b_id (int): The id of the second fighter
        - index (int): The index of the current fight
        - round_number (int): The round number of the current fight
        - differential (bool): Whether to compute the differential or not
        - last_fights (int): The number of last fights to consider

        Returns:
        - (float, float): The ground strikes recieved per minute for each fighter as a tuple
        """
        return self.compute_ground_strikes(df, fighter_a_id, fighter_b_id, index, round_number, last_fights, column_name="ground_attempted", differential=differential, is_defense=True)
        

    def compute_ground_strikes_defended_percentage(self, df, fighter_a_id, fighter_b_id, index, round_number, differential=False, last_fights=0):
        """
        Computes the ground strikes defended percentage for each fighter in the dataset

        Parameters:
        - df (pd.Dataframe): The original dataframe containing all the fights
        - fighter_a_id (int): The id of the first fighter
        - fighter_b_id (int): The id of the second fighter
        - index (int): The index of the current fight
        - round_number (int): The round number of the current fight
        - differential (bool): Whether to compute the differential or not
        - last_fights (int): The number of last fights to consider

        Returns:
        - (float, float): The ground strikes defended percentage for each fighter as a tuple
        """
        fighter_a_ground_strikes_absorbed, fighter_b_ground_strikes_absorbed = self.compute_ground_strikes(df, fighter_a_id, fighter_b_id, index, round_number, last_fights, column_name="ground_landed", differential=differential, is_defense=True, is_percentage=True)
        fighter_a_ground_strikes_recieved, fighter_b_ground_strikes_recieved = self.compute_ground_strikes(df, fighter_a_id, fighter_b_id, index, round_number, last_fights, column_name="ground_attempted", differential=differential, is_defense=True, is_percentage=True)
        return self.compute_ground_strikes_percentages(fighter_a_ground_strikes_absorbed, fighter_a_ground_strikes_recieved, fighter_b_ground_strikes_absorbed, fighter_b_ground_strikes_recieved, differential=differential)

    def compute_ground_strikes_percentages(self, fighter_a_ground_strikes_hit, fighter_a_ground_strikes_taken, fighter_b_ground_strikes_hit, fighter_b_ground_strikes_taken, differential=False):
        """
        Computes the ground strikes percentages for each fighter in the dataset

        Parameters:
        - fighter_a_ground_strikes_hit (float): The number of ground strikes hit by fighter a
        - fighter_a_ground_strikes_taken (float): The number of ground strikes taken by fighter a
        - fighter_b_ground_strikes_hit (float): The number of ground strikes hit by fighter b
        - fighter_b_ground_strikes_taken (float): The number of ground strikes taken by fighter b
        - differential (bool): Whether to compute the differential or not

        Returns:
        - (float, float): The ground strikes percentages for each fighter as a tuple
        """
        fighter_a_ground_strikes = fighter_a_ground_strikes_hit / fighter_a_ground_strikes_taken if fighter_a_ground_strikes_taken != 0 else 0
        fighter_b_ground_strikes = fighter_b_ground_strikes_hit / fighter_b_ground_strikes_taken if fighter_b_ground_strikes_taken != 0 else 0

        if differential:
            return fighter_a_ground_strikes - fighter_b_ground_strikes, fighter_b_ground_strikes - fighter_a_ground_strikes
        else:
            return fighter_a_ground_strikes, fighter_b_ground_strikes
    
    def compute_ground_strikes(self, df, fighter_a_id, fighter_b_id, index, round_number, last_fights, column_name, differential=False, is_defense=False, is_percentage=False):
        """
        Computes the ground strikes for each fighter in the dataset based on column_name

        Parameters:
        - df (pd.Dataframe): The original dataframe containing all the fights
        - fighter_a_id (int): The id of the first fighter
        - fighter_b_id (int): The id of the second fighter
        - index (int): The index of the current fight
        - round_number (int): The round number of the current fight
        - last_fights (int): The number of last fights to consider
        - column_name (string): The name of the column to compute
        - differential (bool): Whether to compute the differential or not
        - is_defense (bool): Whether to compute the defense or not
        - is_percentage (bool): Whether to compute the percentage or not

        Returns:
        - (float, float): The ground strikes for each fighter as a tuple
        """
        all_prev_fights = df.loc[:index-1]
        
        if not all_prev_fights.empty:
            fighter_a_id_vals = all_prev_fights.fighter_a_id.values
            fighter_b_id_vals = all_prev_fights.fighter_b_id.values

            fighter_a_fights = all_prev_fights[(fighter_a_id_vals == fighter_a_id) | (fighter_b_id_vals == fighter_a_id)][-last_fights:]
            fighter_b_fights = all_prev_fights[(fighter_b_id_vals == fighter_b_id) | (fighter_a_id_vals == fighter_b_id)][-last_fights:]

            sum_a, time_a = self.get_fighter_ground_details(fighter_a_fights, fighter_a_id, round_number, f'total_{column_name}' if round_number == 0 else f'round_{round_number}_{column_name}', is_defense)
            sum_b, time_b = self.get_fighter_ground_details(fighter_b_fights, fighter_b_id, round_number, f'total_{column_name}' if round_number == 0 else f'round_{round_number}_{column_name}', is_defense)

            return self.get_ground_strike_return_values(sum_a, time_a, sum_b, time_b, differential, is_percentage)

        return 0, 0
    
    def get_ground_strike_return_values(self, sum_a, time_a, sum_b, time_b, differential, is_percentage):
        """
        Computes the ground strikes averages

        Parameters:
        - sum_a (float): The sum of ground strikes for fighter a
        - sum_b (float): The sum of ground strikes for fighter b
        - count_a (int): The number of fights for fighter a
        - count_b (int): The number of fights for fighter b
        - differential (bool): Whether to compute the differential or not

        Returns:
        - (float, float): The ground strikes for each fighter as a tuple
        """
        fighter_a_ground_strikes = (sum_a / time_a if time_a > 0 else 1) if not is_percentage else sum_a
        fighter_b_ground_strikes = (sum_b / time_b if time_b > 0 else 1) if not is_percentage else sum_b
        
        if differential:
            return fighter_a_ground_strikes - fighter_b_ground_strikes, fighter_b_ground_strikes - fighter_a_ground_strikes
        else:
            return fighter_a_ground_strikes, fighter_b_ground_strikes

    def get_fighter_ground_details(self, fighter_past_fights, fighter_id, round_number, column_name, is_defense=False):
        """
        Computes the ground strikes for each fighter in the dataset based on column_name

        Parameters:
        - fighter_past_fights (pd.Dataframe): The dataframe containing all the past fights for the fighter
        - fighter_id (int): The id of the fighter
        - round_number (int): The round number of the current fight
        - column_name (string): The name of the column to compute
        - is_defense (bool): Whether to compute the defense or not

        Returns:
        - (float, float) : The ground strike sum and time sum for each fighter as a tuple
        """
        if fighter_past_fights.empty:
            return 0, 1

        fights_as_a = fighter_past_fights[fighter_past_fights['fighter_a_id'] == fighter_id]
        fights_as_b = fighter_past_fights[fighter_past_fights['fighter_b_id'] == fighter_id]

        strike_sum_a, time_sum_a = self.get_ground_detail_sums(round_number, f'fighter_a_{column_name}' if not is_defense else f'fighter_b_{column_name}', fights_as_a)
        strike_sum_b, time_sum_b = self.get_ground_detail_sums(round_number, f'fighter_b_{column_name}' if not is_defense else f'fighter_a_{column_name}', fights_as_b)

        return strike_sum_a + strike_sum_b, time_sum_a + time_sum_b
    
    def get_ground_detail_sums(self, round_number, column_name, fights):
        """
        Computes the sum from each of the fights for the ground strikes stats

        Parameters:
        - round_number (int): The round number of the current fight
        - column_name (string): The name of the column to compute
        - fights (pd.Dataframe): The dataframe containing all the past fights for the fighter

        Returns:
        - (float, float): The sum of the ground strikes stats and the total time
        """
        strike_sum = 0
        time_sum = 0

        for _, row in fights.iterrows():
            if row[column_name] == "":
                continue

            strike_sum += float(row[column_name])
            if round_number == 0:
                time_sum += self.convert_time_to_minutes(row["outcome_time"]) + (int(row["outcome_round"])-1)*5
            elif row["outcome_round"] is round_number:
                time_sum += self.convert_time_to_minutes(row["outcome_time"])
            else:
                time_sum += 5
        
        return strike_sum, time_sum
    
    def convert_time_to_minutes(self, time):
        """
        Converts the time from the fights to minutes

        Parameters:
        - time (string): The time from the fights

        Returns:
        - (float): The time in minutes
        """
        minutes, seconds = map(int, time.split(':'))
        total_minutes = minutes + seconds / 60
        return total_minutes
    
    def create_col_names_significant_ground_strikes(self):
        """
        Generates column names for significant strike statistics.

        Returns:
            list: A list of strings, each representing a column name for a specific significant strike statistic.
        """
        col_names = []
        fighters = ['fighter-a', 'fighter-b']
        ground_strike_stats = [
            'ground-strikes-attempted-per-minute', 
            'ground-strikes-landed-per-minute', 
            'ground-strikes-accuracy-percentage', 
            'ground-strikes-absorbed-per-minute', 
            'ground-strikes-recieved-per-minute', 
            'ground-strikes-defended-percentage', 
            'ground-strikes-attempted-per-minute-diff', 
            'ground-strikes-landed-per-minute-diff', 
            'ground-strikes-accuracy-percentage-diff', 
            'ground-strikes-absorbed-per-minute-diff', 
            'ground-strikes-recieved-per-minute-diff', 
            'ground-strikes-defended-percentage-diff'
        ]
        rounds = ['R1', 'R2', 'R3', 'R4', 'R5', 'overall']
        time_periods = ['l3', 'l5', 'alltime']

        # Iterate through all combinations to create column names
        for ground_strike_stat in ground_strike_stats:
            for round in rounds:
                for time_period in time_periods:
                    for fighter in fighters:
                        col_name = f"{fighter.replace(' ', '_')}_{ground_strike_stat.replace(' ', '_')}_{round}_{time_period.replace(' ', '_')}"
                        col_names.append(col_name)
        return col_names
