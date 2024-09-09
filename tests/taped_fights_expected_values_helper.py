import pandas as pd

def calculate_age(dob, fight_date):
    """
    Calculates the age of the fighter at the time of the fight.
    """
    dob = pd.to_datetime(dob)
    fight_date = pd.to_datetime(fight_date)
    age = fight_date.year - dob.year - ((fight_date.month, fight_date.day) < (dob.month, dob.day))
    return age

def create_fights_csv_with_empty_expected_values(input_fights_csv_path, input_fighters_csv_path, output_csv_path):
    """
    Creates a CSV file with raw data and empty columns for expected values like height difference, reach difference, age difference, and average fight time.

    Args:
        input_fights_csv_path (str): Path to the original test_fights.csv file.
        input_fighters_csv_path (str): Path to the original test_fighters.csv file.
        output_csv_path (str): Path to save the CSV file with expected values.
    """
    # Read the original CSV files
    fights_df = pd.read_csv(input_fights_csv_path)
    fighters_df = pd.read_csv(input_fighters_csv_path)

    # Merge fighter data for fighter A
    merged_df = pd.merge(fights_df, fighters_df, left_on='fighter_a_id', right_on='ID', suffixes=('', '_fighter_a'))
    merged_df = merged_df.rename(columns={
        'Height': 'fighter_a_height',
        'Reach': 'fighter_a_reach',
        'DOB': 'fighter_a_dob'
    })

    # Merge fighter data for fighter B
    merged_df = pd.merge(merged_df, fighters_df, left_on='fighter_b_id', right_on='ID', suffixes=('', '_fighter_b'))
    merged_df = merged_df.rename(columns={
        'Height': 'fighter_b_height',
        'Reach': 'fighter_b_reach',
        'DOB': 'fighter_b_dob'
    })

    # Convert heights and reaches to centimeters
    merged_df['fighter_a_height'] = merged_df['fighter_a_height'].apply(lambda x: int(x.split("'")[0]) * 30.48 + int(x.split("'")[1].replace('"', '')) * 2.54)
    merged_df['fighter_b_height'] = merged_df['fighter_b_height'].apply(lambda x: int(x.split("'")[0]) * 30.48 + int(x.split("'")[1].replace('"', '')) * 2.54)

    merged_df['fighter_a_reach'] = merged_df['fighter_a_reach'].apply(lambda x: int(x.replace('"', '')) * 2.54)
    merged_df['fighter_b_reach'] = merged_df['fighter_b_reach'].apply(lambda x: int(x.replace('"', '')) * 2.54)

    # Calculate age
    merged_df['fighter_a_age'] = merged_df.apply(lambda row: calculate_age(row['fighter_a_dob'], row['date']), axis=1)
    merged_df['fighter_b_age'] = merged_df.apply(lambda row: calculate_age(row['fighter_b_dob'], row['date']), axis=1)

    # Create empty columns for differentials
    merged_df['fighter-a_height-diff'] = ''
    merged_df['fighter-b_height-diff'] = ''
    merged_df['fighter-a_reach-diff'] = ''
    merged_df['fighter-b_reach-diff'] = ''
    merged_df['fighter-a_age-diff'] = ''
    merged_df['fighter-b_age-diff'] = ''

    # Calculate average fight time for each fighter up until the current fight
    def calculate_avg_fight_time(fighter_id, current_date):
        past_fights = merged_df[(merged_df['date'] < current_date) &
                                ((merged_df['fighter_a_id'] == fighter_id) |
                                 (merged_df['fighter_b_id'] == fighter_id))]
        if past_fights.empty:
            return 0
        total_time = 0
        for _, row in past_fights.iterrows():
            rounds_time = (int(row['outcome_round']) - 1) * 5 * 60
            outcome_time = sum(int(x) * 60 ** i for i, x in enumerate(reversed(row['outcome_time'].split(':'))))
            total_time += (rounds_time + outcome_time) / 60  # convert to minutes
        return total_time / len(past_fights)

    merged_df['fighter-a_avg-fight-time'] = merged_df.apply(lambda row: calculate_avg_fight_time(row['fighter_a_id'], row['date']), axis=1)
    merged_df['fighter-b_avg-fight-time'] = merged_df.apply(lambda row: calculate_avg_fight_time(row['fighter_b_id'], row['date']), axis=1)

    # Select the relevant columns, including the calculated and empty expected value columns
    relevant_columns = [
        'fighter_a_id', 'fighter_b_id', 'date', 'outcome_round', 'outcome_time',
        'fighter_a_height', 'fighter_b_height',
        'fighter_a_reach', 'fighter_b_reach',
        'fighter_a_dob', 'fighter_b_dob',
        'fighter_a_age', 'fighter_b_age',
        'fighter-a_height-diff', 'fighter-b_height-diff',
        'fighter-a_reach-diff', 'fighter-b_reach-diff',
        'fighter-a_age-diff', 'fighter-b_age-diff',
        'fighter-a_avg-fight-time', 'fighter-b_avg-fight-time'
    ]

    output_df = merged_df[relevant_columns]

    # Save the dataframe to a new CSV file
    output_df.to_csv(output_csv_path, index=False)

    print(f"CSV file with raw data and empty expected value columns created at {output_csv_path}")

# Example usage
input_fights_csv_path = 'tests/test_fights.csv'  # Replace with the actual path to your test_fights.csv
input_fighters_csv_path = 'tests/test_fighters.csv'  # Replace with the actual path to your test_fighters.csv
output_csv_path = 'tests/taped_stats_expected_vals_fights.csv'  # Replace with the desired output path

# Create the CSV file with raw data and empty expected value columns
create_fights_csv_with_empty_expected_values(input_fights_csv_path, input_fighters_csv_path, output_csv_path)