import sys
import os
from subprocess import call

machineNames = ["c1","lb","s1", "s2", "s3", "s4", "s5"]
path = "/mnt/tmp/pf1/"
lanNames= ["LAN1", "LAN2"]
os.chdir(path)


def encender(nServidores):
  for n in range(0,2+nServidores):
    call(["sudo", "virsh", "start", machineNames[n]])
    os.system("xterm -rv -sb -rightbar -fa monospace -fs 10 -title '"+machineNames[n]+"' -e 'sudo virsh console " + machineNames[n] +"' &")

def apagar(nServidores):
  for n in range(0,2+nServidores):
    call(["sudo", "virsh", "shutdown", machineNames[n]])


def destroy(nServidores, encendida):
  if encendida:
    apagar(nServidores)
  for n in range(0,2+nServidores):
    call(["sudo", "virsh", "destroy", machineNames[n]])
  undefineCache()
  os.chdir("/mnt/tmp/")
  call(["rm", "-rf", "pf1"])

def undefineCache():
  #Listamos los uuid de las maquinas definidas
  os.system("sudo virsh list --all --uuid > cache.txt")
  fin = open(path+"cache.txt", 'r')

  #Recorremos la lista, llamando a undefine de cada uuid
  for line in fin:
    if len(line) == 1:
      continue
    end = line.find('\\')
    call(["sudo", "virsh", "undefine", line[0:end]])
  fin.close()

  #Retiramos las interfaces de red del host
  for lan in lanNames:
    call(["sudo","ifconfig", lan, "down"])
    call(["sudo", "brctl","delbr", lan])

def monitor(general,serverName = ""):
  if general:
    os.system("xterm -title MAQUINAS -fa monospace -fs 11 -e 'watch -n 2 \"sudo virsh list --all\"'&")
  else:
    os.system("xterm -title MONITOR_OF_"+ serverName +" -fa monospace -fs 11 -e 'watch -n 2 \"sudo virsh domstate "+serverName+" && sudo virsh dominfo "+serverName+" && sudo virsh cpu-stats "+serverName+"\"'&")
