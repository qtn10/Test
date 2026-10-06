# As Drain learns a template one file at a time, combining the openstack log files
# to make a single openstack.log works better and more efficient as logparser
# may create different templates even though only one is needed for all openstack
#
#
# ran this once to create openstack_combined.log
import os

os.makedirs('OpenStack', exist_ok=True)

with open('OpenStack/openstack_combined.log', 'w') as out:
    for file_name in ['openstack_normal1.log', 'openstack_normal2.log', 'openstack_abnormal.log']:
        with open('OpenStack/' + file_name) as f:
            for line in f:
                out.write(file_name + ' ' + line)