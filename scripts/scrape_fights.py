import argparse
import requests
import csv
from bs4 import BeautifulSoup
from tqdm import tqdm
import re
import configparser
import os
import pandas as pd
import aiohttp
import asyncio
import ssl
import time
import asyncio

UFC_STATS_URL = 'http://www.ufcstats.com/statistics/events/completed?page=all'
FIGHTS_CSV = 'data/ufc_men_fights.csv'

# Add to these columns with new data scraped
MATCH_COLS = ['fight_night_title', 'date', 'location', 'elevation', 'fighter_a', 'fighter_a_id', 'fighter_b', 'fighter_b_id', 'winner', 
              'winner_id', 'division', 'outcome_method', 'outcome_round', 'outcome_time', 'outcome_format', 'referee', 'outcome_detail']
FIGHTER_COLS = ['a', 'b']
STAT_COLS = ['kd', 'sig_str_landed', 'sig_str_attempted', 'sig_str_pct', 'total_str_landed', 'total_str_attempted', 'td_landed', 'td_attempted', 'td_pct', 'sub_att', 'rev', 'ctrl']
ROUND_COLS = range(1, 6)
TARGET_COLS = ['head', 'body', 'leg', 'distance', 'clinch', 'ground']
TARGET_ACCURACY_COLS = ['shots_landed', 'shots_attempted']

COLS = MATCH_COLS + [f'fighter_{f}_round_{r}_{stat}' for f in FIGHTER_COLS for r in ROUND_COLS for stat in STAT_COLS] + \
					[f'fighter_{f}_total_{stat}' for f in FIGHTER_COLS for stat in STAT_COLS] + \
					[f'fighter_{f}_round_{r}_{shot}_{acc}' for f in FIGHTER_COLS for r in ROUND_COLS for shot in TARGET_COLS for acc in TARGET_ACCURACY_COLS] + \
					[f'fighter_{f}_total_{shot}_{acc}' for f in FIGHTER_COLS for shot in TARGET_COLS for acc in TARGET_ACCURACY_COLS]

def clean_up(delete_csv_on_fail):
    """
    Cleans up the CSV file if the script fails

    Parameters:
        delete_csv_on_fail (bool): Whether to delete the CSV file if the script fails
    """

    if delete_csv_on_fail:
        os.remove(FIGHTS_CSV)

def read_config(file_path='config.ini'):
    """
    Reads the config file for the Google Maps API Key

    Parameters:
        file_path (str): Path to the config file

    Returns:
        configparser.ConfigParser: ConfigParser object containing the config file
    """

    config = configparser.ConfigParser()
    config.read(file_path)
    return config

	
def get_fight_date_and_location(soup):
    """
    Obtains the fight date and location from the fight link

    Parameters:
        soup (BeautifulSoup): BeautifulSoup object containing the fight link
        gmaps (googlemaps.Client): Google Maps API client

    Returns:
        tuple: Tuple containing the fight date and location
    """

    data = soup.find_all('li', attrs={'class' : 'b-list__box-list-item'})
    date = data[0].text.strip().split("Date:")[1].strip()
    location = data[1].text.strip().split("Location:")[1].strip()
    location_elevation = get_elevation(location)
    return date, location, location_elevation

def get_coords(city_name):
    base_url = "http://api.openweathermap.org/geo/1.0/direct"
    params = {
        'q': city_name,
        'limit': 1,  # Number of results to return (optional)
        'appid': 'e6b7a294c747e973de19cc9bd7a5e243'
    }
    
    response = requests.get(base_url, params=params)
    
    if response.status_code == 200:
        geocode_data = response.json()
        if geocode_data:
            return geocode_data[0]  # Returns the first result
        else:
            return None
    else:
        return None


def get_elevation(loc):
	"""
	Obtains the elevation of the location from the

	Parameters:
		loc (str): Location to get the elevation of

	Returns:
		float: Elevation of the location
	"""
	coords = get_coords(loc)
	if not coords:
		return None

	latitude = coords['lat']
	longitude = coords['lon']

	# Make the API call to Open-Meteo to get elevation
	open_meteo_url = f"https://api.open-meteo.com/v1/elevation?latitude={latitude}&longitude={longitude}"

	response = requests.get(open_meteo_url)

	if response.status_code == 200:
		elevation_data = response.json()
		if 'elevation' in elevation_data:
			return elevation_data['elevation'][0]
		else:
			return None
	else:
		return None

def isSameName(name1, name2):
    """
    Cleans the names and checks if they are the same

    Parameters:
        name1 (str): Name to be cleaned
        name2 (str): Name to be cleaned

    Returns:
        bool: Whether the names are the same
    """

    clean_name = lambda name: re.sub(r'[^a-zA-Z]', '', name)

    cleaned_name1 = clean_name(name1).lower()
    cleaned_name2 = clean_name(name2).lower()

    return cleaned_name1 == cleaned_name2

def find_fight_pages():
	"""
	Obtains the fight pages from the UFC Stats website

	Returns:
		pages (list): List of fight pages
	"""

	source = requests.get(UFC_STATS_URL).text
	soup = BeautifulSoup(source, 'lxml')
	fights_main = soup.find_all('tr', class_='b-statistics__table-row')
	pages = []

	for i in range(len(fights_main)-1, 0, -1):
		fight = fights_main[i]
		fight_a = fight.find('a')
		if fight_a is not None:
			pages.append(fight_a)

	print(f'Finished obtaining {len(pages)} pages of fights.')
	return pages

async def get_fighters(link, session):
	"""
	Obtains the fighters' names and links from the fight link

	Parameters:
		link (str): Link to the fight
		session (aiohttp.ClientSession): aiohttp session

	Returns:
		data (dict): Dictionary containing the fighters' names and links
	"""

	async with session.get(link) as res:
		soup_fight = BeautifulSoup(await res.text(), 'lxml')
		fighters = soup_fight.find_all('div', class_='b-fight-details__person')
		data = {}

		fighter_a_element, fighter_b_element = fighters[:2]
		fighter_a_status = fighter_a_element.select_one('.b-fight-details__person-status').get_text(strip=True) if fighter_a_element.select_one('.b-fight-details__person-status') else None
		data['fighter_a'] = fighter_a_element.select_one('.b-fight-details__person-name a').get_text(strip=True) if fighter_a_element.select_one('.b-fight-details__person-name a') else None
		data['fighter_a_id'] = fighter_a_element.select_one('.b-fight-details__person-name a').get("href").split('/')[-1].strip()

		fighter_b_status = fighter_b_element.select_one('.b-fight-details__person-status').get_text(strip=True) if fighter_b_element.select_one('.b-fight-details__person-status') else None
		data['fighter_b'] = fighter_b_element.select_one('.b-fight-details__person-name a').get_text(strip=True) if fighter_b_element.select_one('.b-fight-details__person-name a') else None
		data['fighter_b_id'] = fighter_b_element.select_one('.b-fight-details__person-name a').get("href").split('/')[-1].strip()

		data['winner'] = data['fighter_a'] if fighter_a_status == 'W' else data['fighter_b'] if fighter_b_status == 'W' else 'Draw' if fighter_a_status == fighter_b_status == 'D' else 'No Contest' if fighter_a_status == fighter_b_status == 'NC' else None
		data['winner_id'] = data['fighter_a_id'] if fighter_a_status == 'W' else data['fighter_b_id'] if fighter_b_status == 'W' else None
		
		return data
	
async def get_fight_overview(link, session):
	"""
	Obtains the fight overview information from the fight link

	Parameters:
		link (str): Link to the fight
		session (aiohttp.ClientSession): aiohttp session

	Returns:
		data (dict): Dictionary containing the fight overview information
	"""

	async with session.get(link) as res:
		soup_fight = BeautifulSoup(await res.text(), 'lxml')
		details = soup_fight.find_all('i', attrs={'class' : 'b-fight-details__text-item'})
		data = {}

		data['division'] = ' '.join(soup_fight.find('i', attrs={'class' : 'b-fight-details__fight-title'}).text.strip().rsplit((' ', 1)[0])[:-1])
		data['outcome_method'] = soup_fight.find('i', attrs={'style' : 'font-style: normal'}).text.strip()
		data['outcome_round'] = details[0].text.strip().split(' ')[-1]
		data['outcome_time'] = details[1].text.strip().split(' ')[-1]
		data['outcome_format'] = details[2].text.strip().split(' ')[17]
		data['referee'] = details[3].text.strip().split(' ')[-1]
		data['outcome_detail'] = ' '.join([word for word in soup_fight.find_all(True, attrs={'class' : 'b-fight-details__text'})[-1].text.strip().split(' ') if word.strip()][1:])

		return data

def get_total_fight_stats(totals):
	"""
	Obtains the total fight stats from the fight link

	Parameters:
		totals (list): List of total stats

	Returns:
		data (dict): Dictionary containing the total fight stats
	"""

	fighter_a_stats = fighter_b_stats = {}

	fighter_a_stats['kd'] = totals[2].text.strip()
	fighter_a_stats['sig_str_landed'] = totals[4].text.split("of")[0].strip()
	fighter_a_stats['sig_str_attempted'] = totals[4].text.split("of")[1].strip()
	fighter_a_stats['sig_str_pct'] = totals[6].text.strip()
	fighter_a_stats['total_str_landed'] = totals[8].text.split("of")[0].strip()
	fighter_a_stats['total_str_attempted'] = totals[8].text.split("of")[1].strip()
	fighter_a_stats['total_td_landed'] = totals[10].text.split("of")[0].strip()
	fighter_a_stats['total_td_attempted'] = totals[10].text.split("of")[1].strip()
	fighter_a_stats['total_td_pct'] = totals[12].text.strip()
	fighter_a_stats['total_sub_att'] = totals[14].text.strip()
	fighter_a_stats['total_rev'] = totals[16].text.strip()
	fighter_a_stats['total_ctrl'] = totals[18].text.strip()

	fighter_b_stats['kd'] = totals[3].text.strip()
	fighter_b_stats['sig_str_landed'] = totals[5].text.split("of")[0].strip()
	fighter_b_stats['sig_str_attempted'] = totals[5].text.split("of")[1].strip()
	fighter_b_stats['sig_str_pct'] = totals[7].text.strip()
	fighter_b_stats['total_str_landed'] = totals[9].text.split("of")[0].strip()
	fighter_b_stats['total_str_attempted'] = totals[9].text.split("of")[1].strip()
	fighter_b_stats['total_td_landed'] = totals[11].text.split("of")[0].strip()
	fighter_b_stats['total_td_attempted'] = totals[11].text.split("of")[1].strip()
	fighter_b_stats['total_td_pct'] = totals[13].text.strip()
	fighter_b_stats['total_sub_att'] = totals[15].text.strip()
	fighter_b_stats['total_rev'] = totals[17].text.strip()
	fighter_b_stats['total_ctrl'] = totals[19].text.strip()

	return fighter_a_stats, fighter_b_stats

async def get_fight_totals(link, round, session):
	"""
	Obtains the fight totals information from the fight link

	Parameters:
		link (str): Link to the fight
		round (int): Round of the fight
		session (aiohttp.ClientSession): aiohttp session

	Returns:
		data (dict): Dictionary containing the fight totals information
	"""

	async with session.get(link) as res:
		soup_fight = BeautifulSoup(await res.text(), "lxml")
		stats = soup_fight.find_all('section', attrs={'class' : 'b-fight-details__section js-fight-section'})
		data = {}

		if len(stats) > 1:
			total_stats = stats[1].find('table').find_all('tr', attrs={'class' : 'b-fight-details__table-row'})[1].find_all('p', attrs={'class' : 'b-fight-details__table-text'})

			for i in range(0, int(round)):
				totals_per_round = stats[2].find('table').find_all('tr', attrs={'class' : 'b-fight-details__table-row'})[i+1].find_all('p', attrs={'class' : 'b-fight-details__table-text'})
				fighter_a_round_stats, fighter_b_round_stats = get_total_fight_stats(totals_per_round)

				for fighter in ['a', 'b']:
					fighter_round_stats = fighter_a_round_stats if fighter == 'a' else fighter_b_round_stats

					data[f'fighter_{fighter}_round_{i+1}_kd'] = fighter_round_stats['kd']
					data[f'fighter_{fighter}_round_{i+1}_sig_str_landed'] = fighter_round_stats['sig_str_landed']
					data[f'fighter_{fighter}_round_{i+1}_sig_str_attempted'] = fighter_round_stats['sig_str_attempted']
					data[f'fighter_{fighter}_round_{i+1}_sig_str_pct'] = fighter_round_stats['sig_str_pct']
					data[f'fighter_{fighter}_round_{i+1}_total_str_landed'] = fighter_round_stats['total_str_landed']
					data[f'fighter_{fighter}_round_{i+1}_total_str_attempted'] = fighter_round_stats['total_str_attempted']
					data[f'fighter_{fighter}_round_{i+1}_td_landed'] = fighter_round_stats['total_td_landed']
					data[f'fighter_{fighter}_round_{i+1}_td_attempted'] = fighter_round_stats['total_td_attempted']
					data[f'fighter_{fighter}_round_{i+1}_td_pct'] = fighter_round_stats['total_td_pct']
					data[f'fighter_{fighter}_round_{i+1}_sub_att'] = fighter_round_stats['total_sub_att']
					data[f'fighter_{fighter}_round_{i+1}_rev'] = fighter_round_stats['total_rev']
					data[f'fighter_{fighter}_round_{i+1}_ctrl'] = fighter_round_stats['total_ctrl']
				
			fighter_a_total_stats, fighter_b_total_stats = get_total_fight_stats(total_stats)
			
			for fighter in ['a', 'b']:
				fighter_total_stats = fighter_a_total_stats if fighter == 'a' else fighter_b_total_stats

				data[f'fighter_{fighter}_total_kd'] = fighter_total_stats['kd']
				data[f'fighter_{fighter}_total_sig_str_landed'] = fighter_total_stats['sig_str_landed']
				data[f'fighter_{fighter}_total_sig_str_attempted'] = fighter_total_stats['sig_str_attempted']
				data[f'fighter_{fighter}_total_sig_str_pct'] = fighter_total_stats['sig_str_pct']
				data[f'fighter_{fighter}_total_total_str_landed'] = fighter_total_stats['total_str_landed']
				data[f'fighter_{fighter}_total_total_str_attempted'] = fighter_total_stats['total_str_attempted']
				data[f'fighter_{fighter}_total_td_landed'] = fighter_total_stats['total_td_landed']
				data[f'fighter_{fighter}_total_td_attempted'] = fighter_total_stats['total_td_attempted']
				data[f'fighter_{fighter}_total_td_pct'] = fighter_total_stats['total_td_pct']
				data[f'fighter_{fighter}_total_sub_att'] = fighter_total_stats['total_sub_att']
				data[f'fighter_{fighter}_total_rev'] = fighter_total_stats['total_rev']
				data[f'fighter_{fighter}_total_ctrl'] = fighter_total_stats['total_ctrl']

		return data
	
def get_fight_sig_stats(totals):
	"""
	Obtains the specific fight sig strikes stats from the fight link

	Parameters:
		totals (list): List of total stats

	Returns:
		tuple: Tuple containing the fighter's sig strikes stats
	"""

	stats = [total.text.split("of") for total in totals[6:18]]
	fighter_a_stats = fighter_b_stats = {}

	fighter_a_stats['head_shots_landed'] = stats[0][0].strip()
	fighter_a_stats['head_shots_attempted'] = stats[0][1].strip()
	fighter_a_stats['body_shots_landed'] = stats[1][0].strip()
	fighter_a_stats['body_shots_attempted'] = stats[1][1].strip()
	fighter_a_stats['leg_shots_landed'] = stats[2][0].strip()
	fighter_a_stats['leg_shots_attempted'] = stats[2][1].strip()
	fighter_a_stats['distance_shots_landed'] = stats[3][0].strip()
	fighter_a_stats['distance_shots_attempted'] = stats[3][1].strip()
	fighter_a_stats['clinch_shots_landed'] = stats[4][0].strip()
	fighter_a_stats['clinch_shots_attempted'] = stats[4][1].strip()
	fighter_a_stats['ground_shots_landed'] = stats[5][0].strip()
	fighter_a_stats['ground_shots_attempted'] = stats[5][1].strip()

	fighter_b_stats['head_shots_landed'] = stats[6][0].strip()
	fighter_b_stats['head_shots_attempted'] = stats[6][1].strip()
	fighter_b_stats['body_shots_landed'] = stats[7][0].strip()
	fighter_b_stats['body_shots_attempted'] = stats[7][1].strip()
	fighter_b_stats['leg_shots_landed'] = stats[8][0].strip()
	fighter_b_stats['leg_shots_attempted'] = stats[8][1].strip()
	fighter_b_stats['distance_shots_landed'] = stats[9][0].strip()
	fighter_b_stats['distance_shots_attempted'] = stats[9][1].strip()
	fighter_b_stats['clinch_shots_landed'] = stats[10][0].strip()
	fighter_b_stats['clinch_shots_attempted'] = stats[10][1].strip()
	fighter_b_stats['ground_shots_landed'] = stats[11][0].strip()
	fighter_b_stats['ground_shots_attempted'] = stats[11][1].strip()

	return fighter_a_stats, fighter_b_stats
	
async def get_fight_sig_strikes_stats(link, round, session):
	"""
	Obtains the fight significant strikes information from the fight link

	Parameters:
		link (str): Link to the fight
		round (int): Round of the fight
		session (aiohttp.ClientSession): aiohttp session

	Returns:
		data (dict): Dictionary containing the fight significant strikes information
	"""

	async with session.get(link) as res:
		soup_fight = BeautifulSoup(await res.text(), "lxml")
		stats = soup_fight.find_all('section', attrs={'class' : 'b-fight-details__section js-fight-section'})
		data = {}

		if len(soup_fight.find_all('table', attrs={'style': 'width: 745px'})) > 1:
			total_stats = soup_fight.find_all('table', attrs={'style': 'width: 745px'})[1].find_all('tr', attrs={'class' : 'b-fight-details__table-row'})[1].find_all('p', attrs={'class' : 'b-fight-details__table-text'})

			for i in range(0, int(round)):
				totals_per_round = stats[4].find('table').find_all('tr', attrs={'class' : 'b-fight-details__table-row'})[i+1].find_all('p', attrs={'class' : 'b-fight-details__table-text'})
				fighter_a_round_stats, fighter_b_round_stats = get_fight_sig_stats(totals_per_round)

				for fighter in ['a', 'b']:
					fighter_round_stats = fighter_a_round_stats if fighter == 'a' else fighter_b_round_stats

					data[f'fighter_{fighter}_round_{i+1}_head_shots_landed'] = fighter_round_stats['head_shots_landed']
					data[f'fighter_{fighter}_round_{i+1}_head_shots_attempted'] = fighter_round_stats['head_shots_attempted']
					data[f'fighter_{fighter}_round_{i+1}_body_shots_landed'] = fighter_round_stats['body_shots_landed']
					data[f'fighter_{fighter}_round_{i+1}_body_shots_attempted'] = fighter_round_stats['body_shots_attempted']
					data[f'fighter_{fighter}_round_{i+1}_leg_shots_landed'] = fighter_round_stats['leg_shots_landed']
					data[f'fighter_{fighter}_round_{i+1}_leg_shots_attempted'] = fighter_round_stats['leg_shots_attempted']
					data[f'fighter_{fighter}_round_{i+1}_distance_shots_landed'] = fighter_round_stats['distance_shots_landed']
					data[f'fighter_{fighter}_round_{i+1}_distance_shots_attempted'] = fighter_round_stats['distance_shots_attempted']
					data[f'fighter_{fighter}_round_{i+1}_clinch_shots_landed'] = fighter_round_stats['clinch_shots_landed']
					data[f'fighter_{fighter}_round_{i+1}_clinch_shots_attempted'] = fighter_round_stats['clinch_shots_attempted']
					data[f'fighter_{fighter}_round_{i+1}_ground_shots_landed'] = fighter_round_stats['ground_shots_landed']
					data[f'fighter_{fighter}_round_{i+1}_ground_shots_attempted'] = fighter_round_stats['ground_shots_attempted']
				
			fighter_a_total_stats, fighter_b_total_stats = get_fight_sig_stats(total_stats)
			
			for fighter in ['a', 'b']:
				fighter_total_stats = fighter_a_total_stats if fighter == 'a' else fighter_b_total_stats

				data[f'fighter_{fighter}_total_head_shots_landed'] = fighter_total_stats['head_shots_landed']
				data[f'fighter_{fighter}_total_head_shots_attempted'] = fighter_total_stats['head_shots_attempted']
				data[f'fighter_{fighter}_total_body_shots_landed'] = fighter_total_stats['body_shots_landed']
				data[f'fighter_{fighter}_total_body_shots_attempted'] = fighter_total_stats['body_shots_attempted']
				data[f'fighter_{fighter}_total_leg_shots_landed'] = fighter_total_stats['leg_shots_landed']
				data[f'fighter_{fighter}_total_leg_shots_attempted'] = fighter_total_stats['leg_shots_attempted']
				data[f'fighter_{fighter}_total_distance_shots_landed'] = fighter_total_stats['distance_shots_landed']
				data[f'fighter_{fighter}_total_distance_shots_attempted'] = fighter_total_stats['distance_shots_attempted']
				data[f'fighter_{fighter}_total_clinch_shots_landed'] = fighter_total_stats['clinch_shots_landed']
				data[f'fighter_{fighter}_total_clinch_shots_attempted'] = fighter_total_stats['clinch_shots_attempted']
				data[f'fighter_{fighter}_total_ground_shots_landed'] = fighter_total_stats['ground_shots_landed']
				data[f'fighter_{fighter}_total_ground_shots_attempted'] = fighter_total_stats['ground_shots_attempted']

		return data

async def scrape_ufc_fights(fight_page, session, delete_csv_on_fail, is_men=True):
	"""
	Scrapes men's UFC fights
      
	Parameters:
		fight_page (str): Page to scrape
		session (aiohttp.ClientSession): aiohttp session
		google_maps_client (googlemaps.Client): Google Maps API client
		delete_csv_on_fail (bool): Whether to delete the CSV file if the script fails
		is_men (bool): Whether to scrape the men's fights
	"""

	try:
		async with session.get(fight_page.get('href')) as res:
			soup_fights = BeautifulSoup(await res.text(), 'lxml')
			fight_list = soup_fights.find_all('tr', attrs={'class': 'b-fight-details__table-row b-fight-details__table-row__hover js-fight-details-click'})
			date, location, location_elevation = get_fight_date_and_location(soup_fights)

			data = []
			for i in range(len(fight_list) - 1, -1, -1):
				fight = fight_list[i]
				fight_a = fight.find('a')

				if is_men == any('women' in p.text.strip().lower() for p in fight.findChildren('p')):
					continue

				if fight_a is not None:
					fight_night_title = fight_page.text.strip()
					fight_link = fight_a.get('href')

					fighters_data = await get_fighters(fight_link, session)
					fight_overview_data = await get_fight_overview(fight_link, session)
					fight_totals_data = await get_fight_totals(fight_link, fight_overview_data['outcome_round'], session)
					fight_sig_strikes = await get_fight_sig_strikes_stats(fight_link, fight_overview_data['outcome_round'], session)

					fight_data = {
						'fight_night_title': fight_night_title,
						'date': date,
						'location': location,
						'elevation': location_elevation
					}
					
					data_list = [fighters_data, fight_overview_data, fight_totals_data, fight_sig_strikes]
					for d in data_list:
						fight_data.update(d)

					# If a column is missing, add it with a None value
					for col in COLS:
						if col not in fight_data:
							fight_data[col] = None

					data.append(fight_data)
						
			return data
		
	except Exception as e:
		print(f'Error scraping {fight_page.text.strip()}:', str(e))
		clean_up(delete_csv_on_fail)

	except KeyboardInterrupt:
		print('Keyboard interrupt detected, stopping script...')
		clean_up(delete_csv_on_fail)

def store_results(list_of_lists):
	"""
	Stores the results in a CSV file

	Parameters:
		list_of_lists (list): List of lists containing the results
	"""

	fights_list = sum(list_of_lists, []) # flatten lists

	with open(FIGHTS_CSV, 'w') as fights_file:
		fieldnames = COLS
		file_writer = csv.DictWriter(fights_file, fieldnames=fieldnames)
		file_writer.writeheader()
		file_writer.writerows(fights_list)

def load_existing_fights():
    """
    Load existing fights from the CSV file.

    Returns:
        set: A set of fight identifiers (e.g., fight titles) that have already been scraped.
    """
    if os.path.exists(FIGHTS_CSV):
        try:
            df = pd.read_csv(FIGHTS_CSV, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(FIGHTS_CSV, encoding='ISO-8859-1')  # Try a different encoding if UTF-8 fails
        return set(df['fight_night_title'].unique())
    return set()

def append_results_to_csv(list_of_lists):
    """
    Appends the results to the existing CSV file.

    Parameters:
        list_of_lists (list): List of lists containing the results.
    """

    fights_list = sum(list_of_lists, [])  # flatten lists

    with open(FIGHTS_CSV, 'a') as fights_file:  # Open in append mode
        fieldnames = COLS
        file_writer = csv.DictWriter(fights_file, fieldnames=fieldnames)
        if os.path.getsize(FIGHTS_CSV) == 0:
            file_writer.writeheader()  # Write header only if file is empty
        file_writer.writerows(fights_list)
		
async def main():
    parser = argparse.ArgumentParser(description='Scrape UFC fights')
    parser.add_argument("--delete_csv_on_fail", type=bool, help="Whether to delete the CSV file if the script fails", default=True)
    args = parser.parse_args()

    # Load existing fight titles to avoid re-scraping
    existing_fights = load_existing_fights()

    # Create a SSLContext object with SSL verification disabled
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    pages = find_fight_pages()

    # Filter out pages that have already been scraped
    pages = [page for page in pages if page.text.strip() not in existing_fights]

    if not pages:
        print("No new fights to scrape.")
        return

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
        tasks = [
            scrape_ufc_fights(page, session, args.delete_csv_on_fail)
            for page in pages
        ]

        list_of_lists = []
        progress_bar = tqdm(total=len(tasks))  # Initialize the progress bar

        for i in range(0, len(tasks), 10):
            sublist = tasks[i:i+10]
            results = await asyncio.gather(*sublist)
            list_of_lists.extend(results)
            progress_bar.update(len(sublist))  # Update the progress bar

        progress_bar.close()  # Close the progress bar
        append_results_to_csv(list_of_lists)  # Append new results to CSV

if __name__ == "__main__":
	start_time = time.time()  # Start the timer
	asyncio.run(main())
	end_time = time.time()  # Stop the timer
	execution_time = end_time - start_time  # Calculate the total execution time

	print(f"Execution time: {execution_time} seconds")  # Print the execution time