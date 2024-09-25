import yaml
import re
from pathlib import Path
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI


class ConfigError(Exception):
    pass

class ConfigValidator:
    @staticmethod
    def validate_email(email: str) -> bool:
        return re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email) is not None
    
    @staticmethod
    def validate_yaml_file(yaml_path: Path) -> dict:
        try:
            with open(yaml_path, 'r') as stream:
                return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            raise ConfigError(f"Error reading file {yaml_path}: {exc}")
        except FileNotFoundError:
            raise ConfigError(f"File not found: {yaml_path}")


class GeminiModel:
    def __init__(self) -> None:
        self.key = self.set_secrets()
        self.init_gemini()

    def init_gemini(self):
        self.model = ChatGoogleGenerativeAI(
                model="gemini-1.5-pro",
                temperature=0.4,
                max_tokens=None,
                timeout=None,
                max_retries=2,
                google_api_key=self.key['gemini_api_key']
            )

    def set_secrets(self):
        secrets = ConfigValidator.validate_yaml_file('secrets.yaml')
        return secrets
    
    def generate_content(self, text:str):
        return self.model.generate_content(text)

    def generate_text(self, text:str):
        return self.model.invoke(text).content

    def query(self, promt:str):
        return self.model.invoke(promt)

gemini = GeminiModel()
query = "How are you today?"
print("Q:", query)
print("A:", gemini.generate_text(query))