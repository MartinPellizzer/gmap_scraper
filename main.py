from selenium import webdriver
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

sep = ';'


######################################################################################
# CSV
######################################################################################
def create_csv():
	with open('document.csv', 'w', encoding='utf-8') as f:
		f.write(f'name{sep}address{sep}website{sep}phone{sep}emails{sep}district\n')


def get_old_businesses():
	global sep
	if os.path.isfile('document.csv'):
		names = []
		with open('document.csv', 'r', encoding="utf-8") as f:
			lines = f.readlines()
			for line in lines:
				names.append(line.split(sep)[0])
		return names
	else: 
		return []
		

def get_old_businesses_pandas():
	global sep
	# names = []
	# if os.path.isfile('document.csv'):
	# 	for chunk in pandas.read_csv(
	# 		'document.csv', 
	# 		sep=sep,
	# 		chunksize=100
	# 	):
	# 		names.append(chunk['name'].to_list())
	
	if os.path.isfile('document.csv'):
		df = pandas.read_csv('document.csv', sep=sep, error_bad_lines=False, engine='python')
		return df['name'].to_list()
	else: 
		create_csv()
		return []
		

def get_cities():
	global sep
	if os.path.isfile('lista_comuni_veneto.csv'):
		df = pandas.read_csv('lista_comuni_veneto.csv', sep=sep, encoding="ISO-8859-1")
		return df['city'].to_list()
	else: 
		return []
		

def get_districts():
	global sep
	if os.path.isfile('lista_comuni_veneto.csv'):
		df = pandas.read_csv('lista_comuni_veneto.csv', sep=sep, encoding="ISO-8859-1")
		return df['district'].to_list()
	else: 
		return []

		
def get_done():
	global sep
	if os.path.isfile('lista_comuni_veneto.csv'):
		df = pandas.read_csv('lista_comuni_veneto.csv', sep=sep, encoding="ISO-8859-1")
		return df['done'].to_list()
	else: 
		return []


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
	print('finding contact url...')
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
		matches = re.finditer(regex_string, response.text)
		for match in matches: emails.add(match.group())
	except: return emails

	# contact page 1
	try:
		contact_page = find_contact_url(url)
		response = requests.get(contact_page)
		matches = re.finditer(regex_string, response.text)
		for match in matches: emails.add(match.group())
	except: return emails
		
	# contact page 2
	'''
	last_resort_url = f'{url}/contatti'
	try:
		response = requests.get(last_resort_url)
		matches = re.finditer(regex_string, response.text)
		for match in matches: emails.add(match.group())
	except: pass
	'''
		
	return emails
	
######################################################################################
# BROWSER
######################################################################################
def open_browser():
	global driver
	driver = webdriver.Chrome('./chromedriver')
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


def search_map(business_type, cities, districts):
	search_text = f'{business_type} {cities} {districts}'
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
	# get already scraped businesses
	# old_businesses = get_old_businesses_pandas()
	old_businesses = get_old_businesses()

	# get the first new business that was not previously scraped
	business, label = find_new_business(old_businesses)

	# if not new businesses found, scroll down the page to load more
	if not business:
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

	with open('document.csv', 'a', encoding="utf-8") as f:
		f.write(string_to_write)


######################################################################################
# MAIN
######################################################################################

def main():
	open_browser()

	business_type = 'salumificio'
	cities = get_cities()
	districts = get_districts()

	NUM_SCRAPES_X_SEARCH = 50
	for i in range(len(cities)):
		done = get_done()

		if done[i] == 'x':
			continue

		search_map(business_type, cities[i], districts[i])

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

def main_test():
	open_browser()

	business_type = 'salumificio'
	cities = get_cities()
	districts = get_districts()

	NUM_SCRAPES_X_SEARCH = 50
	for i in range(len(cities)):
		done = get_done()

		# if num >= 3:
		# 	break

		if done[i] == 'x':
			continue

		search_map(business_type, cities[i], districts[i])

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