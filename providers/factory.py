from .ocr_provider import GoogleVisionProvider
from .groq_provider import GroqProvider

class ProviderFactory:
    @staticmethod
    def get_ocr_provider():
        # In the future, this can read from Django Settings
        return GoogleVisionProvider()

    @staticmethod
    def get_llm_provider(model_name="llama3-3.1-8b-instant"):
        return GroqProvider(model_name=model_name)