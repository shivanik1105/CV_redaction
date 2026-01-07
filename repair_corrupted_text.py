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
            
            # Additional comprehensive patterns
            r'\bin\s*to\s+engineering\b': 'into engineering',
            r'\bSpecial\s*ization\b': 'Specialization',
            r'\bStr\s*at\s*egy\b': 'Strategy',
            r'\bstr\s*at\s*egy\b': 'strategy',
            r'\bAu\s*to\s*motive\b': 'Automotive',
            r'\bau\s*to\s*motive\b': 'automotive',
            r'\band\s*roid\b': 'Android',
            r'\bAnd\s*roid\b': 'Android',
            r'\bIo\s*T\b': 'IoT',
            r'\bIo\s*Tg\s*at\s*eways\b': 'IoT gateways',
            r'\blowlevelembedded\b': 'low-level embedded',
            r'\bin\s*terfaces\b': 'interfaces',
            r'\bIn\s*terfaces\b': 'Interfaces',
            r'\bc\s*on\s*trol\b': 'control',
            r'\bC\s*on\s*trol\b': 'Control',
            r'\bis\s*O\s*21434\b': 'ISO 21434',
            r'\bISO\s*21434\b': 'ISO 21434',
            r'\bcomplexs\s*oftware\s*s\b': 'complex software',
            r'\bInvolving\b': 'involving',
            r'\bto\s*oling\b': 'tooling',
            r'\bTo\s*oling\b': 'Tooling',
            r'\bf\s*as\s*tlearner\b': 'fast learner',
            r'\bF\s*as\s*tlearner\b': 'Fast learner',
            r'\bSelfmotivated\b': 'Self-motivated',
            r'\bselfmotivated\b': 'self-motivated',
            r'\bEmbeddedhardw\s*are\b': 'Embedded hardware',
            r'\bembeddedhardw\s*are\b': 'embedded hardware',
            r'\bM\s*is\s*RA\b': 'MISRA',
            r'\bHyperv\s*is\s*or\b': 'Hypervisor',
            r'\bhyperv\s*is\s*or\b': 'hypervisor',
            r'\bDebianL\s*in\s*ux\b': 'Debian Linux',
            r'\bdebianL\s*in\s*ux\b': 'debian Linux',
            r'\bC\s*on\s*sultant\s*to\b': 'Consultant to',
            r'\bc\s*on\s*sultant\s*to\b': 'consultant to',
            r'\bas\s*marthome\b': 'a smart home',
            r'\bg\s*at\s*eway\b': 'gateway',
            r'\bG\s*at\s*eway\b': 'Gateway',
            r'\bas\s*s\s*is\s*tant\b': 'assistant',
            r'\bAs\s*s\s*is\s*tant\b': 'Assistant',
            r'\bblue\s*to\s*oth\b': 'Bluetooth',
            r'\bBlue\s*to\s*oth\b': 'Bluetooth',
            r'\bbring-up\b': 'bring-up',
            r'\bBring-up\b': 'Bring-up',
            r'\bbr\s*in\s*gup\b': 'bring-up',
            r'\bBr\s*in\s*gup\b': 'Bring-up',
            r'\bin\s*tel\b': 'Intel',
            r'\bIn\s*tel\b': 'Intel',
            r'\bYoc\s*to\s*l\s*in\s*ux\b': 'Yocto Linux',
            r'\byoc\s*to\s*l\s*in\s*ux\b': 'Yocto Linux',
            r'\bL\s*in\s*aro\b': 'Linaro',
            r'\bl\s*in\s*aro\b': 'Linaro',
            r'\bengineering\s*practices\b': 'Engineering Practices',
            r'\bbuilds\s*oftware\b': 'build software',
            r'\bAIb\s*as\s*ed\b': 'AI-based',
            r'\bpark\s*in\s*gmetre\b': 'parking metre',
            r'\bw\s*as\s+in\s+various\b': 'was in various',
            r'\bstart-upactivities\b': 'start-up activities',
            r'\bHadbeenhost\s*in\s*g\b': 'Had been hosting',
            r'\bstart-upmeetups\b': 'start-up meetups',
            r'\bc\s*on\s*sult\s*in\s*g\b': 'consulting',
            r'\bC\s*on\s*sult\s*in\s*g\b': 'Consulting',
            r'\bIo\s*Tb\s*as\s*ed\b': 'IoT-based',
            r'\bproduct\s*s\b': 'products',
            r'\bwhileworking\b': 'while working',
            r'\bfirmw\s*are\b': 'firmware',
            r'\bFirmw\s*are\b': 'Firmware',
            r'\bin\s*COSE\s*is\s*O\b': 'in COSE ISO',
            r'\bas\s*PICE\s*is\s*O\b': 'as SPICE ISO',
            r'\bC-SEC\s*is\s*O\b': 'C-SEC ISO',
            r'\bth\s*in\s*kerstage\b': 'thinker stage',
            r'\bTh\s*in\s*kerstage\b': 'Thinker stage',
            r'\bfrom\s*scr\s*at\s*ch\b': 'from scratch',
            r'\bagoogle\b': 'a Google',
            r'\bproduct\s*i\s*on\s*st\s*and\s*ard\b': 'production standard',
            r'\bdive\s*in\s*to\s+hardware\b': 'dive into hardware',
            r'\bmicroc\s*on\s*troller\b': 'microcontroller',
            r'\bMicroc\s*on\s*troller\b': 'Microcontroller',
            r'\bcloud\s*interface\b': 'cloud interface',
            r'\bPr\s*in\s*cipal\b': 'Principal',
            r'\bpr\s*in\s*cipal\b': 'principal',
            r'\bTeleph\s*on\s*y\b': 'Telephony',
            r'\bteleph\s*on\s*y\b': 'telephony',
            r'\bXenhyperv\s*is\s*or\b': 'Xen Hypervisor',
            r'\bxenhyperv\s*is\s*or\b': 'Xen hypervisor',
            r'\bcloud\s*in\s*fra\b': 'cloud infra',
            r'\bCloud\s*in\s*fra\b': 'Cloud infra',
            r'\bC\s*on\s*nectivity\b': 'Connectivity',
            r'\bc\s*on\s*nectivity\b': 'connectivity',
            r'\bboardbring-up\b': 'board bring-up',
            r'\bmarket\s*in\s*g\b': 'marketing',
            r'\bMarket\s*in\s*g\b': 'Marketing',
            r'\bMobilefirmw\s*are\b': 'Mobile firmware',
            r'\bmobilefirmw\s*are\b': 'mobile firmware',
            r'\bArchitecture\b': 'Architecture',
            r'\barchitecture\b': 'architecture',
            r'\bto\s*ols\b': 'tools',
            r'\bTo\s*ols\b': 'Tools',
            r'\breamdumpanalys\s*is\b': 'reamdump analysis',
            r'\bAbh\s*is\s*hek\b': 'Abhishek',
            r'\bTilld\s*at\s*e\b': 'Till date',
            r'\btilld\s*at\s*e\b': 'till date',
            r'\bDescripti\s*on\b': 'Description',
            r'\bdescripti\s*on\b': 'description',
            r'\bdoma\s*in\s*s\b': 'domains',
            r'\bDoma\s*in\s*s\b': 'Domains',
            r'\bin\s*cluding\b': 'including',
            r'\bIn\s*cluding\b': 'Including',
            r'\bcus\s*to\s*mization\b': 'customization',
            r'\bCus\s*to\s*mization\b': 'Customization',
            r'\bf\s*in\s*ding\b': 'finding',
            r'\bF\s*in\s*ding\b': 'Finding',
            r'\bupd\s*at\s*e\b': 'update',
            r'\bUpd\s*at\s*e\b': 'Update',
            r'\bKnowledge\b': 'Knowledge',
            r'\bknowledge\b': 'knowledge',
            r'\bin\s*ter\s+virtualization\b': 'inter-virtualization',
            r'\bStakeholders\b': 'Stakeholders',
            r'\bstakeholders\b': 'stakeholders',
            r'\bengagement\b': 'engagement',
            r'\bEngagement\b': 'Engagement',
            r'\bgrooming\b': 'grooming',
            r'\bGrooming\b': 'Grooming',
            r'\bspecification\s*s\b': 'specifications',
            r'\bSpecification\s*s\b': 'Specifications',
            r'\bWorkrequiresexpertise\b': 'Work requires expertise',
            r'\bworkrequiresexpertise\b': 'work requires expertise',
            r'\bperipherals\b': 'peripherals',
            r'\bPeripherals\b': 'Peripherals',
            r'\bgeneral\s*is\s*t\b': 'generalist',
            r'\bGeneral\s*is\s*t\b': 'Generalist',
            r'\bover\s*all\b': 'overall',
            r'\bOver\s*all\b': 'Overall',
            r'\bapplication\s*s\b': 'applications',
            r'\bApplication\s*s\b': 'Applications',
            r'\bAu\s*to\s*sar\b': 'AUTOSAR',
            r'\bC\s*on\s*nected\b': 'Connected',
            r'\bc\s*on\s*nected\b': 'connected',
            r'\bStartupbus\s*in\s*ess\b': 'Startup business',
            r'\bstartupbus\s*in\s*ess\b': 'startup business',
            r'\bBus\s*in\s*ess\b': 'Business',
            r'\bbus\s*in\s*ess\b': 'business',
            r'\bplanto\b': 'plan to',
            r'\bPlanTo\b': 'Plan To',
            r'\bfund\s*in\s*g\b': 'funding',
            r'\bFund\s*in\s*g\b': 'Funding',
            r'\byearroadmap\b': 'year roadmap',
            r'\bmarket\s*in\s*terest\b': 'market interest',
            r'\bhypo\s*the\s*s\s*is\b': 'hypothesis',
            r'\bfounding\b': 'founding',
            r'\bFounding\b': 'Founding',
            r'\bf\s*in\s*ancial\b': 'financial',
            r'\bF\s*in\s*ancial\b': 'Financial',
            r'\br\s*is\s*k\b': 'risk',
            r'\bR\s*is\s*k\b': 'Risk',
            r'\bgreenenergyfield\b': 'green energy field',
            r'\bDem\s*on\s*str\s*at\s*ed\b': 'Demonstrated',
            r'\bdem\s*on\s*str\s*at\s*ed\b': 'demonstrated',
            r'\bMVPstr\s*at\s*egy\b': 'MVP strategy',
            r'\bmvpstr\s*at\s*egy\b': 'MVP strategy',
            r'\bef\s*for\s*t\b': 'effort',
            r'\bEf\s*for\s*t\b': 'Effort',
            r'\bm\s*on\s*ey\b': 'money',
            r'\bM\s*on\s*ey\b': 'Money',
            r'\breduceend\b': 'reduce end',
            r'\bTelem\s*at\s*ics\b': 'Telematics',
            r'\btelem\s*at\s*ics\b': 'telematics',
            r'\bb\s*as\s*ed\s+on\b': 'based on',
            r'\bCodecus\s*to\s*mization\b': 'Code customization',
            r'\bcodecus\s*to\s*mization\b': 'code customization',
            r'\bfollowed\s*b\s*as\s*ed\b': 'followed based',
            r'\bcoding\s*Standards\b': 'coding standards',
            r'\bcoding\b': 'coding',
            r'\bCoding\b': 'Coding',
            r'\bw\s*as\s+the\s+primarywork\b': 'was the primary work',
            r'\bPeripheralbring-up\b': 'Peripheral bring-up',
            r'\bperipheralbring-up\b': 'peripheral bring-up',
            r'\bto\s*uch\b': 'touch',
            r'\bTo\s*uch\b': 'Touch',
            r'\bmodules\b': 'modules',
            r'\bModules\b': 'Modules',
            r'\bto\s*in\s*terface\b': 'to interface',
            r'\bexternalmicroc\s*on\s*troller\b': 'external microcontroller',
            r'\bc\s*on\s*trolling\b': 'controlling',
            r'\bC\s*on\s*trolling\b': 'Controlling',
            r'\bmo\s*to\s*rs\b': 'motors',
            r'\bMo\s*to\s*rs\b': 'Motors',
            r'\bworking\b': 'working',
            r'\bWorking\b': 'Working',
            r'\bserviceto\b': 'service to',
            r'\bServiceTo\b': 'Service To',
            r'\bc\s*on\s*trol\s+stack\b': 'control stack',
            r'\bworked\s*at\b': 'worked at',
            r'\bWorked\s*At\b': 'Worked At',
            r'\bI\s*2\s*C\b': 'I2C',
            r'\bsniffer\b': 'sniffer',
            r'\bSniffer\b': 'Sniffer',
            r'\bal\s*on\s*g\s+with\b': 'along with',
            r'\beng\s*in\s*eers\b': 'engineers',
            r'\bEng\s*in\s*eers\b': 'Engineers',
            r'\bschem\s*at\s*ics\b': 'schematics',
            r'\bSchem\s*at\s*ics\b': 'Schematics',
            r'\band\s*roidcus\s*to\s*mization\b': 'Android customization',
            r'\bper\s+product\b': 'per product',
            r'\bNodeJS\s*b\s*as\s*ed\b': 'NodeJS-based',
            r'\bin\s*terfacing\b': 'interfacing',
            r'\bIn\s*terfacing\b': 'Interfacing',
            r'\bcus\s*to\s*mization\b': 'customization',
            r'\bRNNAIalgorithm\b': 'RNN AI algorithm',
            r'\bd\s*at\s*as\s*et\b': 'dataset',
            r'\bD\s*at\s*as\s*et\b': 'Dataset',
            r'\bupd\s*at\s*e\b': 'update',
            r'\bUpd\s*at\s*e\b': 'Update',
            r'\bOb\s*as\s*ed\b': 'O-based',
            r'\bin\s*fota\s*in\s*ment\b': 'infotainment',
            r'\bIn\s*fota\s*in\s*ment\b': 'Infotainment',
            r'\bplatform\b': 'Platform',
            r'\bof\s*or\s*Car\b': 'for Car',
            r'\bau\s*to\s*motive\b': 'automotive',
            r'\bAu\s*to\s*motive\b': 'Automotive',
            r'\bas\s*anarchitect\b': 'as an architect',
            r'\bd\s*is\s*cussi\s*on\b': 'discussion',
            r'\bD\s*is\s*cussi\s*on\b': 'Discussion',
            r'\bimplementation\b': 'implementation',
            r'\bImplementation\b': 'Implementation',
            r'\bcodeb\s*as\s*ed\b': 'code based',
            r'\bCodeb\s*as\s*ed\b': 'Code based',
            r'\bto\s*d\s*of\s*ur\s*the\s*r\b': 'to do further',
            r'\bto\s*explore\b': 'to explore',
            r'\bto\s*Explore\b': 'to Explore',
            r'\bmentoring\s*Other\b': 'mentoring other',
            r'\bMentoring\s*Other\b': 'Mentoring other',
            r'\beng\s*in\s*eers\b': 'engineers',
            r'\bEng\s*in\s*eers\b': 'Engineers',
            r'\bverification\b': 'verification',
            r'\bVerification\b': 'Verification',
            r'\bTo\s*men\s*to\s*r\b': 'To mentor',
            r'\bto\s*men\s*to\s*r\b': 'to mentor',
            r'\bin\s*tegra\s*to\s*r\b': 'integrator',
            r'\bIn\s*tegra\s*to\s*r\b': 'Integrator',
            r'\bapplication\s*sto\b': 'applications to',
            r'\bApplication\s*sTo\b': 'Applications To',
            r'\band\s*roidO\b': 'Android O',
            r'\bvariousembedded\b': 'various embedded',
            r'\bVariousembedded\b': 'Various embedded',
            r'\bNodeMCU/ESP\b': 'NodeMCU / ESP',
            r'\bArdu\s*in\s*o\b': 'Arduino',
            r'\bardu\s*in\s*o\b': 'Arduino',
            r'\bat\s*t\s*in\s*y\b': 'ATtiny',
            r'\bsensor\s*modules\b': 'sensor modules',
            r'\bSensor\s*Modules\b': 'Sensor Modules',
            r'\bimplementing\b': 'implementing',
            r'\bImplementing\b': 'Implementing',
            r'\bend\s*to\s*end\b': 'end-to-end',
            r'\bEnd\s*to\s*End\b': 'End-to-end',
            r'\bal\s*on\s*g\s+with\b': 'along with',
            r'\bEnd\s*sensor\b': 'End sensor',
            r'\bend\s*sensor\b': 'end sensor',
            r'\bProgramming\b': 'Programming',
            r'\bprogramming\b': 'programming',
            r'\bin\s*tegration\b': 'integration',
            r'\bIn\s*tegration\b': 'Integration',
            r'\bMEAN\s*stack\b': 'MEAN stack',
            r'\bhardware\s*selecti\s*on\b': 'hardware selection',
            r'\bHardware\s*Selecti\s*on\b': 'Hardware Selection',
            r'\bproposal\s*creation\b': 'proposal creation',
            r'\bProposal\s*Creation\b': 'Proposal Creation',
            r'\bfit\s*in\b': 'fit in',
            r'\bFit\s*In\b': 'Fit In',
            r'\bSomeR&D\b': 'Some R&D',
            r'\bsomeR&D\b': 'some R&D',
            r'\bstr\s*at\s*egy\b': 'strategy',
            r'\bStr\s*at\s*egy\b': 'Strategy',
            r'\breduceend\b': 'reduce end',
            r'\bReduceend\b': 'Reduce end',
            r'\b3\s*D\b': '3D',
            r'\benclosure\b': 'enclosure',
            r'\bEnclosure\b': 'Enclosure',
            r'\bmechanical\b': 'mechanical',
            r'\bMechanical\b': 'Mechanical',
            r'\bfusion\s*360\b': 'Fusion 360',
            r'\bFusion\s*360\b': 'Fusion 360',
            r'\bpr\s*in\s*ted\b': 'printed',
            r'\bPr\s*in\s*ted\b': 'Printed',
            r'\bdemo\b': 'demo',
            r'\bDemo\b': 'Demo',
            r'\bc\s*on\s*trac\s*to\s*rs\b': 'contractors',
            r'\bC\s*on\s*trac\s*to\s*rs\b': 'Contractors',
            r'\bmanufacturing\b': 'manufacturing',
            r'\bManufacturing\b': 'Manufacturing',
            r'\bas\s*sembly\b': 'assembly',
            r'\bAs\s*sembly\b': 'Assembly',
            r'\bPartner\b': 'Partner',
            r'\bpartner\b': 'partner',
            r'\bsupplier\b': 'supplier',
            r'\bSupplier\b': 'Supplier',
            r'\bbuilt-up\b': 'built-up',
            r'\bBuilt-up\b': 'Built-up',
            r'\bSmartcityg\s*at\s*eway\b': 'Smart city gateway',
            r'\bsmartcityg\s*at\s*eway\b': 'smart city gateway',
            r'\bRequirementanalys\s*is\b': 'Requirement analysis',
            r'\brequirementanalys\s*is\b': 'requirement analysis',
            r'\bESP\s*8266\b': 'ESP8266',
            r'\bESP\s*32\b': 'ESP32',
            r'\bb\s*as\s*edmulti\b': 'based multi',
            r'\bB\s*as\s*edmulti\b': 'Based multi',
            r'\bnode\s*network\b': 'node network',
            r'\bNode\s*Network\b': 'Node Network',
            r'\bsolution\b': 'solution',
            r'\bSolution\b': 'Solution',
            r'\bin\s*terfacing\s*nodes\b': 'interfacing nodes',
            r'\bIn\s*terfacing\s*Nodes\b': 'Interfacing Nodes',
            r'\bMQTT\b': 'MQTT',
            r'\bREST\b': 'REST',
            r'\bin\s*terfaces\b': 'interfaces',
            r'\bIn\s*terfaces\b': 'Interfaces',
            r'\bbuilt\s*gateway\b': 'built gateway',
            r'\bBuilt\s*Gateway\b': 'Built Gateway',
            r'\bcoded\b': 'coded',
            r'\bCoded\b': 'Coded',
            r'\bNode-RED\b': 'Node-RED',
            r'\bcomplete\b': 'complete',
            r'\bComplete\b': 'Complete',
            r'\bbuilt\s*at\s*eam\b': 'built a team',
            r'\bBuilt\s*at\s*eam\b': 'Built a team',
            r'\bneweng\s*in\s*eers\b': 'new engineers',
            r'\bNeweng\s*in\s*eers\b': 'New engineers',
            r'\band\s*roidtraveller\b': 'Android traveller',
            r'\bAnd\s*roidtraveller\b': 'Android traveller',
            r'\bapplication\b': 'application',
            r'\bApplication\b': 'Application',
            r'\bcloud\s*development\b': 'cloud development',
            r'\bCloud\s*Development\b': 'Cloud Development',
            r'\bImplemented\b': 'Implemented',
            r'\bimplemented\b': 'implemented',
            r'\bM\s*on\s*goDB\b': 'MongoDB',
            r'\bm\s*on\s*goDB\b': 'MongoDB',
            r'\bExpress\b': 'Express',
            r'\bexpress\b': 'express',
            r'\binto\s*Dev\s*Ops\b': 'into DevOps',
            r'\bData\s*Analysis\b': 'Data Analysis',
            r'\bdata\s*analysis\b': 'data analysis',
            r'\bcloud\b': 'cloud',
            r'\bCloud\b': 'Cloud',
            r'\blearning\b': 'learning',
            r'\bLearning\b': 'Learning',
            r'\buser\s*activity\b': 'user activity',
            r'\bUser\s*Activity\b': 'User Activity',
            r'\bproviding\b': 'providing',
            r'\bProviding\b': 'Providing',
            r'\bsuggesti\s*on\s*s\b': 'suggestions',
            r'\bSuggesti\s*on\s*s\b': 'Suggestions',
            r'\bUsed\b': 'Used',
            r'\bused\b': 'used',
            r'\bGoogle\s*place\b': 'Google Place',
            r'\bgoogle\s*place\b': 'Google Place',
            r'\bGoogle\s*Maps\b': 'Google Maps',
            r'\bgoogle\s*maps\b': 'Google Maps',
            r'\brecyclerview\b': 'RecyclerView',
            r'\bRecyclerview\b': 'RecyclerView',
            r'\bfragments\b': 'fragments',
            r'\bFragments\b': 'Fragments',
            r'\bapplication\s*development\b': 'application development',
            r'\bApplication\s*Development\b': 'Application Development',
            r'\bDid\s*marketing\b': 'Did marketing',
            r'\bdid\s*marketing\b': 'did marketing',
            r'\bbuilt\s*solution\b': 'built solution',
            r'\bBuilt\s*Solution\b': 'Built Solution',
            r'\bf\s*in\s*d\b': 'find',
            r'\bF\s*in\s*d\b': 'Find',
            r'\bpotential\b': 'potential',
            r'\bPotential\b': 'Potential',
            r'\bpartners\b': 'partners',
            r'\bPartners\b': 'Partners',
            r'\bVCto\s*in\s*vest\b': 'VC to invest',
            r'\bfur\s*the\s*r\b': 'further',
            r'\bFur\s*the\s*r\b': 'Further',
            r'\bexpansi\s*on\b': 'expansion',
            r'\bExpansi\s*on\b': 'Expansion',
            r'\bGotmarkettracti\s*on\b': 'Got market traction',
            r'\bgotmarkettracti\s*on\b': 'got market traction',
            r'\bNode-RED\b': 'Node-RED',
            r'\bKa\s*as\s*DK\b': 'KaaS DK',
            r'\bAdded\b': 'Added',
            r'\badded\b': 'added',
            r'\bSDK\s*interface\b': 'SDK interface',
            r'\bsdk\s*interface\b': 'SDK interface',
            r'\bJavaScript\s*using\b': 'JavaScript using',
            r'\bjavaScript\s*using\b': 'JavaScript using',
            r'\bNAN\s*interface\b': 'NAN interface',
            r'\bnan\s*interface\b': 'NAN interface',
            r'\bbackendg\s*at\s*eway\b': 'backend gateway',
            r'\bBackendg\s*at\s*eway\b': 'Backend gateway',
            r'\bfetching\b': 'fetching',
            r'\bFetching\b': 'Fetching',
            r'\bstreetd\s*at\s*a\b': 'street data',
            r'\bStreetd\s*at\s*a\b': 'Street data',
            r'\banalyticsd\s*as\s*hboard\b': 'analytics dashboard',
            r'\bAnalyticsd\s*as\s*hboard\b': 'Analytics dashboard',
            r'\bMen\s*to\s*redafew\b': 'Mentored a few',
            r'\bmen\s*to\s*redafew\b': 'mentored a few',
            r'\bbuildESP\b': 'build ESP',
            r'\bBuildESP\b': 'Build ESP',
            r'\bb\s*as\s*ed\s*edge\b': 'based edge',
            r'\bB\s*as\s*ed\s*Edge\b': 'Based edge',
            r'\bnodes\b': 'nodes',
            r'\bNodes\b': 'Nodes',
            r'\bWi\s*Fi\s*mesh\b': 'Wi-Fi mesh',
            r'\bwi\s*Fi\s*mesh\b': 'Wi-Fi mesh',
            r'\bmanufacturers\b': 'manufacturers',
            r'\bManufacturers\b': 'Manufacturers',
            r'\bmarketready\b': 'market ready',
            r'\bMarketready\b': 'Market ready',
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
