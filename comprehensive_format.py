#!/usr/bin/env python3
"""
Comprehensive resume reformatting for better readability
"""
import re

def comprehensive_format(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove duplicate name in middle of document
    content = re.sub(r'\nAbhishek Kumar Dwivedi\n', '\n', content)
    
    # Fix all-caps sections to title case
    content = re.sub(r'POWER STATES AND HAL IMPLEMENTATIONS\. EXPERTISE IN CODING SKILLS AND\nANALYTICAL SKILLS WERE THE PRIMARY REQUIREMENT\. WORK INVOLVED HANDS ON',
                    'Power states and HAL implementations. Expertise in coding skills and analytical skills were the primary requirement. Work involved hands-on',
                    content)
    
    content = re.sub(r'US MARKET; USED TRACE32 DEBUGGING TOOLS WITH GOOD UNDERSTANDING OF',
                    'US market; used Trace32 debugging tools with good understanding of',
                    content)
    
    content = re.sub(r'PRODUCTION LINES TO UNDERSTAND TOOLS AND LIMITATIONS\. GOT A SOLUTION',
                    'production lines to understand tools and limitations. Got a solution',
                    content)
    
    content = re.sub(r'DESCRIPTION: WORKED FOR CDMA PHONES; USED DEBUGGING TOOLS TRACE32',
                    'Description: Worked for CDMA phones; used debugging tools Trace32',
                    content)
    
    # Fix conjested project entries - add proper structure
    # Clean up broken lines and consolidate text
    lines = content.split('\n')
    formatted = []
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip excessive separators
        if line == '--------------------------------------------------':
            # Only add separator if previous line is not empty and not already a separator
            if formatted and formatted[-1].strip() and not formatted[-1].strip().startswith('-'):
                formatted.append('')
                formatted.append('--------------------------------------------------')
            i += 1
            continue
        
        # Fix Platform/Programming lines that are separate
        if line.startswith('Platform:') or line.startswith('Programming:'):
            # Check if next line is also Platform/Programming or Description
            if i + 1 < len(lines) and (lines[i+1].strip().startswith('Programming:') or 
                                       lines[i+1].strip().startswith('Platform:') or
                                       lines[i+1].strip().startswith('Description:')):
                formatted.append(line)
                i += 1
                continue
        
        formatted.append(lines[i].rstrip())
        i += 1
    
    content = '\n'.join(formatted)
    
    # Remove triple+ blank lines
    content = re.sub(r'\n\n\n+', '\n\n', content)
    
    # Clean up specific conjested sections
    replacements = {
        # Fix Collabera entry
        r'Lead Engineer\nCollabera, India\n\n--------------------------------------------------\nAndroid bring-up, Automotive stack development':
            'Lead Engineer\nCollabera, India\n\nAndroid bring-up, Automotive stack development',
        
        # Fix broken project titles
        r'PROJECT: \[Contractor\] Yocto based Embedded gateway bring-up for Intel\n\n--------------------------------------------------\nPlatform:':
            'PROJECT: [Contractor] Yocto based Embedded gateway bring-up for Intel\n\nPlatform:',
        
        r'PROJECT: \[Contractor\]  home gateway hub development\n\n--------------------------------------------------\nPlatform: , Android':
            'PROJECT: [Contractor] Smart Home Gateway Hub Development\n\nPlatform: Android',
        
        r'Android O based Automotive infotainment HAL development\n\n--------------------------------------------------\nPlatform:':
            'PROJECT: Android O based Automotive Infotainment HAL Development\n\nPlatform:',
        
        r'PROJECT: \[Startup\]Implementation of various embedded devices\n\n--------------------------------------------------\nPlatform:':
            'PROJECT: [Startup] Implementation of Various Embedded Devices\n\nPlatform:',
        
        r'Programming: NodeJS\nDescription:':
            '\nProgramming: NodeJS\n\nDescription:',
        
        # Fix broken descriptions
        r'Automotive BSP for AMD \(Android and Linux\)\nDescription:\nWorked\nandroid':
            'PROJECT: Automotive BSP for AMD (Android and Linux)\n\nDescription: Worked on Android',
        
        r'Telematics RIL development based on Yocto and Android for LG\nDescription:':
            'PROJECT: Telematics RIL Development for LG (Yocto and Android)\n\nDescription:',
        
        # Fix city gateway
        r'PROJECT: \[Startup\]  city gateway development':
            'PROJECT: [Startup] Smart City Gateway Development',
        
        # Fix 2006-2015 section
        r'2006 to 2015\nAndroid OS stack specification, design and development for\nDescription:\nImplemented\nmanager\nframework\nstack\nupon':
            'PROJECT: Android OS Stack Specification and Development (2006-2015)\n\nDescription: Implemented manager framework stack upon',
        
        # Fix IoT server
        r'IoT server automation framework, Android\n\n--------------------------------------------------\nPlatform:':
            'PROJECT: IoT Server Automation Framework (Android)\n\nPlatform:',
        
        # Fix VOIP
        r'VOIP audio and SIP implementation, Android\nDescription:':
            'PROJECT: VOIP Audio and SIP Implementation (Android)\n\nDescription:',
        
        # Fix MM1
        r'--------------------------------------------------\nMM1 proxy server development\nDescription:':
            '--------------------------------------------------\nPROJECT: MM1 Proxy Server Development\n\nDescription:',
        
        # Fix Android customization
        r'Android customization, HAL and JNI development on\nQualcomm Snapdragon S2\nRole:':
            'PROJECT: Android Customization, HAL and JNI Development\nPlatform: Qualcomm Snapdragon S2\n\nRole:',
        
        # Fix Solaris
        r'Soaris and RedHat OS issues root case finding\nDescription:':
            'PROJECT: Solaris and RedHat OS Issues Root Cause Finding\n\nDescription:',
        
        # Fix BREW sections
        r'BREW OEM developer for Samsung phones\nDescription:':
            'PROJECT: BREW OEM Developer for Samsung Phones\n\nDescription:',
        
        r'BREW platform stability on Kyocera phones on\nHardware\n\n--------------------------------------------------\nPlatform:':
            'PROJECT: BREW Platform Stability on Kyocera Phones\n\nPlatform:',
        
        # Fix Android RIL Changes
        r'Android  and RIL Changes\nDescription:':
            'PROJECT: Android and RIL Changes\n\nDescription:',
        
        # Fix Android Audio
        r'Android Audio stack analysis and HAL changes\n\n--------------------------------------------------\nPlatform:':
            'PROJECT: Android Audio Stack Analysis and HAL Changes\n\nPlatform:',
        
        # Fix Android porting
        r'Android porting, Intel and TI SoCs\nDescription:':
            'PROJECT: Android Porting for Intel and TI SoCs\n\nDescription:',
        
        # Fix framework stability
        r'Android framework stability\nDuration: February 2011 to May 2011\n\n--------------------------------------------------\nPlatform:':
            'PROJECT: Android Framework Stability\nDuration: February 2011 to May 2011\n\nPlatform:',
        
        # Fix Samsung platform
        r'Samsung platform stability on Samsung phones\nDuration: November 2008 to February 2009\n\n--------------------------------------------------\nPlatform:':
            'PROJECT: Samsung Platform Stability\nDuration: November 2008 to February 2009\n\nPlatform:',
        
        # Fix Kyocera
        r'and Kyocera native platform stability on\nHardware\nDuration: November 2006 to July 2007\n\n--------------------------------------------------\nPlatform:':
            'PROJECT: Kyocera Native Platform Stability\nDuration: November 2006 to July 2007\n\nPlatform:',
        
        # Fix Automotive rig
        r'--------------------------------------------------\nAutomotive rig development\nDuration:':
            '--------------------------------------------------\nPROJECT: Automotive Rig Development\n\nDuration:',
    }
    
    for pattern, replacement in replacements.items():
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    # Fix broken multi-line words
    content = re.sub(r'\n([a-z])', r' \1', content)  # Join lines that continue mid-word
    
    # Clean up multiple spaces
    content = re.sub(r'  +', ' ', content)
    
    # Final cleanup of excessive blank lines
    content = re.sub(r'\n\n\n+', '\n\n', content)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✓ Comprehensive formatting complete!")
    print(f"✓ Output saved to: {output_file}")

if __name__ == '__main__':
    input_file = r'c:\Users\shiva\Downloads\samplecvs\redacted_resumes\AbhishekKumarDwivedi__formatted.txt'
    output_file = r'c:\Users\shiva\Downloads\samplecvs\redacted_resumes\AbhishekKumarDwivedi__final.txt'
    comprehensive_format(input_file, output_file)
