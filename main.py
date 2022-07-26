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

driver = webdriver.Chrome('./chromedriver')
driver.maximize_window()
driver.get('https://www.google.com')
sleep(2)
driver.find_element(By.XPATH, '//div[text()="Rifiuta tutto"]').click()
sleep(2)

def scrape_emails(url):
	parts = urlsplit(url)
	base_url = f"{parts.scheme}://{parts.netloc}"

	try: response = requests.get(base_url)
	except (requests.exceptions.MissingSchema, requests.exceptions.ConnectionError): return ''

	matches = re.finditer(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.(com|net|edu|it|eu)', response.text)

	emails = set()
	for match in matches:
		emails.add(match.group())

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
	


try: os.remove('document.csv')
except OSError: pass

driver.get('https://www.google.com/maps/search/azienda+vitivinicola+friuli')
#driver.get('https://www.google.com/search?q=cantine+near+me')

done = []
for i in range(20):
	sleep(2)

	# get the first new business found
	todo = get_new_business()

	# if not new business found, try to load more businesses
	if not todo:
		print('nothing new...')
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
	try: website = element_main.find_element(By.XPATH, './/a[@data-item-id="authority"]').get_attribute("href")
	except: pass
	try: phone = element_main.find_element(By.XPATH, './/button[contains(@data-item-id, "phone")]').text
	except: pass
	try: emails = scrape_emails(website)
	except: pass

	print(name)
	print(address)
	print(website)
	print(phone)
	print(emails)
	print()

	s_emails =' '.join(emails)

	divider = ';'

	with open('document.csv','a') as f:
		f.write(f'{name}{divider}{address}{divider}{website}{divider}{phone}{divider}{s_emails}\n')
