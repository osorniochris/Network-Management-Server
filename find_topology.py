import getpass
from pexpect import pxssh
from graphviz import Digraph

#funciones para checar si un router ya se visitó
def visitedBefore(interface, ints):
	ya = 0
	j = 0

	for i in ints:
		if ints[j][0] == interface:
			ya = 1
		j = j+1

	return ya

def repeated(interface, ints):
	ya = 0
	j = 0

	for i in ints:
		if str(ints[j]) == str(interface):
			ya = 1
		j = j+1

	return ya

#función que regresa a que router pertenece cada interfaz		
def get_origin(ip, tried_ints):
	aux = " "
	j=0

	for x in tried_ints:
		if tried_ints[j][0] == ip:
			aux = tried_ints[j][1]
		j = j+1

	return aux

#funcion principal
def get_topology():

	#datos conocidos
	username = 'cisco'
	password = 'cisco'
	gateway = '192.168.0.17'
	gateway_id =''

	#arreglos de apoyo
	ips = []
	ips_puras = []
	tried_ints = []
	routers = []
	topologia= []

	#Primera conexión con el gateway 
	child = pxssh.pxssh()
	child.login(gateway, username.strip(), password.strip(), auto_prompt_reset=False)

	#obtener las primeras ips de salto
	child.sendline('show ip route | include via')
	child.expect('#')
	a = str(child.before, 'utf-8') #se recupera texto
	saltos = a.splitlines()
	idR = saltos[len(saltos)-1] #id del router
	gateway_id = idR

	tried_ints.append([gateway, idR])#relación de pertenencia int-router

	saltos.pop(0)
	saltos.pop(len(saltos)-1)

	for ip in saltos:
		ips.append(ip[ip.rfind("via ")+4: ip.find(',')])#se sacan las puras direcciones

	child.sendline('exit')

	ips = list(dict.fromkeys(ips)) #evitar repeticiones


	for aux in ips:
		if visitedBefore(str(aux), tried_ints) == 1: #evitar ciclos
			break
		
		child = pxssh.pxssh()
		child.login(aux, username.strip(), password.strip(), auto_prompt_reset=False)
		child.sendline('show ip route | include via')
		child.expect('#')
		a = str(child.before, 'utf-8')
		saltos = a.splitlines()
		idR = saltos[len(saltos)-1]

		routers.append(idR)

		tried_ints.append([aux, idR]) #se crean las relaciones router-int

		saltos.pop(0)
		saltos.pop(len(saltos)-1)

		for ip in saltos:
			if repeated(ip[ip.rfind("via ")+4: ip.find(',')], ips) == 0:
				ips.append(ip[ip.rfind("via ")+4: ip.find(',')])
			
		print("Cargando...")
		child.sendline('exit')

	routers = list(dict.fromkeys(routers))

	ps = Digraph(name='topologia', node_attr={'shape': 'box', 'color':'#F5BDA2', 'style':'filled'}, comment="Topología de la red", format='png', engine='sfdp')

	file1 = open("interfaces.txt", "w")

	for aux in ips:
		child = pxssh.pxssh()
		child.login(aux, username.strip(), password.strip(), auto_prompt_reset=False)
		child.sendline('show ip route | include via')
		child.expect('#')
		a = str(child.before, 'utf-8')
		saltos = a.splitlines()
		idR = saltos[len(saltos)-1]

		existe =  False#ver si el Router ya se agrego al diagrama o no
		for w in routers:
			if w == idR:
				existe = True

		if existe:
			topologia.append([idR, aux])
			routers.remove(idR)

			saltos.pop(0)
			saltos.pop(len(saltos)-1)

			ips_puras = []

			for ip in saltos:
				ips_puras.append(ip[ip.rfind("via ")+4: ip.find(',')])


			ips_puras = list(dict.fromkeys(ips_puras))

			ps.node(idR) #se agrega cada Router como nodo
			for x in ips_puras:
				ps.edge(idR, get_origin(x, tried_ints), label= x, fontsize='10') #creación de aristas
				file1.write(x+"\n")

		child.sendline('exit')

		if len(routers) == 0:
			break
	file1.write(gateway+"\n")
	file1.close()

	#archivo de ips
	file = open("routers.txt", "w")
	for i in topologia:
		file.write(i[0]+":"+i[1]+"\n")
	file.close()

	#se imprime el grafo y se crea la imagen
	ps.attr('node', shape='diamond', style='filled', color='lightgrey')
	ps.node("MV") #Nodo de la MV
	ps.edge("MV", gateway_id, label= gateway, fontsize='10') #creación de arista con gateway


	print("\nTopología generada\n")
	ps.render("static/imgs/topologia")
