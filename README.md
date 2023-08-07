# Python-Mega

```
監聽指定資料夾 分割檔案並上傳至mega雲端
```

## 用法

```bash
# test.tar._xx 分割檔數字xx除於[總數] 根據 [餘數] 進行分配上傳
usage:
python main-mega_sql_script.py [-h] [-u MEGA_UPLOAD_ID] [-s MEGA_SCHEDULE_QUANTITY] [-l LISTEN_TYPE]

optional arguments:
  -h, --help            show this help message and exit
  -u MEGA_UPLOAD_ID, --mega_upload_id MEGA_UPLOAD_ID
                        多開指定id
  -s MEGA_SCHEDULE_QUANTITY, --mega_schedule_quantity MEGA_SCHEDULE_QUANTITY
                        多開總量
  -l LISTEN_TYPE, --listen_type LISTEN_TYPE
                        功能 0: 分割, 1: 上傳, 2: 檢查過期
```
