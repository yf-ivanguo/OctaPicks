import pandas as pd
import numpy as np

class Date():
    def __init__(self) -> None:
        pass

    def convert_date_to_variables(self, df):
        df['date'] = pd.to_datetime(df['date'])

        df['year'] = df['date'].dt.year
        temp_col = df['date'].dt.day_of_year
        
        df['day_cos'] = temp_col.apply(lambda x: np.cos(x * 2 * np.pi / 365.25))
        df['day_sin'] = temp_col.apply(lambda x: np.sin(x * 2 * np.pi / 365.25))

        return df