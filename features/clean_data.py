import pandas as pd

"""
Usage:
    from clean_data import CleanData

    df = pd.read_csv('data.csv')
    df = CleanData(df).df

    Renames all the columns to work with easier, drops useless columns, and imputes missing data with 0
"""
class CleanData():
    def __init__(self):
        self.fighter_cols = ['a', 'b']
        self.stat_cols = ['kd', 'sig_str_landed', 'sig_str_attempted', 'sig_str_pct', 'total_str_landed', 'total_str_attempted', 'td_landed', 'td_attempted', 'td_pct', 'sub_att', 'rev', 'ctrl']
        self.round_cols = ['1', '2', '3', '4', '5']
        self.target_cols = ['head', 'body', 'leg', 'distance', 'clinch', 'ground']
        self.target_accuracy_cols = ['shots_landed', 'shots_attempted']
        self.cols = [f'fighter_{f}_round_{r}_{stat}' for f in self.fighter_cols for r in self.round_cols for stat in self.stat_cols] + \
					[f'fighter_{f}_total_{stat}' for f in self.fighter_cols for stat in self.stat_cols] + \
					[f'fighter_{f}_round_{r}_{shot}_{acc}' for f in self.fighter_cols for r in self.round_cols for shot in self.target_cols for acc in self.target_accuracy_cols] + \
					[f'fighter_{f}_total_{shot}_{acc}' for f in self.fighter_cols for shot in self.target_cols for acc in self.target_accuracy_cols]

    def clean_data(self, df):
        self.df = df
        self.convert_to_datetime()
        self.drop_useless_cols()
        self.impute_data()
        self.enforce_types()
        self.replace_divisions()
        self.rename_data()
        return self.df

    def convert_to_datetime(self):
        self.df['date'] = pd.to_datetime(self.df['date'])

    def drop_useless_cols(self):
        self.df = self.df.drop(['outcome_detail', 'elevation'], axis=1)
    
    def impute_data(self):
        self.df = self.df.fillna(0)

    def replace_outdated_rounds(self):
        self.df['outcome_format'] = self.df['outcome_format'].apply(lambda x: 3 if x == 'No' or int(x) < 3 else int(x))

    def enforce_types(self):
        for col in self.cols:
            # Convert to numeric, all that can't be converted convert to NaN
            self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
            self.df = self.df.fillna(0)
            self.df[col] = self.df[col].astype(int)

    def replace_divisions(self):
        self.df['division'] = self.df['division'].replace({
            'Open Weight' : 'Lightweight',
            'UFC 2 Tournament Title' : 'Lightweight',
            'UFC 3 Tournament Title' : 'Lightweight',
            'UFC 4 Tournament Title' : 'Lightweight',
            'UFC 5 Tournament Title' : 'Lightweight',
            'UFC 6 Tournament Title' : 'Lightweight',
            'UFC 7 Tournament Title' : 'Lightweight',
            'UFC 8 Tournament Title' : 'Lightweight',
            'UFC 10 Tournament Title' : 'Lightweight',
            'UFC Superfight Championship' : 'Lightweight',
            'Ultimate Ultimate \'95 Tournament Title' : 'Lightweight',
            'Ultimate Ultimate \'96 Tournament Title' : 'Lightweight',
            'UFC Heavyweight Title' : 'Heavyweight',
            'UFC 13 Lightweight Tournament Title' : 'Lightweight',
            'UFC 13 Heavyweight Tournament Title' : 'Heavyweight',
            'UFC 14 Middleweight Tournament Title' : 'Middleweight',
            'UFC 14 Heavyweight Tournament Title' : 'Heavyweight',
            'UFC 15 Heavyweight Tournament Title' : 'Heavyweight',
            'UFC Light Heavyweight Title' : 'Light Heavyweight',
            'Ultimate Japan Heavyweight Tournament Title' : 'Heavyweight',
            'UFC 17 Middleweight Tournament Title' : 'Middleweight',
            'UFC Welterweight Title' : 'Welterweight',
            'Ultimate Japan 2 Heavyweight Tournament Title' : 'Heavyweight',
            'Super Heavyweight' : 'Heavyweight',
            'UFC Lightweight Title' : 'Lightweight',
            'UFC Middleweight Title' : 'Middleweight',
            'UFC Interim Light Heavyweight Title' : 'Heavyweight',
            'UFC Interim Heavyweight Title' : 'Heavyweight',
            'Ultimate Fighter 1 Middleweight Tournament Title' : 'Middleweight',
            'Ultimate Fighter 1 Light Heavyweight Tournament Title' : 'Light Heavyweight',
            'Ultimate Fighter 2 Welterweight Tournament Title' : 'Welterweight',
            'Ultimate Fighter 2 Heavyweight Tournament Title' : 'Heavyweight',
            'Ultimate Fighter 3 Middleweight Tournament Title' : 'Middleweight',
            'Ultimate Fighter 3 Light Heavyweight Tournament Title' : 'Light Heavyweight',
            'Ultimate Fighter 4 Welterweight Tournament Title' : 'Welterweight',
            'Ultimate Fighter 4 Middleweight Tournament Title' : 'Middleweight',
            'Ultimate Fighter 5 Lightweight Tournament Title' : 'Lightweight',
            'Ultimate Fighter 6 Welterweight Tournament Title' : 'Welterweight',
            'UFC Interim Welterweight Title' : 'Welterweight',
            'Ultimate Fighter 7 Middleweight Tournament Title' : 'Middleweight',
            'Ultimate Fighter 8 Lightweight Tournament Title' : 'Lightweight',
            'Ultimate Fighter 8 Light Heavyweight Tournament Title' : 'Light Heavyweight',
            'Ultimate Fighter 9 Welterweight Tournament Title' : 'Welterweight',
            'Ultimate Fighter 9 Lightweight Tournament Title' : 'Lightweight',
            'Ultimate Fighter 10 Heavyweight Tournament Title' : 'Heavyweight',
            'Ultimate Fighter 11 Middleweight Tournament Title' : 'Middleweight',
            'Ultimate Fighter 12 Lightweight Tournament Title' : 'Lightweight',
            'Ultimate Fighter 13 Welterweight Tournament Title' : 'Welterweight',
            'UFC Bantamweight Title' : 'Bantamweight',
            'Ultimate Fighter 14 Bantamweight Tournament Title' : 'Bantamweight',
            'Ultimate Fighter 14 Featherweight Tournament Title' : 'Featherweight',
            'Ultimate Fighter 15 Lightweight Tournament Title' : 'Lightweight',
            'Ultimate Fighter Brazil Middleweight Tournament Title' : 'Middleweight',
            'Ultimate Fighter Brazil Featherweight Tournament Title' : 'Featherweight',
            'UFC Interim Bantamweight Title' : 'Bantamweight',
            'UFC Flyweight Title' : 'Flyweight',
            'Ultimate Fighter Australia vs UK Welterweight Tournament Title' : 'Welterweight',
            'Ultimate Fighter Australia vs UK Lightweight Tournament Title' : 'Lightweight',
            'Ultimate Fighter 16 Welterweight Tournament Title' : 'Welterweight',
            'Ultimate Fighter 17 Middleweight Tournament Title' : 'Middleweight',
            'Ultimate Fighter Brazil 2 Welterweight Tournament Title' : 'Welterweight',
            'Ultimate Fighter 18 Bantamweight Tournament Title' : 'Bantamweight',
            'Ultimate fighter China Welterweight Tournament Title' : 'Welterweight',
            'TUF Nations Canada vs Australia Middleweight Tournament Title' : 'Middleweight',
            'TUF Nations Canada vs Australia Welterweight Tournament Title' : 'Welterweight',
            'Ultimate Fighter Brazil 3 Middleweight Tournament Title' : 'Middleweight',
            'Ultimate Fighter Brazil 3 Heavyweight Tournament Title' : 'Heavyweight',
            'Ultimate Fighter 19 Middleweight Tournament Title' : 'Middleweight',
            'Ultimate Fighter 19 Light Heavyweight Tournament Title' : 'Light Heavyweight',
            'Ultimate Fighter China Featherweight Tournament Title' : 'Featherweight',
            'Ultimate Fighter Latin America Bantamweight Tournament Title' : 'Bantamweight',
            'Ultimate Fighter Latin America Featherweight Tournament Title' : 'Featherweight',
            'UFC Interim Featherweight Title' : 'Featherweight',
            'UFC Featherweight Title' : 'Featherweight',
            'Ultimate Fighter 21 Welterweight Tournament Title' : 'Welterweight',
            'Ultimate Fighter Brazil 4 Lightweight Tournament Title' : 'Lightweight',
            'Ultimate Fighter Brazil 4 Bantamweight Tournament Title' : 'Bantamweight',
            'Ultimate Fighter Latin America 2 Lightweight Tournament Title' : 'Lightweight',
            'Ultimate Fighter Latin America 2 Welterweight Tournament Title' : 'Welterweight',
            'Ultimate Fighter 22 Lightweight Tournament Title' : 'Lightweight',
            'Ultimate Fighter 23 Light Heavyweight Tournament Title' : 'Light Heavyweight',
            'Ultimate Fighter Latin America 3 Lightweight Tournament Title' : 'Lightweight',
            'Ultimate Fighter 25 Welterweight Tournament Title' : 'Welterweight',
            'UFC Interim Middleweight Title' : 'Middleweight',
            'UFC Interim Lightweight Title' : 'Lightweight',
            'Ultimate Fighter 27 Featherweight Tournament Title' : 'Featherweight',
            'Ultimate Fighter 27 Lightweight Tournament Title' : 'Lightweight',
            'Ultimate Fighter 28 Heavyweight Tournament Title' : 'Heavyweight',
            'UFC Interim Flyweight Title' : 'Flyweight',
            'Ultimate Fighter Brazil 1 Featherweight Tournament Title' : 'Featherweight',
            'Ultimate Fighter Brazil 1 Middleweight Tournament Title' : 'Middleweight',
            'Ultimate fighter Australia vs. UK Lightweight Tournament Title' : 'Lightweight',
            'Ultimate Fighter Australia vs. UK Welterweight Tournament Title' : 'Welterweight',
            'Ultimate Fighter China Welterweight Tournament Title' : 'Welterweight',
            'TUF Nations Canada vs. Australia Welterweight Tournament Title' : 'Welterweight',
            'TUF Nations Canada vs. Australia Middleweight Tournament Title' : 'Middleweight',
            'Catch Weight' : 'Catchweight'
        })

    def rename_data(self):
        self.df.rename(columns={'division' : 'weight_class', 'outcome_format' : 'rounds_format'})
