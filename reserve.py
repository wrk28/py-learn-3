import os
import dotenv
import time
import progress.bar
import argparse
import json
import requests
from datetime import datetime


class ConsoleParamsReader:
    """Reads the parameters from the Console"""

    def __init__(self):
        """Initialize a new console params reader"""
        self.album = []
        self.cloud = []
        self.__get_args()
       
    def __get_args(self):
        """Storing the parameters as the object's fields"""
        arg_parser = argparse.ArgumentParser()

        arg_parser.add_argument('-n', '--count', nargs=1, type=int, default=5, help='set the count of photos')
        arg_parser.add_argument('-a', '--album', nargs='*', type=str, default=['profile'], help='set one or many albums')
        arg_parser.add_argument('-c', '--cloud', nargs='+', type=str, default=['yandex'], help='set one or many clouds')
        
        args = arg_parser.parse_args()
        self.count = args.count
        self.album.append(args.album)
        self.cloud.append(args.cloud)


class EnvReader:
    """Reads the config file settings"""

    def __init__(self, path=None):
        """Initialize a new config file settings reader"""
        if path is None:
            dotenv_path = os.path.dirname(__file__)
        else:
            dotenv_path = path
        dotenv.load_dotenv(dotenv_path)
        
        self.vk_id = os.getenv('VK_ID')
        self.vk_api_version = os.getenv('VK_API_VERSION')
        self.vk_token = os.getenv('VK_TOKEN')
        self.yandex_token = os.getenv('YANDEX_TOKEN')
        self.google_token = os.getenv('GOOGLE_TOKEN')
        self.folder_name_pattern = os.getenv('FOLDER_NAME_PATTERN')
        self.json_name = str(os.getenv('JSON_NAME'))
        self.store_json_to_cloud = str(os.getenv('STORE_JSON_TO_CLOUD')).lower() in ('true', '1', 't')


class DataCopier:
    """Copies the photos from one site to the clouds storages"""

    def __init__(
            self, 
            vk_id, 
            vk_token, 
            yandex_token, 
            vk_api_version, 
            google_token, 
            folder_name_pattern, 
            json_name, 
            store_json_to_cloud, 
            count, 
            album, 
            cloud
        ):
        """Initialize a new copier"""
        self.vk_common_params = {'owner_id': vk_id, 'access_token': vk_token, 'v': vk_api_version}
        self.yandex_token = yandex_token
        self.google_token = google_token
        self.folder_name_pattern = folder_name_pattern
        self.json_name = json_name
        self.stored_json_to_cloud = store_json_to_cloud
        self.count = count
        self.file_name = []
        self.vk_api = r'https://api.vk.com/method/'
        self.yandex_api = r'https://cloud-api.yandex.net/'
        self.albums = set(['profile'] + album[0])
        self.clouds = set(cloud[0])

    def __get_album_list(self) -> set:
        """Getting the list of album id from where need to download the photos"""
        # We can add a method to get photos from albums by album names
        # For now it searches only by album id
        # ----------------------------------------------------------------
        return set(self.albums)

    def vk_download(self):
        """Download the photos to from the VK site"""     
        photos = self.__get_list_photos_to_download()
        photos_report = []
        progress_bar = progress.bar.IncrementalBar('Downloading from VK:', max=len(photos))
        for photo in photos:
            photo_url = photo['url']
            response = requests.get(photo_url)
            with open(photo['name'], 'wb') as f:
                f.write(response.content)
            photos_report.append({'name': photo['name'], 'size': photo['size']})
            self.file_name.append(photo['name'])
            time.sleep(0.2)
            progress_bar.next()
        progress_bar.finish()
        self.__add_report(photos_report)

    def __add_report(self, photos_report: list):
        """Saving the downloaded photos report"""
        with open(data_copier.json_name, 'w') as f:
            json.dump(photos_report, f)

    def __get_list_photos_to_download(self) -> list:
        """Get list of photos to download"""
        url = f'{self.vk_api}photos.get'
        albums = self.__get_album_list()
        items = []
        for album in albums:
            params = self.vk_common_params.copy()
            params.update({'count': self.count, 'album_id': {album}, 'extended': 1}) 
            response = requests.get(url, params)
            if 'error' in response.json():
                raise NameError('Access to VK is denied') 
            items.extend(response.json()['response']['items'])
        return self.__process_response(items)

    def __process_response(self, items: list) -> list:
        """Getting only sufficient data in a required form"""
        photos = []
        name_count = {}
        for photo in items:
            id = photo['id']
            album_id = photo['album_id']
            url, size = self.__get_photo_url(photo['sizes'])
            name = f'{photo['likes']['count']}'
            date = photo['date']
            photos.append({'name': name, 'id': id, 'album_id': album_id, 'size': size, 'url': url, 'date': date})
            if name in name_count:
                 name_count[name] += 1
            else:
                name_count[name] = 1          
        return self.__change_repeated_photos(photos, name_count)
    
    def __get_photo_url(self, sizes: list) -> list[str, str]:
        """Finding the url of the photo"""
        func = lambda photo: photo['height'] * photo['width']
        photo = max(sizes, key=func)
        url = photo['url']
        size = f'{photo['width']}x{photo['height']}'
        return url, size
    
    def __change_repeated_photos(self, photos: list, name_count: dict) -> list:
        """Adding date to the name of photos which repeat"""
        for photo in photos:
            name = photo['name']
            if name_count[name] > 1:
                str_time = datetime.fromtimestamp(photo['date']).strftime('%Y%m%d_%H%M%S')
                new_name = f'{photo['name']}_{str_time}'
                photo['name'] = f'{new_name}.jpg'
            else:
                photo['name'] = f'{photo['name']}.jpg'
        return photos
    
    def __create_yandex_folder(self):
        """Create a folder in Yandex disk to upload the files"""
        url = f'{self.yandex_api}v1/disk/resources/'
        headers = {'Authorization': f'OAuth {self.yandex_token}'}
        time_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.folder_name = f'{self.folder_name_pattern}_{time_str}'
        params = {'path': self.folder_name}
        response = requests.put(url=url, headers=headers, params=params)
        if 'error' in response.json():
            raise NameError('Access to Yandex disk is denied')

    def yandex_upload(self):
        """Upload the photos to Yandex cloud"""
        self.__create_yandex_folder()
        url = f'{self.yandex_api}v1/disk/resources/upload'
        headers = {'Authorization': f'OAuth {self.yandex_token}'}
        progress_bar = progress.bar.IncrementalBar('Uploading to Yandex disk:', max=len(self.file_name))
        for file in self.file_name:                
            params = {'path': f'{self.folder_name}/{file}'}
            response = requests.get(url, headers=headers, params=params)
            if 'error' in response.json():
                raise NameError('Access to Yandex disk is denied')
            href = response.json()['href']
            with open(file, 'rb') as f:
                response = requests.put(href, files={'file': f})
                time.sleep(0.2)
            progress_bar.next()
        if self.stored_json_to_cloud:
            self.__store_report_file_to_yandex_disk()
        progress_bar.finish()

    def __store_report_file_to_yandex_disk(self):
        url = f'{self.yandex_api}v1/disk/resources/upload'
        headers = {'Authorization': f'OAuth {self.yandex_token}'}
        params = {'path': f'{self.folder_name}/{self.json_name}'}
        response = requests.get(url, headers=headers, params=params)
        if 'error' in response.json():
            raise NameError('Access to Yandex disk is denied')
        href = response.json()['href']
        with open(self.json_name, 'rb') as f:
            response = requests.put(href, files={'file': f})

    def google_upload(self):
        """Upload the photos to Google could"""
        pass


if __name__ == "__main__":
    # Read the console params settings
    console_params = ConsoleParamsReader()
    # Read the config file settings
    env_args = EnvReader()

    # Creating a new copier objects with the setting
    data_copier = DataCopier(
        vk_id=env_args.vk_id,
        vk_token=env_args.vk_token, 
        vk_api_version=env_args.vk_api_version,
        yandex_token=env_args.yandex_token, 
        google_token=env_args.google_token,
        folder_name_pattern= env_args.folder_name_pattern,
        json_name=env_args.json_name, 
        store_json_to_cloud=env_args.store_json_to_cloud,
        count=console_params.count,
        album=console_params.album,
        cloud=console_params.cloud
    )

    try:        
        data_copier.vk_download()

        if 'yandex' in data_copier.clouds:
            data_copier.yandex_upload()

        # Not implemented yet
        # if 'google' in data_copier.clouds:
        #     data_copier.google_upload()

    except NameError:
        print('Access error')
        raise
