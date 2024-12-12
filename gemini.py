import yaml
import re
from pathlib import Path
from langchain_google_genai import ChatGoogleGenerativeAI


class ConfigError(Exception):
    pass

class ConfigValidator:
    @staticmethod
    def validate_yaml_file(yaml_path: Path) -> dict:
        try:
            with open(yaml_path, 'r') as stream:
                return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            raise ConfigError(f"Error reading file {yaml_path}: {exc}")
        except FileNotFoundError:
            raise ConfigError(f"File not found: {yaml_path}")


def init_gemini(yaml_file='secrets.yaml'):
    secrets = ConfigValidator.validate_yaml_file('secrets.yaml')
    model = ChatGoogleGenerativeAI(
                model="gemini-1.5-pro",
                temperature=0.2,
                max_tokens=None,
                timeout=None,
                max_retries=2,
                google_api_key=secrets['gemini_api_key']
    )
    return model


    
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompt_values import StringPromptValue
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate

gemini = init_gemini()
prompt = ChatPromptTemplate.from_template("")
chain = prompt | gemini | StrOutputParser()
output = chain.invoke({"role":"human", "content": "I love programming."})
print(output)