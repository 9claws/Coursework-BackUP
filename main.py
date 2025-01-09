import configparser
import requests
import json
import os
from tqdm import tqdm
from time import sleep

class VkApi:
    def __init__(self, token):
        self.token = token

    def _get_user_id_by_screen_name(self, screen_name):
        """Получить ID пользователя по screen_name."""
        url = 'https://api.vk.com/method/utils.resolveScreenName'
        params = {
            'screen_name': screen_name,
            'access_token': self.token,
            'v': '5.199'
        }
        response = requests.get(url=url, params=params).json()
        if 'error' in response:
            raise ValueError(f"Ошибка при получении ID по screen_name: {response['error']['error_msg']}")
        return response['response']['object_id']

    def get_profile_photos(self, owner_id):
        """Получить информацию о фотографиях профиля."""
        url = 'https://api.vk.com/method/photos.get'
        params = {
            'owner_id': owner_id,
            'album_id': 'profile',
            'access_token': self.token,
            'v': '5.199',
            'extended': '1',
            'photo_sizes': '1',
            'count': 5
        }
        response = requests.get(url=url, params=params)
        return response.json()

    def get_max_resolution_urls(self, profile_list):
        """Получить ссылки на фотографии максимального разрешения."""
        max_size_photo = {}  # Словарь {Название фото - URL фото максимального разрешения}

        for photo in tqdm(profile_list['response']['items']):
            sleep(0.25)
            max_size = 0
            for size in photo['sizes']:
                if size['height'] >= max_size:
                    max_size = size['height']
                    max_res_url = size['url']
            if photo['likes']['count'] not in max_size_photo.keys():
                max_size_photo[photo['likes']['count']] = max_res_url
            else:
                max_size_photo[f"{photo['likes']['count']} + {photo['date']}"] = max_res_url

        return max_size_photo

class YandexDiskApi:
    def __init__(self, token):
        self.token = token

    def upload_to_yandex_disk(self, file_name, file_content):
        """Загрузить фотографию на Яндекс.Диск."""
        url_upload = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'OAuth {self.token}'
        }
        params = {'path': f'image_vk/{file_name}.jpg'}
        response = requests.get(url_upload, headers=headers, params=params)
        link_upload = response.json().get('href')
        
        try:
            response = requests.put(link_upload, data=file_content)
            print(response.json())
        except KeyError:
            print(response)

# Чтение токенов из конфигурационного файла
config = configparser.ConfigParser()
config.read('config.ini')
vk_token = config['vk']['token']
ya_disk_token = config['yandex_disk']['token']

# Инициализация классов
vk_api = VkApi(vk_token)
ya_disk_api = YandexDiskApi(ya_disk_token)

# Входные данные
user_input = input("Введите ID или screen_name пользователя: ")

try:
    if user_input.isdigit():
        owner_id = user_input
    else:
        owner_id = vk_api._get_user_id_by_screen_name(user_input)
except ValueError as e:
    print(e)
    exit(1)

# Получение фотографий профиля
profile_list = vk_api.get_profile_photos(owner_id)
max_res_urls = vk_api.get_max_resolution_urls(profile_list)

# Загрузка фотографий на Яндекс.Диск
for photo_name, photo_url in max_res_urls.items():
    ya_disk_api.upload_to_yandex_disk(photo_name, requests.get(photo_url).content)

# Сохранение информации о фотографиях в json-файл
with open('photos_load.json', 'w') as file:
    json.dump(max_res_urls, file)