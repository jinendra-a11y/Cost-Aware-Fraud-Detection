import os
from google.cloud import vision
from .base import BaseProvider, ProviderResponse

class GoogleVisionProvider(BaseProvider):
    def __init__(self):
        # Ensure credentials are set via env or settings
        self.client = vision.ImageAnnotatorClient()

    def execute(self, image_path: str) -> ProviderResponse:
        with open(image_path, "rb") as img:
            content = img.read()
        
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
    