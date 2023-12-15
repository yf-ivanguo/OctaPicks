import pandas as pd

"""
Usage:
    from clean_data import CleanData

    df = pd.read_csv('data.csv')
    df = CleanData(df).df

    Renames all the columns to work with easier, drops useless columns, and imputes missing data with 0
"""
class CleanData():
    def __init__(self, df) -> None:
        self.df = df
        self.rename_data()
        self.drop_useless_cols()
        self.impute_data()

    def rename_data(self):
        self.df.columns = self.df.columns.str.lower().str.replace(' ', '_').str.replace('%', 'pct')
    
    def drop_useless_cols(self):
        self.df = self.df.drop('outcome_detail', axis=1)
    
    def impute_data(self):
        self.df = self.df.fillna(0)