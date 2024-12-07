import requests
import json
import os
from tqdm import tqdm
from time import sleep

class PhotosLoad:
    def __init__(self, token, user_id):
        self.token = token
        self.user_id = user_id

    def get_profile_photos(self):
        url = 'https://api.vk.com/method/photos.get'
        params = {'owner_id': self.user_id,
                  'album_id': 'profile',
                  'access_token': self.token,
                  'v': '5.199',
                  'extended': '1',
                  'photo_sizes': '1',
                  'count': 5
                  }
        response = requests.get(url=url, params=params)
        return response.json()

    def maxsize_photo(self):
        profile_list = self.get_profile_photos()
        photo_count = profile_list['response']['count']
        i = 0
        max_size_photo = {}  # Словарь {Название фото - URL фото максимального разрешения}

        # Создаём папку на компьютере для скачивания фотографий
        if not os.path.exists('vk_backup'):
            os.mkdir('vk_backup')

        while i <= photo_count:
            if i != 0:
                profile_list = self.get_profile_photos()

            # Проход по фотографиям
            for photo in tqdm(profile_list['response']['items']):
                sleep(0.25)
                max_size = 0
                photos_info = {}
                # Выбор фото максимального разрешения и добавление в словарь {max_size_photo}
                for size in photo['sizes']:
                    if size['height'] >= max_size:
                        max_size = size['height']
                if photo['likes']['count'] not in max_size_photo.keys():
                    max_size_photo[photo['likes']['count']] = size['url']
                    photos_info['file_name'] = f"{photo['likes']['count']}.jpg"
                else:
                    max_size_photo[f"{photo['likes']['count']} + {photo['date']}"] = size['url']
                    photos_info['file_name'] = f"{photo['likes']['count']} + {photo['date']}.jpg"

        # Cписок всех фотографий
        photos_load = []  # Список загруженных фото
        photos_info['size'] = size['type']
        photos_load.append(photos_info)

        # Скачиваем фотографии
        for photo_name, photo_url in max_size_photo.items():
            with open('vk_backup/%s' % f'{photo_name}.jpg', 'wb') as file:
                img = requests.get(photo_url)
                file.write(img.content)

        # Запись информации о скачанных фоторафиях в файл .json
        with open('photos_load.json', 'w') as file:
            json.dump(photos_load, file)



# Создаем папку на Яндекс.Диске
url_create_folder = 'https://cloud-api.yandex.net/v1/disk/resources'
headers = {'Content-Type': 'application/json',
           'Accept': 'application/json',
           'Authorization': f'OAuth {token}'
           }
params = {'path': 'image_vk'}
response = requests.put(url=url_create_folder, headers=headers, params=params)

# Загружаем фото на Яндекс.Диск
url_upload = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
headers = {'Content-Type': 'application/json',
           'Accept': 'application/json',
           'Authorization': f'OAuth {token}'
           }
params = {'path': 'image_vk/{file_image}'}

# Получение ссылки на загрузку
response = requests.get(url=url_upload, headers=headers, params=params)
link_upload = response.json().get('href')

# Загрузка файла
with open('vk_backup/{file_image}', 'rb') as file:
    try:
        requests.put(link_upload, files={'file': file})
        print(response.json())
    except KeyError:
        print(response)