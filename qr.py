import base64
from io import BytesIO
from PIL import Image
import qrcode
import requests
from pyzbar.pyzbar import decode


def check_qr_content(data: str):
    if data.startswith("http://") or data.startswith("https://"):
        try:
            r = requests.head(data, timeout=5)
            ctype = r.headers.get("Content-Type", "")
            if ctype.startswith("image/"):
                return "URL_IMAGE"
            return "URL"
        except Exception:
            return "URL"
    elif data.startswith("data:image"):
        return "IMAGEBASE_URL"
    return "TEXT"


def read_qr_from_image(image_obj):
    #Сканирует изображение, извлекает текст и формирует ответ по ТЗ
    decode_objects = decode(image_obj)
    if not decode_objects:
        return {"error": "QR not found in file"}

    #Извлечение данных из первого найденного QR-кода
    qr_data = decode_objects[0].data.decode("utf-8")
    
    #Если на входе изображение, то тип в ответе становится "text", а в data — сам текст
    return {
        "type": "text", 
        "data": qr_data
    }


def is_image_data(data: str) -> bool:
    # Проверка на Base64 картинку
    if data.startswith("data:image") or ";base64," in data:
        return True
        
    # Проверка на локальный файл (по расширению)
    if any(data.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp"]):
        return True
        
    # Проверка на веб-ссылку, ведущую на картинку
    if data.startswith("http"):
        try:
            r = requests.head(data, timeout=3)
            if r.headers.get("Content-Type", "").startswith("image/"):
                return True
        except Exception:
            pass
            
    return False


def process_image(data):
    #Определяет формат переданного изображения и открывает его
    #Обработка Base64 строки
    if data.startswith("data:image") or ";base64," in data:
        try:
            if "," in data:
                header, base64_str = data.split(",", 1)
            else:
                base64_str = data
            
            base64_str = "".join(base64_str.split())
            image_bytes = base64.b64decode(base64_str)
            img = Image.open(BytesIO(image_bytes))
        except Exception as e:
            return {"error": f"Failed to decode Base64 image: {e}"}

    #Обработка ссылки на изображение (HTTP/HTTPS)
    elif data.startswith("http"):
        try:
            response = requests.get(data)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content))
        except Exception as e:
            return {"error": f"Failed to load image from URL: {e}"}
            
    #Обработка локального пути к файлу
    else:
        try:
            img = Image.open(data)
        except Exception as e:
            return {"error": f"Failed to open local image: {e}"}

    return read_qr_from_image(img)


def process_text(data):
    #ТЗ: Если идет обычный текст или обычная ссылка — генерирует QR-код
    img = qrcode.make(data)
    file_path = "generated_qr.png"
    img.save(file_path)
    return {
        "type": "image", 
        "data": file_path
    }


def process_requests(payload):
    #Основной диспетчер. Автоматически определяет тип операции
    if not isinstance(payload, dict):
        return {"error": "Payload must be a dictionary/JSON object"}

    data = payload.get("data")
    if not data or not isinstance(data, str):
        return {"error": "Missing or invalid 'data' parameter"}

    # Если строка — это картинка (Base64, URL картинки или файл), то распозн её.
    # Иначе (обычный текст, обычная ссылка на сайт) — генерируется из неё QR-код.
    if is_image_data(data):
        return process_image(data)
    else:
        return process_text(data)
if __name__ == "__main__":
    print("\n--- Скрипт запущен и готов к работе ---")
    user_input = input("Вставьте текст, ссылку или Base64-строку: ").strip()
    
    if user_input:
        #тип определится автоматически
        payload = {"data": user_input}
        
        # Вызываем ваш основной диспетчер
        result = process_requests(payload)
        
        print("\n[Результат работы по ТЗ]:")
        print(result)
    else:
        print("Вы ничего не ввели.")
