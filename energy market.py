import socket
import signal
import os
import sys 
import time
import struct
import random
import sysv_ipc
import concurrent.futures
import multiprocessing
from multiprocessing import Process, Value, Array, Lock
from threading import Thread

"""
message queue type:
type = 1: the lack of enegy
type = 2: tell no enegy, the energy sent
"""

def noenegy(n, nhomes):
	i = 0
	while i < nhomes:
		i+=1
		keyother = i+10*i+100*i
		if i != n+1:
			try:
				mq_connect = sysv_ipc.MessageQueue(keyother)
			except sysv_ipc.ExistentialError:
				print("Cannot connect to message queue", keyother, ", terminating.")
				sys.exit(1)
			mq_connect.send(b"no enegy left", type = 2)

def home(homes_info):
	#get weather
	lock.acquire()
	temperature = weather.value
	lock.release()
	
	#get home info
	n = homes_info[0]
	nhomes = homes_info[2]
	month = homes_info[3]
	key = (n+1)+10*(n+1)+100*(n+1)
	
	"""three modes of home: 1 = always give; 2 = always sell; 3 = sell when no one wants energy"""
	mode = homes_info[1][0]
	
	prod = homes_info[1][1]
	cons = homes_info[1][2]
	if temperature <= 10 or temperature >= 20:
		cons = cons + random.randint(20, 50)
	
	rest_before = rests[n]
	rest = prod - cons + rests[n]
	print(f"home {n+1}: \n mode {mode} \n production: {prod} \n consumption: {cons} \n energy stored: {rest_before} \n rest: {rest}")

	#connect to my message queue
	try:
		mq = sysv_ipc.MessageQueue(key)
	except sysv_ipc.ExistentialError:
		sys.exit(1)
	
	#rest < 0, receive enegy
	n_noenegy = 0
	send_noenegy = False
	while rest < 0 and n_noenegy < nhomes-1:
		#tell others that no enegy left
		if send_noenegy == False:
			noenegy(n, nhomes)
			send_noenegy = True
		
		#send "need" to message queue
		dm = str(rest)
		m = dm.encode()
		mq.send(m, type = 1) 
		m, t = mq.receive(type = 2)
		dm = m.decode()
		while dm == "no enegy left" and n_noenegy < nhomes-1:
			n_noenegy += 1
			if n_noenegy < nhomes-1:
				m, t = mq.receive(type = 2)
				dm = m.decode()
		if dm != "no enegy left":
			rest = float(dm)
			print(f"home {n+1}: rest: {rest}")
				
	#tell others that I don't need enegy	
	for tell_home in range(nhomes):
		mq.send(b"0", type = 1)
	
	enough = 0	
	
	#rest > 0, give enegy
	while rest > 0 and enough < nhomes-1:
		
		#check in other message queues to find "need"
		if mode in [1, 3]:
			#connect to others' message queue
			i = 0
			while i < nhomes:
				i+=1
				keyother = i+10*i+100*i
				if keyother != key:
					try:
						mq_con = sysv_ipc.MessageQueue(keyother)
					except sysv_ipc.ExistentialError:
						print("Cannot connect to message queue", keyother, ", terminating.")
						sys.exit(1)
						
					#receive and send
					if rest != 0:
						m, t = mq_con.receive(type = 1)
						dm = m.decode()
						need = float(dm)
						if need == 0:
							enough += 1
						else:
							if need + rest < 0:
								need += rest
								rest = 0
							else:
								rest += need
								need = 0
								enough += 1
							dm = str(need)
							m = dm.encode()
							mq_con.send(m, type = 2)
		elif mode == 2:
			noenegy(n, nhomes)
			break;





	to_market = 0
	buy_sell = 0				
	if rest == 0 and send_noenegy == False:
		noenegy(n, nhomes)
		to_market = 0
		buy_sell = 0
	if rest<0:
		buy_sell = 0
		to_market = -rest
		rest = 0
	if rest>0 and mode in [2, 3]:
		buy_sell = 1
		to_market = rest
		rest = 0
	while True:	
		try:
			client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			client.connect(('localhost', 6666+month))

			# Communication with market
			dataf = struct.pack('!f', to_market)
			client.send(buy_sell.to_bytes(1,byteorder='little'))
			client.sendall(dataf)
			print('home',n+1,':',client.recv(1024))
			client.send(b'end')
			break
		except ConnectionRefusedError:
			time.sleep(0.1)

	
	rests[n]=rest


def handle_client(client_socket,totalBuy,totalSell):
	while True:
		request = client_socket.recv(1024)
		if not request:
			print("market: no request !!! ")
			break
		elif request != b'end' :
			buy_sell=int.from_bytes(request[0:1],byteorder='little')
			data = struct.unpack('!f', request[1:])[0]
			if buy_sell==1:
				client_socket.send(b'you are selling your energy on market')
				totalSell.append(data)
			elif buy_sell==0:
				if data == 0:
					client_socket.send(b'you visited the market but haven\'t bought any energy')
				else:
					client_socket.send(b'you have bought your energy from market')
				totalBuy.append(data)

		else:
			if request==b"end":
				break
	client_socket.close()


def sum(tab):
	res = 0
	for i in range(len(tab)):
		res += tab[i]
	return res


def market(month):

	totalBuy=[]
	totalSell=[]
	
	#set up external event
	signal.signal(signal.SIGUSR1, handler)
	
	external_event = Process(target=set_external, args=())
	external_event.start()
	external_event.join()
	
	external = {
		0:{"name":"no external event!", "price":1}, 
		1:{"name":"diplomatic tension !!!", "price":1.001}, 
		2:{"name":"social unrest !!!", "price":1.005}, 
		3:{"name":"fuel shortage !!!", "price":1.01}
	}
	
	print("\n\nmarket: external event: ", external[event.value]["name"], "\n\n")
	
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
		server.bind(('localhost', 6666+month))
		server.listen(3)
		i=0
		for i in range(5):
			client_socket, _ = server.accept()
			client_thread = Thread(target=handle_client, args=(client_socket,totalBuy,totalSell))
			client_thread.start()
			while client_thread.is_alive():
				time.sleep(0.2)
		print("\n\n-----report of this month-----")
		print('energy total on sell by home:',sum(totalSell))
		print('energy total sold to home:',sum(totalBuy))
		if month == 1:
			pricemonth = 20+0.001*sum(totalBuy)-0.001*sum(totalSell)
		else:
			pricemonth = 0.99*priceyearly[(month-2)%12]+0.001*sum(totalBuy)-0.001*sum(totalSell)
		pricemonth *= external[event.value]["price"]
		print("price of this month:",pricemonth)
		priceyearly[(month-1)%12]=pricemonth
		print('priceyearly',priceyearly[:])
		time.sleep(2)
		
def handler(sig, frame):
	event_number = random.randint(1, nevents.value)
	event.value = event_number
	
	os.kill(ex_event_pid.value, signal.SIGKILL)
	
def set_external():
	number = random.randint(1, 100)
	if number <= 30:
		ex_event_pid.value = os.getpid()
		os.kill(os.getppid(), signal.SIGUSR1)
		while True:
			time.sleep(1)
			
			
def weatherfonc(weather,month):
	dict_weather = {
		1:random.randint(1,7), 
		2:random.randint(1,8), 
		3:random.randint(4,13), 
		4:random.randint(7,16), 
		5:random.randint(11,21), 
		6:random.randint(14,24), 
		7:random.randint(16,27), 
		8:random.randint(16,27), 
		9:random.randint(13,23), 
		10:random.randint(9,17), 
		11:random.randint(4,11), 
		12:random.randint(2,7)
	}
	
	weather.value = dict_weather[(month-1)%12+1]

	print('weather decide:',weather.value)


if __name__ == "__main__":

	nhomes = 5
	priceyearly= Array('f',range(12))
	rests = Array('d', range(nhomes)) #to store the rest of energy of (time-1)
	for i in range(nhomes):
		rests[i] = 0
	
	#set up production, consumption and mode
	mode = [random.randint(1, 3) for i in range(nhomes)]
	prods = [random.uniform(20, 99) for i in range(nhomes)]
	cons = [random.uniform(20, 99) for i in range(nhomes)]
	
	#init external_event
	nevents = Value('i', 3) 
	event = Value('i', 0)
	ex_event_pid = Value('i', 0)
	
	#init weather
	weather = Value('i', 0)
	lock = Lock()
	
	with multiprocessing.Pool(processes = nhomes+1) as pool:
		month = 12
		i = 1
		while i <= month:
			homes_info = [ (nbr, [mode[nbr], prods[nbr], cons[nbr]], nhomes, i) for nbr in range(nhomes) ]
			
			print(f"----------month {i}----------")
			weatherfonc(weather, i)

			#create market
			p_market = Process(target = market, args = (i, ))
			p_market.start()

			#create message queues
			message_queue = []
			for n in range(nhomes):
				key = (n+1)+10*(n+1)+100*(n+1)
				try:
					message_queue.append( sysv_ipc.MessageQueue(key, sysv_ipc.IPC_CREX) )
				except sysv_ipc.ExistentialError:
					#if existed, remove and create new one
					message_queue.append( sysv_ipc.MessageQueue(key) )
					message_queue[len(message_queue)-1].remove()
					message_queue[len(message_queue)-1] = sysv_ipc.MessageQueue(key, sysv_ipc.IPC_CREX)

			pool.map(home, homes_info)
			
			p_market.join()
			print(f"\n\n----------home communicate of month {(i-1)%12+1} end----------\n\n")
			
			#close message queues
			for n in range(len(message_queue)):
				try:
					message_queue[n].remove()
				except sysv_ipc.ExistentialError:
					print(f"The queue {n+1} no longer exists")
			i+=1
		
			
			
			
