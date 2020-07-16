from pysnmp.hlapi import *
from pysnmp.entity.rfc3413.oneliner import cmdgen


cmdGen = cmdgen.CommandGenerator()

sysName = "1.3.6.1.2.1.1.5.0"
sysDescr = "1.3.6.1.2.1.1.1.0"
sysContact = "1.3.6.1.2.1.1.4.0"
sysLocation = "1.3.6.1.2.1.1.6.0"
community = '4CM1'
port = '161'

def get_routers_info():

	lista_ips = get_ips_from_file("routers.txt")
	lista_info = []

	for x in lista_ips:
		
		errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(
			cmdgen.CommunityData(community),
			cmdgen.UdpTransportTarget((x, port)),
			sysName,
			sysLocation, 
			sysContact,
			sysDescr

		)

		if errorIndication:
			print(errorIndication)
		else:
			if errorStatus:
				print('%s en %s' % (
					errorStatus.prettyPrint(),
					errorIndex and varBinds[int(errorIndex)-1] or '?'
					)
				)
			else:
				
				lista_aux = []
				for val  in varBinds:
					str_val = str(val)
					lista_aux.append(str_val[str_val.find('=')+2 : len(str_val)])

				lista_info.append(lista_aux)

	return lista_info	

def get_ips_from_file(file_path):
	file1 = open(file_path, 'r')

	Lines = file1.readlines()

	ips = []

	for x in Lines:
		ips.append(x[x.find(':')+1:len(x)-1])

	return ips

def get_ip_from_file(file_path, router_name):
	file1 = open(file_path, 'r')

	Lines = file1.readlines()

	ips = []
	aux = ""

	for x in Lines:
		if x.find(router_name) != -1:
			aux = x[x.find(':')+1:len(x)-1]

	return aux

def set_router_name(router_name, new_name):
	_ip = get_ip_from_file("routers.txt", router_name)

	errorIndication, errorStatus, errorIndex, varBinds = cmdGen.setCmd(
		cmdgen.CommunityData(community),
		cmdgen.UdpTransportTarget((_ip, port)),
		ObjectType(ObjectIdentity(sysName), OctetString(new_name))

	)

	if errorIndication:
		print(errorIndication)
	else:
		if errorStatus:
			print('%s en %s' % (
				errorStatus.prettyPrint(),
				errorIndex and varBinds[int(errorIndex)-1] or '?'
				)
			)
		else:
				
			lista_aux = []
			for val  in varBinds:
				print(str(val))
