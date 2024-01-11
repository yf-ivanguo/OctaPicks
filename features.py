import pandas as pd
from clean_data import CleanData

FIGHT_CSV = 'data/ufc_men_fights.csv'
FIGHTERS_CSV = 'data/ufc_men_fighters.csv'

class FeatureCreation():
    def __init__(self) -> None:
        self.fights_df = pd.read_csv(FIGHT_CSV, encoding='latin-1')
        self.fighter_df = pd.read_csv(FIGHTERS_CSV, encoding='latin-1')
        self.cleaner = CleanData()
        
    def create_features(self):
        """
        This function creates features for the fights dataframe.
        """

        cleaned_df = self.cleaner.clean_data(self.fights_df)

        # Create all features

        return cleaned_df