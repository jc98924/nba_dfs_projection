import os
import path

import requests
requests.__path__
from bs4 import BeautifulSoup as BS
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from datetime import datetime, timedelta
import time
import string
import re
from functools import reduce

import numpy as np
import pandas as pd

def generate_game_log_range(starting_game_id, ending_game_id, time_out, driver, path):
    for game in range(starting_game_id, ending_game_id + 1):
        game_id = '00' + str(game)
        save_path = path + 'GameId_' + game_id

        try:
            merge_tables(game_id, time_out, driver, save_path)
            print('Attempt 1: Game ID {} pickled successfully'.format(game_id))
        except:
            try:
                print('Failed Attempt 1: Page did not load properly. Closing and starting new webdriver instance.')
                driver.close()
                time.sleep(5)
                driver = webdriver.Chrome(executable_path = '/usr/bin/chromedriver')
                merge_tables(game_id, time_out + .5 * random.random(), driver, save_path)
                print('Attempt 2: Game ID {} pickled successfully'.format(game_id), '\n')

            except:
                try:
                    print('Failed Attempt 2: Page did not load properly. Closing and starting new webdriver instance.')
                    driver.close()
                    time.sleep(5)
                    driver = webdriver.Chrome(executable_path = '/usr/bin/chromedriver')
                    merge_tables(game_id, time_out + .6 * random.random(), driver, save_path)
                    print('Attempt 3: Game ID {} pickled successfully'.format(game_id), '\n')
                except:
                    print('Failed Attempt 3: Terminating Instance ')
                    break

                    continue
                continue
            continue


def clean_merged_tables(df):
    dnp_descriptions = ['DND - Injury/Illness', 'DNP - Injury/Illness', 'NWT - Suspended', 'NWT - Personal', 'NWT - Injury/Illness',
            'DND - Rest', 'NWT - Trade Pending', 'DND - Personal', 'DND_COACH', 'NWT_COACH', 'NWT - Trade Pending', 'DNP - Coach\'s Decision']
    dnp_desc = [x if x in dnp_descriptions else 'Active' for x in df['MIN']]
    df.insert(11,'DNP_TAG',dnp_desc)
    df['MIN'] = df['MIN'].apply(lambda x: '00:00' if x in dnp_descriptions else x)
    df.fillna(0, inplace = True)

    df['Date'] = pd.to_datetime(df['Date'], infer_datetime_format = True)
    df['MIN'] = df['MIN'].map(lambda x: x.replace(':60',':59') if x[-2:] in x else x)
    minutes_converted = [round(datetime.strptime(x,'%M:%S').minute + datetime.strptime(x,'%M:%S').second/60, 4) for x in df['MIN']]
    df.insert(11, 'MP', minutes_converted)

    columns_to_numeric = df.columns.to_list()[13:]
    columns_to_numeric.insert(0, 'OPP_SCORE')
    columns_to_numeric.insert(0, 'TEAM_SCORE')
    df[columns_to_numeric] = df[columns_to_numeric].apply(pd.to_numeric)

    return df

def merge_tables(game_id, time_out, driver, save_path):
    '''
    Merges gamelog with all other advanced metrics from stats.nba
    args: game_id - unique game id for each game of the nba season
          time_out - set higher value if stats.nba is taking too long to load
          driver - webdriver instance
    returns: DataFrame object, pickles each merged log
    '''

    basic_df = game_log(game_id, time_out, driver)
    adv_df = get_statistics(game_id, time_out, driver, 'advanced')
    misc_df = get_statistics(game_id, time_out, driver, 'misc')
    scoring_df = get_statistics(game_id, time_out, driver, 'scoring')
    usage_df = get_statistics(game_id, time_out, driver, 'usage')
    tracking_df = get_statistics(game_id, time_out, driver, 'tracking')
    hustle_df = get_statistics(game_id, time_out, driver, 'hustle')
    defense_df = get_statistics(game_id, time_out, driver, 'defense')

    df = reduce(lambda x,y: pd.merge(x,y, on = 'Player', how = 'left'),
        [basic_df, adv_df, misc_df, scoring_df, usage_df, tracking_df, hustle_df, defense_df])

    df.to_pickle(save_path)

    return df


# Gamelog
def game_log(game_id, time_out, driver):    #Basic Game Stats (LOG)
    driver.get('https://stats.nba.com/game/{}/'.format(game_id))
    time.sleep(time_out)
    soup = BS(driver.page_source, 'lxml')

    positions = ['F', 'G', 'C']
    final_score = soup.find_all('tr')[1:3]
    team_record = soup.find_all('div',{'class':'game-summary-team__record'})
    team_name = soup.find_all('td',{'class': 'team-name show-for-medium'})
    court_advantage = ['AWAY', 'HOME']
    basic_stat_table = soup.find_all('div', {'class': 'nba-stat-table__overflow'})

    basic_stats = []

    for i in range(0,2):
        for a in basic_stat_table[i].find_all('tr')[1:-1]:
            unformatted_row = a.get_text().strip().split('\n')
            filtered_list = list(filter(None, unformatted_row))
            cleaned_list = [numbers.strip() for numbers in filtered_list]

            if cleaned_list[0][-1] in positions:
                cleaned_list[0] = cleaned_list[0][:-2]
            else:
                None

            cleaned_list.insert(1, court_advantage[i]) #ok
            cleaned_list.insert(1, final_score[i-1].find_all('td')[-1].text) #ok
            cleaned_list.insert(1, team_record[i-1].text)
            cleaned_list.insert(1, team_name[i-1].text)
            cleaned_list.insert(1, final_score[i].find_all('td')[-1].text)
            cleaned_list.insert(1, team_record[i].text)
            cleaned_list.insert(1, team_name[i].text)
            cleaned_list.insert(0, game_id)
            basic_stats.append(cleaned_list)

    basic_headers = soup.find_all('tr')[10].text.replace('\n',' ').strip().split(' ')
    basic_headers = list(filter(None, basic_headers))
    basic_headers.insert(1, 'COURT')
    basic_headers.insert(1, 'OPP_SCORE')
    basic_headers.insert(1, 'OPP_Rec')
    basic_headers.insert(1, 'OPP')
    basic_headers.insert(1, 'TEAM_SCORE')
    basic_headers.insert(1, 'TEAM_REC')
    basic_headers.insert(1, 'TEAM')
    basic_headers.insert(0, 'Game_ID')

    basic_df = pd.DataFrame(basic_stats, columns = basic_headers)
        # Inserts the date of the game into the first basic stats table
    #basic_df.rename(columns = lambda x: x.upper())
    basic_df.insert(2, 'Date', [soup.find('div',{'class':'game-summary__date'}).text] * len(basic_stats))
    #basic_df = basic_df.apply(pd.to_numeric, errors = 'ignore')
    basic_df['Date'] = pd.to_datetime(basic_df['Date'], infer_datetime_format = True)

    basic_df['Index'] = basic_df['Player'] + ' ' + basic_df['Date'].apply(lambda x: datetime.strftime(x, '%m-%d-%y'))
    basic_df.set_index('Index', drop = True, inplace = True)

    return basic_df

def get_statistics(game_id, time_out, driver, table_type):
    '''
    Scrape statistics from the 8 advanced statisics table from stats.nba.com.
    args:
        game_id: game_id on stats.nba.com
        time_out:
        driver: webdriver object
        table_type: advanced, misc, scoring, usage, four-factors, tracking
                    hustle, defense
    returns:
        DataFrame object
    '''

    driver.get('https://stats.nba.com/game/{}/{}/'.format(game_id, table_type))
    time.sleep(time_out)
    soup = BS(driver.page_source, 'lxml')

    positions = ['F', 'G', 'C']
    table_type_dict = {
    'advanced': 'AD',
    'misc': 'MS',
    'scoring': 'SC',
    'usage': 'US',
    'four-factors': 'FF',
    'tracking': 'TR',
    'hustle': 'HU',
    'defense': 'DF',
    }

    stats_table = soup.find_all('div', {'class': 'nba-stat-table__overflow'})
    stats = []

    for i in range(0,2):
        for row in stats_table[i].find_all('tr')[1:-1]:
            unformatted_row = row.get_text().strip().split('\n')
            filtered_list = list(filter(None, unformatted_row))

            if table_type == 'hustle':
                temp_list = [numbers.strip() for numbers in filtered_list]
                cleaned_list = list(filter(None, temp_list))
            else:
                cleaned_list = [numbers.strip() for numbers in filtered_list]

            if cleaned_list[0][-1] in positions:
                cleaned_list[0] = cleaned_list[0][:-2]
            else:
                None
            stats.append(cleaned_list)

    if table_type == 'hustle':
        #headers = ['Player', 'MIN', 'ScrnAssts', 'ScrnAsstsPTS', 'Deflections',
           #'OffLooseBallsRecov', 'DefLooseBallsRecov', 'LooseBallsRecov',
           #'ChgsDrawn', 'Contested2PT', 'Contested3PT', 'ContestedShot']
        headers = [header.get_text().strip() for header in stats_table[0].find_all('thead')[0].find_all('th')]
    else:
        headers = list(filter(None, soup.find_all('tr')[10].text.replace('\n',' ').strip().split(' ')))

    df = pd.DataFrame(stats, columns = headers)

    df.insert(2, 'Date', [soup.find('div',{'class':'game-summary__date'}).text] * len(stats))
    df['Date'] = pd.to_datetime(df['Date'], infer_datetime_format = True)
    df['Index'] = df['Player'] + ' ' + df['Date'].apply(lambda x: datetime.strftime(x, '%m-%d-%y'))
    df.set_index('Index', drop = True, inplace = True)

    if table_type == 'defense':
        df.drop('Date', axis = 1, inplace = True)
        df.dropna(axis = 0, how = 'any', inplace = True, subset = ['TEAMPTS'])
        df.columns = df.columns.map(lambda x: x + '_{}'.format(table_type_dict[table_type]) if x != 'Player' else x)
    else:
        df.drop(['Date', 'MIN'], axis = 1, inplace = True)
        df.columns = df.columns.map(lambda x: x + '_{}'.format(table_type_dict[table_type]) if x != 'Player' else x)

    return df





def merge_game_logs(start_game_id, ending_game_id, path):
    game_log_dfs = []
    for game_log_pickle in range(start_game_id, ending_game_id + 1):
        game_id = '00' + str(game_log_pickle)
        load_path = path + game_id
        game_log_dfs.append(pd.read_pickle(load_path))
    return pd.concat(game_log_dfs, axis = 0, ignore_index = True)
