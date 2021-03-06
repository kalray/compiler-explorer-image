import logging
import os
import subprocess
import requests
from requests import ConnectTimeout

logger = logging.getLogger('ssh')

# TODO maybe use paramiko?

_running_on_ec2 = None


def running_on_ec2():
    global _running_on_ec2
    if _running_on_ec2 is None:
        logger.debug("Checking to see if running on ec2...")
        _running_on_ec2 = False
        try:
            result = requests.get(
                'http://169.254.169.254/latest/dynamic/instance-identity/document',
                timeout=2)
            logger.debug(f"Result {result}")
            if result.ok and result.json():
                logger.debug("Running on ec2")
                _running_on_ec2 = True
            else:
                logger.debug("Not running on ec2")
        except ConnectTimeout:
            logger.debug("Timeout: not running on ec2")
    return _running_on_ec2


def ssh_address_for(instance):
    if running_on_ec2():
        return instance.instance.private_ip_address
    else:
        return instance.instance.public_ip_address


def run_remote_shell(args, instance):
    logger.debug(f"Running remote shell on {instance}")
    ssh_command = 'ssh -o ConnectTimeout=5 ' \
                  '-o UserKnownHostsFile=/dev/null ' \
                  '-o StrictHostKeyChecking=no -o ' \
                  'LogLevel=ERROR'
    if args['mosh']:
        ssh_command = f'mosh --ssh=\'{ssh_command}\''
    os.system(f'{ssh_command} ubuntu@{ssh_address_for(instance)}')


def exec_remote(instance, command):
    logger.debug(f"Running '{' '.join(command)}' on {instance}")
    return subprocess.check_output(ssh_args_for(command, instance)).decode('utf-8')


def exec_remote_to_stdout(instance, command):
    logger.debug(f"Running '{' '.join(command)}' on {instance}")
    subprocess.check_call(ssh_args_for(command, instance))


def ssh_args_for(command, instance):
    return ['ssh', '-o', 'ConnectTimeout=5', '-o', 'UserKnownHostsFile=/dev/null', '-o', 'StrictHostKeyChecking=no',
            '-o', 'LogLevel=ERROR',
            'ubuntu@' + ssh_address_for(instance), '--'] + [f"'{c}'" for c in command]


def exec_remote_all(instances, command):
    for instance in instances:
        result = exec_remote(instance, command)
        print(f'{instance}: {result or "(no output)"}')
