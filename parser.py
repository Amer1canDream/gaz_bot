#!/usr/bin/python3

from selenium import webdriver
from bs4 import BeautifulSoup
import sqlite3
import re
from datetime import datetime, date
import time
import telepot
import sys


'''
Функция парсера.

Парсит данные, записывает их в базу, формирует сообщение для телеграма. Необходимо указать путь к webdriver. В моем случае это /home/artem/chromedriver
'''
def Parser():


	'''
	Парсим данные с помощью selenium
	'''

	options = webdriver.ChromeOptions()
	options.add_argument("headless")
	
	driver = webdriver.Chrome('/home/artem/chromedriver', chrome_options=options) 

	driver.get("http://spimex.com/markets/oil_products/trades/")

	results = driver.find_elements_by_tag_name('table')

	kusok =	results[0].get_attribute("outerHTML")
	
	
	tr_tags = BeautifulSoup(kusok, "lxml").find('tbody').find_all('tr')

	'''
	Вытаскиваем то, что содержит Конденсат газовый
	и его значения.
	'''
	for tr in tr_tags[::2]:
		name = tr.find('a', target='_blank').text
		
		if not name.find('ДТ ЕВРО'):
			id = tr['id']
			
			green = tr.find('span', class_='green')
			if green is None:
				green_amount = 0
				green = 0
			else:
				green_amount = green.findNext('span').text
				green = re.sub(r'\D', '', green.text)
				green_amount = re.sub(r'\D', '', green_amount)


			red = tr.find('span', class_="red")
			if red is None:
				red_amount = 0
				red = 0
			else:
				red_amount = red.findNext('span').text
				red_amount = re.sub(r'\D', '', red_amount)
				red = re.sub(r'\D', '', red.text)

			dealings_and_amount = tr.find('td', style='text-align: right;')
			count = dealings_and_amount.findNext('td')
			npz = count.findNext('td')
			dealings_and_amount = dealings_and_amount.text
			dealings_and_amount = re.sub(r'\s+', '', dealings_and_amount).split('.')

			if len(dealings_and_amount) == 1:
				dealings = 0
				amount = 0
				count = 0
				npz = 0
			else:
				dealings = int(re.sub(r'\D', '', dealings_and_amount[0]))
				amount = re.sub(r'\D', '', dealings_and_amount[1])
				count = count.text
				npz = npz.text
			
			'''
			Ищет совпадение найденного с тем, что есть в базе, если не находит, то записывает и шлет сообщение о спросе\предложении.
			'''
			
			values = (id, name, green, green_amount, red, red_amount, dealings, amount, count, npz)
			search_in_db = ''
			cursor.execute("SELECT * FROM OFFERS WHERE id=? AND name=?", (id, name))
			search_in_db = cursor.fetchall()
			
			if  len(search_in_db) == 0:
				
				cursor.execute("INSERT INTO OFFERS (id, name, green, green_amount, red, red_amount, dealings, amount, count, npz) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",	(id, name, green, green_amount, red, red_amount, dealings, amount, count, npz))
				conn.commit()

				if (green != 0 and red != 0):
					value = ('Предложение/спрос id - %s, name - %s, Предложение -  %d р. %d т., Спрос - %d р. %d т.'% id, name, green, green_amount, red, red_amount)
					Bot(value)
				elif (green == 0 and red == 0):
					value = ('Еще без предложения id - %s, name - %s,'% (id, name))
					Bot(value)
				elif ( green == 0 and red != 0):
					value = ('Предложение id - %s, name - %s, %d р. %d т.,'% (id, name, int(red), int(red_amount)))
					Bot(value)
				elif ( green != 0 and red == 0 ):
					value = ('Спрос id - %s, name - %s, %d р. %d т.,'% (id, name, int(green), int(green_amount)))
					Bot(value)

			else:
				
				'''
				Если есть совпадения, то проверяет значения суммы сделок, если они расходятся, то шлет сообщение о совершенной сделке и перезаписывает.

				'''

				cursor.execute("SELECT dealings FROM OFFERS WHERE id=? AND name=?", (id, name))
				test_dealings = cursor.fetchall()
				test_dealings = re.sub(r'\D', '', str(test_dealings))
				test_dealings = int(test_dealings)
				if dealings > test_dealings:
					cursor.execute("SELECT amount FROM OFFERS WHERE id=? AND name=?", (id, name))
					old_amount = cursor.fetchall()
					cursor.execute("SELECT count FROM OFFERS WHERE id=? AND name=?", (id, name))
					old_count = cursor.fetchall()
					
					cursor.execute("DELETE FROM OFFERS WHERE id=? AND name=?", (id, name))
					cursor.execute("INSERT INTO OFFERS (id, name, green, green_amount, red, red_amount, dealings, amount, count, npz) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",	(id, name, green, green_amount, red, red_amount, dealings, amount, count, npz))
					conn.commit()
					
					old_count = re.sub(r'\D', '', str(old_count))
					old_amount = re.sub(r'\D', '', str(old_amount))

					deal_difference = (int(dealings) - int(test_dealings))
					count_difference = (int(count) - int(old_count))
					amount_difference = (int(amount) - int(old_amount))
					value = ('Зафиксированы сделки. id - %s, name - %s, Сумма - %d, Количество сделок - %d, Тоннаж - %d'% (id, name, int(deal_difference), int(count_difference), int(amount_difference)))
					Bot(value)

	driver.quit()


'''
Функция отправки сообщения, необходимо подставить токен своего бота и чат id
'''

def Bot(value):

	bot = telepot.Bot('BOT_API')

	cursor.execute("SELECT * FROM CHAT_ID")
	show = cursor.fetchall()
	for chat_id in show:
		chat_id = re.sub(r',', '', str(chat_id))
		chat_id = re.sub(r'\(', '', str(chat_id))
		chat_id = re.sub(r'\)', '', str(chat_id))
		bot.sendMessage(chat_id, '%s'% value)



	

if __name__== "__main__":
	
	'''
	Создает базу, таблицы, а также удаляет их при каждом новом запуске скрипта. Скрипт работает до 15.00 по Челябинскому (время проверяется).
	Запуск скрипта необходимо настроить на кроне. Каждые 5 секунд осуществляется запрос к сайту (Вызывается функция Parser). При наступлении 15.00
	собираются все значения сделок и высылается в чат.

	'''

	hour = ''
	minutes = ''
	
	hour_stop = 15
		
	conn = sqlite3.connect('database.sqllite3')
	cursor = conn.cursor()
	cursor.execute("DELETE FROM OFFERS")
	
	cursor.execute('''CREATE TABLE IF NOT EXISTS OFFERS
						(id, name, green, green_amount, red, red_amount, dealings, amount, count, npz)''')

	
	while (hour != hour_stop):
		try:
			Parser()
			now = datetime.now()
		
			hour = now.hour
			time.sleep(5)
		except KeyboardInterrupt:
			sys.exit()
		except:
			value = 'Error, веряотно страничка долго формируется. Не стоит паниковать ;)'
			Bot(value)

	cursor.execute("SELECT dealings FROM OFFERS")
	s_dealings = cursor.fetchall()
	summ_dealings = 0
	
	cursor.execute("SELECT amount FROM OFFERS")
	s_amount = cursor.fetchall()
	summ_amount = 0 

	cursor.execute("SELECT count FROM OFFERS")
	s_count = cursor.fetchall()
	summ_count = 0

	for i in s_amount:
		i = re.sub(r'\D', '', str(i))
		i = int(i)
		
		summ_amount += i

	for i in s_count:
		i = re.sub(r'\D', '', str(i))
		i = int(i)
		
		summ_count += i


	for i in s_dealings:
		i = re.sub(r'\D', '', str(i))
		i = int(i)
		
		summ_dealings += i

	value = ('Всего совершено %d сделок на %d рублей, %d тонн'% (int(summ_count), int(summ_dealings), int(summ_amount)))
	Bot(value)
		