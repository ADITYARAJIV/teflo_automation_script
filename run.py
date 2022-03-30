#!/usr/bin/env python3

'''
usage:
  run.py [options]
  run.py --conf=<file1> --inventory=<file2>
'''

import yaml
import os
from yaml.loader import SafeLoader
import re
from jinja2 import Environment, FileSystemLoader
from docopt import docopt

if __name__ == "__main__":
	arguments = docopt(__doc__)
	global_conf = arguments['--conf']
	inventory = arguments['--inventory']
	gfile = open(global_conf, 'r')
	ifile = open(inventory, 'r')
	cvalues = yaml.load(gfile, Loader=SafeLoader)
	ivalues = yaml.load(ifile, Loader=SafeLoader)

#*************giving the path of the result scenario.yaml file*********
	env = Environment(loader = FileSystemLoader('./teflo_template'), trim_blocks=True, lstrip_blocks=True)
	temp = env.get_template('template.yaml')
	file = open("output/scenario.yaml", "w")


#**************assinging values to the variables************************
	image1=ivalues["instance"].get("create")["image-name"]
	flavor1=ivalues["instance"].get("create")["vm-size"]
	size1=cvalues["globals"][0]["ceph-cluster"].get("node1").get("disk-size")

	
#***************finding no of nodes in the cluster************************
	pattern = r'\bnode\d*\b'
	text = cvalues["globals"][0]["ceph-cluster"]
	stri=""
	for i in text.items():
		ini=list(i)
		stri = stri+" "+ini[0]
	ser_size1 = len(re.findall(pattern, stri))


#***************To make dictionary no_of_volumes per node******************
	di = {}
	for i in range(1,ser_size1+1):
		n="node"+str(i)
		key = "no-of-volumes"
		if key in text[n].keys():
			no_vol = text[n]["no-of-volumes"]
			di[i]=no_vol
		else:
			no_vol = 0
			di[i] = no_vol


#***************Creating the vol_scenario file*****************************
	with open("./output/vol_scenario.yaml", "w") as file2:
		c=0
		for i in range(1, ser_size1+1):
			v = di[i]
			dev_skel = '/dev/vd'
			l='b'
			for j in range(1, v+1):
				c+=1
				volume_n1='team_volume'
				node_n1='team_node'
				name = 'add_volume'+str(c)
				res_name = volume_n1+'-'+str(i)
				vol_name = node_n1+'-'+str(c)
				dev_name = dev_skel+l
				if c==1 :
					data = {'provision':  [{'name':name,'provisioner': 'openstack-client','credential':'openstack','server_add_volume':  [{'device':dev_name, 'tgt_res':vol_name,'res':res_name}]}]}
				else :
					data = [{'name':name,'provisioner': 'openstack-client','credential':'openstack','server_add_volume':  [{'device':dev_name, 'tgt_res':vol_name,'res':res_name}]}]
				yaml.dump(data,file2, default_flow_style=False, sort_keys=False)
				l = chr(ord(l)+1)


#***************dumping values into the variables in the scenario file******

	file.write(temp.render(volume_n=volume_n1, node_n=node_n1, image=image1, flavor=flavor1, size=size1, maxim=c, ser_size=ser_size1))

#***************************************************************************
	file.close()
	file2.close()

#**************Executing the Teflo provisiong command***********************

	os.system("teflo run -t provision -s ./output/scenario.yaml")
	os.system("cp ./.teflo/.results/results.yml ./results.yml")
	os.system("teflo run -t provision -s ./output/vol_scenario.yaml")
	print("Results are stored in ./results.yml")

