#!/usr/bin/python3.8
# -*- coding: utf-8 -*-
from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime
import logging
from sys import argv
import sys
import mysql.connector.pooling
from pysnmp.hlapi import *
import os
import time



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
                        filename=f'./logs/NOKIA-MPRE-{argv[1]}-{timestamp}.log',
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

            sql =("INSERT INTO `mpre_device_new` (`version`, `uptime`, `name`, `erp`, `ip`, `host_time`) VALUES (%s,%s,%s,%s,%s,%s)")
            sqldata=result['mpre_device_6']

            if len(sqldata)==6:
                device_name = sqldata[2]
                logging.info('Start inject Device: ' + str(device_name))
                cursor.execute(sql, sqldata)
                chassis_id = cursor.lastrowid

                for data in result['mpre_neighbour_1']:
                    if len(data) > 0:
                        sql =("INSERT INTO `mpre_neighbours_new` (`deviceid`,`ip`) VALUES (%s,%s)")
                        sqldata=[]
                        sqldata.append(chassis_id)
                        sqldata.append(data)
                        cursor.execute(sql, sqldata)

                for data in result['mpre_version_2']:
                    if len(data) > 0:
                        sql =("INSERT INTO `mpre_version_new` (`deviceid`,`active_version`,`standby_version`) VALUES (%s,%s,%s)")
                        sqldata=[]
                        sqldata.append(chassis_id)
                        for i in data:
                            sqldata.append(i)
                        cursor.execute(sql, sqldata)

                for data in result['mpre_interfaces']:
                    if len(data) > 0:
                        sql =("INSERT INTO `mpre_interface_new` (`deviceid`,`interface`,`capacity`) VALUES (%s,%s,%s)")
                        sqldata=[]
                        sqldata.append(chassis_id)
                        for i in data:
                            sqldata.append(i)
                        cursor.execute(sql, sqldata)

                for data in result['mpre_company_id_3']:
                    if len(data) > 0:
                        sql =("INSERT INTO `mpre_comp_id_new` (`deviceid`,`company_id`) VALUES (%s,%s)")
                        sqldata=[]
                        sqldata.append(chassis_id)
                        sqldata.append(data)
                        cursor.execute(sql, sqldata)

                for data in result['mpre_mnemonic_3']:
                    if len(data) > 0:
                        sql =("INSERT INTO `mpre_mnemonic_new` (`deviceid`,`mnemonic`) VALUES (%s,%s)")
                        sqldata=[]
                        sqldata.append(chassis_id)
                        sqldata.append(data)
                        cursor.execute(sql, sqldata)

                for data in result['mpre_hard_part_num_3']:
                    if len(data) > 0:
                        sql =("INSERT INTO `mpre_hard_part_new` (`deviceid`,`hard_part_num`) VALUES (%s,%s)")
                        sqldata=[]
                        sqldata.append(chassis_id)
                        sqldata.append(data)
                        cursor.execute(sql, sqldata)

                for data in result['mpre_soft_part_num_3']:
                    if len(data) > 0:
                        sql =("INSERT INTO `mpre_soft_part_new` (`deviceid`,`soft_part_num`) VALUES (%s,%s)")
                        sqldata=[]
                        sqldata.append(chassis_id)
                        sqldata.append(data)
                        cursor.execute(sql, sqldata)

                for data in result['mpre_factory_identity_3']:
                    if len(data) > 0:
                        sql =("INSERT INTO `mpre_factory_id_new` (`deviceid`,`factory_identity`) VALUES (%s,%s)")
                        sqldata=[]
                        sqldata.append(chassis_id)
                        sqldata.append(data)
                        cursor.execute(sql, sqldata)

                for data in result['mpre_lldp_neighbours_6']:
                    if len(data) > 0:
                        sql =("INSERT INTO `mpre_lldp_neighbours_new` (`deviceid`,`id_1`,`neighbour_mac`,`id_2`,`neighbour_num`,`neighbour_intf`,`neighbour_name`) VALUES (%s,%s,%s,%s,%s,%s,%s)")
                        sqldata=[]
                        sqldata.append(chassis_id)
                        for i in data:
                            sqldata.append(i)
                        cursor.execute(sql, sqldata)


            conn.commit()
            self.close(conn, cursor)
            logging.info('Finish inject Device ID:' + str(chassis_id)) 
            logging.info('='*50) 


def snmp_session(host, community, oid, max_rows = 16):
    itog = []
    for (errorIndication,
         errorStatus,
         errorIndex,
         varBinds) in nextCmd(SnmpEngine(),
                              CommunityData(community),
                              UdpTransportTarget((host, 161)),
                              ContextData(),
                              ObjectType(ObjectIdentity(oid)),
                              maxRows = max_rows,
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
                value = str(varBind)
                data = value.split('=')[-1].strip()
                if oid == '1.3.111.2.802.1.1.13.1.4.1.1':
                    data = value.split('70001.1.1 =')[-1].strip()
                if len(data) > 0 and 'SNMP' not in data:
                    itog.append(data)
                if len(data) == 0 and oid == '1.3.111.2.802.1.1.13.1.4.1.1':
                    data = 'none'
                    itog.append(data)

    return itog


def pars_data(data, ip, find = None):

    if find == 'mpre_device_6':
        data.append(ip)
        data[1] = str(round(int(data[1])/8640000, 2)) + ' days'

    if find == 'mpre_capacity_interface_2':
        data[0] = str(round(int(data[0])/1000000, 3)) + ' Mbit/s'
        data[1] = str(round(int(data[1])/1000000, 3)) + ' Mbit/s'
    
    return data


def convert(dictionary):

    result = dictionary.copy()

    del result['mpre_type_interfaces_2']
    del result['mpre_capacity_interface_2']
    interfaces = []
    if dictionary['mpre_type_interfaces_2'] and dictionary['mpre_capacity_interface_2']:
        interfaces.append([dictionary['mpre_type_interfaces_2'][0], dictionary['mpre_capacity_interface_2'][0]])
        interfaces.append([dictionary['mpre_type_interfaces_2'][1], dictionary['mpre_capacity_interface_2'][1]])
    result['mpre_interfaces'] = interfaces

    if dictionary['mpre_date_2']:
        result['mpre_date_2'] = [x for x in dictionary['mpre_date_2'] if x != 'notYetActivated']
        if result['mpre_date_2']:
            result['mpre_device_6'].append(result['mpre_date_2'][0])
        else:
            result['mpre_device_6'].append('none')
    else:
        result['mpre_device_6'].append('none')
    del result['mpre_date_2']

    if dictionary['mpre_version_2']:
        result['mpre_version_2'] = [dictionary['mpre_version_2']]
        if len(result['mpre_version_2'][0]) < 2:
            result['mpre_version_2'][0].append('none')

    if dictionary['mpre_lldp_neighbours_6']:
        result['mpre_lldp_neighbours_6'] = [dictionary['mpre_lldp_neighbours_6']]

    return result


def send_show(device):

    ip = device['ip']
    community = device['community']

    logging.info('Start interview --> '+ ip)

    oids = {
    'mpre_device_6':'iso.3.6.1.2.1.1.1',
    'mpre_neighbour_1':'iso.3.6.1.4.1.637.54.1.1.6.1.14.1',
    'mpre_version_2' : 'iso.3.6.1.4.1.637.54.1.1.3.1.40.1.7',
    'mpre_date_2' : 'iso.3.6.1.4.1.637.54.1.1.3.1.40.1.4',
    'mpre_type_interfaces_2' : 'iso.3.6.1.2.1.2.2.1.2',
    'mpre_capacity_interface_2' : 'iso.3.6.1.2.1.2.2.1.5',
    'mpre_company_id_3' : 'iso.3.6.1.4.1.637.54.1.1.8.1.4.1.2.1.11',
    'mpre_mnemonic_3' : 'iso.3.6.1.4.1.637.54.1.1.8.1.4.1.3.1.11',
    'mpre_hard_part_num_3' : 'iso.3.6.1.4.1.637.54.1.1.8.1.4.1.5.1.11',
    'mpre_soft_part_num_3' : 'iso.3.6.1.4.1.637.54.1.1.8.1.4.1.6.1.11',
    'mpre_factory_identity_3' : 'iso.3.6.1.4.1.637.54.1.1.8.1.4.1.7.1.11',
    'mpre_serial_num_3' : 'iso.3.6.1.4.1.637.54.1.1.8.1.4.1.8.1.11',
    'mpre_lldp_neighbours_6' : '1.3.111.2.802.1.1.13.1.4.1.1',
    }

    result = {}

    for key in oids:
        result[key] = []

    for key in oids:
        oid = oids[key]
        try:   
            logging.info(f'start snmp_session {ip} --> {key}')
            snmp = snmp_session(ip, community, oid, max_rows = int(key.split('_')[-1]))
            if not snmp:
                if key == 'mpre_device_6':
                    break
                else:
                    continue
            logging.info(f'stop snmp_session {ip} --> {key}')
            result[key] = pars_data(snmp, ip, find = key)
        except (Exception) as e :
            logging.info('Err recive -->:'+ ip +':'+ str(e))
            pass
        
    result = convert(result) 
    logging.info(result)
    return result


def LoadHandDevices():

    devices = []
    dictDevice = {}
    dictDevice['ip'] = '10.175.193.74'
    dictDevice['community'] = 'public'
    devices.append(dictDevice)

    return devices


def LoadSQLDevices():

    sqlQuery = ("SELECT ip from hosts_mpre;")
    mysql_pool = MySQLPool(**dbconfig)
    records = mysql_pool.execute(sqlQuery)
    logging.info(f"In base found {len(records)} devices") 

    tables_clear = [
    "mpre_device_new",
    "mpre_neighbours_new",
    "mpre_interface_new",
    "mpre_version_new",
    "mpre_factory_id_new",
    "mpre_hard_part_new",
    "mpre_mnemonic_new",
    "mpre_soft_part_new",
    "mpre_comp_id_new",
    "mpre_lldp_neighbours_new",
    ]

    mysql_pool.clear_database(tables_clear)

    devices = []

    for row in records:
        dictDevice = {}
        dictDevice['ip'] = row[0]
        dictDevice['community'] = 'public'
        devices.append(dictDevice)

    return devices


def send_command_to_devices(devices):
    future_ssh = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_ssh = [executor.submit(send_show, device) for device in devices]
        for f in as_completed(future_ssh):
            logging.info("Poll is completed")
            try:
                result = f.result()
            except (Exception) as e :
                logging.info(e)
            else:
                mysql_pool = MySQLPool(**dbconfig)
                mysql_pool.injectdata(result)


def prepare_for_crawling():

    if not os.path.isdir('./logs/'):
        os.mkdir('./logs/')
    os.system('rm -rf ./logs/*.log')


def main_nokia_mpre(datatbase):

    prepare_for_crawling()
    dbconfig["database"] = datatbase
    logger1 = get_logger()
    devices=LoadSQLDevices()
    send_command_to_devices(devices)


if __name__ == '__main__':

    main_nokia_mpre(argv[1])