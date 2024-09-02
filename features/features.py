import pandas as pd
from .clean_data import CleanData
from .elo_features import Elo
from .fight_stats_features import FightStats
from .frequency_stats_features import FrequencyStats
from .significant_strike_features import SignificantStrikeFeatures
from .date_features import DateFeatures
from .taped_stats import TapedStats
from .win_loss_stats_features import WinLossStats

FIGHT_CSV = 'data/ufc_men_fights.csv'
FIGHTERS_CSV = 'data/ufc_men_fighters.csv'

class FeatureCreation():
    def __init__(self) -> None:
        self.fights_df = pd.read_csv(FIGHT_CSV, encoding='latin-1')
        self.fighter_df = pd.read_csv(FIGHTERS_CSV, encoding='latin-1')
        self.cleaner = CleanData()
        self.elo = Elo()
        self.fight_stats = FightStats()
        self.frequency_stats = FrequencyStats()
        self.significant_strike_features = SignificantStrikeFeatures()
        self.date_features = DateFeatures()
        self.taped_stats = TapedStats()
        self.win_loss_stats = WinLossStats()

    def create_features(self):
        """
        This function creates features for the fights dataframe.
        """

        cleaned_df = self.cleaner.clean_data(self.fights_df)
        elo_df = self.elo.compute_elo_features(cleaned_df)
        fight_stats_df = self.fight_stats.create_fight_stats_features(elo_df)
        frequency_stats_df = self.frequency_stats.create_frequency_feats(fight_stats_df, True)
        significant_strike_df = self.significant_strike_features.create_significant_strike_feats(frequency_stats_df)
        spatial_df = self.date_features.create_date_features(significant_strike_df)
        taped_stats_df = self.taped_stats.create_taped_stats_feats(spatial_df, self.fighter_df)
        final_df = self.win_loss_stats.create_win_loss_stat_features(taped_stats_df)

        return final_df