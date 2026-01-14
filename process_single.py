#!/usr/bin/env python3
"""Quick script to process a single CV"""
import sys
import os
os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'

from universal_pipeline_engine import PipelineOrchestrator

def main():
    orchestrator = PipelineOrchestrator()
    pdf_path = 'samples/Resume_preeti_wadhwani 06.10.24.pdf'
    output_path = 'final_output/REDACTED_Resume_preeti_wadhwani 06.10.24.txt'
    
    print(f"Processing: {pdf_path}")
    redacted_text, profile = orchestrator.process_cv(pdf_path)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(redacted_text)
    
    print(f"Done! Saved to: {output_path}")

if __name__ == '__main__':
    main()
