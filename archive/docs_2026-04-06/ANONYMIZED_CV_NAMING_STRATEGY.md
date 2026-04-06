# Anonymized CV Naming & Storage Strategy

## 🎯 Problem Statement

**Current Issues**:
1. Anonymized IDs are random (CAND_882) - hard to trace back
2. Original filename → Anonymized ID mapping stored in database
3. If database fails, mapping is lost
4. No easy way to find original CV from anonymized ID
5. Redacted files have generic names (REDACTED_timestamp_*.txt)

**Requirements**:
1. Maintain privacy (no PII in filenames)
2. Enable reverse lookup (Anonymized ID → Original filename)
3. Work offline (without database)
4. Be human-readable for debugging
5.