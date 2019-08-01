# MulVal Demo

1. Run in the same directory as Vagrantfile to install the requirements:
``` ansible-galaxy install -r requirements.yml ```

1. Run ```vagrant up``` to create environment

1. Run only tagged tasks:
```
ansible-playbook -i inventory --private-key ~/.vagrant.d/insecure_private_key -u vagrant playbooks/provision.yml --tags ”run”
```
