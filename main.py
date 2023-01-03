from time import time, sleep
from mega import Mega
import os

from general import MEGA_LISTEN_DIR, MEGA_ACCOUNT, MEGA_PASSWORD

MEGA_ACCOUNT = MEGA_ACCOUNT
MEGA_PASSWORD = MEGA_PASSWORD
if MEGA_LISTEN_DIR == '':
    MEGA_LISTEN_DIR = f'{os.path.dirname(__file__)}/target_dir'
    os.mkdir(MEGA_LISTEN_DIR)
else:
    MEGA_LISTEN_DIR = MEGA_LISTEN_DIR


class MegaBackupFile:
    """上傳檔案至mega
    """

    def __init__(self, file_path: str, mega_folder: str = None, test=False) -> None:
        """_summary_

        Args:
            file_path (str): 路徑
            mega_folder (str): 上傳的資料夾名稱
        """
        self.file_path = file_path

        # 紀錄分割檔案
        self.split_files = []

        if mega_folder:
            self.mega_folder = mega_folder
        else:
            self.mega_folder = 'ProductUpload'

        self.chunk_size = 500000000
        self.test = test

    def set_mega_auth(self, account: str, password: str):
        """
        設置帳號

        Args:
            account (str): mega 帳號
            password (str): mega 密碼
        """
        mega = Mega()
        self.mega_client = mega.login(account, password)

    def set_chunk_size(self, size: int):
        """設置分割檔案大小 byte

        Args:
            size (int): byte
        """
        self.chunk_size = size

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
            msg += f"{days} 天"
        if hours != 0:
            msg += f"{hours} 時"
        if minutes != 0:
            msg += f"{minutes} 分"
        msg += f"{int(seconds)} 秒"
        return msg

    def __print_msg(self, msg: str):
        """顯示訊息

        Args:
            msg (str): 訊息內容
        """
        print(f'=== {msg} ===')

    def __split_file(self, path: str, chunk_size: int = 500000000, filename: str = None):
        """分割檔案

        Args:
            path (str): 檔案路徑
            chunk_size (str): 分割大小. Defaults to 500MB
            filename (str, optional): 檔名. Defaults to None.
        """
        file_number = 1

        if not filename:
            filename = os.path.basename(path)
        file_dir = os.path.dirname(path)

        self.__print_msg(f'分割 {filename} 開始')

        with open(path, 'rb') as f:
            chunk = f.read(chunk_size)
            while chunk:
                split_file = f'{file_dir}/{filename}._{str(file_number)}'
                with open(split_file, 'wb') as chunk_file:
                    chunk_file.write(chunk)
                file_number += 1
                chunk = f.read(chunk_size)

                # 紀錄分割檔位置
                self.split_files.append(split_file)

        self.__print_msg(f'分割 {filename} 結束')

    def __cat_files(self, path: str, filename: str = None):
        """合併檔案

        Args:
            path (str): 檔案路徑
            filename (str, optional): 檔名. Defaults to None.
        """
        if not filename:
            filename = os.path.basename(path)
        file_dir = os.path.dirname(path)

        self.__print_msg(f'合併 {filename} 開始')

        command = f'cat {file_dir}/{filename}* >> {file_dir}/{filename}'
        print(command)
        os.system(command)

        self.__print_msg(f'合併 {filename} 結束')

    def __upload_to_mega(self, path: str):
        """上傳至mega

        Args:
            path (str): 檔案路徑

        Returns:
            _type_: 非測試時回傳上傳資訊
        """
        # 取得檔案大小 MB
        tar_size = round(os.path.getsize(self.file_path) / float(1000 * 1000), 2)
        filename = os.path.basename(path)

        self.__print_msg(f'上傳資料 {filename} 至 {self.mega_folder}, 檔案大小 {tar_size} MB')

        upload_start_time = time()

        if not self.test:
            mega_info = self.mega_client.upload(
                filename=path,
                dest=self.mega_client.find(self.mega_folder)[0],  # tHcCFDAZ mega的id
                dest_filename=filename
            )

        upload_end_time = time()

        take_time = self.__get_time_str(round(upload_end_time - upload_start_time, 0))
        self.__print_msg(f'上傳資料 {filename} 至 {self.mega_folder} 完成, 共花費 {take_time}')

        if not self.test:
            return mega_info

    def __remove_file(self, path: str):
        """刪除檔案

        Args:
            path (str): 檔案路徑
        """
        filename = os.path.basename(path)
        self.__print_msg(f'刪除 {filename} 開始')
        os.remove(path)
        self.__print_msg(f'刪除 {filename} 結束')

    def run(self):
        """執行
        """
        if os.path.getsize(self.file_path) > self.chunk_size:
            self.__split_file(self.file_path, self.chunk_size)
            # 上傳分割檔案
            for file in self.split_files:
                self.__upload_to_mega(file)
                self.__remove_file(file)
        else:
            self.__upload_to_mega(self.file_path)
            if not self.test:
                self.__remove_file(self.file_path)


class MegaListen:
    """監聽資料夾 若有符合條間的檔案則執行上傳至mega
    """

    def __init__(self, dir_path: str, mega_account: str, mega_password: str, test=False) -> None:
        """_summary_

        Args:
            dir_path (str): 監聽路徑
            mega_account (str): mega帳號
            mega_password (str): mega密碼
            test (bool, optional): 是否為測試. Defaults to False.
        """
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            
        self.dir_path = dir_path
        self.files = []

        self.mega_account = mega_account
        self.mega_password = mega_password

        self.test = test
        self.is_sleep = False
        self.file_extensions = None

    def set_file_extension(self, *extension: str):
        """設置 篩選副檔名條件

        extension: 指定副檔名
        """
        self.file_extensions = extension

    def __check_extension(self, filename: str):
        """檢查 是否符合副檔名條件

        Args:
            filename (str): 檔名

        Returns:
            bool: 是否符合副檔名條件
        """
        if self.file_extensions == None:
            return True
        else:
            _, file_extension = os.path.splitext(filename)
            return file_extension[1:] in self.file_extensions

    def listen(self):
        """執行監聽
        """
        while True:
            for file in os.listdir(self.dir_path):
                if file not in self.files and self.__check_extension(file):
                    mbf = MegaBackupFile(f'{self.dir_path}/{file}', test=self.test)
                    if not self.test:
                        mbf.set_mega_auth(self.mega_account, self.mega_password)
                    mbf.run()
                    self.is_sleep = False
            else:
                if not self.is_sleep:
                    self.is_sleep = True
                    print('等候中')
                sleep(1)


if __name__ == "__main__":
    ml = MegaListen(
        dir_path=MEGA_LISTEN_DIR,
        mega_account=MEGA_ACCOUNT,
        mega_password=MEGA_PASSWORD,
        test=True)
    ml.set_file_extension('tar')
    ml.listen()
