import os
import asyncio
import aiohttp
import json
from decouple import config
from bs4 import BeautifulSoup

BASE_URL = 'https://www.urionlinejudge.com.br'
LOGIN = BASE_URL + '/judge/en/login'
ALLPROBLEMS = BASE_URL + '/judge/en/problems/all'

form_data = {
	'email': config('EMAIL', ''),
	'password': config('PASSWORD', ''),
	'remember_me': config('REMEMBER_ME', 0),
	'_csrfToken': '', 
	'_Token[fields]': '40aa819a1f388146da80ca67cdaf803b21ac5e01%3A',
	'_Token[unlocked]': '',
}

def get_csrfToken(soup):
	return soup.form.find_all('input')[1].get('value')

async def fetch(session, url):
	async with session.get(url) as response:
		return await response.text()
		
async def main():
	assert form_data['email'] != '', 'Missing URI email! Please create a .env file.'
	assert form_data['password'] != '', 'Missing URI password! Please create a .env file.'

	async with aiohttp.ClientSession() as session:
		login_page = await fetch(session, LOGIN)
		soup = BeautifulSoup(login_page, 'html.parser')
		
		csrf = get_csrfToken(soup)
		form_data['_csrfToken'] = csrf
		
		await session.post(LOGIN, data=form_data)
		
		allproblems = await fetch(session, ALLPROBLEMS)
		
		if '/judge/en/logout' in allproblems or '/judge/pt/logout' in allproblems or '/judge/es/logout' in allproblems:
			print('Login was successful.')
		else:
			print('Login failed.')
			exit(1)

		soup = BeautifulSoup(allproblems, 'html.parser')

		num_pages = int(soup.find('div', {'id' : 'table-info'}).text.split(' ')[2])

		problems = []

		for i in range(1, num_pages + 1):
			print(f'Page: {i}/{num_pages}')

			allproblems = await fetch(session, ALLPROBLEMS + f'?page={i}')
			
			soup = BeautifulSoup(allproblems, 'html.parser')

			rows = soup.find_all('tr')

			for row in rows:
				tds = row.find_all('td')

				if len(tds) == 7:
					problem = {
						'id'       : tds[0].text.strip(),
						'name'     : tds[2].text.strip(),
						'category' : tds[3].text.strip(),
						'solved'   : tds[5].text.strip().replace(',', ''),
						'level'    : tds[6].text.strip(),
					}

					problems.append(problem)

		with open('problems.json', 'w') as file:
			json.dump(problems, file, indent=4)

if __name__ == '__main__':
	loop = asyncio.get_event_loop()
	loop.run_until_complete(main())
	loop.close()
