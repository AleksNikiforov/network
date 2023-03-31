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
                        filename=f'./logs/UBT-{timestamp}.log',
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

    def injectdata(self, result, ip):
        if len(result)>0:
            conn = self.pool.get_connection()
            cursor = conn.cursor()

            sqldata = result['device_info']
            if len(sqldata)==7:
                logging.info('Inject: ' + str(ip))
                sql =("INSERT INTO `rrl_ubt_neinfo` (`Sitename`,`SiteLocation`,`Latitude`,`Longitude`,`IPLocalAddress`,`WavenceVersion`,`MACAddress`) VALUES (%s,%s,%s,%s,%s,%s,%s)")
                cursor.execute(sql, sqldata)


                for data in result['neighbours']:
                    if len(data)>0:
                        sql = ("INSERT INTO `ubt_neighbor` (`ne_ip`,`if_index1`,`rem_ip`,`if_index2`,`if_name`) VALUES (%s,%s,%s,%s,%s)")
                        sqldata = [i for i in data]
                        cursor.execute(sql, sqldata)

                for data in result['radio_info']:
                    if len(data)>0:
                        sql = ("INSERT INTO `rrl_ubt_modeminfo` (`ip`,`radio_name`,`ch_spacing`,`modulation`,`options`, `net_bandw`,`shifter`,`tx_freq_plan_min`,`tx_freq_plan_max`,`rx_freq_plan_min`,`rx_freq_plan_max`,`tx_freg`,`rx_freg`,`tx_power`) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)")
                        sqldata = [i for i in data]
                        cursor.execute(sql, sqldata)

            conn.commit()
            self.close(conn, cursor)
            logging.info('Finish inject: ' + str(ip))
            logging.info('='*50)


def pars_neighbour(buff, ip):
    
    data = []
    neighbour = re.findall(r'(\S+[\S ]+) (\d+\.\d+\.\d+\.\d+) (\S+ [\S ]+)', buff)
    for ne in neighbour:
        data_tepm = []
        data_tepm.append(ip)
        for n in ne:
            data_tepm.append(n)
        if len(data_tepm[-1]) > 15:
            data_tepm[-1] = ne[-1].split(' ')[0]
            name = ne[-1].split(' ')[1]
            data_tepm.append(name)
        if len(ne[2]) < 15:
            data_tepm.append('none')
        data.append(data_tepm)
    
    return data


def pars_radio_data(device_radio, ip):

    data = []
    data.append(ip)
    data.append(device_radio[0])
    modem_profile = device_radio[1].split(' ')
    for n in modem_profile:
        data.append(n)
    shifter_value = device_radio[2].split(' ')
    for n in shifter_value:
        data.append(n)
    data.append(device_radio[3])
    data.append(device_radio[4])
    data.append(device_radio[5])

    return data
    

def get_data(device):

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--no-sandbox')

    ip = device['ip']
    user = device['username']
    password = device['password']
    user_2 = device['username_2']
    password_2 = device['password_2']
    
    try:

        result = {}
        result['device_info'] = []
        result['neighbours'] = []
        result['radio_info'] = []

        driver = webdriver.Chrome(executable_path="/usr/bin/chromedriver", options=chrome_options)

        driver.get(f'https://{ip}/login?link_to=%2F')
        logging.info(f'LOG-IN to {ip}') 
        username_textbox = driver.find_element(by=By.XPATH, value='//*[@id="username"]')
        username_textbox.send_keys(user)
        password_textbox = driver.find_element(by=By.XPATH, value='//*[@id="userpassword"]')
        password_textbox.send_keys(password)
        driver.find_element(by=By.XPATH, value='/html/body/div[2]/div[2]/form/div[4]/input').click()

        try:
            wrong_user = driver.find_element(by=By.XPATH, value='/html/body/div[2]/div[2]/div/span').text
            logging.info('device: ' + str(ip)+ ' : '+ wrong_user)
            if 'User has been blocked' in wrong_user or 'Wrong user credentials' in wrong_user:
                password = password_2
                user = user_2
                username_textbox = driver.find_element(by=By.XPATH, value='//*[@id="username"]')
                username_textbox.send_keys(user)
                password_textbox = driver.find_element(by=By.XPATH, value='//*[@id="userpassword"]')
                password_textbox.send_keys(password)
                driver.find_element(by=By.XPATH, value='/html/body/div[2]/div[2]/form/div[4]/input').click()
        except Exception as ex:
            pass

        logging.info('device ' + ip + ' user '+ user)

        logging.info(f'ACCEPT to {ip}')       
        element = driver.find_element(by=By.CSS_SELECTOR, value='body > div:nth-child(6) > div > div.signin-form > form > div > input:nth-child(2)')
        driver.execute_script("arguments[0].click();", element)
        logging.info(f'COLLECT DEVICE INFO from {ip}')
        try:
            ip_address = driver.find_element(by=By.NAME, value='an-nei-lb-ipadd').text
            wavence_version = driver.find_element(by=By.NAME, value='an-nei-lb-version').text
            mac = driver.find_element(by=By.NAME, value='an-nei-lb-nemacaddress').text
            name = driver.find_element(by=By.NAME, value='an-nei-lb-sname').text
            erp = driver.find_element(by=By.NAME, value='an-nei-lb-sloc').text
            latitude = driver.find_element(by=By.NAME, value='an-nei-lb-lati').text
            longitude = driver.find_element(by=By.NAME, value='an-nei-lb-long').text
            device = [name, erp, latitude, longitude, ip_address, wavence_version, mac]
            result['device_info'] = device
        except Exception as ex:
            logging.info('#Caught an error in device_info#:'+ ip +':' + str(ex))
            pass   

        if wavence_version == '20.1.0':
            logging.info(f'Monitoring & Maintenance from {ip}')
            monitor_button = driver.find_element(by=By.CSS_SELECTOR, value='#navTop > li:nth-child(2) > a')
            driver.execute_script("arguments[0].click();", monitor_button)

            logging.info(f'NE Neighbours from {ip}')
            ne_naighbour_button = driver.find_element(by=By.CSS_SELECTOR, value='#main-menu-inner > ul > li:nth-child(11) > a > span')
            driver.execute_script("arguments[0].click();", ne_naighbour_button)

            logging.info(f'TRY TO FIND Neighbours from {ip}')
            neighbours = driver.find_element(by=By.ID, value='ne_neighbor_info_dataTable').text
            result['neighbours'] = pars_neighbour(neighbours, ip)

        logging.info(f'TRY TO FIND interfaces from {ip}')

        if wavence_version == '20.1.0':
            logging.info(f'WV {wavence_version} in {ip}')
            interface_button = driver.find_element(by=By.CSS_SELECTOR, value='#navTop > li:nth-child(4) > a')
            driver.execute_script("arguments[0].click();", interface_button)

        else:
            logging.info(f'WV {wavence_version} in {ip}')
            interface_button = driver.find_element(by=By.CSS_SELECTOR, value='#navTop > li:nth-child(3) > a')
            driver.execute_script("arguments[0].click();", interface_button) 

        logging.info(f'radio interfaces from {ip}')
        radio_button = driver.find_element(by=By.CSS_SELECTOR, value='#main-menu-inner > ul > li:nth-child(2) > a > span.mm-text.mmc-dropdown-delay.animated.fadeIn')
        driver.execute_script("arguments[0].click();", radio_button)  

        logging.info(f'radio interfaces detail from {ip}')
        interface_detail_button = driver.find_element(by=By.CSS_SELECTOR, value='#main-menu-inner > ul > li.mm-dropdown.mm-dropdown-root.open > ul > li > a > span')
        driver.execute_script("arguments[0].click();", interface_detail_button)

        expand_all_button = driver.find_element(by=By.CSS_SELECTOR, value='#expand_all > span')
        driver.execute_script("arguments[0].click();", expand_all_button)


        try:
            device_radio = []
            radio_name = driver.find_element(by=By.XPATH, value='//*[@id="radio_config"]/div/div[1]/span').text
            protect_mode = radio_name[-5:]
            modem_profile_a = driver.find_element(by=By.XPATH, value='//*[@id="open_modemp_1"]/center[2]/table/tbody/tr[4]').text
            freg_settings_profile_a = driver.find_element(by=By.XPATH, value='//*[@id="open_frequency_1"]/div/div/center/table/tbody/tr[2]').text
            tx_freg_a = driver.find_element(by=By.ID, value='tx_freq1_1').get_attribute('value')
            rx_freg_a = driver.find_element(by=By.ID, value='rx_freq1_1').get_attribute('value')
            tx_power_a = driver.find_element(by=By.ID, value='acm_rtpc_tx_power1_1').get_attribute('value')
            device_radio_a = [radio_name, modem_profile_a, freg_settings_profile_a, tx_freg_a, rx_freg_a, tx_power_a]
            device_radio.append(pars_radio_data(device_radio_a, ip))

            if protect_mode == '(2+0)':
                modem_profile_b = driver.find_element(by=By.XPATH, value='//*[@id="open_modemp_2"]/center[2]/table/tbody/tr[4]').text
                freg_settings_profile_b = driver.find_element(by=By.XPATH, value='//*[@id="open_frequency_2"]/div/div/center/table/tbody/tr[2]').text
                tx_freg_b = driver.find_element(by=By.ID, value='tx_freq1_1').get_attribute('value')
                rx_freg_b = driver.find_element(by=By.ID, value='rx_freq1_1').get_attribute('value')
                tx_power_b = driver.find_element(by=By.ID, value='acm_rtpc_tx_power1_1').get_attribute('value')
                device_radio_b = [radio_name, modem_profile_b, freg_settings_profile_b, tx_freg_b, rx_freg_b, tx_power_b]
                device_radio.append(pars_radio_data(device_radio_b, ip))

            result['radio_info'] = device_radio

        except Exception as ex:
            logging.info('#Caught an error in radio_info#:'+ ip +':'+ str(ex))
            pass  
        
        logging.info(f'{result} from {ip}')     

    except Exception as ex:
        logging.info('Err recive -->:'+ ip +':'+ str(ex))
    finally:
        driver.close()
        driver.quit()

    mysql_pool = MySQLPool(**dbconfig)
    mysql_pool.injectdata(result, ip)


def LoadSQLDevices():
    
    sqlQuery = ("SELECT ip from hosts_ubt ;")
    mysql_pool = MySQLPool(**dbconfig)
    records = mysql_pool.execute(sqlQuery)
    logging.info(f"In base found {len(records)} devices")

    tables_clear = [
    "rrl_ubt_modeminfo",
    "rrl_ubt_neinfo",
    "ubt_neighbor",
    ]

    mysql_pool.clear_database(tables_clear)

    devices = []

    for row in records:
        dictDevice = {}
        dictDevice['ip'] = row[0]
        dictDevice['username'] = 'initial'
        dictDevice['password'] = 'adminadmin'
        dictDevice['username_2'] = 'Craftperson'
        dictDevice['password_2'] = 'craftcraft'
        devices.append(dictDevice)

    return devices


def LoadHandDevices():
    
    devices = []
    dictDevice = {}
    dictDevice['ip'] = '10.174.82.118' #'10.174.152.103' #'10.174.150.173'# 
    dictDevice['username'] = 'initial'
    dictDevice['password'] = 'adminadmin'
    dictDevice['username_2'] = 'Craftperson'
    dictDevice['password_2'] = 'craftcraft'
    devices.append(dictDevice)

    return devices


def prepare_for_crawling():

    if not os.path.isdir('./logs/'):
        os.mkdir('./logs/')
    os.system('rm -rf ./logs/*')


def pool_ubt_devices(invenrory):

    prepare_for_crawling()
    dbconfig["database"] = invenrory
    logger1 = get_logger()
    devices = LoadSQLDevices()
    send_command_to_devices(devices)


def send_command_to_devices(devices):

    try:
        p = Pool(processes=5)
        p.map(get_data, devices)
    except Exception as ex:
            logging.info('Caught an error:'+ str(ex))
            pass  
    else:
        logging.info("Device poll completed")


if __name__ == '__main__':

    pool_ubt_devices(argv[1])




 