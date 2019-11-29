#!/usr/bin/python
import sys
import subprocess
import os
from lxml import etree
from subprocess import call

machineNames = ["c1","lb","s1", "s2", "s3", "s4", "s5"]
configAddrs = {"c1":
            {"adresses":["10.0.1.2"], 
             "gateways":["10.0.0.1"]},
            "lb":
            {"adresses":["10.0.1.1", "10.0.2.1"],
              "gateways":[]},
            "s1":
            {"adresses":["10.0.2.11"], 
             "gateways":["10.0.2.1"]},
            "s2":
            {"adresses":["10.0.2.12"], 
             "gateways":["10.0.2.1"]},
            "s3":
            {"adresses":["10.0.2.13"], 
             "gateways":["10.0.2.1"]},
            "s4":
            {"adresses":["10.0.2.14"], 
             "gateways":["10.0.2.1"]},
            "s5":
            {"adresses":["10.0.2.15"], 
             "gateways":["10.0.2.1"]}
            }
lanNames= ["LAN1", "LAN2"]
lanConfig = {"c1" : ["LAN1"],"lb":["LAN1","LAN2"], "s1":["LAN2"],"s2":["LAN2"],"s3":["LAN2"],"s4":["LAN2"],"s5":["LAN2"]}
path = "/mnt/tmp/pf1/"

def crear(nServidores = 2):
  # Creamos las maquinas virtuales y archivos de configuracion
  for n in range(0,2+nServidores):
    call(["qemu-img","create", "-f", "qcow2", "-b", "/lab/cdps/pf1/cdps-vm-base-pf1.qcow2", machineNames[n]+".qcow2"])
    call(["cp","/lab/cdps/pf1/plantilla-vm-pf1.xml", machineNames[n]+".xml"])
    cambiarXml(path + machineNames[n] + ".xml" , machineNames[n])

  #Anyadimos las LANs que se vayan a usar  
  for lan in lanNames:
    call(["sudo", "brctl","addbr", lan])
    call(["sudo","ifconfig", lan, "up"])

  #Definimos las maquinas
  for n in range(0,2+nServidores):
    call(["sudo", "virsh", "define", machineNames[n] + ".xml"])

  #Cambiamos los archivos de configuracion de red de las maquinas
  for n in range(0,2+nServidores):
    changeFiles(machineNames[n])
  call(["sudo", "ifconfig", "LAN1", "10.0.1.3/24"])
  call(["sudo", "ip", "route", "add", "10.0.0.0/16" ,"via", "10.0.1.1"])
  #Configuramos el Haproxy
  configureHaProxy(nServidores)

def cambiarXml(file,name):
  tree = etree.parse(file)
  root = tree.getroot()
  #Cambiamos el nombre
  nameField = root.find("name")
  nameField.text = name

  #Cambiamos la source
  source = root.find("./devices/disk/source")
  source.set("file",path+name+".qcow2")

  #Cambiamos el bridge
  interfaceSource = root.find("./devices/interface/source")
  lans = lanConfig[name]
  interfaceSource.set("bridge" ,lans[0])
  fout = open(file, 'w')
  fout.write(etree.tostring(tree, pretty_print = True))
  fout.close()

  #Anyadimos las interfaces extra a aquellas maquinas que las tengan
  if len(lans) > 1:
    for n in range(1, len(lans)): 
      addExtraInterfaceTo(file, lans[n])
  
def addExtraInterfaceTo(file, name):
  fin = open(file,'r')
  fout = open("out.xml",'w')
  hasBeenAdded = False
  for line in fin:
    if "</interface>" in line and not hasBeenAdded:
      fout.write("    </interface>\n    <interface type='bridge'>\n      <source bridge='"+name+"'/>\n      <model type='virtio'/>\n    </interface>\n")
      hasBeenAdded = True
    else:
      fout.write(line)
  fin.close()
  fout.close()
  call(["cp","./out.xml", file])
  call(["rm", "-f", "./out.xml"])

def changeFiles(name):
  #Cambiamos el nombre de la maquina
  os.system("echo " + name + " > hostname")
  call(["sudo", "virt-copy-in", "-a", path + name + ".qcow2", path + "hostname", "/etc/" ])

  #Cambiamos hosts
  call(["sudo", "virt-copy-out", "-a", path + name + ".qcow2", "/etc/hosts", path + "."])
  call(["mv", "hosts", "hostsR"])
  fin = open("hostsR",'r')
  fout = open("hosts",'w')
  for line in fin:
    if "cdps" in line:
      end = line.find('c')
      fout.write(line[0:end]+name+"\n")
    else:
      fout.write(line)
  fin.close()
  fout.close()
  call(["rm", "-f","./hostsR"])
  call(["sudo", "virt-copy-in", "-a", path + name + ".qcow2", path + "hosts", "/etc/" ])

  #Cambiamos las configuraciones de red
  call(["sudo", "virt-copy-out", "-a", path + name + ".qcow2", "/etc/network/interfaces", path+"."])
  call(["mv", "interfaces", "interfacesR"])
  fin = open("interfacesR",'r')
  fout = open("interfaces",'w')
  for line in fin:
      fout.write(line)
      if "dhcp" in line:
        writeNetConfig(fout,name)
  fin.close()
  fout.close()
  call(["rm", "-f","./interfacesR"])
  call(["sudo", "virt-copy-in", "-a", path + name + ".qcow2", path + "interfaces", "/etc/network/" ])

  #Anyadimos la configuracion de root de lb
  if name == "lb":
    os.system("sudo virt-edit -a " + path +"lb.qcow2 /etc/sysctl.conf -e 's/#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/'")

  #Distinguimos htmls 
  if "s" in name:
    os.system("echo " + name + " > index.html")
    call(["sudo", "virt-copy-in", "-a", path + name + ".qcow2", path + "index.html", "/var/www/html/" ])

def writeNetConfig(fout,name):
  counter = 0
  for adress in configAddrs[name]["adresses"]:
    if counter > 0:
      fout.write("auto eth"+str(counter)+"\n")
      fout.write("iface eth"+str(counter)+" inet dhcp\n")
    fout.write("iface eth"+str(counter)+" inet static\n")
    fout.write("address "+adress+"\n")
    fout.write("netmask 255.255.255.0"+"\n")
    for gateway in configAddrs[name]["gateways"]:
      fout.write("gateway "+gateway+"\n")
    counter = counter + 1

def configureHaProxy(nServidores):
  #Editamos el fichero haproxy.cfg
  call(["sudo", "virt-copy-out", "-a", path + "lb" + ".qcow2", "/etc/haproxy/haproxy.cfg", path+"."])
  call(["mv", "haproxy.cfg", "tmp.cfg"])
  fin = open("tmp.cfg", "r")
  fout = open("haproxy.cfg", "w")
  for line in fin:
    fout.write(line)
  fout.write("\nfrontend lb\n")
  fout.write("        bind *:80\n")
  fout.write("        mode http\n")
  fout.write("        default_backend webservers\n")
  fout.write("        backend webservers\n")
  fout.write("        mode http\n")
  fout.write("balance roundrobin\n")
  for n in range(1,nServidores + 1):
    for adress in configAddrs["s"+str(n)]["adresses"]:
      fout.write("        server s"+str(n)+" "+ str(adress) + " check\n")
  fin.close()
  fout.close()
  call(["rm", "-f","./tmp.cfg"])
  call(["sudo", "virt-copy-in", "-a", path + "lb" + ".qcow2", path + "haproxy.cfg", "/etc/haproxy/" ])
  #Editamos rc.local
  fout = open("rc.local", "w")
  fout.write("#!/bin/sh\n")
  fout.write("service apache2 stop\n")
  fout.write("sudo service haproxy restart")
  fout.close()
  call(["sudo", "virt-copy-in", "-a", path + "lb" + ".qcow2", path + "rc.local", "/etc/" ])
