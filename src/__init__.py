from configparser import ConfigParser

conf = ConfigParser()
conf.read('conf/config.ini', encoding='utf-8')

# ******log設定******
# 關閉log功能 輸入選項 (true, True, 1) 預設 不關閉
LOG_DISABLE = conf.getboolean('LOG', 'LOG_DISABLE', fallback=False)
# logs路徑 預設 logs
LOG_PATH = conf.get('LOG', 'LOG_PATH', fallback='logs')
# 關閉紀錄log檔案 輸入選項 (true, True, 1)  預設 不關閉
LOG_FILE_DISABLE = conf.getboolean('LOG', 'LOG_FILE_DISABLE', fallback=False)
# 設定紀錄log等級 DEBUG,INFO,WARNING,ERROR,CRITICAL 預設WARNING
LOG_LEVEL = conf.get('LOG', 'LOG_LEVEL', fallback='WARNING')

MEGA_ACCOUNT = conf.get('SETTING', 'MEGA_ACCOUNT', fallback='')
MEGA_PASSWORD = conf.get('SETTING', 'MEGA_PASSWORD', fallback='')
MEGA_LISTEN_DIR = conf.get('SETTING', 'MEGA_LISTEN_DIR', fallback='')