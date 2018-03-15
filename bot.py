#!/usr/bin/python3
import sys
from telepot.loop import MessageLoop
import telepot
import time
import sqlite3
import re

conn = sqlite3.connect('database.sqllite3', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS CHAT_ID
						(id)''')

def handle(msg):
	chat_id = msg['chat']['id']
	command = msg['text']
	print(chat_id, command)

	if command == '/start_gaz_bot':
		cursor.execute("SELECT * FROM CHAT_ID WHERE id=%d"% (int(chat_id)))
		check = cursor.fetchall()
		if  len(check) == 0:
			cursor.execute("INSERT INTO CHAT_ID (id) VALUES (%d)"% (int(chat_id)))
			conn.commit()
			print('dobavlen')
	if command == '/stop_gaz_bot':
		cursor.execute("DELETE FROM CHAT_ID WHERE id=%d"% (int(chat_id)))
		conn.commit()
		check = cursor.fetchall()
		print(check, 'udalen')
		cursor.execute("SELECT * FROM CHAT_ID WHERE id=%d"% (int(chat_id)))
		conn.commit()
		check = cursor.fetchall()
		print(check, 'udalen')





def Sender(message):

	bot = telepot.Bot('BOT_API')

	cursor.execute("SELECT * FROM CHAT_ID")
	show = cursor.fetchall()
	for chat_id in show:
		chat_id = re.sub(r',', '', str(chat_id))
		chat_id = re.sub(r'\(', '', str(chat_id))
		chat_id = re.sub(r'\)', '', str(chat_id))
		print(chat_id)
		bot.sendMessage(chat_id, '%s'% message)

bot = telepot.Bot('BOT_API')

MessageLoop(bot, handle).run_as_thread()

while 1:
	time.sleep(10)

