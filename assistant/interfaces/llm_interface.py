from abc import ABC, abstractmethod

class ILLMService(ABC):
    """
    Interface for LLM Services.
    Defines the contract for generating responses from a Large Language Model.
    """

    @abstractmethod
    def generate_response(self, prompt: str):
        """Generates a text response based on the provided prompt."""
        pass

    @abstractmethod
    def get_model_name(self):
        """Returns the name of the model being used."""
        pass
