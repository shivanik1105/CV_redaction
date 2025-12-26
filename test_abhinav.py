from resume_redactor import *

pipeline = ResumePipeline()
result = pipeline.process('samples/Naukri_AbhinavVinodSolapurkar[5y_8m].pdf')

# Find SKILLS sections
lines = result.split('\n')
skills_indices = [i for i, l in enumerate(lines) if l.strip() == 'SKILLS']
print(f'SKILLS appears {len(skills_indices)} times at lines: {skills_indices}\n')

for idx in skills_indices:
    print(f'=== Around SKILLS at line {idx} ===')
    for i in range(max(0, idx-3), min(len(lines), idx+25)):
        print(f'{i:3d}: {lines[i][:75]}')
    print()
