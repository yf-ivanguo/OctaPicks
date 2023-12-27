import argparse
import requests
import csv
import googlemaps
from bs4 import BeautifulSoup
from tqdm import tqdm
import re
import configparser
import googlemaps

UFC_STATS_URL = 'http://www.ufcstats.com/statistics/events/completed?page=all'

# Add to these columns with new data scraped
MATCH_COLS = ['fight_night_title', 'date', 'location', 'fighter_a', 'fighter_a_id', 'fighter_b', 'fighter_b_id', 'winner', 'winner_id', \
              'division', 'outcome_method', 'outcome_round', 'outcome_time', 'outcome_format', 'referee', 'outcome_detail']
FIGHTER_COLS = ['a', 'b']
STAT_COLS = ['kd', 'sig_str_landed', 'sig_str_attempted', 'sig_str_pct', 'total_str_landed', 'total_str_attempted', 'td_landed', 'td_attempted', 'td_pct', 'sub_att', 'rev', 'ctrl']
ROUND_COLS = range(1, 6)
TARGET_COLS = ['head', 'body', 'leg', 'distance', 'clinch', 'ground']
TARGET_ACCURACY_COLS = ['shots_landed', 'shots_attempted']

COLS = MATCH_COLS + [f'fighter_{f}_round_{r}_{stat}' for f in FIGHTER_COLS for r in ROUND_COLS for stat in STAT_COLS] + \
                    [f'fighter_{f}_total_{stat}' for f in FIGHTER_COLS for stat in STAT_COLS] + \
                    [f'fighter_{f}_round_{r}_{shot}_{acc}' for f in FIGHTER_COLS for r in ROUND_COLS for shot in TARGET_COLS for acc in TARGET_ACCURACY_COLS] + \
                    [f'fighter_{f}_total_{shot}_{acc}' for f in FIGHTER_COLS for shot in TARGET_COLS for acc in TARGET_ACCURACY_COLS]

def read_config(file_path='config.ini'):
    config = configparser.ConfigParser()
    config.read(file_path)
    return config

def scrape_ufc_men_stats(api_key_file, include_progress_bar=True):
    try:
        config = read_config(file_path=api_key_file)
        google_maps_api_key = config.get('GoogleMaps', 'api_key')
        google_maps_client = googlemaps.Client(key=google_maps_api_key)

        # Test sending a response to Google Maps API
        google_maps_client.geocode('1600+Amphitheatre+Parkway,+Mountain+View,+CA')
    except Exception as e:
        print("Error reading Google Maps API key:", str(e))
        return
    
    with open('ufc_men_fights.csv', 'a', newline='') as csv_file:
        writer = csv.writer(csv_file)

        if csv_file.tell() == 0:
            writer.writerow(COLS)
        
        source_main = requests.get(UFC_STATS_URL).text
        soup_main = BeautifulSoup(source_main, "lxml")
        fights_main = soup_main.find_all('tr', attrs={'class': 'b-statistics__table-row'})
        fight_range = tqdm(range(len(fights_main) - 1, 0, -1), desc="Scraping UFC Stats", leave=True) if include_progress_bar else range(len(fights_main) - 1, 0, -1)

        for i in fight_range:
            fight_night = fights_main[i]
            fight_night_ahref = fight_night.find('a')

            if fight_night_ahref is not None:
                fight_night_title = fight_night_ahref.text.strip()
                fight_night_link = fight_night_ahref.get("href")
                data = []

                get_fights(fight_night_link, data, fight_night_title, True, google_maps_client)

                for row in data:
                    writer.writerow(row)

def get_fights(link, data, fight_night_title, is_men, gmaps):
    source_fight_night = requests.get(link).text
    soup_fight_night = BeautifulSoup(source_fight_night, "lxml")
    fight_night_fights = soup_fight_night.find_all('tr', attrs={'class': 'b-fight-details__table-row b-fight-details__table-row__hover js-fight-details-click'})
    date, location, location_elevation = get_fight_date_and_location(soup_fight_night, gmaps)

    for i in range(len(fight_night_fights) - 1, -1, -1):
        fight = fight_night_fights[i]
        fight_ahref = fight.find('a')

        if is_men != any('women' in p.text.strip().lower() for p in fight.findChildren('p')):
                continue

        if fight_ahref is not None:
            fight_link = fight_ahref.get("href")
            fighters_data = get_fighters(fight_link)

            fight_overview_data = get_fight_overview(fight_link)

            fight_totals = get_fight_totals(fight_link, fight_overview_data[2])
            fight_totals_tuple = tuple(element for tuple in fight_totals for element in tuple)
            fight_sig_strikes = get_fight_sig_strikes(fight_link, fight_overview_data[2])
            fight_sig_strikes_tuple = tuple(element for tuple in fight_sig_strikes for element in tuple)

            data.append([fight_night_title] + [date] + [location] + [location_elevation] + list(fighters_data) + \
                        list(fight_overview_data) + list(fight_totals_tuple) + list(fight_sig_strikes_tuple))

# Gets the fighters' names and links
def get_fighters(link):
    source_fight = requests.get(link).text
    soup_fight = BeautifulSoup(source_fight, "lxml")
    fighters = soup_fight.find_all('div', class_='b-fight-details__person')

    fighter_a_element, fighter_b_element = fighters[:2]

    fighter_a_status = fighter_a_element.select_one('.b-fight-details__person-status').get_text(strip=True) if fighter_a_element.select_one('.b-fight-details__person-status') else None
    fighter_a_name = fighter_a_element.select_one('.b-fight-details__person-name a').get_text(strip=True) if fighter_a_element.select_one('.b-fight-details__person-name a') else None
    fighter_a_id = fighter_a_element.select_one('.b-fight-details__person-name a').get("href").split('/')[-1].strip()

    fighter_b_status = fighter_b_element.select_one('.b-fight-details__person-status').get_text(strip=True) if fighter_b_element.select_one('.b-fight-details__person-status') else None
    fighter_b_name = fighter_b_element.select_one('.b-fight-details__person-name a').get_text(strip=True) if fighter_b_element.select_one('.b-fight-details__person-name a') else None
    fighter_b_id = fighter_b_element.select_one('.b-fight-details__person-name a').get("href").split('/')[-1].strip()

    winner_name = fighter_a_name if fighter_a_status == 'W' else fighter_b_name if fighter_b_status == 'W' else 'Draw' if fighter_a_status == fighter_b_status == 'D' else 'No Contest' if fighter_a_status == fighter_b_status == 'NC' else None
    winner_id = fighter_a_id if fighter_a_status == 'W' else fighter_b_id if fighter_b_status == 'W' else None

    return fighter_a_name, fighter_a_id, fighter_b_name, fighter_b_id, winner_name, winner_id

# Gets the overview box information
def get_fight_overview(link):
    source = requests.get(link).text
    soup = BeautifulSoup(source, "lxml")

    details = soup.find_all('i', attrs={'class' : 'b-fight-details__text-item'})

    division = ' '.join(soup.find('i', attrs={'class' : 'b-fight-details__fight-title'}).text.strip().rsplit((' ', 1)[0])[:-1])
    outcome_method = soup.find('i', attrs={'style' : 'font-style: normal'}).text.strip()
    outcome_round = details[0].text.strip().split(' ')[-1]
    outcome_time = details[1].text.strip().split(' ')[-1]
    outcome_format = details[2].text.strip().split(' ')[17]
    referee = details[3].text.strip().split(' ')[-1]
    outcome_detail = ' '.join([word for word in soup.find_all(True, attrs={'class' : 'b-fight-details__text'})[-1].text.strip().split(' ') if word.strip()][1:])

    return division, outcome_method, outcome_round, outcome_time, outcome_format, referee, outcome_detail

def get_fight_totals(link, round):
    source = requests.get(link).text
    soup = BeautifulSoup(source, "lxml")
    stats = soup.find_all('section', attrs={'class' : 'b-fight-details__section js-fight-section'})
    player_a_round_stats = []
    player_b_round_stats = []
    player_a_total_stats = player_b_total_stats = (None, None, None, None, None, None, None, None, None, None, None, None)

    if len(stats) > 1:
        total_stats = stats[1].find('table').find_all('tr', attrs={'class' : 'b-fight-details__table-row'})[1].find_all('p', attrs={'class' : 'b-fight-details__table-text'})
        for i in range(int(round)):
            round_stats = stats[2].find('table').find_all('tr', attrs={'class' : 'b-fight-details__table-row'})[i+1].find_all('p', attrs={'class' : 'b-fight-details__table-text'})
            player_a_round_stats.append(get_total_fight_stats(round_stats)[0])
            player_b_round_stats.append(get_total_fight_stats(round_stats)[1])

        player_a_total_stats = get_total_fight_stats(total_stats)[0]
        player_b_total_stats = get_total_fight_stats(total_stats)[1]

    return tuple(player_a_round_stats), tuple(player_b_round_stats), player_a_total_stats, player_b_total_stats

def get_total_fight_stats(totals):
    fighter_a = (
        totals[2].text.strip(),
        totals[4].text.split("of")[0].strip(),
        totals[4].text.split("of")[1].strip(),
        totals[6].text.strip(),
        totals[8].text.split("of")[0].strip(),
        totals[8].text.split("of")[1].strip(),
        totals[10].text.split("of")[0].strip(),
        totals[10].text.split("of")[1].strip(),
        totals[12].text.strip(),
        totals[14].text.strip(),
        totals[16].text.strip(),
        totals[18].text.strip()
    )
    fighter_b = (
        totals[3].text.strip(),
        totals[5].text.split("of")[0].strip(),
        totals[5].text.split("of")[1].strip(),
        totals[7].text.strip(),
        totals[9].text.split("of")[0].strip(),
        totals[9].text.split("of")[1].strip(),
        totals[11].text.split("of")[0].strip(),
        totals[11].text.split("of")[1].strip(),
        totals[13].text.strip(),
        totals[15].text.strip(),
        totals[17].text.strip(),
        totals[19].text.strip()
    )

    return fighter_a, fighter_b

def get_fight_sig_strikes(link, round):
    source = requests.get(link).text
    soup = BeautifulSoup(source, "lxml")
    stats = soup.find_all('section', attrs={'class' : 'b-fight-details__section js-fight-section'})
    player_a_round_stats = []
    player_b_round_stats = []

    if len(soup.find_all('table', attrs={'style': 'width: 745px'})) > 1:
        total_stats = soup.find_all('table', attrs={'style': 'width: 745px'})[1].find_all('tr', attrs={'class' : 'b-fight-details__table-row'})[1].find_all('p', attrs={'class' : 'b-fight-details__table-text'})
        
        for i in range(int(round)):
            totals_per_round = stats[4].find('table').find_all('tr', attrs={'class' : 'b-fight-details__table-row'})[i+1].find_all('p', attrs={'class' : 'b-fight-details__table-text'})
            player_a_round_stats.append(get_fight_sig_stats(totals_per_round)[0])
            player_b_round_stats.append(get_fight_sig_stats(totals_per_round)[1])
        
        player_a_total_stats = get_fight_sig_stats(total_stats)[0]
        player_b_total_stats = get_fight_sig_stats(total_stats)[1]

    return tuple(player_a_round_stats), tuple(player_b_round_stats), player_a_total_stats, player_b_total_stats

def get_fight_sig_stats(totals):
    stats = [total.text.split("of") for total in totals[6:18]]
    fighter_a = tuple(stat.strip() for stat in sum(stats[:6], []))
    fighter_b = tuple(stat.strip() for stat in sum(stats[6:], []))
    return fighter_a, fighter_b

def get_fight_date_and_location(soup, gmaps):
    data = soup.find_all('li', attrs={'class' : 'b-list__box-list-item'})
    date = data[0].text.strip().split("Date:")[1].strip()
    location = data[1].text.strip().split("Location:")[1].strip()
    location_elevation = get_elevation(location, gmaps)
    return date, location, location_elevation

def get_elevation(loc, gmaps):
    # Geocoding an address
    geocode_result = gmaps.geocode(loc)
    # print(geocode_result)
    if(len(geocode_result) == 0):
        return None
    coords = geocode_result[0]['geometry']['location']

    # Elevation
    elev_res = gmaps.elevation((coords['lat'], coords['lng']))

    elevation = elev_res[0]['elevation']

    return elevation

def isSameName(name1, name2):
    # Function to clean the name by removing non-letter characters
    clean_name = lambda name: re.sub(r'[^a-zA-Z]', '', name)

    # Clean both names
    cleaned_name1 = clean_name(name1).lower()
    cleaned_name2 = clean_name(name2).lower()

    return cleaned_name1 == cleaned_name2

def main():
    parser = argparse.ArgumentParser(description="Script to scrape UFC data")

    parser.add_argument("--api_key_file", type=str, help="File containing Google Maps API key", default="config.ini")

    args = parser.parse_args()

    scrape_ufc_men_stats(args.api_key_file)

if __name__ == "__main__":
    main()
