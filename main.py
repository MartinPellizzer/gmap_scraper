from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from time import sleep

import re
import os
import requests
from urllib.parse import urlsplit
from collections import deque
from bs4 import BeautifulSoup
import pandas

import sys
import csv

driver = None
output_file = 'friuli.csv'

sep = ';'

VENETO_DISTRICTS = ['BL', 'PD', 'RO', 'TV', 'VE', 'VR', 'VI']

zone = {
	'region': 'friuli',
	'provinces': [
		{
			'name': 'gorizia',
			'abbreviation': 'GO',
		},
		{
			'name': 'pordenone',
			'abbreviation': 'PN',
		},
		{
			'name': 'trieste',
			'abbreviation': 'TS',
		},
		{
			'name': 'udine',
			'abbreviation': 'UD',
		},
	]
}


######################################################################################
# PROVINCES
######################################################################################
def get_provinces_names():
	names_list = []
	for key, value in zone.items():
		if key == 'provinces':
			for province in value:
				for key, value in province.items():
					if key == 'name':
						names_list.append(value)
			break
	return names_list


def get_provinces_abbreviations():
	abbreviations_list = []
	for key, value in zone.items():
		if key == 'provinces':
			for province in value:
				for key, value in province.items():
					if key == 'abbreviation':
						abbreviations_list.append(value)
						break
			break
	return abbreviations_list


def get_provinces():
	rows = []
	with open('friuli_provinces.csv', 'r', encoding="utf-8") as f:
		reader = csv.reader(f, delimiter=';')
		for i, row in enumerate(reader):
			if i == 0: continue
			rows.append(row)
	return rows


######################################################################################
# CSV
######################################################################################
def get_old_businesses():
	global sep
	global output_file
	if not os.path.isfile(output_file): 
		with open(output_file, 'w', encoding="utf-8") as f:
			return []
	else:
		with open(output_file, 'r', encoding="utf-8") as f:
			return [line.split(sep)[0] for line in f.readlines()]


######################################################################################
# STRINGS
######################################################################################
def to_ascii(text):
	encoded_string = text.encode('ascii', 'ignore')
	decoded_string = encoded_string.decode()
	return text


######################################################################################
# EMAILS
######################################################################################
def find_contact_url(url):
	contact_page = ''

	response = requests.get(url)
	soup = BeautifulSoup(response.text, 'lxml')

	for link in soup.find_all('a'):
		if 'contatti' in str(link).lower():
			link = link.get('href')
			contact_page = link
	
	return contact_page


def scrape_emails(url):
	emails = set()

	regex_string = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'

	# homepage
	try: 
		print('finding contact url...')
		response = requests.get(url)
		print(response)
		matches = re.finditer(regex_string, response.text)
		for match in matches: emails.add(match.group())
	except: return emails

	# contact page 1
	try:
		print('finding contact url...')
		contact_page = find_contact_url(url)
		response = requests.get(contact_page)
		print(response)
		matches = re.finditer(regex_string, response.text)
		for match in matches: emails.add(match.group())
	except: return emails
	
	print('done scraping website')
	return emails
	
######################################################################################
# BROWSER
######################################################################################
def open_browser():
	global driver
	options = Options()
	# options.add_argument('--headless')
	options.add_argument('--disable-gpu')
	driver = webdriver.Chrome(r'C:\drivers\chromedriver', options=options)
	driver.maximize_window()
	driver.get('https://www.google.com')
	sleep(2)
	driver.find_element(By.XPATH, '//div[text()="Rifiuta tutto"]').click()
	sleep(2)


def scroll_down_up_down():
	global driver
	driver.find_element(By.XPATH, '//div[@role="feed"]').send_keys(Keys.PAGE_DOWN)
	sleep(2)
	driver.find_element(By.XPATH, '//div[@role="feed"]').send_keys(Keys.PAGE_UP)
	sleep(2)
	driver.find_element(By.XPATH, '//div[@role="feed"]').send_keys(Keys.PAGE_DOWN)
	sleep(2)


def search(business_type, province):
	search_text = f'{business_type} {province}'
	print(search_text.lower())
	search_text = search_text.replace(' ', '+')
	driver.get(f'https://www.google.com/maps/search/{search_text}')


def click_on_listing(business):
	for _ in range(3):
		try: 
			business.click()
			return True
		except: 
			continue
	return False


######################################################################################
# SCRAPE
######################################################################################
def get_card_element(e):
	try: return e.find_elements(By.XPATH, '//div[@role="main"]')[1]
	except: return None


def scrape_name(e):
	try: return e.find_element(By.XPATH, './/h1').text
	except: return ''


def scrape_address(e):
	try: return e.find_element(By.XPATH, './/button[@data-item-id="address"]').text
	except: return ''


def scrape_district(e):
	try: return e.find_element(By.XPATH, './/button[@data-item-id="address"]').text.split(' ')[-1]
	except: return ''


def scrape_website(e):
	try: return e.find_element(By.XPATH, './/a[@data-item-id="authority"]').get_attribute("href")
	except: return ''


def scrape_phone(e):
	try: return e.find_element(By.XPATH, './/button[contains(@data-item-id, "phone")]').text
	except: return ''


def find_new_business(old_businesses):
	global driver
	elements = driver.find_elements(By.XPATH, '//div[@role="article"]')
	for e in elements:
		name = e.get_attribute('aria-label')
		if name not in old_businesses:
			return e, name
	return None, None


def debug_info(name, address, district, website, phone, emails):
	print(f'{"Name:":<8} {name}')
	print(f'{"Address:":<8} {address}')
	print(f'{"District:":<8} {district}')
	print(f'{"Website:":<8} {website}')
	print(f'{"Phone:":<8} {phone}')
	print(f'{"Emails:":<8} {emails}')
	print(f'{"":->64}')
	print()


def scrape_new_business():
	print('Check Old Businesses...')
	old_businesses = get_old_businesses()
	business, label = find_new_business(old_businesses)

	if not business:
		print('No New Businesses!!!')
		try: 
			scroll_down_up_down()
		except: 
			return 'skip_search'
		return 'no_new_business_found'

	# google maps is bugged: scroll a bit the screen and try clicking again if needed
	if not click_on_listing(business):
		return 'failed_to_click_listing'

	sleep(2)
	
	card_element = get_card_element(business)

	name = scrape_name(card_element)
	if name != label:
		return 'name_not_equal_label'

	address = scrape_address(card_element)
	district = scrape_district(card_element)
	website = scrape_website(card_element)
	phone = scrape_phone(card_element)
	emails = scrape_emails(website)
	s_emails = ' '.join(emails)

	debug_info(name, address, district, website, phone, s_emails)

	global sep
	string_to_write = ''
	string_to_write += f'{name}{sep}'
	string_to_write += f'{address}{sep}'
	string_to_write += f'{website}{sep}'
	string_to_write += f'{phone}{sep}'
	string_to_write += f'{s_emails}{sep}'
	string_to_write += f'{district}\n'

	with open(output_file, 'a', encoding="utf-8") as f:
		f.write(string_to_write)


######################################################################################
# MAIN
######################################################################################		
def get_done():
	if os.path.isfile('lista_comuni_veneto.csv'):
		df = pandas.read_csv('lista_comuni_veneto.csv', sep=';', encoding="ISO-8859-1")
		return df['done'].to_list()
	else: 
		return []

def main():
	open_browser()

	business_type = 'salumificio'
	# provinces_names = get_provinces_names()
	# provinces_abbreviations = get_provinces_abbreviations()
	provinces = get_provinces()
	
	NUM_SCRAPES_X_SEARCH = 100
	for i in range(len(provinces)):
		province_name = provinces[i][0].strip()
		province_abbr = provinces[i][1].strip()
		province_done = provinces[i][2].strip()

		# if province_done == 'x': continue

		search(business_type, province_name)

		for _ in range(NUM_SCRAPES_X_SEARCH):
			err = scrape_new_business()
			if err == 'skip_search':
				break
		
		# with open('friuli_provinces.csv', 'r', newline='') as f:
		# 	rows = [row for row in csv.reader(f, delimiter=';')]
			
		# rows[i+1][2] = 'x'

		# with open('friuli_provinces.csv', 'w', newline='') as f:
		# 	writer = csv.writer(f, delimiter=';')
		# 	writer.writerows(rows)
	
	driver.quit()

		


main()


'''
open_browser()

business_type = 'salumificio'
cities = get_cities()
districts = get_districts()

search_map(business_type, cities[0], districts[0])
scrape_new_business()

NUM_SCRAPES_X_SEARCH = 50
for i in range(len(cities)):
	done = get_done()

	if done[i] == 'x':
		continue

	search_map2(business_type, cities[0], districts[0])

	for _ in range(NUM_SCRAPES_X_SEARCH):
		err = scrape_new_business()
		if err == 'skip_search':
			break

	with open('lista_comuni_veneto.csv', newline='') as f:
		reader = csv.reader(f, delimiter=sep)
		rows = []
		for row in reader:
			rows.append(row)

	rows[i+1][3] = 'x'

	with open('lista_comuni_veneto.csv', 'w', newline='') as f:
		writer = csv.writer(f, delimiter=sep)
		writer.writerows(rows)
'''
