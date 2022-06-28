import os
import pathlib
import random
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv


def get_url_extension(file_path):
    parsed = urlparse(file_path)
    path, extension = os.path.splitext(parsed.path)
    return extension


def save_image_file(directory, image_url, file_name):
    image_response = requests.get(image_url)
    image_response.raise_for_status()
    extension = get_url_extension(image_url)
    with open(f'{directory}{file_name}{extension}', 'wb') as file:
        file.write(image_response.content)


def get_upload_url(api_url, group_id, api_token):
    url = f'{api_url}photos.getWallUploadServer'
    params = {
        'group_id': group_id,
        'access_token': api_token,
        'v': '5.131'
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    content = response.json()
    if not content.get('response'):
        raise VkApiError(content)
    upload_url = content.get('response').get('upload_url')
    return upload_url


def upload_photo(upload_url, file_name, directory):
    with open(f'{directory}{file_name}.png', 'rb') as file:
        files = {
            'photo': file,
        }
        response = requests.post(upload_url, files=files)
        response.raise_for_status()
        content = response.json()
        return content


def save_uploaded_photo(response, group_id, api_token, api_url):
    photo = response.get('photo')
    server = response.get('server')
    hash = response.get('hash')
    params = {
        'group_id': group_id,
        'photo': photo,
        'server': server,
        'hash': hash,
        'access_token': api_token,
        'v': '5.131'
    }
    url = f'{api_url}photos.saveWallPhoto'
    save_wallphoto_response = requests.post(url, params=params)
    save_wallphoto_response.raise_for_status()
    content = save_wallphoto_response.json()
    if not content.get('response'):
        raise VkApiError(content)
    json_response = content.get('response')
    return json_response


def publish_comics(media_id, owner_id, message, group_id, api_token, api_url):
    url = f'{api_url}wall.post'
    params = {
        'owner_id': f'-{group_id}',
        'from_group': 1,
        'attachments': f'photo{owner_id}_{media_id}',
        'message': message,
        'access_token': api_token,
        'v': '5.131'
    }
    response = requests.post(url, params=params)
    response.raise_for_status()


def get_comics_num(comics_url):
    response = requests.get(comics_url)
    response.raise_for_status()
    num = response.json().get('num')
    return num


def get_random_comics(num):
    random_comics_num = random.randint(1, num)
    random_comics_url = f'https://xkcd.com/{random_comics_num}/info.0.json'
    comics_response = requests.get(random_comics_url)
    comics_response.raise_for_status()
    content = comics_response.json()
    return content


class VkApiError(Exception):
    def __init__(self, content):
        self.code_error = content['error']['error_code']
        self.msg_error = content['error']['error_msg']

    def __str__(self):
        return f'Error code: {self.code_error}; {self.msg_error}'


def main():
    load_dotenv()
    directory = '/comics/'
    pathlib.Path(directory).mkdir(exist_ok=True)
    vk_api_token = os.getenv('ACCESS_TOKEN')
    group_id = os.getenv('GROUP_ID')
    vk_api_url = 'https://api.vk.com/method/'
    comics_url = 'https://xkcd.com/info.0.json'
    num = get_comics_num(comics_url)
    random_comics_content = get_random_comics(num)
    img = random_comics_content.get('img')
    file_name = random_comics_content.get('title')
    message = random_comics_content.get('alt')
    save_image_file(directory, img, file_name)
    upload_url = get_upload_url(vk_api_url, group_id, vk_api_token)
    try:
        upload_response = upload_photo(upload_url, file_name, directory)
    finally:
        os.remove(f'{directory}{file_name}.png')
    save_photo_response = save_uploaded_photo(
        upload_response,
        group_id,
        vk_api_token,
        vk_api_url
    )
    media_id = save_photo_response[0].get('id')
    owner_id = save_photo_response[0].get('owner_id')
    publish_comics(
        media_id,
        owner_id,
        message,
        group_id,
        vk_api_token,
        vk_api_url
    )


if __name__ == "__main__":
    main()
