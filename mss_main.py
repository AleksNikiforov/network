#!/usr/bin/python3.8
# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from multiprocessing import Pool
from sys import argv
import time
import datetime
import logging
import re
import mysql.connector.pooling
import os
import textfsm
import sys
from pysnmp.hlapi import *



dbconfig = {
    "host":"127.0.0.1",
    #"port":"3306",
    "user":"user",
    "password":"pass",
}


def get_logger(fileLevel = "INFO"):
    timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H-%M-%S')
    logging.basicConfig(level=fileLevel,
                        format='%(asctime)s %(threadName)s %(levelname)s %(message)s',
                        datefmt='%H:%M',
                        filename=f'./logs/MSS-{timestamp}-{argv[1]}.log',
                        filemode='a')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(threadName)s: %(levelname)s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    logger1 = logging.getLogger()
    return logger1


class MySQLPool(object):

    def __init__(self, host="127.0.0.1", user="user",
                 password="pass", database="inv_dev", pool_name="mypool",
                 pool_size=3):
        res = {}
        self._host = host
        self._user = user
        self._password = password
        self._database = database

        res["host"] = self._host
        res["user"] = self._user
        res["password"] = self._password
        res["database"] = self._database
        self.dbconfig = res
        self.pool = self.create_pool(pool_name=pool_name, pool_size=pool_size)

    def create_pool(self, pool_name="mypool", pool_size=3):

        pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name=pool_name,
            pool_size=pool_size,
            pool_reset_session=True,
            **self.dbconfig)
        return pool

    def close(self, conn, cursor):
        cursor.close()
        conn.close()

    def execute(self, sql, args=None, commit=False):
        conn = self.pool.get_connection()
        cursor = conn.cursor()
        if args:
            cursor.execute(sql, args)
        else:
            cursor.execute(sql)
        if commit is True:
            conn.commit()
            self.close(conn, cursor)
            return None
        else:
            res = cursor.fetchall()
            self.close(conn, cursor)
            return res

    def executeid(self, sql, args=None, commit=False):

        conn = self.pool.get_connection()
        cursor = conn.cursor()
        if args:
            cursor.execute(sql, args)
        else:
            cursor.execute(sql)
        if commit is True:
            conn.commit()
            self.close(conn, cursor)
            return None
        else:
            res= cursor.lastrowid
            self.close(conn, cursor)
            return res

    def executemany(self, sql, args, commit=False):
        conn = self.pool.get_connection()
        cursor = conn.cursor()
        cursor.executemany(sql, args)
        if commit is True:
            conn.commit()
            self.close(conn, cursor)
            return None
        else:
            res = cursor.fetchall()
            self.close(conn, cursor)
            return res

    def clear_database(self, spisok):
        conn = self.pool.get_connection()
        cursor = conn.cursor()
        for table in spisok:
            sqlQuery = f"truncate table {table} ;"
            cursor.execute(sqlQuery)

    def injectdata(self, result):
        if len(result)>0:
            conn = self.pool.get_connection()
            cursor = conn.cursor()
            chassis_id = 0

            sql =("INSERT INTO `rrl_mss_info` (`version`,`uptime`,`vendor`,`name`,`erp`,`serial_num`,`license`,`ip`) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)")
            sqldata=result['device_info']

            if len(sqldata)==8:
                device_ip = sqldata[-1]
                logging.info('Start inject Device: ' + str(device_ip))
                cursor.execute(sql, sqldata)
                chassis_id = cursor.lastrowid

                for data in result['fdb']:
                    if len(data) > 0:
                        sql = ("INSERT INTO `rrl_mss_fdb` (`deviceid`,`mac`,`vlan`,`status`,`port`) VALUES (%s,%s,%s,%s,%s)")
                        sqldata=[]
                        sqldata.append(chassis_id)
                        for i in data:
                            sqldata.append(i)
                        cursor.execute(sql, sqldata)

                for data in result['network']:
                    if len(data) > 0:
                        sql = ("INSERT INTO `rrl_mss_network` (`deviceid`,`number`,`name`,`ip`,`mask`,`gw`,`type`,`speed`,`status`) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)")
                        sqldata=[]
                        sqldata.append(chassis_id)
                        for i in data:
                            sqldata.append(i)
                        cursor.execute(sql, sqldata)

                for data in result['bridge']:
                    if len(data) > 0:
                        sql = ("INSERT INTO `rrl_mss_bridge` (`deviceid`,`vlan_id`,`allowed_ports`,`untagged_ports`) VALUES (%s,%s,%s,%s)")
                        sqldata=[]
                        sqldata.append(chassis_id)
                        for i in data:
                            sqldata.append(i)
                        cursor.execute(sql, sqldata)

                for data in result['neighbours']:
                    if len(data) > 0:
                        sql = ("INSERT INTO `rrl_mss_neighbours` (`deviceid`,`neighbour_ip`) VALUES (%s,%s)")
                        sqldata=[]
                        sqldata.append(chassis_id)
                        for i in data:
                            sqldata.append(i)
                        cursor.execute(sql, sqldata)

                for data in result['interfaces']:
                    if len(data) > 0:
                        sql = ("INSERT INTO `rrl_mss_interfaces` (`deviceid`,`eth_port`,`status`,`auto_negotiation`,`bit_rate`,`flow_contr`,`port_in_lag`,`sync_mode`,`acceptable_frame_type`,`eth_rate_limit`,`eth_storm_contr`,`description`) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)")
                        sqldata=[]
                        sqldata.append(chassis_id)
                        for i in data:
                            sqldata.append(i)
                        cursor.execute(sql, sqldata)

                for data in result['odu']:
                    if len(data) > 0:
                        sql = ("INSERT INTO `rrl_mss_odu` (`deviceid`,`slot`,`slot_status`,`port`,`port_status`,`mpt_type`,`link_status`,`value_expected`,`value_transmitted`, `tmn_status`, `ospf_area`, `channel_spacing`,`modulation`,`capacity`,`option`,`shifter`,`tx_frequency`,`min_tx_freq`,`max_tx_freq`,`rx_frequency`,`atpc`,`tx_power`,`power_mode`,`ssm_status`,`booster_status`,`ehcrypt_status`,`passphrase`,`radio_label`,`mpt_in_lag`,`mpt_in_ring`,`xpic_polarization`) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)")
                        sqldata=[]
                        sqldata.append(chassis_id)
                        for i in data:
                            sqldata.append(i)
                        cursor.execute(sql, sqldata)

            conn.commit()
            self.close(conn, cursor)
            logging.info('Finish inject Device ID:' + str(chassis_id)) 
            logging.info('='*50) 


def snmp_session_device(host, community, oid):
    device = []
    for (errorIndication,
         errorStatus,
         errorIndex,
         varBinds) in nextCmd(SnmpEngine(),
                              CommunityData(community),
                              UdpTransportTarget((host, 161)),
                              ContextData(),
                              ObjectType(ObjectIdentity(oid)),
                              maxRows = 6,
                              ):
        if errorIndication:
            print(errorIndication, file=sys.stderr)
            break
        elif errorStatus:
            print('%s at %s' % (errorStatus.prettyPrint(),
                                errorIndex and varBinds[int(errorIndex) - 1][0] or '?'),
                                file=sys.stderr)
            break
        else:
            for varBind in varBinds:
                data = str(varBind)
                data = data.split('=')[-1][:50].strip()
                device.append(data)
    if device:
        dev = []
        device[2] = str(round(int(device[2])/8640000, 2)) + ' days'
        for data in device:
            if 'SNMP' not in data:
                dev.append(data)      
        return dev


def convert_hex_to_int(neigh_hex):
    
    neigh = []
    for data in neigh_hex:
        neigh_list = []
        oktet = data.split('.')
        ip_data = []
        for n in oktet:
            ip_oct = str(int(n, 16))
            ip_data.append(ip_oct)
        neighbour = '.'.join(ip_data)
        neigh_list.append(neighbour)
        neigh.append(neigh_list)

    return neigh


def pars_data(buff, data):

    def template_fsm(data):
        filename = f'show_{data}_mss'
        with open(f'../../fsm-templ/nokia/{filename}.textfsm') as template:
            fsm = textfsm.TextFSM(template)
            fsm.Reset()
            data = fsm.ParseText(buff)
            return data

    if data == 'fdb':
        mac = re.findall(r'mac=(\S+) vlan=(\d+) *(\S+) +\S+ *=(\S+)', buff)
        return mac

    if data == 'bridge':
        with open('../../fsm-templ/nokia/show_bridge_mss.textfsm') as template:
            fsm = textfsm.TextFSM(template)
            fsm.Reset()
            data = fsm.ParseText(buff)
            vlans = []
            for vlan in data:
                for i in range(3):
                    vlan[i] = vlan[i].replace(' ', '')
                vlans.append(vlan)
            return vlans

    if data == 'neighbours':
        find = re.findall(r'(\w\w\.\w\w\.\w\w\.\w\w)', buff)
        neigh_hex = []
        neighbours = []
        for data in find:
            if data.count('0') < 7:
                neigh_hex.append(data)
        if neigh_hex:
            neighbours = convert_hex_to_int(neigh_hex)
        return neighbours

    else:
        return template_fsm(data)


def get_key(dictionary, value):
    for k, v in dictionary.items():
        if v == value:
            return k


def find_file(device_name):
    if device_name == '': return 'NEReport.txt'
    path='./'
    for rootdir, dirs, files in os.walk(path):
        for file in files:       
            if file.split('.')[-1]=='txt' or file.split('.')[-1]=='crdownload':
                data = os.path.join(rootdir, file)
                file_name = data.split('/')[-1]
                if device_name in file_name:
                    return file_name


def delete_file(file_name):
    path = os.path.join(os.path.abspath(os.path.dirname(__file__)), f'{file_name}')
    os.remove(path)


def get_data(device):

    ip = device['ip']
    user = device['username']
    password = device['password']
    oid_device = device['oid_device']
    community = device['community']
    get_data_from_v07 = {'fdb':'35', 'network':'16', 'bridge':'33', 'neighbours' : '39'}
    get_data_from_v06 = {'fdb':'34', 'network':'16', 'bridge':'32', 'neighbours' : '41'}
    get_data_from_v05 = {'fdb':'37', 'network':'19', 'bridge':'35', 'neighbours' : '44'}
    result = {}
    list_of_config = ['device_info','fdb','network','bridge','neighbours', 'interfaces', 'odu']
    for data in list_of_config : result[data] = []

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    
    try:

        logging.info(f'Try to poll the device {ip}')
        device_data = snmp_session_device(ip, community, oid_device)
        logging.info(f'Try to find data about device {ip} info by SNMP')

        if device_data:

            try:
                logging.info(f'Try to find data about device {ip} info by Selenium')
                driver = webdriver.Chrome(executable_path="/usr/bin/chromedriver", options=chrome_options)
                driver.set_page_load_timeout(40)
                driver.get(f'http://{user}:{password}@{ip}/Key')
                rmu_serial_number = driver.find_element(by=By.XPATH, value='/html/body/div[6]/p[1]/label/input').get_attribute('value')
                license_string = driver.find_element(by=By.XPATH, value='/html/body/div[6]/p[2]/label/input').get_attribute('value')
                device_data.append(rmu_serial_number)
                device_data.append(license_string)
                device_data.append(ip)
                result['device_info'] = device_data
                logging.info(f'Data about device {ip} info collected')

                try:
                    logging.info(f'Try to find data from device {ip} about: interfaces and odu from file')
                    driver.get(f'http://{user}:{password}@{ip}/Report')
                    time.sleep(5)
                    device_name = device_data[3]
                    file_name = find_file(device_name)
                    f = open(f'{file_name}', 'r')
                    data = f.read()
                    result['interfaces'] = pars_data(data, 'interfaces')
                    result['odu'] = pars_data(data, 'odu')
                    delete_file(file_name)
                    logging.info(f'Collected data from device {ip} about: interfaces and odu from file')
                except Exception as ex:
                    logging.info('Err recive -->:'+ ip +':'+ str(ex))
                    pass
                
                if 'V05' in device_data[0]: get_data = get_data_from_v05
                elif 'V06' in device_data[0]: get_data = get_data_from_v06
                elif 'V07' in device_data[0]: get_data = get_data_from_v07

                for data in get_data.values():
                    try:
                        key = get_key(get_data, data)
                        logging.info(f'Try to find data from device {ip} about: {key}')
                        driver.get(f'http://{user}:{password}@{ip}/DebugCom?iplbl=0&menu={data}')
                        page = driver.page_source
                        result[key] = pars_data(page, key)
                        logging.info(f'Collected data from device {ip} about: {key}')
                    except Exception as ex:
                        logging.info('Err recive -->:'+ ip +':'+ str(ex))
                        pass
            except Exception as ex:
                logging.info('Err recive -->:'+ ip +':'+ str(ex))
            finally:
                driver.close()
                driver.quit()
        else:
            logging.info(f'Not response from device {ip} by SNMP')
            
    except Exception as ex:
        logging.info('Err recive -->:'+ ip +':'+ str(ex))

    mysql_pool = MySQLPool(**dbconfig)
    mysql_pool.injectdata(result)


def LoadSQLDevices():
    
    sqlQuery = ("SELECT ip from hosts_mss ;")
    mysql_pool = MySQLPool(**dbconfig)
    records = mysql_pool.execute(sqlQuery)
    logging.info(f"In base found {len(records)} devices")

    tables_clear = [
    "rrl_mss_bridge",
    "rrl_mss_fdb",
    "rrl_mss_info",
    "rrl_mss_neighbours",
    "rrl_mss_network",
    "rrl_mss_interfaces",
    "rrl_mss_odu"
    ]

    mysql_pool.clear_database(tables_clear)

    devices = []

    for row in records:
        dictDevice = {}
        dictDevice['ip'] = row[0]
        dictDevice['username'] = 'initial'
        dictDevice['password'] = 'adminadmin'
        dictDevice['oid_device'] = 'iso.3.6.1'
        dictDevice['community'] = 'public'
        devices.append(dictDevice)

    return devices


def LoadHandDevices():
    
    devices = []
    dictDevice = {}
    dictDevice['ip'] = '10.173.143.209'#10.173.87.51'#'10.173.89.27'
    dictDevice['username'] = 'initial'
    dictDevice['password'] = 'adminadmin'
    dictDevice['oid_device'] = 'iso.3.6.1'
    dictDevice['community'] = 'public'
    devices.append(dictDevice)

    return devices


def prepare_for_crawling():

    if not os.path.isdir('./logs/'):
        os.mkdir('./logs/')
    os.system('rm -rf ./logs/*.log')
    os.system('rm -rf ~/scout-crawler/NOKIA/MSS/*.txt')
    os.system('rm -rf ~/scout-crawler/NOKIA/MSS/*.crdownload')


def pool_nokia_mss_devices(invenrory):

    prepare_for_crawling()
    dbconfig["database"] = invenrory
    logger1 = get_logger()
    devices=LoadSQLDevices()

    try:
        p = Pool(processes=20)
        p.map(get_data, devices)
    except Exception as ex:
            logging.info('#Caught an error#:'+ str(ex))
            pass  
    else:
        logging.info("Script is completed")


if __name__ == '__main__':

    pool_nokia_mss_devices(argv[1])



 