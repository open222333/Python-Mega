import os
import subprocess
from src.logger import Log


class MegaCMDUploader:
    def __init__(self, email, password, mega_folder_path, log_level="DEBUG"):
        self.email = email
        self.password = password
        self.mega_folder_path = mega_folder_path

        self.logger = Log('MegaCMDUploader')
        self.logger.set_level(log_level)
        self.logger.set_msg_handler()

    def ensure_login(self):
        """檢查是否已登入，未登入則執行登入"""
        try:
            result = subprocess.run(["mega-whoami"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode != 0:  # 未登入
                self.logger.info("未登入，執行登入...")
                login = subprocess.run(["mega-login", self.email, self.password], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if login.returncode == 0:
                    self.logger.info("登入成功！")
                else:
                    raise Exception(f"登入失敗：{login.stderr}")
            else:
                self.logger.info("已登入，不需要重新登入。")
        except Exception as e:
            raise Exception(f"登入檢查失敗：{str(e)}")

    def upload_files(self, local_files):
        """批量上傳檔案"""
        for file_path in local_files:
            if not os.path.exists(file_path):
                self.logger.info(f"檔案不存在，跳過：{file_path}")
                continue

            dest_file_name = os.path.basename(file_path)  # 使用原檔名
            command = ["mega-put", file_path, f"{self.mega_folder_path}/{dest_file_name}"]

            try:
                self.logger.info(f"上傳中：{file_path} -> {self.mega_folder_path}/{dest_file_name}")
                result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if result.returncode == 0:
                    self.logger.info(f"成功上傳：{dest_file_name}")
                else:
                    self.logger.error(f"上傳失敗：{result.stderr}")
            except Exception as e:
                self.logger.error(f"上傳時發生例外：{str(e)}")
