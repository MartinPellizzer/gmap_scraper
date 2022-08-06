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
import pandas as pd

import sys
import csv

driver = None
num_operations = 5

def find_contact_url(url):
	contact_page = ''

	response = requests.get(url)
	soup = BeautifulSoup(response.text, 'lxml')

	for link in soup.find_all('a'):
		if 'contatti' in str(link).lower():
			link = link.get('href')
			contact_page = link
			print(link)
	
	return contact_page

def scrape_validate_emails():
	pass

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
			print(parts.netloc + ' --> ' + match.group())
			for domain in list_domains:
				if domain in match.group():
					emails.add(match.group())
					break
	except (requests.exceptions.MissingSchema, requests.exceptions.ConnectionError): 
		print('*** cant load page')
		return set()

	# contact page 1
	contact_page = find_contact_url(url)
	try:
		response = requests.get(contact_page)
		matches = re.finditer(regex_string, response.text)
		for match in matches:
			print(parts.netloc + ' --> ' + match.group())
			for domain in list_domains:
				if domain in match.group():
					emails.add(match.group())
					break
	except (requests.exceptions.MissingSchema, requests.exceptions.ConnectionError): 
		print('*** cant find contact link')
		pass
		
	# contact page 2
	last_resort_url = f'{url}/contatti'
	print(f'LAST RESORT: {last_resort_url}')
	try:
		response = requests.get(last_resort_url)
		matches = re.finditer(regex_string, response.text)
		for match in matches:
			print(parts.netloc + ' --> ' + match.group())
			for domain in list_domains:
				if domain in match.group():
					emails.add(match.group())
					break
	except (requests.exceptions.MissingSchema, requests.exceptions.ConnectionError):
		print('*** has no contact url')
		pass
		
	return emails

def get_new_business():
	todo = ''
	elements = driver.find_elements(By.XPATH, '//div[@role="article"]')

	for e in elements:
		id = e.get_attribute('aria-label')
		if id not in done:
			done.append(id)
			todo = e
			break

	return todo
	
def scroll_down_up_down():
	driver.find_element(By.XPATH, '//div[@role="feed"]').send_keys(Keys.PAGE_DOWN)
	sleep(2)
	driver.find_element(By.XPATH, '//div[@role="feed"]').send_keys(Keys.PAGE_UP)
	sleep(2)
	driver.find_element(By.XPATH, '//div[@role="feed"]').send_keys(Keys.PAGE_DOWN)
	sleep(2)
	


done = []

try: os.remove('document.csv')
except OSError: pass

try:
	with open('document.csv', mode='r') as f:
		csv_reader = csv.reader(f, delimiter=',')
		for row in f:
			info = row.split(';')
			done.append(info[0])
except:
	pass




def open_browser():
	global driver
	driver = webdriver.Chrome('./chromedriver')
	driver.maximize_window()
	driver.get('https://www.google.com')
	sleep(2)
	driver.find_element(By.XPATH, '//div[text()="Rifiuta tutto"]').click()
	sleep(2)
open_browser()


search_text = sys.argv[1]
search_text = search_text.replace(' ', '+')
print(search_text)
driver.get(f'https://www.google.com/maps/search/{search_text}')
#driver.get(f'https://www.google.com/maps/search/azienda+vinicola+padova')

for i in range(num_operations):
	print(f'SCRAPING: {i}/{num_operations}')
	sleep(2)

	# get the first new business found
	todo = get_new_business()

	# if not new business found, try to load more businesses
	if not todo:
		print('---------------------------------------------')
		print('nothing new...')
		print('---------------------------------------------')
		print()
		scroll_down_up_down()
		continue
	
	aria_label = todo.get_attribute('aria-label')
	print(aria_label)

	try: todo.click()
	except:
		scroll_down_up_down()
		try: todo.click()
		except: continue
	sleep(2)

	name = ''
	phone = ''
	address = ''
	website = ''
	emails = []

	try: element_main = todo.find_elements(By.XPATH, '//div[@role="main"]')[1]
	except: continue

	try: name = element_main.find_element(By.XPATH, './/h1').text
	except: pass
	
	if name != aria_label: continue

	try: address = element_main.find_element(By.XPATH, './/button[@data-item-id="address"]').text
	except: pass
	try: 
		website = element_main.find_element(By.XPATH, './/a[@data-item-id="authority"]').get_attribute("href")
		parts = urlsplit(website)
		website = f"{parts.scheme}://{parts.netloc}"
	except: pass
	try: phone = element_main.find_element(By.XPATH, './/button[contains(@data-item-id, "phone")]').text
	except: pass

	emails = scrape_emails(website)
	
	print(name)
	print(address)
	print(website)
	print(phone)
	print(emails)
	print()

	s_emails =' '.join(emails)

	divider = ';'

	string_to_write = f'{name}{divider}{address}{divider}{website}{divider}{phone}{divider}{s_emails}\n'
	string_to_write = string_to_write.replace('"', '')

	with open('document.csv','a', encoding="utf-8") as f:
		f.write(string_to_write)

#driver.close()
