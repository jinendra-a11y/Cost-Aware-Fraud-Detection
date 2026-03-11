import json
import os
from google.cloud import vision
from google.oauth2 import service_account
from .base import BaseProvider, ProviderResponse

class GoogleVisionProvider(BaseProvider):
    def __init__(self):
        """
        Google Vision OCR.

        Supports two auth modes:
        - File path via GOOGLE_APPLICATION_CREDENTIALS (Google default)
        - JSON blob via GOOGLE_APPLICATION_CREDENTIALS_JSON (Render-friendly; avoids shipping a key file)
        """
        creds_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
        if creds_json:
            info = json.loads(creds_json)
            creds = service_account.Credentials.from_service_account_info(info)
            self.client = vision.ImageAnnotatorClient(credentials=creds)
        else:
            # Falls back to ADC / GOOGLE_APPLICATION_CREDENTIALS file path behavior
            self.client = vision.ImageAnnotatorClient()

    def execute(self, image_path: str) -> ProviderResponse:
        content = None

        # 1) If it's a real filesystem path, open directly.
        if image_path and os.path.exists(image_path):
            with open(image_path, "rb") as img:
                content = img.read()
        else:
            # 2) Otherwise, assume it's a Django `default_storage` path (e.g. "uploads/<job>/<file>").
            try:
                from django.core.files.storage import default_storage
                with default_storage.open(image_path, "rb") as f:
                    content = f.read()
            except Exception:
                # 3) Last attempt: resolve relative path under MEDIA_ROOT (common with FileSystemStorage).
                try:
                    from django.conf import settings
                    candidate = os.path.join(str(settings.MEDIA_ROOT), image_path)
                    if os.path.exists(candidate):
                        with open(candidate, "rb") as img:
                            content = img.read()
                except Exception:
                    content = None

        if content is None:
            raise FileNotFoundError(
                f"OCR input image not found: {image_path}. "
                f"Expected an absolute filesystem path or a valid Django storage path."
            )
        
        image = vision.Image(content=content)
        response = self.client.text_detection(image=image)
        
        if response.error.message:
            raise Exception(response.error.message)
            
        text = response.text_annotations[0].description if response.text_annotations else ""
        
        return ProviderResponse(
            content=text,
            input_units=1,  # Google charges per image
            output_units=0,
            model_name="google-vision-ocr"
        )

    async def extract_text(self, image_path: str) -> ProviderResponse:
        import asyncio
        return await asyncio.to_thread(self.execute, image_path)
    