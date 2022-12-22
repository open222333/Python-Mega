from configparser import ConfigParser

conf = ConfigParser()
conf.read('config.ini', encoding='utf-8')

MEGA_ACCOUNT = conf.get('MEGA', 'MEGA_ACCOUNT', fallback='')
MEGA_PASSWORD = conf.get('MEGA', 'MEGA_PASSWORD', fallback='')
MEGA_LISTEN_DIR = conf.get('MEGA', 'MEGA_LISTEN_DIR', fallback='')