#!/usr/bin/env python3
# Ambar Installation Script (Python 3)
# https://ambar.cloud

import argparse
import subprocess
import os
import json
import socket
import time
import re

AMBAR_LOGO = """ 

______           ____     ______  ____       
/\  _  \  /'\_/`\/\  _`\  /\  _  \/\  _`\    
\ \ \L\ \/\      \ \ \L\ \\ \ \L\ \ \ \L\ \  
 \ \  __ \ \ \__\ \ \  _ <'\ \  __ \ \ ,  /   
  \ \ \/\ \ \ \_/\ \ \ \L\ \\ \ \/\ \ \ \\ \  
   \ \_\ \_\ \_\\ \_\ \____/ \ \_\ \_\ \_\ \_\\
    \/_/\/_/\/_/ \/_/\/___/   \/_/\/_/\/_/\/ /


                                              """

VERSION = '1.0.0'
STATIC_FILE_HOST = 'https://static.ambar.cloud/'
DOCKER_COMPOSE_TEMPLATE_URL = 'https://static.ambar.cloud/docker-compose.yml'
BLOG_HOST = 'https://blog.ambar.cloud/'
START = 'start'
STOP = 'stop'
INSTALL = 'install'
UPDATE = 'update'
RESTART = 'restart'
RESET = 'reset'
UNINSTALL = 'uninstall'

PATH = os.path.dirname(os.path.realpath(__file__))

parser = argparse.ArgumentParser(description='Ambar Installation Script (https://ambar.cloud)')

parser.add_argument('action', choices=[INSTALL, START, STOP, RESTART, UPDATE, RESET, UNINSTALL])
parser.add_argument('--version', action='version', version = VERSION)
parser.add_argument('--useLocalConfig', action='store_true', help = 'use config.json from the script directory')
parser.add_argument('--configUrl', default = '{0}config.json'.format(STATIC_FILE_HOST), help = 'url of configuration file')

args = parser.parse_args()

def isValidIpV4Address(address):
    try:
        socket.inet_pton(socket.AF_INET, address)
    except AttributeError:  # no inet_pton here, sorry
        try:
            socket.inet_aton(address)
        except socket.error:
            return False
        return address.count('.') == 3
    except socket.error:  # not a valid address
        return False

    return True

def runShellCommandStrict(command):
     subprocess.check_call(command, shell = True)

def runShellCommand(command):
     return subprocess.call(command, shell = True)

def checkRequirements():
    # Check That Docker Installed
    if (runShellCommand('docker -v') != 0):
        print('docker is not installed. Check Ambar requirements here: {0}'.format(BLOG_HOST))
        exit(-1)

    # Check That Docker-Compose Installed
    if (runShellCommand('docker-compose -v') != 0):
        print('docker-compose is not installed. Check Ambar requirements here: {0}'.format(BLOG_HOST))
        exit(-1)

    # Check That Running Under Sudo
    if (os.geteuid() != 0):
        print('Please run this script as root user')
        exit(-1)

def getMachineIpAddress():
    ipAddress = subprocess.check_output("echo $(ip route get 8.8.8.8 | head -1 | cut -d' ' -f8)", shell=True)
    return str(ipAddress.decode("utf-8").replace('\n', ''))

def writeOsConstantIfNotExists(sysConfig, writeDescriptor, key, value):
    if (sysConfig.find(key) == -1):
        writeDescriptor.write("{0}={1}\n".format(key,value))

def writeRcLocalDirectiveIfNotExist(rcLocal, writeDescriptor, directive):
    if (rcLocal.find(directive) == -1):
        writeDescriptor.write("{0}\n".format(directive))

def setOsConstants():
    sysConfig = None
    rcLocal = None

    with open('/etc/sysctl.conf', 'r') as sysConfigFile:
        sysConfig = sysConfigFile.read()
    
    with open('/etc/sysctl.conf', 'a') as sysConfigFile:
        writeOsConstantIfNotExists(sysConfig, sysConfigFile, 'vm.max_map_count', '262144')
        writeOsConstantIfNotExists(sysConfig, sysConfigFile, 'net.ipv4.ip_local_port_range', '"15000 61000"')
        writeOsConstantIfNotExists(sysConfig, sysConfigFile, 'net.ipv4.tcp_fin_timeout', '30')
        writeOsConstantIfNotExists(sysConfig, sysConfigFile, 'net.core.somaxconn', '1024')
        writeOsConstantIfNotExists(sysConfig, sysConfigFile, 'net.core.netdev_max_backlog', '2000')
        writeOsConstantIfNotExists(sysConfig, sysConfigFile, 'net.ipv4.tcp_max_syn_backlog', '2048')        
        writeOsConstantIfNotExists(sysConfig, sysConfigFile, 'vm.overcommit_memory', '1')      

    with open('/etc/rc.local', 'r') as rcLocalConfigFile:
        rcLocal = rcLocalConfigFile.read()
        
    with open('/etc/rc.local', 'a') as rcLocalConfigFile:
        writeRcLocalDirectiveIfNotExist(rcLocal, rcLocalConfigFile, 'echo never > /sys/kernel/mm/transparent_hugepage/enabled')      

def setRunTimeOsConstants():
    runShellCommandStrict('sysctl -w vm.max_map_count=262144')
    runShellCommandStrict('sysctl -w net.ipv4.ip_local_port_range="15000 61000"')
    runShellCommandStrict('sysctl -w net.ipv4.tcp_fin_timeout=30')
    runShellCommandStrict('sysctl -w net.core.somaxconn=1024')
    runShellCommandStrict('sysctl -w net.core.netdev_max_backlog=2000')
    runShellCommandStrict('sysctl -w net.ipv4.tcp_max_syn_backlog=2048')
    runShellCommandStrict('sysctl -w vm.overcommit_memory=1')
    runShellCommandStrict('echo never > /sys/kernel/mm/transparent_hugepage/enabled')
        
def pullImages(configuration):
    dockerRepo = configuration['dockerRepo']

    runShellCommandStrict("docker pull {0}/ambar-crawler:latest".format(dockerRepo))
    runShellCommandStrict("docker pull {0}/ambar-pipeline:latest".format(dockerRepo))
    runShellCommandStrict("docker-compose -f {0}/docker-compose.yml pull".format(PATH))

def generateEnvFile(configuration):  
    envFileLines = []

    if os.path.exists('{0}/.env'.format(PATH)):
        with open('{0}/.env'.format(PATH), 'r') as envFile:
            envFileLines = envFile.readlines()
    
    settings = {}
    for line in envFileLines:
        if '=' in line:
            settings[line.split('=')[0]] = line.split('=')[1]
    
    for key in configuration.keys():
        settings[key]=configuration[key]

    newEnvFileLines = []
    for key in settings.keys():
        newEnvFileLines.append('{0}={1}'.format(key, settings[key]))
    
    with open('{0}/.env'.format(PATH), 'w') as envFile:
        envFile.write('\n'.join(newEnvFileLines))

def loadConfigFromFile():   
    with open('{0}/config.json'.format(PATH), 'r') as configFile:
        config = json.load(configFile)

    return config

def loadFromWeb():
    runShellCommandStrict('wget -O {0}/config.json {1}'.format(PATH, args.configUrl))
    return loadConfigFromFile()

def downloadDockerComposeTemplate():
    runShellCommandStrict('wget -O {0}/docker-compose.yml {1}'.format(PATH, DOCKER_COMPOSE_TEMPLATE_URL))

def install(configuration):                             
    downloadDockerComposeTemplate()
        
    machineAddress = getMachineIpAddress()

    print('Assigning {0} IP address to Ambar, type "Y" to confirm or type in another IP address...'.format(machineAddress))
    userInput = input().lower()
    if (userInput == 'y'):
        configuration['host'] = machineAddress        
    elif (isValidIpV4Address(userInput)):
        configuration['host'] = userInput
    else:
        print('{0} is not a valid ipv4 address, try again...'.format(userInput))
        return
    
    defaultPort = configuration['port']
    print('Assigning {0} port address to Ambar, type "Y" to confirm or type in another port...'.format(defaultPort))
    userInput = input().lower()
    if (userInput != 'y'):
        try:
            userPort = int(userInput)
            if (userPort < 0 or userPort > 65535):
               raise ValueError()
            configuration['port'] = userInput
        except:
             print('{0} is not a valid port, try again...'.format(userInput))

    with open('{0}/config.json'.format(PATH), 'w') as configFile:
        json.dump(configuration, configFile, indent=4)

    generateEnvFile(configuration)
    pullImages(configuration)
    setOsConstants()
    print('Ambar installed successfully! Run `sudo ./ambar.py start` to start Ambar')

def start(configuration):    
    setRunTimeOsConstants()    
    generateEnvFile(configuration)
    runShellCommandStrict('docker-compose -f {0}/docker-compose.yml -p ambar up -d'.format(PATH))
    print('Ambar is on {0}://{1}:{2}'.format(configuration['protocol'], configuration['host'], configuration['port']))

def stop(configuration):
    dockerRepo = configuration['dockerRepo']
    print('Stopping Ambar...')               
    runShellCommand('docker rm -f $(docker ps -a -q --filter ancestor="{0}/ambar-crawler" --format="{{{{.ID}}}}")'.format(dockerRepo)) 
    print('Crawlers containers removed')
    runShellCommand('docker rm -f $(docker ps -a -q --filter ancestor="{0}/ambar-pipeline" --format="{{{{.ID}}}}")'.format(dockerRepo))
    print('Pipeline containers removed')
    runShellCommand('docker-compose -f {0}/docker-compose.yml -p ambar down'.format(PATH))
    print('Ambar is stopped')        

def update(configuration):    
    stop(configuration)
    downloadDockerComposeTemplate()
    generateEnvFile(configuration)
    pullImages(configuration)
    start(configuration)

def restart(configuration):
    stop(configuration)
    start(configuration)

def reset(configuration):
    dataPath = configuration['dataPath']
    print('All data from Ambar will be removed ({0}). Are you sure? (y/n)'.format(dataPath))
    choice = input().lower()
    
    if (choice != 'y'):
        return

    stop(configuration)
    runShellCommand('rm -rf {0}'.format(dataPath))
    print('Done. To start Ambar use `sudo ./ambar.py start`')

def uninstall(configuration):
    dataPath = configuration['dataPath']
    print('Ambar will be uninstalled and all data will be removed ({0}). Are you sure? (y/n)'.format(dataPath))
    choice = input().lower()
    
    if (choice != 'y'):
        return
    
    stop(configuration)
    runShellCommand('rm -rf {0}'.format(dataPath))
    runShellCommand('rm -f ./config.json')
    runShellCommand('rm -f ./docker-compose.yml')  
    print('Thank you for your interest in our product, you can send your feedback to hello@ambar.cloud. To remove the installer run `rm -f ambar.py`.')

print(AMBAR_LOGO)
checkRequirements()

if (args.action == START):
    configuration = loadConfigFromFile()
    start(configuration)
    exit(0)

if (args.action == STOP):
    configuration = loadConfigFromFile()
    stop(configuration)
    exit(0)

if (args.action == RESTART):
    configuration = loadConfigFromFile()
    restart(configuration)
    exit(0)

if (args.action == INSTALL):
    if (args.useLocalConfig == True):
        configuration = loadConfigFromFile()    
    else:
        configuration = loadFromWeb()        

    install(configuration)
    exit(0)

if (args.action == UPDATE):
    configuration = loadConfigFromFile()
    update(configuration)
    exit(0)

if (args.action == RESET):
    configuration = loadConfigFromFile()
    reset(configuration)
    exit(0)

if (args.action == UNINSTALL):
    configuration = loadConfigFromFile()
    uninstall(configuration)
    exit(0)


