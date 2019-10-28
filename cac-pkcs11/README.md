# Ansible Playbook Template

### Running playbooks
1. Run in the same directory as Vagrantfile to install the requirements:
``` ansible-galaxy install -r requirements.yml ```

1. Run ```vagrant up``` to create environment

### Configuring playbook template

1. Modify Vagrantfile, inventory to match hostnames and IP addys

1. Update requirements.yml to include necessary roles

1. update ansible.cfg for current roles_path, etc

1. Assumes playbooks/provision.yml is playbook entrypoint so start configs here

### handy ansible commands

1. ansible-playbook -i inventory --private-key ~/.vagrant.d/insecure_private_key -u vagrant playbooks/provision.yml --tags setup

