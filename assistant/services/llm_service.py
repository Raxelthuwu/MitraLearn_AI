import ollama
from django.conf import settings
from assistant.interfaces.llm_interface import ILLMService

class OllamaLLMService(ILLMService):
    """
    Concrete implementation of the LLM Service using Ollama.
    """

    def __init__(self):
        # Load model name from global Django settings (default: gemma2)
        self.model_name = settings.LLM_MODEL

    def generate_response(self, prompt: str):
        """Generates a response from the LLM via Ollama API."""
        try:
            response = ollama.chat(model=self.model_name, messages=[
                {'role': 'user', 'content': prompt},
            ])
            return response['message']['content']
        except Exception as e:
            raise Exception(f"Failed to connect to Ollama. {str(e)}")

    def generate(self, prompt: str):
        """Alias for generate_response — used by forum similarity services."""
        return self.generate_response(prompt)

    def get_model_name(self):
        """Returns the configured model name."""
        return self.model_name
