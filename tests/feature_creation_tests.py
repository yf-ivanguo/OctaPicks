import pandas as pd

class FeatureCreationTests():
    def __init__(self) -> None:
        self.fights_df = pd.read_csv('tests/test_fights.csv', encoding='latin-1')
        self.fighter_df = pd.read_csv('tests/test_fighters.csv', encoding='latin-1')
        
    def test_example(self):
        """
        This tests the functionality of the X function.
        """

        # Create the expected values and populate them, can use df.rolling(), etc.
        expected_vals = []

        # Call feature creation function on the dataframes

        # Assert that the values are equal
        assert True