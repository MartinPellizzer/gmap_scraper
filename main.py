from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from time import sleep

import re
import requests
from urllib.parse import urlsplit
from collections import deque
from bs4 import BeautifulSoup
import pandas as pd

driver = webdriver.Chrome('./chromedriver')

driver.get('https://www.google.com')
sleep(3)
driver.find_element(By.XPATH, '//div[text()="Rifiuta tutto"]').click()

sleep(3)
driver.get('https://www.google.com/maps/search/cantine+near+me')
#driver.get('https://www.google.com/search?q=cantine+near+me')

elements = driver.find_elements(By.XPATH, '//div[@role="article"]')
print(len(elements))
print()

def scrape_emails(url):
	parts = urlsplit(url)
	base_url = f"{parts.scheme}://{parts.netloc}"

	try: response = requests.get(base_url)
	except (requests.exceptions.MissingSchema, requests.exceptions.ConnectionError): return ''

	# return re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', response.text)
	
	# print(re.findall(r'[a-zA-Z.]+@[a-zA-Z]+\.(com)', response.text)

	matches = re.finditer(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.(com|net|edu|it|eu)', response.text)

	emails = set()
	for match in matches:
		emails.add(match.group())

	return emails

websites = []
for i, e in enumerate(elements):
	if i > 10: break
	e.click()
	sleep(5)

	name = ''
	phone = ''
	address = ''
	website = ''
	emails = []

	element_main = e.find_elements(By.XPATH, '//div[@role="main"]')[1]
	try: name = element_main.find_element(By.XPATH, './/h1').text
	except: pass
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

	# driver.find_element(By.XPATH, '//div[@role="feed"]').send_keys(Keys.PAGE_DOWN)
