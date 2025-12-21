import requests
from PIL import Image
from io import BytesIO

def meme():
    url = "https://meme-api.com/gimme"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        url = data.get("url")

        if url:
            return url
    
    except Exception as e:
        print(e)
        return None
    
def download(url, path):
    try:
        response = requests.get(url)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))
        image.save(path, format="PNG")
        return path

    except Exception as e:
        print(e)
        return None

