import requests
import os

def download_image(url, filepath):
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, 'wb') as f:
            f.write(response.content)

        return {'success': True, 'message': f'Image downloaded: {filepath}', 'filepath': filepath}
    except Exception as e:
        return {'success': False, 'error': str(e)}

# Download Subnautica cover
result = download_image(
    'https://byxatab.com/uploads/posts/2023-01/1672839558_subnautica.png',
    'downloads/game_covers/subnautica_original_cover.jpg'
)
print(result)