
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
import logging

logging.basicConfig(level=logging.INFO)

text = "My name is John Doe and I live in New York. Call me at 555-555-5555."

analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

results = analyzer.analyze(text=text, entities=['PERSON', 'LOCATION', 'PHONE_NUMBER'], language='en')
print(f"Analyzer results: {results}")

anonymized_result = anonymizer.anonymize(
    text=text,
    analyzer_results=results,
    operators={
        "PERSON": OperatorConfig("replace", {"new_value": "REDACTED_NAME"}),
        "LOCATION": OperatorConfig("replace", {"new_value": ""}), # Expect removal
        "PHONE_NUMBER": OperatorConfig("replace", {"new_value": ""}),
        "DEFAULT": OperatorConfig("replace", {"new_value": "REDACTED_DEFAULT"})
    }
)

print(f"Original: {text}")
print(f"Redacted: {anonymized_result.text}")
