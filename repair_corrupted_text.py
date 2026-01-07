"""
Text Corruption Repair Utility
Fixes common text extraction issues from PDFs with corrupted text layers
"""

import re
from typing import Dict, List, Tuple
import os
from pathlib import Path


class TextCorruptionRepairer:
    """Repairs text corrupted by poor PDF text layer extraction"""
    
    def __init__(self):
        # Common corrupted patterns found in PDFs
        self.corruption_patterns = {
            # Technical terms
            r'\beng in eer(?:ing)?\b': 'engineer',
            r'\bEng in eer(?:ing)?\b': 'Engineer',
            r'\bPyth on\b': 'Python',
            r'\bJav as cript\b': 'JavaScript',
            r'\band roid(?:OS)?\b': 'Android',
            r'\band roidOS\b': 'AndroidOS',
            r'\bYoc to\b': 'Yocto',
            r'\bL in ux\b': 'Linux',
            r'\bs of tw are\b': 'software',
            r'\bS of tw are\b': 'Software',
            r'\bhardw are\b': 'hardware',
            r'\bHardw are\b': 'Hardware',
            r'\bcomp on ent\b': 'component',
            r'\bComp on ent\b': 'Component',
            r'\bin terface\b': 'interface',
            r'\bIn terface\b': 'Interface',
            r'\bg at eway\b': 'gateway',
            r'\bG at eway\b': 'Gateway',
            r'\bdevice\s*s\b': 'devices',
            r'\bfirmw are\b': 'firmware',
            r'\bkern el\b': 'kernel',
            r'\bmicro ?c on troller\b': 'microcontroller',
            r'\bMicro ?c on troller\b': 'Microcontroller',
            r'\barchitecture\b': 'architecture',
            r'\bArchitecture\b': 'Architecture',
            r'\bimplement at i on\b': 'implementation',
            r'\bImplement at i on\b': 'Implementation',
            r'\bc on figur at i on\b': 'configuration',
            r'\bC on figur at i on\b': 'Configuration',
            r'\bsoluti on\b': 'solution',
            r'\bSoluti on\b': 'Solution',
            r'\bappl ic at i on\b': 'application',
            r'\bAppl ic at i on\b': 'Application',
            r'\bper for m(?:ance)?\b': 'perform',
            r'\bPer for m(?:ance)?\b': 'Perform',
            r'\bplatform\b': 'platform',
            r'\bPl at for m\b': 'Platform',
            r'\bst and ard\b': 'standard',
            r'\bSt and ard\b': 'Standard',
            r'\bcon gur at ion\b': 'configuration',
            
            # Common words
            r'\bto\s+the\b': 'to the',
            r'\bin\s+to\b': 'into',
            r'\bin\s+the\b': 'in the',
            r'\bof\s+the\b': 'of the',
            r'\bat\s+the\b': 'at the',
            r'\bto\s+be\b': 'to be',
            r'\bwith\s+the\b': 'with the',
            r'\bfor\s+the\b': 'for the',
            r'\band\s+the\b': 'and the',
            r'\bPRAK as H\b': 'PRAKASH',
            r'\bproblemsolv in g\b': 'problem solving',
            r'\bproblem-solv in g\b': 'problem-solving',
            
            # Action verbs
            r'\bwork(?:ed|ing) in g\b': 'working',
            r'\bWork(?:ed|ing) in g\b': 'Working',
            r'\bdesign in g\b': 'designing',
            r'\bDesign in g\b': 'Designing',
            r'\bdevelop in g\b': 'developing',
            r'\bDevelop in g\b': 'Developing',
            r'\bbuild in g\b': 'building',
            r'\bBuild in g\b': 'Building',
            r'\bcod in g\b': 'coding',
            r'\bCod in g\b': 'Coding',
            r'\btest in g\b': 'testing',
            r'\bTest in g\b': 'Testing',
            r'\bdebugg in g\b': 'debugging',
            r'\bDebugg in g\b': 'Debugging',
            r'\banalyz in g\b': 'analyzing',
            r'\bAnalyz in g\b': 'Analyzing',
            r'\bimplement in g\b': 'implementing',
            r'\bImplement in g\b': 'Implementing',
            r'\bmanag in g\b': 'managing',
            r'\bManag in g\b': 'Managing',
            r'\blead in g\b': 'leading',
            r'\bLead in g\b': 'Leading',
            r'\bmen to r in g\b': 'mentoring',
            r'\bMen to r in g\b': 'Mentoring',
            r'\bresolv in g\b': 'resolving',
            r'\bResolv in g\b': 'Resolving',
            r'\bfix in g\b': 'fixing',
            r'\bFix in g\b': 'Fixing',
            r'\bconfigurin g\b': 'configuring',
            r'\bConfigurin g\b': 'Configuring',
            r'\bin tegr at in g\b': 'integrating',
            r'\bIn tegr at in g\b': 'Integrating',
            r'\boptimiz in g\b': 'optimizing',
            r'\bOptimiz in g\b': 'Optimizing',
            r'\bscal in g\b': 'scaling',
            r'\bScal in g\b': 'Scaling',
            r'\blearning\b': 'learning',
            r'\bLearn in g\b': 'Learning',
            
            # Technical abbreviations
            r'\bR to S\b': 'RTOS',
            r'\bA to m\b': 'Atom',
            r'\bD at a\b': 'Data',
            r'\bd at a\b': 'data',
            r'\bA P I\b': 'API',
            r'\bAPI\b': 'API',
            r'\be the real\b': 'Ethereal',
            
            # Specific corruptions
            r'\bis\s*at\s*i\s*on\b': 'ization',
            r'\bSpecial\s*is\s*at\s*i\s*on\b': 'Specialization',
            r'\bexpert\s*is\s*e\b': 'expertise',
            r'\bExpert\s*is\s*e\b': 'Expertise',
            r'\banalys\s*is\b': 'analysis',
            r'\bAnalys\s*is\b': 'Analysis',
            r'\bin\s*volv(?:ed|ing)\b': 'involving',
            r'\bIn\s*volv(?:ed|ing)\b': 'Involving',
            r'\bpr\s*of\s*icient\b': 'proficient',
            r'\bPr\s*of\s*icient\b': 'Proficient',
            r'\bPR\s*of\s*ILE\b': 'PROFILE',
            r'\bst\s*and\s*ard\b': 'standard',
            r'\bSt\s*and\s*ard\b': 'Standard',
            
            # Multi-word corruptions
            r'\bdevice\s+s\b': 'devices',
            r'\bsystem\s+s\b': 'systems',
            r'\bmodule\s+s\b': 'modules',
            r'\bsolution\s+s\b': 'solutions',
            r'\bfe\s*at\s*ure\b': 'feature',
            r'\bFe\s*at\s*ure\b': 'Feature',
            r'\bcre\s*at\s*e\b': 'create',
            r'\bCre\s*at\s*e\b': 'Create',
            r'\blever\s*ag\s*in\s*g\b': 'leveraging',
            r'\bLever\s*ag\s*in\s*g\b': 'Leveraging',
            r'\bexcepti\s*on\s*al\b': 'exceptional',
            r'\bExcepti\s*on\s*al\b': 'Exceptional',
            r'\bprogramm\s*in\s*g\b': 'programming',
            r'\bProgramm\s*in\s*g\b': 'Programming',
            r'\bc\s*on\s*t\s*in\s*uous\b': 'continuous',
            r'\bC\s*on\s*t\s*in\s*uous\b': 'Continuous',
            r'\bma\s*in\s*tenance\b': 'maintenance',
            r'\bMa\s*in\s*tenance\b': 'Maintenance',
            r'\bma\s*in\s*ta\s*in\s*ed\b': 'maintained',
            r'\bMa\s*in\s*ta\s*in\s*ed\b': 'Maintained',
            r'\benvir\s*on\s*ment\b': 'environment',
            r'\bEnvir\s*on\s*ment\b': 'Environment',
            r'\bfuncti\s*on\s*al\b': 'functional',
            r'\bFuncti\s*on\s*al\b': 'Functional',
            r'\bCollabor\s*at\s*ed\b': 'Collaborated',
            r'\bcollabor\s*at\s*ed\b': 'collaborated',
            r'\bevolv\s*in\s*g\b': 'evolving',
            r'\bEvolv\s*in\s*g\b': 'Evolving',
            r'\bC\s*on\s*ducted\b': 'Conducted',
            r'\bc\s*on\s*ducted\b': 'conducted',
            r'\bin\s*nov\s*at\s*ive\b': 'innovative',
            r'\bIn\s*nov\s*at\s*ive\b': 'Innovative',
            r'\bl\s*at\s*est\b': 'latest',
            r'\bL\s*at\s*est\b': 'Latest',
            r'\bstr\s*on\s*g\b': 'strong',
            r'\bStr\s*on\s*g\b': 'Strong',
            r'\bW\s*in\s*dows\b': 'Windows',
            r'\bw\s*in\s*dows\b': 'windows',
            r'\bUltr\s*as\s*ound\b': 'Ultrasound',
            r'\bultr\s*as\s*ound\b': 'ultrasound',
            r'\bC\s*on\s*cepts\b': 'Concepts',
            r'\bc\s*on\s*cepts\b': 'concepts',
            r'\bcomp\s*on\s*ents\b': 'components',
            r'\bComp\s*on\s*ents\b': 'Components',
            r'\bD\s*is\s*k\b': 'Disk',
            r'\bd\s*is\s*k\b': 'disk',
            r'\bC\s*as\s*e\b': 'Case',
            r'\bc\s*as\s*e\b': 'case',
            r'\bEDUC\s*at\s*I\s*on\b': 'EDUCATION',
            r'\bin\s*tern\b': 'intern',
            r'\bIn\s*tern\b': 'Intern',
            r'\bin\s*ternals\b': 'internals',
            r'\bIn\s*ternals\b': 'Internals',
            r'\bdirecti\s*on\b': 'direction',
            r'\bDirecti\s*on\b': 'Direction',
            r'\bdem\s*on\s*strated\b': 'demonstrated',
            r'\bDem\s*on\s*strated\b': 'Demonstrated',
            r'\bg\s*at\s*hered\b': 'gathered',
            r'\bG\s*at\s*hered\b': 'Gathered',
            r'\bAccompl\s*is\s*hed\b': 'Accomplished',
            r'\baccompl\s*is\s*hed\b': 'accomplished',
            r'\bm\s*is\s*si\s*on\b': 'mission',
            r'\bM\s*is\s*si\s*on\b': 'Mission',
            r'\bo\s*the\s*r\b': 'other',
            r'\bO\s*the\s*r\b': 'Other',
            r'\bteams\s*to\b': 'teams to',
            r'\brequirements\s*for\b': 'requirements for',
            r'\bsolution\s*sto\b': 'solutions to',
            r'\breview\s*sto\b': 'reviews to',
            r'\bst\s*and\s*ards\b': 'standards',
            r'\bSt\s*and\s*ards\b': 'Standards',
            r'\btests\s*to\b': 'tests to',
            r'\bbugsto\b': 'bugs to',
            r'\bsolution\s*sby\b': 'solutions by',
            r'\bability\s*to\b': 'ability to',
            r'\badapt\s*to\b': 'adapt to',
            r'\badherence\s*to\b': 'adherence to',
            r'\bcommitment\s*to\b': 'commitment to',
            r'\bis\s*sues\b': 'issues',
            r'\bIs\s*sues\b': 'Issues',
        }
        
        # Pattern for detecting excessive spacing in general
        self.general_spacing_pattern = re.compile(r'\b(\w)\s+(\w{1,2})\s+(\w)\b')
        
    def calculate_corruption_score(self, text: str) -> float:
        """
        Calculate corruption score based on frequency of spaced-out words
        Returns score between 0.0 (clean) and 1.0 (heavily corrupted)
        """
        # Count patterns like "in g", "at i on", "er in g"
        spaced_patterns = re.findall(r'\b\w\s+\w{1,2}\s+\w\b|\b\w{1,2}\s+\w\s+\w{1,2}\b', text)
        
        # Count total words
        words = text.split()
        total_words = len(words)
        
        if total_words == 0:
            return 0.0
        
        # Score based on percentage of corrupted patterns
        corruption_ratio = len(spaced_patterns) / total_words
        return min(corruption_ratio * 10, 1.0)  # Scale up, cap at 1.0
        
    def repair_text(self, text: str) -> str:
        """Apply all corruption repair patterns"""
        repaired = text
        
        # Apply specific corruption patterns
        for pattern, replacement in self.corruption_patterns.items():
            repaired = re.sub(pattern, replacement, repaired, flags=re.IGNORECASE)
        
        # Clean up excessive spacing between characters
        # Handle patterns like "eng in eer in g" → "engineering"
        repaired = self._fix_character_spacing(repaired)
        
        # Fix concatenated words (no space between)
        repaired = self._fix_concatenated_words(repaired)
        
        # Clean up multiple spaces
        repaired = re.sub(r'\s{2,}', ' ', repaired)
        repaired = re.sub(r'\n{3,}', '\n\n', repaired)
        
        return repaired.strip()
    
    def _fix_character_spacing(self, text: str) -> str:
        """Fix words broken by spaces: 'eng in eer in g' → 'engineering'"""
        lines = text.split('\n')
        fixed_lines = []
        
        for line in lines:
            # Look for patterns like "word1 in word2 ing" - common in corrupted text
            # But be careful not to break legitimate two-word phrases
            
            # Fix specific ending patterns
            line = re.sub(r'(\w+)\s+in\s+g\b', r'\1ing', line)
            line = re.sub(r'(\w+)\s+at\s+i\s+on\b', r'\1ation', line)
            line = re.sub(r'(\w+)\s+at\s+ed\b', r'\1ated', line)
            line = re.sub(r'(\w+)\s+er\s+in\s+g\b', r'\1ering', line)
            line = re.sub(r'(\w+)\s+is\s+e\b', r'\1ise', line)
            line = re.sub(r'(\w+)\s+is\s+at\s+i\s+on\b', r'\1isation', line)
            line = re.sub(r'(\w+)\s+th\s+on\b', r'\1thon', line)
            line = re.sub(r'(\w+)\s+as\s+cript\b', r'\1ascript', line)
            line = re.sub(r'(\w+)\s+oid\b', r'\1oid', line)
            line = re.sub(r'(\w+)\s+to\b(?!\s+(?:the|be|a|an))', r'\1to', line)
            line = re.sub(r'(\w+)\s+w\s+are\b', r'\1ware', line)
            line = re.sub(r'(\w+)\s+tw\s+are\b', r'\1tware', line)
            line = re.sub(r'(\w+)\s+for\s+m(?:ance)?\b', r'\1form', line)
            line = re.sub(r'(\w+)\s+on\s+ent\b', r'\1onent', line)
            line = re.sub(r'(\w+)\s+ic\s+at\s+i\s+on\b', r'\1ication', line)
            line = re.sub(r'(\w+)\s+as\s+h\b', r'\1ash', line)
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _fix_concatenated_words(self, text: str) -> str:
        """Fix words that are concatenated without spaces"""
        # Common word+to patterns
        text = re.sub(r'(\w+)sto\b', r'\1s to', text)
        text = re.sub(r'ability to\b', r'ability to', text)
        text = re.sub(r'methodologies to\b', r'methodologies to', text)
        text = re.sub(r'teams to\b', r'teams to', text)
        text = re.sub(r'solutions to\b', r'solutions to', text)
        text = re.sub(r'reviews to\b', r'reviews to', text)
        text = re.sub(r'tests to\b', r'tests to', text)
        text = re.sub(r'bugs to\b', r'bugs to', text)
        text = re.sub(r'by to\b', r'by to', text)
        
        # Common word+in patterns
        text = re.sub(r'with in\b', r'within', text)
        text = re.sub(r'ma in ta in\b', r'maintain', text)
        text = re.sub(r'bus in ess\b', r'business', text)
        text = re.sub(r'in tegration\b', r'integration', text)
        
        # Common word+at patterns  
        text = re.sub(r'Alc at el\b', r'Alcatel', text)
        
        # Add space before 'to' when concatenated
        text = re.sub(r'([a-z])to\s+([a-z])', r'\1 to \2', text)
        
        return text
    
    def repair_file(self, input_path: str, output_path: str = None) -> Dict[str, any]:
        """
        Repair a text file with corruption issues
        
        Args:
            input_path: Path to corrupted text file
            output_path: Optional output path (defaults to overwriting input)
            
        Returns:
            Dictionary with repair statistics
        """
        if not os.path.exists(input_path):
            return {'success': False, 'error': 'File not found'}
        
        # Read original text
        with open(input_path, 'r', encoding='utf-8') as f:
            original_text = f.read()
        
        # Calculate corruption score
        corruption_score = self.calculate_corruption_score(original_text)
        
        # Repair text
        repaired_text = self.repair_text(original_text)
        
        # Write repaired text
        output_file = output_path or input_path
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(repaired_text)
        
        return {
            'success': True,
            'file': input_path,
            'corruption_score': corruption_score,
            'original_length': len(original_text),
            'repaired_length': len(repaired_text),
            'output_file': output_file
        }


def repair_directory(directory: str, pattern: str = "*.txt") -> List[Dict]:
    """Repair all text files in a directory"""
    repairer = TextCorruptionRepairer()
    results = []
    
    dir_path = Path(directory)
    for file_path in dir_path.glob(pattern):
        result = repairer.repair_file(str(file_path))
        results.append(result)
    
    return results


def main():
    """Command-line interface for text repair"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Repair corrupted text from PDF extraction')
    parser.add_argument('input', help='Input file or directory')
    parser.add_argument('-o', '--output', help='Output file (for single file repair)')
    parser.add_argument('-d', '--directory', action='store_true', help='Process directory')
    parser.add_argument('-p', '--pattern', default='*.txt', help='File pattern for directory mode')
    
    args = parser.parse_args()
    
    if args.directory:
        results = repair_directory(args.input, args.pattern)
        print(f"\n✓ Repaired {len(results)} files in {args.input}/")
        for result in results:
            if result['success']:
                score = result['corruption_score']
                status = "🔴 Severe" if score > 0.3 else "🟡 Moderate" if score > 0.1 else "🟢 Minor"
                print(f"  {status} | {Path(result['file']).name} (score: {score:.2f})")
    else:
        repairer = TextCorruptionRepairer()
        result = repairer.repair_file(args.input, args.output)
        
        if result['success']:
            print(f"\n✓ Successfully repaired: {result['file']}")
            print(f"  Corruption score: {result['corruption_score']:.2f}")
            print(f"  Output: {result['output_file']}")
        else:
            print(f"\n✗ Error: {result['error']}")


if __name__ == '__main__':
    main()
