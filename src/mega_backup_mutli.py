from .crypto import a32_to_str, get_chunks, makebyte, str_to_a32, a32_to_base64, base64_url_encode, encrypt_attr, encrypt_key
from .logger import Log
from . import LOG_LEVEL, LOG_FILE_DISABLE
from datetime import datetime
from mega import Mega
from time import sleep, time
from Crypto.Cipher import AES
from Crypto.Util import Counter
import requests
import random
import json
import re
import os

logger = Log('BACKUP')
logger.set_level(LOG_LEVEL)
if not LOG_FILE_DISABLE:
    logger.set_file_handler()
logger.set_msg_handler


class MegaBackupFile:
    """上傳檔案至mega
    """

    def __init__(self, file_path: str, mega_folder_id: str, mega_folder: str = None, test=False) -> None:
        """_summary_

        Args:
            file_path (str): 路徑
            mega_folder_id (str): 上傳的資料夾id
            mega_folder (str): 上傳的資料夾名稱. Defaults to None.
            test (bool): 是否為測試. Defaults to False.
        """
        self.file_path = file_path

        self.mega_folder = mega_folder
        self.mega_folder_id = mega_folder_id

        self.sub_f = False
        self.sub_folder_id = None
        self.sub_folder_name = None

        self.chunk_size = 500000000
        self.expired_days = 7
        self.test = test

    def set_mega_auth(self, account: str, password: str):
        """
        設置帳號

        Args:
            account (str): mega 帳號
            password (str): mega 密碼
        """
        mega = Mega_Custom()
        self.mega_client = mega.login(account, password)

    def set_chunk_size(self, size: int):
        """設置分割檔案大小 byte

        Args:
            size (int): byte
        """
        self.chunk_size = size

    def set_expired_days(self, days: int):
        """設置過期天數

        Args:
            days (int): 天數
        """
        self.expired_days = days

    def set_sub_folder_upload_on(self):
        """使用子資料夾資訊上傳
        """
        self.sub_f = True

    def set_sub_folder_upload_off(self):
        """關閉使用子資料夾資訊上傳
        """
        self.sub_f = False

    def set_folder_info(self, folder_id: str, folder_name: str):
        """設置mega資料夾資訊

        Args:
            folder_id (str): 資料夾id
            folder_name (str): 資料夾名稱
        """
        self.mega_folder_id = folder_id
        self.mega_folder = folder_name

    def set_sub_folder_info(self, folder_id: str, folder_name: str):
        """設置mega子資料夾資訊

        Args:
            folder_id (str): 子資料夾id
            folder_name (str): 子資料夾名稱
        """
        self.sub_folder_id = folder_id
        self.sub_folder_name = folder_name

    def __get_time_str(self, total_secends: int) -> str:
        """依照秒數 回傳時間

        Args:
            total_secends (int): 總秒數

        Returns:
            str: 時間字串
        """
        msg = ''
        seconds = total_secends % 60
        minutes = (total_secends // 60) % 60
        hours = ((total_secends // 60) // 60) % 24
        days = ((total_secends // 60) // 60) // 24
        if days != 0:
            msg += f"{days}天"
        if hours != 0:
            msg += f"{hours}時"
        if minutes != 0:
            msg += f"{minutes}分"
        msg += f"{int(seconds)}秒"
        return msg

    def __get_date(self, timestamp: int, format: str = "%Y-%m-%d %H:%M:%S") -> str:
        """使用時間戳取得日期格式

        Args:
            timestamp (int): 時間戳
            format (str): 日期格式, Defaults to "%Y-%m-%d %H:%M:%S".

        Returns:
            str: 回傳日期格式 預設 2019-05-10 23:40:00
        """
        return datetime.utcfromtimestamp(timestamp).strftime(format)

    def __print_msg(self, msg: str):
        """顯示訊息

        Args:
            msg (str): 訊息內容
        """
        logger.info(f'=== {msg} ===')

    def __split_file(self, path: str, chunk_size: int = 1024 * 1024 * 5, filename: str = None):
        """分割檔案

        Args:
            path (str): 檔案路徑
            chunk_size (str): 分割大小. Defaults to 500MB 1024 * 1024 * 5
            filename (str, optional): 檔名. Defaults to None.
        """
        if not filename:
            filename = os.path.basename(path)
        file_dir = os.path.dirname(path)

        self.__print_msg(f'分割 {filename} 開始')

        command = f'split -d -a 3 -b {chunk_size} {file_dir}/{filename} {file_dir}/{filename}._'
        os.system(command)

        self.__print_msg(f'分割 {filename} 結束')

    def create_folder(self, name: str, folder_id: str = None) -> dict:
        """建立mega資料夾 回傳資料夾名稱 資料夾id

        Args:
            name (str): 指定資料夾名稱
            folder_id (str, optional): 指定父資料夾id. Defaults to None.

        Returns:
            dict: 回傳資料夾名稱 資料夾id {name:id}
        """
        if not folder_id:
            info = self.mega_client.create_folder_from_id(name, folder_id)
        else:
            info = self.mega_client.create_folder_from_id(name, self.mega_folder_id)
        return info

    def __upload_to_mega(self, path: str, folder_id: str = None, folder_name: str = None):
        """上傳至mega

        Args:
            path (str): 檔案路徑
            folder_id (str): 指定上傳目標資料夾id. Defaults to self.mega_folder_id.
            folder_name (str): 指定上傳目標資料夾名稱. Defaults to self.mega_folder.

        Returns:
            _type_: 回傳上傳資訊
        """
        # 取得檔案大小 MB
        tar_size = round(os.path.getsize(path) / float(1000 * 1000), 2)
        filename = os.path.basename(path)

        if not folder_name:
            folder_name = self.mega_folder

        if not folder_id:
            folder_id = self.mega_folder_id

        self.__print_msg(f'上傳資料 {filename} 至 {folder_name}, 檔案大小 {tar_size} MB')

        upload_start_time = time()

        mega_info = self.mega_client.upload_c(
            filename=path,
            dest=folder_id,
            dest_filename=filename
        )

        logger.debug(mega_info)

        upload_end_time = time()

        take_time = self.__get_time_str(int(round(upload_end_time - upload_start_time, 0)))

        self.__print_msg(f'上傳資料 {filename} 至 {folder_name} 完成,耗時{take_time}')

        return mega_info

    def __remove_mega_file_by_private_id(self, private_id, filename=None):
        """根據 private_id 刪除mega上檔案

        Args:
            private_id (_type_): 檔案id
            filename (_type_, optional): 檔案名稱. Defaults to None.
        """
        if filename:
            filename = filename
        else:
            filename = private_id

        self.__print_msg(f'刪除mega上的 {filename} 開始')
        try:
            self.mega_client.destroy(private_id)
        except Exception as err:
            logger.error(msg=err, exc_info=True)
        self.__print_msg(f'刪除mega上的 {filename} 結束')

    def __remove_file(self, path: str):
        """刪除檔案

        Args:
            path (str): 檔案路徑
        """
        filename = os.path.basename(path)
        self.__print_msg(f'刪除 {filename} 開始')
        try:
            os.remove(path)
        except Exception as err:
            logger.error(msg=err, exc_info=True)
        self.__print_msg(f'刪除 {filename} 結束')

    def __get_mega_folder_files(self):
        """取得 指定mega資料夾內所有檔案資訊

        [mega.py API_INFO.md 詳細說明](https://github.com/odwyersoftware/mega.py/blob/master/API_INFO.md)
        """
        # folder_id = self.mega_client.find(self.mega_folder)[0]
        folder_id = self.mega_folder_id
        all_files = self.mega_client.get_files()
        folder_files = {}
        for _, file_info in all_files.items():
            if file_info['p'] == folder_id:
                folder_files[file_info['h']] = file_info
        return folder_files

    def __is_expired(self, file_ts: int) -> bool:
        """檢查是否超出設定的期限日期

        Args:
            file_ts (int): 檔案創建 時間戳

        Returns:
            bool: _description_
        """
        now = int(round(time()))
        sec = now - file_ts
        expired_sec = self.expired_days * 24 * 60 * 60

        if sec > expired_sec:
            return True
        return False

    def check_mega_files(self):
        """刪除過期的mega檔案
        """
        start = time()
        self.__print_msg(f'檢查已超過{self.expired_days}天的檔案')
        files = self.__get_mega_folder_files()

        # 紀錄已處理的id
        processed_id = []

        for private_id, info in files.items():
            if private_id not in processed_id:
                processed_id.append(private_id)
                if self.__is_expired(info['ts']):
                    if isinstance(info['a'], dict):
                        self.__print_msg(f'{info["a"]["n"]} 創建日期{self.__get_date(info["ts"])} 已超過{self.expired_days}天')
                        self.__remove_mega_file_by_private_id(private_id, info['a']['n'])
                    else:
                        self.__print_msg(f'{info["a"]} 創建日期{self.__get_date(info["ts"])} 已超過{self.expired_days}天')
                        self.__remove_mega_file_by_private_id(private_id, info['a'])

        end = time()
        self.__print_msg(f'檢查完畢 耗時{self.__get_time_str(int(round(end - start)))}')

    def run_split(self, path=None):
        """執行分割
        """
        if path == None:
            path = self.file_path

        if os.path.getsize(self.file_path) > self.chunk_size:
            # 分割檔案
            self.__split_file(self.file_path, self.chunk_size)

            # 非測試時 刪除檔案
            if not self.test:
                self.__remove_file(self.file_path)
        else:
            filename = os.path.basename(self.file_path)
            file_dir = os.path.dirname(self.file_path)
            logger.debug(f'執行分割 filename: {filename}, file_dir: {file_dir}')
            if not bool(re.search(r'\.tar\._[\d]{1,10}$', filename)):
                os.rename(self.file_path, f"{file_dir}/{filename}._1")

    def run(self, path=None):
        """執行上傳
        """
        if path == None:
            path = self.file_path

        if self.sub_f:
            info = self.__upload_to_mega(path, self.sub_folder_id, f'{self.mega_folder}/{self.sub_folder_name}')
        else:
            info = self.__upload_to_mega(path)

        # 非測試時
        logger.debug(info)

        # 非測試時 刪除檔案
        if not self.test:
            self.__remove_file(path)


class MegaListen:
    """監聽資料夾 若有符合條間的檔案則執行上傳至mega
    """

    def __init__(self, dir_path: str, mega_account: str, mega_password: str, folder_id: str, listen_type: int = 1, test=False) -> None:
        """_summary_

        Args:
            dir_path (str): 監聽路徑
            mega_account (str): mega帳號
            mega_password (str): mega密碼
            folder_id (str): mega目標資料夾ID
            test (bool, optional): 是否為測試. Defaults to False.
            listen_type (int): 0: 'split', 1: 'upload', 2: 'check_expired_file' . Defaults to 1.
        """
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        type_dict = {
            0: 'split',
            1: 'upload',
            2: 'check_expired_file'
        }

        self.dir_path = dir_path

        self.schedule_quantity = None

        self.mega_account = mega_account
        self.mega_password = mega_password
        self.folder_id = folder_id

        self.test = test
        self.listen_type = type_dict[listen_type]
        self.is_sleep = False
        self.file_extensions = None
        self.pattern = None

        self.expired_days = None

        self.date = datetime.now().__format__("%Y%m%d")
        self.sub_f_info_json = 'sub_folder_info.json'

        self.pass_extensions = ['.temp']

        # 分割功能 才進行 初始化子資料夾
        if not self.__check_sub_f_name() and listen_type == 0:
            client = Mega_Custom().login(self.mega_account, self.mega_password)
            sub_f_info = client.create_folder_from_id(self.date, self.folder_id)
            self.set_sub_folder_info_to_json(self.date, sub_f_info[self.date])

    def set_file_extension(self, *extension: str):
        """設置 篩選副檔名條件

        extension: 指定副檔名
        """
        self.file_extensions = extension

    def set_expired_days(self, days: int):
        """設置過期天數

        Args:
            days (int): 天數
        """
        self.expired_days = days

    def set_schedule_quantity(self, schedule_quantity: int):
        """設置 排程數量

        Args:
            schedule_quantity (int): 排程數量
        """
        self.schedule_quantity = schedule_quantity

    def set_pattern(self, pattern):
        """設置 匹配檔名 pattern

        Args:
            pattern (_type_): re規則
        """
        self.pattern = pattern

    def set_date(self, date: str):
        """設定日期 格式: 20230101

        Args:
            date (_type_): 格式: 20230101
        """
        self.date = date

    def set_folder_id(self, folder_id: str):
        """設定資料夾ID

        Args:
            folder_id (_type_): 資料夾id
        """
        self.folder_id = folder_id

    def set_sub_f_info_json(self, path: str):
        """設置sub_f_info_json

        Args:
            path (str): json路徑
        """
        self.sub_f_info_json = path

    def set_sub_folder_info_to_json(self, folder_name: str, folder_id: str):
        """設置json紀錄子資料夾資訊

        Args:
            folder_name (str): 子資料夾名稱
            folder_id (str): 子資料夾id
        """
        sub_f_info = {
            'name': folder_name,
            'folder_id': folder_id
        }
        with open(self.sub_f_info_json, 'w') as f:
            try:
                f.write(json.dumps(sub_f_info))
            except Exception as err:
                logger.error(msg=err, exc_info=True)
        logger.debug(f'設置json紀錄子資料夾資訊: {sub_f_info}')
        self.sub_f_info = sub_f_info

    def get_sub_folder_info_from_json(self):
        """從json取得json紀錄子資料夾資訊

        Returns:
            _type_:
            格式：{
                'name': folder_name,
                'folder_id': folder_id
            }
        """
        with open(self.sub_f_info_json, 'r') as f:
            try:
                sub_f_info = json.loads(f.read())
            except Exception as err:
                logger.error(msg=err, exc_info=True)
        logger.debug(f'取得json紀錄子資料夾資訊: {sub_f_info}')
        self.sub_f_info = sub_f_info
        return sub_f_info

    def __check_sub_f_name(self) -> bool:
        """檢查子資料夾名稱是否已建立id資訊

        若self.sub_f_info_json紀錄的
        name值 與 今日日期相同
        folder_id值 非空值
        回傳 True

        Returns:
            bool :
        """
        if not os.path.exists(self.sub_f_info_json):
            return False

        with open(self.sub_f_info_json, 'r') as f:
            sub_f_info = json.loads(f.read())

        today = datetime.now().__format__("%Y%m%d")

        if self.date != today:
            self.set_date(today)

        logger.debug(f'檢查子資料夾名稱是否已建立id資訊, info[\'name\']: {sub_f_info["name"]}, date: {today}')
        if today == sub_f_info['name'] and sub_f_info['folder_id'] != '':
            return True
        return False

    def __check_extension(self, filename: str, *file_extensions):
        """檢查 是否符合副檔名條件
        若無設置file_extensions 則回傳True

        Args:
            filename (str): 檔名

        Returns:
            bool: 是否符合副檔名條件
        """
        if len(file_extensions) > 0:
            _, file_extension = os.path.splitext(filename)
            return file_extension[1:] in file_extensions
        elif self.file_extensions:
            _, file_extension = os.path.splitext(filename)
            return file_extension[1:] in self.file_extensions
        else:
            return True

    def __check_filename(self, filename: str, pattern=None):
        """檢查檔名是否匹配
        若無設置pattern 則回傳True

        Args:
            filename (str): 檔名

        Returns:
            _type_: _description_
        """
        if pattern:
            r = re.search(pattern, filename)
            # logger.debug(f'檢查檔名是否匹配 {filename}, pattern={pattern}, {r}')
            if r:
                return True
            else:
                return False
        else:
            return True

    def listen(self, cannal_id=None):
        """執行監聽
        """
        while True:
            files = os.listdir(self.dir_path)
            for file in files:
                _, file_extension = os.path.splitext(file)
                if file_extension not in self.pass_extensions:
                    msg = {
                        'file': file,
                        'check_filename': self.__check_filename(file, self.pattern),
                        'check_extension': self.__check_extension(file)
                    }
                    logger.debug(msg)
                    if self.__check_filename(file, self.pattern) and self.__check_extension(file):
                        if self.listen_type == 'upload':
                            # 判斷是否多開
                            if self.schedule_quantity > 0:
                                try:
                                    split_num = int(re.findall(r'\.tar\._(.*)', file)[0])
                                    s_info = {
                                        'split_num': split_num,
                                        'schedule_quantity': self.schedule_quantity,
                                        'cannal_id': cannal_id,
                                        'remainder': split_num % self.schedule_quantity
                                    }
                                except Exception as err:
                                    logger.error(msg=err, exc_info=True)

                                logger.debug(s_info)

                                # 若非分割檔格式 進入下一圈
                                if split_num is None:
                                    continue

                                if s_info['remainder'] == s_info['cannal_id']:
                                    mbf = MegaBackupFile(f'{self.dir_path}/{file}', mega_folder_id=self.folder_id, test=self.test)

                                    if not self.test:
                                        mbf.set_mega_auth(self.mega_account, self.mega_password)

                                    if self.expired_days:
                                        mbf.set_expired_days(self.expired_days)

                                    try:
                                        # 使用日期子資料夾
                                        sub_f_info = self.get_sub_folder_info_from_json()
                                        mbf.set_sub_folder_info(
                                            folder_id=sub_f_info['folder_id'],
                                            folder_name=sub_f_info['name']
                                        )
                                        mbf.set_sub_folder_upload_on()
                                    except Exception as err:
                                        logger.error(msg=err, exc_info=True)
                                        mbf.set_sub_folder_upload_off()

                                    mbf.run()
                            else:
                                mbf = MegaBackupFile(f'{self.dir_path}/{file}', mega_folder_id=self.folder_id, test=self.test)

                                if not self.test:
                                    mbf.set_mega_auth(self.mega_account, self.mega_password)

                                if self.expired_days:
                                    mbf.set_expired_days(self.expired_days)

                                try:
                                    # 使用日期子資料夾
                                    sub_f_info = self.get_sub_folder_info_from_json()
                                    mbf.set_sub_folder_info(
                                        folder_id=sub_f_info['folder_id'],
                                        folder_name=sub_f_info['name']
                                    )
                                    mbf.set_sub_folder_upload_on()
                                except Exception as err:
                                    logger.error(msg=err, exc_info=True)
                                    mbf.set_sub_folder_upload_off()

                                mbf.run()
                        elif self.listen_type == 'split':

                            mbf = MegaBackupFile(f'{self.dir_path}/{file}', mega_folder_id=self.folder_id, test=self.test)

                            # 是否建立日期子資料夾
                            if not self.__check_sub_f_name():
                                if not self.test:
                                    mbf.set_mega_auth(self.mega_account, self.mega_password)

                                sub_f_info = mbf.create_folder(self.date, mbf.mega_folder_id)

                                self.set_sub_folder_info_to_json(self.date, sub_f_info[self.date])

                            # 分割
                            mbf.run_split()
                        elif self.listen_type == 'check_expired_file':
                            # 刪除超過指定天數的檔案
                            mbf = MegaBackupFile(f'{self.dir_path}/{file}', mega_folder_id=self.folder_id, test=self.test)

                            if not self.test:
                                mbf.set_mega_auth(self.mega_account, self.mega_password)

                            if self.expired_days:
                                mbf.set_expired_days(self.expired_days)

                            # 刪除過期的mega檔案
                            mbf.check_mega_files()
                self.is_sleep = False
            else:
                if not self.is_sleep:
                    self.is_sleep = True
                    print('等候中')
                sleep(1)


class Mega_Custom(Mega):
    """繼承Mega套件 客製化功能
    """

    def create_folder_from_id(self, directory_name, parent_node_id):
        """依照資料夾id 在資料夾內建立新資料夾

        Args:
            directory_name (_type_): 新資料夾名稱
            parent_node_id (_type_): 資料夾id

        Returns:
            _type_: {directory_name: node_id}
        """
        created_node = self._mkdir(
            name=directory_name,
            parent_node_id=parent_node_id
        )
        node_id = created_node['f'][0]['h']
        return {directory_name: node_id}

    def upload_c(self, filename, dest=None, dest_filename=None):
        # determine storage node
        if dest is None:
            # if none set, upload to cloud drive node
            if not hasattr(self, 'root_id'):
                self.get_files()
            dest = self.root_id

        # request upload url, call 'u' method
        with open(filename, 'rb') as input_file:
            file_size = os.path.getsize(filename)
            ul_url = self._api_request({'a': 'u', 's': file_size})['p']

            # generate random aes key (128) for file
            ul_key = [random.randint(0, 0xFFFFFFFF) for _ in range(6)]
            k_str = a32_to_str(ul_key[:4])
            count = Counter.new(128, initial_value=((ul_key[4] << 32) + ul_key[5]) << 64)
            aes = AES.new(k_str, AES.MODE_CTR, counter=count)

            upload_progress = 0
            completion_file_handle = None

            mac_str = '\0' * 16
            mac_encryptor = AES.new(
                k_str, AES.MODE_CBC,
                mac_str.encode("utf8")
            )
            iv_str = a32_to_str([ul_key[4], ul_key[5], ul_key[4], ul_key[5]])
            if file_size > 0:
                for chunk_start, chunk_size in get_chunks(file_size):
                    chunk = input_file.read(chunk_size)
                    upload_progress += len(chunk)

                    encryptor = AES.new(k_str, AES.MODE_CBC, iv_str)
                    for i in range(0, len(chunk) - 16, 16):
                        block = chunk[i:i + 16]
                        encryptor.encrypt(block)

                    # fix for files under 16 bytes failing
                    if file_size > 16:
                        i += 16
                    else:
                        i = 0

                    block = chunk[i:i + 16]
                    if len(block) % 16:
                        block += makebyte('\0' * (16 - len(block) % 16))
                    mac_str = mac_encryptor.encrypt(encryptor.encrypt(block))

                    # encrypt file and upload
                    chunk = aes.encrypt(chunk)
                    output_file = requests.post(
                        ul_url + "/" +
                        str(chunk_start),
                        data=chunk,
                        timeout=self.timeout
                    )
                    completion_file_handle = output_file.text
                    # 計算百分比
                    precent = float(round(100 * upload_progress / file_size, 1))
                    logger.info(f'{upload_progress} of {file_size} uploaded, {precent}%')
            else:
                output_file = requests.post(
                    ul_url + "/0",
                    data='',
                    timeout=self.timeout
                )
                completion_file_handle = output_file.text

            file_mac = str_to_a32(mac_str)

            # determine meta mac
            meta_mac = (file_mac[0] ^ file_mac[1], file_mac[2] ^ file_mac[3])

            dest_filename = dest_filename or os.path.basename(filename)
            attribs = {'n': dest_filename}

            encrypt_attribs = base64_url_encode(
                encrypt_attr(attribs, ul_key[:4]))
            key = [
                ul_key[0] ^ ul_key[4],
                ul_key[1] ^ ul_key[5],
                ul_key[2] ^ meta_mac[0],
                ul_key[3] ^ meta_mac[1],
                ul_key[4],
                ul_key[5],
                meta_mac[0],
                meta_mac[1]
            ]
            encrypted_key = a32_to_base64(encrypt_key(key, self.master_key))
            # update attributes
            data = self._api_request({
                'a': 'p',
                't': dest,
                'i': self.request_id,
                'n': [{
                    'h': completion_file_handle,
                    't': 0,
                    'a': encrypt_attribs,
                    'k': encrypted_key
                }]
            })
            return data
