import pandas as pd
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
print(sys.path)
from features.taped_stats import TapedStats
class FeatureCreationTests():
    def __init__(self) -> None:
        self.fights_df = pd.read_csv('tests/test_fights.csv', encoding='latin-1')
        self.fighter_df = pd.read_csv('tests/test_fighters.csv', encoding='latin-1')
        self.expected_df = pd.read_csv('tests/taped_stats_expected_vals_fights.csv', encoding='latin-1')  # The CSV with filled expected values
        self.taped_stats = TapedStats()

    def test_example(self):
        """
        This tests the functionality of the X function.
        """

        # Create the expected values and populate them, can use df.rolling(), etc.
        expected_vals = []

        # Call feature creation function on the dataframes

        # Assert that the values are equal
        assert True
    def test_create_taped_stats_feats(self):
        """
        Tests the create_taped_stats_feats function of the TapedStats class.
        """
        # Call the feature creation function
        result_df = self.taped_stats.create_taped_stats_feats(self.fights_df, self.fighter_df)
        # Remove specified columns from expected DataFrame
        columns_to_compare = self.expected_df.columns.difference(['fighter-a_dob', 'fighter-b_dob', 'date'])

        # Ensure the same columns are being compared in both DataFrames
        result_df = result_df[columns_to_compare]
        expected_df = self.expected_df[columns_to_compare]

        # Compare the generated results with the expected values
        pd.testing.assert_frame_equal(result_df, expected_df, check_dtype=False)

        print("Taped stats feature tests passed")

# Example usage
if __name__ == "__main__":
    tests = FeatureCreationTests()
    tests.test_create_taped_stats_feats()