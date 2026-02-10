# Extractors for dependencies, configs, API definitions
from scribe.extractors.dependencies import extract_dependencies
from scribe.extractors.configs import extract_configs
from scribe.extractors.apis import extract_api_definitions

__all__ = ["extract_dependencies", "extract_configs", "extract_api_definitions"]
