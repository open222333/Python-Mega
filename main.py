from src import MEGA_LISTEN_DIR, MEGA_ACCOUNT, MEGA_PASSWORD
from src.mega_backup import MegaListen
import os


MEGA_ACCOUNT = MEGA_ACCOUNT
MEGA_PASSWORD = MEGA_PASSWORD
if MEGA_LISTEN_DIR == '':
    MEGA_LISTEN_DIR = f'{os.path.dirname(__file__)}/target_dir'
    os.mkdir(MEGA_LISTEN_DIR)
else:
    MEGA_LISTEN_DIR = MEGA_LISTEN_DIR


if __name__ == "__main__":
    ml = MegaListen(
        dir_path=MEGA_LISTEN_DIR,
        mega_account=MEGA_ACCOUNT,
        mega_password=MEGA_PASSWORD,
        test=True)
    ml.set_file_extension('tar')
    ml.listen()
