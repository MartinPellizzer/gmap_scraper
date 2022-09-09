
def search_map(business_type, cities, districts):
	search_text = f'{business_type} {cities} {districts}'
	print(search_text.lower())
	search_text = search_text.replace(' ', '+')
	driver.get(f'https://www.google.com/maps/search/{search_text}')
	
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

			
def get_old_businesses():
	global sep
	if not os.path.isfile('document.csv'): return []

	names = []
	with open('document.csv', 'r', encoding="utf-8") as f:
		lines = f.readlines()
		for line in lines:
			names.append(line.split(sep)[0])
	return names

def create_csv():
	with open('document.csv', 'w', encoding='utf-8') as f:
		f.write(f'name{sep}address{sep}website{sep}phone{sep}emails{sep}district\n')


def get_cities():
	global sep
	if os.path.isfile('lista_comuni_veneto.csv'):
		df = pandas.read_csv('lista_comuni_veneto.csv', sep=',', encoding="ISO-8859-1")
		return df['city'].to_list()
	else: 
		return []
		

def get_districts():
	global sep
	if os.path.isfile('lista_comuni_veneto.csv'):
		df = pandas.read_csv('lista_comuni_veneto.csv', sep=',', encoding="ISO-8859-1")
		return df['district'].to_list()
	else: 
		return []

		
def get_done():
	global sep
	if os.path.isfile('lista_comuni_veneto.csv'):
		df = pandas.read_csv('lista_comuni_veneto.csv', sep=',', encoding="ISO-8859-1")
		return df['done'].to_list()
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
		
		
def scrape_website(e):
	try: 
		website = e.find_element(By.XPATH, './/a[@data-item-id="authority"]').get_attribute("href")
		# parts = urlsplit(website)
		# website = f"{parts.scheme}://{parts.netloc}"
		return website
	except: return ''


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
	except: 
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
	except: 
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
	except:
		# print('*** has no contact url')
		pass
		
	return emails

    
def search_map():
	driver.get(f'https://www.google.com/maps/search/azienda+vinicola+padova')
	

def scrape_new_business():
	# get already scraped businesses
	old_businesses = get_old_businesses_pandas()

	# get the first new business that was not previously scraped
	business, label = find_new_business(old_businesses)

	# if not new businesses found, scroll down the page to load more
	if not business:
		try: scroll_down_up_down()
		except: return 'skip_search'
		return 'ok'

	# google maps is bugged: scroll a bit the screen and try clicking again if needed
	if not click_on_listing(business):
		return 'ok'

	sleep(2)
	
	card_element = get_card_element(business)

	name = scrape_name(card_element)
	if name != label: return 'ok'

	address = scrape_address(card_element)
	website = scrape_website(card_element)
	phone = scrape_phone(card_element)
	emails = scrape_emails(website)
	s_emails = ' '.join(emails)

	debug_info(name, address, website, phone, s_emails)

	global sep
	string_to_write = ''
	string_to_write += f'{name}{sep}'
	string_to_write += f'{address}{sep}'
	string_to_write += f'{website}{sep}'
	string_to_write += f'{phone}{sep}'
	string_to_write += f'{s_emails}\n'

	# with open('document.csv', 'a', encoding="utf-8") as f:
	# 	f.write(string_to_write)