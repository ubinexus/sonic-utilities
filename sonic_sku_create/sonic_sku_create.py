#! /usr/bin/python
"""
using soni_sku_create.py  to create a new SONiC SKU based on a <SKU-DEF>.xml file

usage: sonic_sku_create.py [-h] [-v] [-f FILE] [-r] [-l2] [-p] [-vv]

Create a new SKU

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  -f FILE, --file FILE  SKU definition file (default <cwd>/sku_def.xml)
  -r, --remove          Remove SKU folder
  -l2, --l2_mode        Configure SKU to L2 Mode
  -p, --print           Print port_config.ini without creating a new SKU
  -vv, --verbose        Verbose output

"""

from __future__ import print_function

import argparse
import json
import os
import re
import subprocess
import swsssdk
import sys
import shutil

from tabulate import tabulate
import xml.etree.ElementTree as ET


DEFAULT_DEV_PATH = '/usr/share/sonic/device/'
### port_config.ini header
PORTCONFIG_HEADER = ["# name", "lanes", "alias", "speed", "index"]


class SkuCreate(object):
	"""
	Process aclstat
	"""

	def __init__(self):
		self.metadata = {}
		self.portconfig_dict = {}
		self.platform_specific_dict = {"x86_64-mlnx_msn2700-r0":self.msn2700_specific}
		self.default_lanes_per_port = []
		self.platform = 'NA'
		self.fpp = []
		self.fpp_split  =  {}
		self.num_of_fpp = 0
		self.num_of_lanes_dict = {"1" : 4, "2" : 2, "4" : 1}
		
		# Set up db connections
		self.db = swsssdk.SonicV2Connector(host="127.0.0.1")
		self.db.connect(self.db.CONFIG_DB)
		
		self.configdb = swsssdk.ConfigDBConnector()
		self.configdb.connect()

		self.read_metadata()
		self.platform = self.metadata['platform']
		self.sku_name = None
		self.base_sku_name = None
		self.base_sku_dir = None
		self.base_file_path = None		
		self.new_sku_dir = None

	def read_metadata(self):
		"""
		Redis database platform info
		"""
		self.metadata = self.db.get_all(self.db.CONFIG_DB, "DEVICE_METADATA|localhost" )

	def sku_def_parser(self,sku_def) :
		try:
			f = open(sku_def,"r")
		except IOError:
			print ("Couln't open file: " + sku_def)
		element = ET.parse(f)
		
		root = element.getroot()
		#print ( "tag=%s, attrib=%s" % (root.tag, root.attrib))
		self.sku_name = root.attrib["HwSku"]
		self.base_sku_name = root.attrib["BaseSku"]
		self.base_sku_dir = DEFAULT_DEV_PATH + self.platform + '/' + self.base_sku_name + '/'
		self.base_file_path = self.base_sku_dir + "port_config.ini"
		self.new_sku_dir = DEFAULT_DEV_PATH+self.platform+"/"+self.sku_name+ '/'
		for child in root:
			if child.tag == "Ethernet":
				for interface in child:
					for eth_iter in interface.iter():
						if eth_iter is not None:
							self.portconfig_dict["Ethernet"+eth_iter.get("PortName")] = ["Ethernet"+eth_iter.get("PortName"),[1,2,3,4], eth_iter.get("InterfaceName"), eth_iter.get("Speed"), eth_iter.get("Index")]
		f.close()
		

		
	def split_analyze(self) :
		# Analyze the split ports based on the interfaces alias names
		alias_index = PORTCONFIG_HEADER.index('alias')
		for ifc in self.portconfig_dict.values():
			pattern = '^etp([0-9]{1,})([a-d]?)'
			m = re.match(pattern,str(ifc[alias_index]))
			if m.group(1) not in self.fpp_split :
				self.fpp_split[m.group(1)] = 1
			else:
				self.fpp_split[m.group(1)] += 1
		self.num_of_fpp = len(self.fpp_split.keys())

		
	def get_default_lanes(self) :
		try:
			f = open(self.base_file_path,"r")
		except IOError:
			print ("Could not open file "+ self.base_file_path)
			
		for i in range(1): f.next() # skip first  line
		pattern = '^etp([0-9]{1,})'
		for line in f:
			line_arr = line.split()
			m = re.match(pattern,line_arr[2])
			self.default_lanes_per_port.insert(int(m.group(1))-1,line_arr[1])
		#print(self.default_lanes_per_port)
		f.close()
		
	def set_lanes(self) :
		#set lanes and index per interfaces based on split
		lanes_index = PORTCONFIG_HEADER.index('lanes')
		index_index = _index = PORTCONFIG_HEADER.index('index')

		
		for fp, splt in self.fpp_split.iteritems():
			pattern = '(\d+),(\d+),(\d+),(\d+)'
			m = re.match(pattern,self.default_lanes_per_port[int(fp)-1])

			if (splt == 1) :
				self.portconfig_dict["Ethernet"+str((int(fp)-1)*4)][lanes_index] = m.group(1)+","+m.group(2)+","+m.group(3)+","+m.group(4) 
				self.portconfig_dict["Ethernet"+str((int(fp)-1)*4)][index_index] = fp
			elif (splt == 2) :
				self.portconfig_dict["Ethernet"+str((int(fp)-1)*4)][lanes_index] = m.group(1)+","+m.group(2) 
				self.portconfig_dict["Ethernet"+str((int(fp)-1)*4+2)][lanes_index] = m.group(3)+","+m.group(4)
				self.portconfig_dict["Ethernet"+str((int(fp)-1)*4)][index_index] = fp 
				self.portconfig_dict["Ethernet"+str((int(fp)-1)*4+2)][index_index] = fp				
			elif (splt == 4) :
				self.portconfig_dict["Ethernet"+str((int(fp)-1)*4)][lanes_index] = m.group(1) 
				self.portconfig_dict["Ethernet"+str((int(fp)-1)*4+1)][lanes_index] = m.group(2) 
				self.portconfig_dict["Ethernet"+str((int(fp)-1)*4+2)][lanes_index] = m.group(3) 
				self.portconfig_dict["Ethernet"+str((int(fp)-1)*4+3)][lanes_index] = m.group(4)
				self.portconfig_dict["Ethernet"+str((int(fp)-1)*4)][index_index] = fp 
				self.portconfig_dict["Ethernet"+str((int(fp)-1)*4+1)][index_index] = fp 
				self.portconfig_dict["Ethernet"+str((int(fp)-1)*4+2)][index_index] = fp 
				self.portconfig_dict["Ethernet"+str((int(fp)-1)*4+3)][index_index] = fp
		self.platform_specific()	

	
	

		
	def create_port_config(self) :
		#create a port_config.ini file based on the sku definition 
		if not os.path.exists(self.new_sku_dir):
			print ("Error - path:", self.new_sku_dir, " doesn't exist")
			
		try:
			f = open(self.new_sku_dir+"port_config.ini","w+")
		except IOError:
			print ("Could not open file "+ self.new_sku_dir+"port_config.ini")
		header = PORTCONFIG_HEADER # ["name", "lanes", "alias", "index"]
		port_config = []
		for line in self.portconfig_dict.values():
			port_config.append(line)
		 
		port_config.sort(key=lambda x: (int(re.search(('\d+'),x[0]).group(0)))) # sort the list with interface name
		f.write(tabulate(port_config, header,tablefmt="plain"))
		f.close()
	
	def print_port_config(self) :
		#print a port_config.ini file based on the sku definition 
		
		header = PORTCONFIG_HEADER # ["name", "lanes", "alias", "index"]
		port_config = []
		for line in self.portconfig_dict.values():
			port_config.append(line)
		 
		port_config.sort(key=lambda x: (int(re.search(('\d+'),x[0]).group(0)))) # sort the list with interface name
		print(tabulate(port_config, header,tablefmt="plain"))
		
		
	def create_sku_dir(self) :
		# create a new SKU directory based on the base SKU
		try:
			shutil.copytree(self.base_sku_dir, self.new_sku_dir)
		except OSError as e:
			print(e.message, file=sys.stderr) 
	
	def remove_sku_dir(self) :
		# remove SKU directory 
		try:
			if (self.base_sku_dir == self.new_sku_dir) :
				print ("Removing the base SKU" + self.new_sku_dir + " is not allowed")
				return
			shutil.rmtree(self.new_sku_dir)
		except OSError as e:
			print(e.message, file=sys.stderr) 
					
	def platform_specific(self) :
		func = self.platform_specific_dict.get(self.platform, lambda: "nothing")
		return func()
		
		
	def msn2700_specific(self) :
		for fp, splt in self.fpp_split.iteritems():
			fp=int(fp)
			if ((fp%2) == 1 and splt == 4) :
				self.portconfig_dict.pop("Ethernet"+str(fp*4),"nothing" )
				print ("MSN2700 -  Removed interface ","Ethernet"+str((int(fp+1)-1)*4),"Due to port ",fp,"Split by 4") 
			elif ((fp%2) == 0 and splt == 4) :
				print ("MSN2700 -  even front panel ports (2,4..) are not allowed to split by 4")
				return -1


	def l2_mode(self) :
		if not os.path.exists(self.new_sku_dir):
			print ("Error - path:", self.new_sku_dir, " doesn't exist")
		cfg_db_str = "{\n\t\"DEVICE_METADATA\": {\n\t\t\"localhost\": {\n\t\t\t\"hostname\": \"sonic\"\n\t\t}\n\t}\n}\n"	
		ps = subprocess.Popen(('echo',cfg_db_str), stdout=subprocess.PIPE)
		output = subprocess.check_output(('grep', 'DEV'), stdin=ps.stdout)
		print (cmd)
		#cmd.append("sudo sonic-cfggen -H --write-to-db ;")
		#cmd.append("sonic-cfggen -t /usr/local/lib/python2.7/dist-packages/usr/share/sonic/templates/l2switch.j2 -p -k "+ self.sku_name ) #| sudo config load /dev/stdin -y ;")
		#cmd.append("sudo config save -y ;")
		#cmd.append("sudo systemctl restart swss ;")
		# for c in cmd :
			# subprocess.call(c,shell=True)
		# print( "Finished configuration of L2 mode based on "+self.sku_name+" SKU")
		
def main():
	parser = argparse.ArgumentParser(description='Create a new SKU',
									version='1.0.0',
									formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument('-f', '--file', action='store', help='SKU definition file (default <cwd>/sku_def.xml)', default=None)
	parser.add_argument('-r', '--remove', action='store_true', help='Remove SKU folder')
	parser.add_argument('-l2', '--l2_mode', action='store_true', help='Configure SKU to L2 Mode', default=False)
	parser.add_argument('-p', '--print', action='store_true', help='Print port_config.ini without creating a new SKU', default=False)
	parser.add_argument('-vv', '--verbose', action='store_true', help='Verbose output', default=False)
	args = parser.parse_args()

	try:
		sku = SkuCreate()
		if args.file:
			SKU_DEF_FILE = args.file
		else:
			SKU_DEF_FILE = os.getcwd() + '/sku_def.xml'
		sku.sku_def_parser(SKU_DEF_FILE)	
		#print (SKU_DEF_FILE)
		if args.remove:
			sku.remove_sku_dir()
			return
		sku.get_default_lanes()
		sku.split_analyze()
		sku.set_lanes()
		if args.print:
			sku.print_port_config()
		else:
			sku.create_sku_dir()
			sku.create_port_config()
			print ("Created a new sku ",sku.sku_name)
		#if args.l2_mode :
		#	sku.l2_mode()
		
	except Exception as e:
		print(e.message, file=sys.stderr)
		sys.exit(1)

if __name__ == "__main__":
    main()
