import os
import sys

# Mock setting env var
os.environ["LLM_PROVIDER"] = "ollama"
os.environ["LLM_MODEL"] = "qwen2.5:7b"

try:
    print("Importing LLMBatchProcessor...")
    from llm_batch_processor import LLMBatchProcessor
    
    print("Initializing LLMBatchProcessor...")
    processor = LLMBatchProcessor(api_provider="ollama", model="qwen2.5:7b")
    
    print("Running generated_analysis test...")
    prompt = "Say hello in JSON format like {\"greeting\": \"hello\"}."
    
    # We can't call proces_single_cv without mocking more stuff, but let's try direct call to _call_ollama if possible
    # But _call_ollama is internal. Let's try process_single_cv with dummy data.
    
    result = processor.process_single_cv(
        cv_text="This is a resume.",
        cv_filename="test_resume.txt",
        job_description="Need a developer."
    )
    
    print("Result:", result)

except Exception as e:
    print("\n❌ EXCEPTION OCCURRED:")
    print(str(e))
    import traceback
    traceback.print_exc()
