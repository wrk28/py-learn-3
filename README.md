# Примечание

1. Для работы программы заполните конфигурационный файл .env
   
```
VK_ID=<Add your user_id here>
VK_TOKEN=<Add your token here>
VK_API_VERSION=5.199
YANDEX_TOKEN=<Add your token here>
GOOGLE_TOKEN=0
FOLDER_NAME="Stored_Data"
JSON_NAME="report.txt"
STORE_JSON_TO_CLOUD=True
```
2. Программа может запускаться с консоли с аргументами
```
reserve.py -h
usage: reserve.py [-h] [-n COUNT] [-a [ALBUM ...]] [-c CLOUD [CLOUD ...]]

options:
  -h, --help            show this help message and exit
  -n, --count COUNT     set the count of photos
  -a, --album [ALBUM ...]
                        set one or many albums
  -c, --cloud CLOUD [CLOUD ...]
                        set one or many clouds
```
Ни один из аргументов не является обязательным. По умолчанию будет находится 5 фотографий из профайла и загружаться на Yandex disk.

-n число фотографий
-a идентификаторы альбомов
-с место резервного копирования

Пример:

Загрузить фото из профайла и альбома с идентификатором 0000001 на Yandex disk
```
python3 reserve.py -a profile 0000001 -c yandex
```

Файлы из профайла загружаются всегда, даже если явно не указывать.

3. Возможные доработки

1) Кроме добавления альбомов по идентификаторам, сделать возможным добавлять по названиям. Для этого можно применить photos.getAlbums
2) Сделать возможность загрузки на Google Drive







