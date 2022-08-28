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

import sys
import csv

driver = None

num_operations = 5
sep = ';'


######################################################################################
# CSV
######################################################################################
def create_csv():
	with open('document.csv', 'w', encoding='utf-8') as f:
		f.write(f'name{sep}address{sep}website{sep}phone{sep}emails\n')

def get_old_businesses():
	global sep
	if os.path.isfile('document.csv'):
		names = list()
		with open('document.csv', 'r', encoding="utf-8") as f:
			lines = f.readlines()
			for line in lines:
				names.append(line.split(sep)[0])
		return names
	else: 
		return []
		
def get_old_businesses_pandas():
	global sep
	if os.path.isfile('document.csv'):
		df = pandas.read_csv('document.csv', sep=sep)
		return df['name'].to_list()
	else: 
		create_csv()
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
	contact_page = ''

	response = requests.get(url)
	soup = BeautifulSoup(response.text, 'lxml')

	for link in soup.find_all('a'):
		if 'contatti' in str(link).lower():
			link = link.get('href')
			contact_page = link
			# print(link)
	
	return contact_page


def scrape_emails(url):
	emails = set()
	
	parts = urlsplit(url)
	domain_name = parts.netloc.replace('www.', '').split('.')[0]

	list_domains = [domain_name, 'gmail', 'hotmail', 'legalmail']

	regex_string = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'

	# homepage
	try: 
		response = requests.get(url)
		matches = re.finditer(regex_string, response.text)
		for match in matches:
			# print(parts.netloc + ' --> ' + match.group())
			for domain in list_domains:
				if domain in match.group():
					emails.add(match.group())
					break
	except (requests.exceptions.MissingSchema, requests.exceptions.ConnectionError): 
		# print('*** cant load page')
		return set()

	# contact page 1
	contact_page = find_contact_url(url)
	try:
		response = requests.get(contact_page)
		matches = re.finditer(regex_string, response.text)
		for match in matches:
			# print(parts.netloc + ' --> ' + match.group())
			for domain in list_domains:
				if domain in match.group():
					emails.add(match.group())
					break
	except (requests.exceptions.MissingSchema, requests.exceptions.ConnectionError): 
		# print('*** cant find contact link')
		pass
		
	# contact page 2
	last_resort_url = f'{url}/contatti'
	# print(f'LAST RESORT: {last_resort_url}')
	try:
		response = requests.get(last_resort_url)
		matches = re.finditer(regex_string, response.text)
		for match in matches:
			# print(parts.netloc + ' --> ' + match.group())
			for domain in list_domains:
				if domain in match.group():
					emails.add(match.group())
					break
	except (requests.exceptions.MissingSchema, requests.exceptions.ConnectionError):
		# print('*** has no contact url')
		pass
		
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


def search_map():
	driver.get(f'https://www.google.com/maps/search/azienda+vinicola+padova')


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


def scrape_website(e):
	try: 
		website = e.find_element(By.XPATH, './/a[@data-item-id="authority"]').get_attribute("href")
		parts = urlsplit(website)
		website = f"{parts.scheme}://{parts.netloc}"
		return website
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

def debug_info(name, address, website, phone, emails):
	print(f'{"Name:":<8} {name}')
	print(f'{"Address:":<8} {address}')
	print(f'{"Website:":<8} {website}')
	print(f'{"Phone:":<8} {phone}')
	print(f'{"Emails:":<8} {emails}')
	print(f'{"":->64}')
	print()

def scrape_new_business():
	# get already scraped businesses
	old_businesses = get_old_businesses_pandas()

	# get the first new business that was not previously scraped
	business, label = find_new_business(old_businesses)

	# if not new businesses found, scroll down the page to load more
	if not business:
		scroll_down_up_down()
		return

	# google maps is bugged: scroll a bit the screen and try clicking again if needed
	if not click_on_listing(business):
		return

	sleep(2)
	
	card_element = get_card_element(business)

	name = scrape_name(card_element)
	if name != label: return

	address = scrape_address(card_element)
	website = scrape_website(card_element)
	phone = scrape_phone(card_element)
	emails = scrape_emails(website)
	# s_emails = ' '.join(emails)

	debug_info(name, address, website, phone, emails)

	global csv_sep
	string_to_write = ''
	string_to_write += f'{name}{csv_sep}'
	string_to_write += f'{address}{csv_sep}'
	string_to_write += f'{website}{csv_sep}'
	string_to_write += f'{phone}{csv_sep}'
	string_to_write += f'{emails}\n'

	with open('document.csv', 'a', encoding="utf-8") as f:
		f.write(string_to_write)

	
######################################################################################
# MAIN
######################################################################################
open_browser()
search_map()
scrape_new_business()

for i in range(5):
	scrape_new_business()


main()

quit()

'''
search_text = sys.argv[1]
search_text = search_text.replace(' ', '+')
driver.get(f'https://www.google.com/maps/search/{search_text}')
'''

