#!/usr/bin/python
import sys
import subprocess
import os
from lxml import etree
from subprocess import call
import json
import time
import crear
from crear import crear
import administrar
from administrar import encender, apagar, destroy, monitor

machineNames = ["c1","lb","s1", "s2", "s3", "s4", "s5"]
path = "/mnt/tmp/pf1/"

#Estado global del programa guardado en el archivo de configuracion
def getState():
  if os.path.exists(path):
    os.chdir(path)
    return readState()
  else:
    os.system("mkdir "+path)
    os.chdir(path)
    conf = []
    conf.append({
        "nServers": "2",
        "creado": "False",
        "encendido": "False"
    })
    fout = open("pf1.json", "w")
    json.dump(conf, fout)
    fout.close()
    return 2,False,False

def readState():
  with open('pf1.json', "r") as json_file:
    conf = json.load(json_file)
    nServ = int(conf[0]["nServers"])
    creado = False if conf[0]["creado"].lower() == "false" else True
    encendido = False if conf[0]["encendido"].lower() == "false" else True
    json_file.close()

  return nServ,creado,encendido

def changeConf(keys,values):
  with open('pf1.json', "r") as json_file:
    conf = json.load(json_file)
    json_file.close()
  for n in range(0,len(keys)):
    conf[0][keys[n]] = values[n]
  call(["rm","-rf","pf1.json"])
  with open("pf1.json", "w") as fout:
      json.dump(conf, fout)
      fout.close()


def getHelp():
  print("Para usar la herramienta, escriba una de las opciones:")
  print("crear <numero de servidores(opcional)>")
  print("arrancar")
  print("apagar")
  print("destruir")
  print("monitor")

#Recuperamos los argumentos escritos por el terminal
arguments = sys.argv

#Recuperamos el estado global del programa
nServ, creada, encendida = getState()

#Ejecutamos una herramienta u otra segun el estado y los argumentos introducidos
if len(arguments) < 2:
  getHelp()
else:
  tool = arguments[1]
  #CREAR
  if tool == "crear":
    if len(arguments) > 2:
      nServ = int(arguments[2])
    if creada:
      print("ERROR: EL ESCENARIO YA HA SIDO CREADO\n")
    if nServ > 5:
      print("ERROR: EL MAXIMO NUMERO DE MAQUINAS QUE SE PUEDE CREAR ES 5\n")
    if nServ < 2:
      print("ERROR: EL MINIMO NUMERO DE MAQUINAS QUE SE PUEDE CREAR ES 2\n")
    else:
      crear(nServ)
      changeConf(["nServers","creado"], [nServ, "True"])
  #ARRANCAR
  elif tool == "arrancar":
    if not creada:
      print("ERROR: EL ESCENARIO NO EXISTE\n")
    else:
      if len(arguments) > 2:
        if arguments[2] in machineNames:
          encender(False,arguments[2])
        else:
          print("ERROR: LA MAQUINA ESPECIFICADA NO EXISTE\n")
      elif encendida:
        print("ERROR: EL ESCENARIO YA HA SIDO ARRANCADO\n")
      else:
        encender(True,nServ)
        changeConf(["encendido"], ["True"])
  #APAGAR
  elif tool == "apagar":
    if not creada:
      print("ERROR: EL ESCENARIO NO EXISTE\n")
    elif not encendida:
      print("ERROR: EL ESCENARIO NO ESTA ENCENDIDO\n")
    else:
      if len(arguments) > 2:
        if arguments[2] in machineNames:
          apagar(False,arguments[2])
        else:
          print("ERROR: LA MAQUINA ESPECIFICADA NO EXISTE\n")
      else:
        apagar(True,nServ)
        changeConf(["encendido"], ["False"])

  #DESTRUIR
  elif tool == "destruir":
    if len(arguments) > 2:
      print("Esta herramienta no tiene opciones. Se destruiran las maquinas creadas.\n")
    if not creada:
      print("ERROR: EL ESCENARIO NO HA SIDO CREADO AUN\n")
    else:
      destroy(nServ, encendida)
  #HELP
  elif tool == "help":
    getHelp()
  #MONITOR
  elif tool == "monitor":
    if not creada:
      print("ERROR: EL ESCENARIO NO HA SIDO CREADO AUN\n")
    else:
      if len(arguments) > 2:
        if arguments[2] in machineNames:
          monitor(False,arguments[2])
        else:
          print("ERROR: LA MAQUINA ESPECIFICADA NO EXISTE\n")
      else:
        monitor(True)
  #COMANDO ERRONEO
  else:
    print("El comando que ha introducido no existe, para visualizar las herramientas disponibles, use la herramienta help.\n")

