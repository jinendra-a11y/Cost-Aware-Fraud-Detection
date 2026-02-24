from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional

@dataclass
class ProviderResponse:
    content: Any          # The actual result (text or dict)
    input_units: int      # Tokens or Images used
    output_units: int     # Tokens generated
    model_name: str       # Exact model string used

class BaseProvider(ABC):
    @abstractmethod
    def execute(self, *args, **kwargs) -> ProviderResponse:
        pass