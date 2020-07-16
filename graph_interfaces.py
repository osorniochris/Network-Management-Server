#!/usr/bin/python3
from pysnmp.entity.rfc3413.oneliner import cmdgen
import datetime
import pygal
import time
import tkinter as tk
import tkinter.messagebox as mb

cmdGen = cmdgen.CommandGenerator()

host = '192.168.0.17'
community = '4CM1'

# Hostname OID
system_name = '1.3.6.1.2.1.1.5.0'

# Interface OID
fa_in_oct = '1.3.6.1.2.1.2.2.1.10.1'
fa_in_uPackets = '1.3.6.1.2.1.2.2.1.11.1'
fa_out_oct = '1.3.6.1.2.1.2.2.1.16.1'
fa_out_uPackets = '1.3.6.1.2.1.2.2.1.17.1'
if_name = '1.3.6.1.2.1.31.1.1.1.1'


def snmp_query(host, community, oid):
    errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(
        cmdgen.CommunityData(community),
        cmdgen.UdpTransportTarget((host, 161)),
        oid
    )
    
    # Revisamos errores e imprimimos resultados
    if errorIndication:
        print(errorIndication)
    else:
        if errorStatus:
            print('%s at %s' % (
                errorStatus.prettyPrint(),
                errorIndex and varBinds[int(errorIndex)-1] or '?'
                )
            )
        else:
            for name, val in varBinds:
                return str(val)

def generate_files():
    
    file1 = open("interfaces.txt", 'r')
    file2 = open("graficas.txt", 'w')

    Lines = file1.readlines()

    
    for x in Lines:

        try:
            result = {}
            aux_time = datetime.datetime.today()
            result['Tiempo'] = aux_time.strftime("%b %d %Y %H:%M:%S")
            result['hostname'] = snmp_query(x, community, system_name)
            result['Fa_In_Octet'] = snmp_query(x, community, fa_in_oct)
            result['Fa_In_uPackets'] = snmp_query(x, community, fa_in_uPackets)
            result['Fa_Out_Octet'] = snmp_query(x, community, fa_out_oct)
            result['Fa_Out_uPackets'] = snmp_query(x, community, fa_out_uPackets)


            name_file = "static/graphs/"+result['hostname']+"-"+x.replace("\n", "")+".txt"

            with open(name_file, 'a') as f:
                f.write(str(result))
                f.write('\n')

            #arreglos auxiliares
            x_time = []
            out_octets = []
            out_packets = []
            in_octets = []
            in_packets = []

            with open(name_file, 'r') as f2:
                for line in f2.readlines():
                    line = eval(line)
                    x_time.append(line['Tiempo'])
                    out_packets.append(float(line['Fa_Out_uPackets']))
                    out_octets.append(float(line['Fa_Out_Octet']))
                    in_packets.append(float(line['Fa_In_uPackets']))
                    in_octets.append(float(line['Fa_In_Octet']))

                    line_chart = pygal.Bar()
                    line_chart.title = result['hostname']+"-"+x
                    line_chart.x_labels = x_time
                    line_chart.add('Oct. salida', out_octets)
                    line_chart.add('Paq. salida', out_packets)
                    line_chart.add('Oct. entrada', in_octets)
                    line_chart.add('Paq. entrada', in_packets)
                    line_chart.render_to_file("static/graphs/"+result['hostname']+"-"+x.replace("\n", "")+".svg")


                    file2.write(result['hostname']+"-"+x.replace("\n", "")+".svg\n")
            
            print("Gráfica "+name_file.replace(".txt", "")+" actualizada")            
            

        except Exception as e:
            print("Gráfica no actualizada [SNMP Timeout]")
            


    check_interface_R3_R5()  

def check_interface_R3_R5():
    f1_0_R3 = "192.168.0.145"
    f1_0_R5 = "192.168.0.146"
    standard_percentage = .75

    try:
        out_packets = str(snmp_query(f1_0_R3, community, fa_out_oct))
        in_packets = str(snmp_query(f1_0_R5, community, fa_in_oct)) 


        n_out = float(out_packets)
        n_in = float(in_packets)

        current_percentage = n_in / n_out 
        print(current_percentage)

        if current_percentage < standard_percentage:
            print("[WARNING] Pérdida de paquetes entre R3 y R5 mayor al 25%")
            root = tk.Tk()
            root.title("WARNING")
            label = tk.Label(root, text="Pérdida de paquetes entre R3 y R5 mayor al 25%")
            label.pack(side="top", fill="both", expand=True, padx=20, pady=20)
            button = tk.Button(root, text="OK", command=lambda: root.destroy())
            button.pack(side="bottom", fill="none", expand=True)
            root.mainloop()

    except Exception as e: 
        print("Error de monitoreo")

        


    
    