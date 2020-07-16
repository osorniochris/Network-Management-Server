from flask import Flask
from flask import render_template
from flask import flash
from flask import request
from flask_sqlalchemy import SQLAlchemy

from apscheduler.schedulers.background import BackgroundScheduler

import tkinter as tk
import tkinter.messagebox as mb

import find_topology as ft
import pysnmp_lib as pysnmp
import graph_interfaces as gi
import atexit

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///miRed.db'
app.secret_key = 'my_secret_key'

bd = SQLAlchemy(app)

#modelo de datos
class Dispositivo(bd.Model):
	__tablename__ = 'router'
	id = bd.Column('id', bd.Integer, primary_key=True)
	hostname = bd.Column('hostname', bd.String(80), primary_key=False)
	contact = bd.Column('contact', bd.String(80), primary_key=False)
	location = bd.Column('location', bd.String(80), primary_key=False)
	description = bd.Column('description', bd.String(200), primary_key=False)

	def __init__(self, id, hostname, contact, location, description):
		self.id = id
		self.hostname = hostname
		self.contact = contact
		self.location = location
		self.description = description

	def insert_router( _hostname, _contact, _location, _description):
		found = Dispositivo.query.filter_by(hostname = _hostname).first()
		aux = Dispositivo.query.all()
		new_id = len(aux) + 1

		if found is None:
			_router = Dispositivo(new_id, _hostname, _contact, _location, _description)
			bd.session.add(_router)
			bd.session.commit()

			print(str(_router.id)+" insertado")

	def update_name(_hostname, new_name):
		found = Dispositivo.query.filter_by(hostname = _hostname).first()
		found.hostname = new_name
		bd.session.commit()

	def delete_all():
		aux = Dispositivo.query.all()
		lon = len(aux)

		if lon > 0:
			for x in range(1,lon+1):
				w = Dispositivo.query.filter_by(id = x).first()
				bd.session.delete(w)
				bd.session.commit()
				print(str(x) +" eliminado")

	def get_all():
		return Dispositivo.query.order_by(Dispositivo.hostname).all()

#vistas
@app.route('/', methods=['GET', 'POST'])
def index(title='Home'):
	if request.method == 'POST':

		try:
			ft.get_topology()
			routers = pysnmp.get_routers_info()

			Dispositivo.delete_all()

			for x in routers:
				Dispositivo.insert_router(x[0], x[2], x[1], x[3])

		except Exception as e:
			print(e)
			flash("Error al actualizar", "red lighten-3 red-text text-darken-4")
		else:
			flash("Actualización de red completada", "green lighten-3 green-text text-darken-4")
			
	
	return render_template('index.html', title = title)

@app.route('/topologia', methods=['GET'])
def topologia(title='Topología'):
	return render_template('topologia.html', title = title)

@app.route('/dispositivos', methods=['GET'])
def dispositivos(title='Dispositivos'):
	current_routers = Dispositivo.get_all()

	return render_template('dispositivos.html', title = title, current_routers = current_routers)

@app.route('/monitoreo', methods=['GET'])
def monitoreo(title='Monitoreo de la Red'):
	#gi.generate_files()
	my_file = open("graficas.txt", 'r')
	lines = my_file.readlines()

	return render_template('monitoreo.html', title = title, lines = lines)

@app.route('/monitoreo/<router_name>/', methods=['GET'])
def monitoreo_router(title='Monitoreo de la Red', router_name="No se encontró la interfaz especificada"):
	_router_name = router_name+".svg"

	return render_template('monitoreo1.html', title = title, _router_name = _router_name)

@app.route('/editar', methods=['GET'])
def editar(title='Editar Router'):
	current_routers = Dispositivo.get_all()

	return render_template('editar.html', title = title, current_routers = current_routers)

@app.route('/editar/<hostname>', methods=['GET', 'POST'])
def nuevo_nombre(title='Cambiar nombre ', hostname="No se encontró el router"):
	if request.method == 'POST':

		try:	
			_new_name = request.form['new_name']
			print(_new_name)
			print(hostname)
			pysnmp.set_router_name(hostname, _new_name)

			ft.get_topology()
			Dispositivo.delete_all()
			
			routers = pysnmp.get_routers_info()
			for x in routers:
				Dispositivo.insert_router(x[0], x[2], x[1], x[3])

		except Exception as e:
			print(e)
			flash("Error al actualizar hostname", "red lighten-3 red-text text-darken-4")
		else:
			flash("Actualización de hostname completada", "green lighten-3 green-text text-darken-4")
		current_routers = Dispositivo.get_all()	
		
		return render_template('editar.html', title = "Editar Router", current_routers = current_routers)
	else:
		return render_template('new_name.html', title = title, hostname=hostname)

def update_graphs():
	gi.generate_files()

"""def interface_is_ok():
	if gi.check_interface_R3_R4() == False:
		print("[WARNING] Pérdida de paquetes entre R3 y R5 mayor al 60%")
		root = tk.Tk()
		root.title("WARNING")
		label = tk.Label(root, text="Pérdida de paquetes entre R3 y R5 mayor al 60%")
		label.pack(side="top", fill="both", expand=True, padx=20, pady=20)
		button = tk.Button(root, text="OK", command=lambda: root.destroy())
		button.pack(side="bottom", fill="none", expand=True)
		root.mainloop()"""



if __name__ == '__main__':
	#app.run(debug = True, port=8000)
	scheduler = BackgroundScheduler()
	scheduler.add_job(func=update_graphs, trigger="interval", seconds= 60)
	#scheduler.add_job(func=interface_is_ok, trigger="interval", seconds= 40)
	scheduler.start()
	atexit.register(lambda: scheduler.shutdown())	
	app.run(port=8000)

