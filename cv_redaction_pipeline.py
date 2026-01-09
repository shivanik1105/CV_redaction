#!/usr/bin/env python3
"""
Universal CV Redaction Pipeline - Configuration-Driven CLI
===========================================================
Zero hardcoded data. All rules, terms, and patterns from JSON configs.

QUICKSTART:
    # Process CVs (auto-creates configs on first run)
    python cv_redaction_pipeline.py resume/ final_output/
    
    # With debug output
    python cv_redaction_pipeline.py resume/ final_output/ --debug

ADD NEW DATA (No code changes needed):
    # Add locations
    python cv_redaction_pipeline.py add-city "San Francisco"
    python cv_redaction_pipeline.py add-state "California"
    python cv_redaction_pipeline.py add-country "Canada"
    
    # Add protected technical terms
    python cv_redaction_pipeline.py add-term "tensorflow"
    python cv_redaction_pipeline.py add-term "kubernetes" --category cloud
    
    # Add spacing fix rules
    python cv_redaction_pipeline.py add-healing "administr at ion" "administration"
    
    # List current configurations
    python cv_redaction_pipeline.py list-cities
    python cv_redaction_pipeline.py list-terms
    python cv_redaction_pipeline.py list-config

OR EDIT JSON DIRECTLY:
    config/locations.json          - Cities, states, countries
    config/protected_terms.json    - Technical terms to preserve
    config/sections.json           - Section headers
    config/pii_patterns.json       - PII detection patterns
    config/text_healing.json       - Spacing fix rules
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Optional

# Import the engine
from universal_pipeline_engine import (
    PipelineOrchestrator,
    ConfigLoader,
    logger
)


# ============================================================================
# CONFIG MANAGEMENT COMMANDS
# ============================================================================

class ConfigManager:
    """Manage configuration files with a friendly CLI"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.loader = ConfigLoader(config_dir)
    
    def add_city(self, city: str) -> None:
        """Add a city to locations config"""
        config_path = self.config_dir / "locations.json"
        locations = self.loader.load('locations')
        
        if city not in locations['cities']:
            locations['cities'].append(city)
            locations['cities'].sort()
            self._save_json(config_path, locations)
            print(f"✓ Added city: {city}")
        else:
            print(f"⚠ City already exists: {city}")
    
    def add_state(self, state: str) -> None:
        """Add a state to locations config"""
        config_path = self.config_dir / "locations.json"
        locations = self.loader.load('locations')
        
        if state not in locations['states']:
            locations['states'].append(state)
            locations['states'].sort()
            self._save_json(config_path, locations)
            print(f"✓ Added state: {state}")
        else:
            print(f"⚠ State already exists: {state}")
    
    def add_country(self, country: str) -> None:
        """Add a country to locations config"""
        config_path = self.config_dir / "locations.json"
        locations = self.loader.load('locations')
        
        if country not in locations['countries']:
            locations['countries'].append(country)
            locations['countries'].sort()
            self._save_json(config_path, locations)
            print(f"✓ Added country: {country}")
        else:
            print(f"⚠ Country already exists: {country}")
    
    def add_term(self, term: str, category: str = "technical_terms") -> None:
        """Add a protected technical term"""
        config_path = self.config_dir / "protected_terms.json"
        protected = self.loader.load('protected_terms')
        
        if category not in protected:
            protected[category] = []
        
        term_lower = term.lower()
        if term_lower not in [t.lower() for t in protected[category]]:
            protected[category].append(term_lower)
            protected[category].sort()
            self._save_json(config_path, protected)
            print(f"✓ Added term '{term}' to category '{category}'")
        else:
            print(f"⚠ Term already exists: {term}")
    
    def add_healing_rule(self, broken: str, fixed: str) -> None:
        """Add a text healing rule"""
        config_path = self.config_dir / "text_healing.json"
        healing = self.loader.load('text_healing')
        
        healing['common_words'][broken] = fixed
        
        # Sort by key for better readability
        healing['common_words'] = dict(sorted(healing['common_words'].items()))
        
        self._save_json(config_path, healing)
        print(f"✓ Added healing rule: '{broken}' → '{fixed}'")
    
    def list_cities(self) -> None:
        """List all cities"""
        locations = self.loader.load('locations')
        cities = locations.get('cities', [])
        print(f"\n📍 Cities ({len(cities)}):")
        for city in cities:
            print(f"   • {city}")
    
    def list_states(self) -> None:
        """List all states"""
        locations = self.loader.load('locations')
        states = locations.get('states', [])
        print(f"\n🗺️  States ({len(states)}):")
        for state in states:
            print(f"   • {state}")
    
    def list_countries(self) -> None:
        """List all countries"""
        locations = self.loader.load('locations')
        countries = locations.get('countries', [])
        print(f"\n🌍 Countries ({len(countries)}):")
        for country in countries:
            print(f"   • {country}")
    
    def list_terms(self, category: Optional[str] = None) -> None:
        """List protected terms"""
        protected = self.loader.load('protected_terms')
        
        if category:
            if category in protected:
                terms = protected[category]
                print(f"\n🔒 Protected Terms - {category} ({len(terms)}):")
                for term in terms:
                    print(f"   • {term}")
            else:
                print(f"⚠ Category not found: {category}")
                print(f"Available categories: {', '.join(protected.keys())}")
        else:
            print(f"\n🔒 Protected Terms by Category:")
            for cat, terms in protected.items():
                print(f"\n   {cat} ({len(terms)}):")
                for term in terms[:5]:
                    print(f"      • {term}")
                if len(terms) > 5:
                    print(f"      ... and {len(terms) - 5} more")
    
    def list_healing_rules(self) -> None:
        """List text healing rules"""
        healing = self.loader.load('text_healing')
        rules = healing.get('common_words', {})
        print(f"\n🔧 Text Healing Rules ({len(rules)}):")
        for broken, fixed in list(rules.items())[:10]:
            print(f"   • '{broken}' → '{fixed}'")
        if len(rules) > 10:
            print(f"   ... and {len(rules) - 10} more")
    
    def show_config_summary(self) -> None:
        """Show summary of all configs"""
        print("\n" + "=" * 80)
        print("📦 CONFIGURATION SUMMARY")
        print("=" * 80)
        
        locations = self.loader.load('locations')
        protected = self.loader.load('protected_terms')
        sections = self.loader.load('sections')
        pii = self.loader.load('pii_patterns')
        healing = self.loader.load('text_healing')
        
        print(f"\n📍 Locations:")
        print(f"   Cities:     {len(locations.get('cities', []))}")
        print(f"   States:     {len(locations.get('states', []))}")
        print(f"   Countries:  {len(locations.get('countries', []))}")
        
        print(f"\n🔒 Protected Terms:")
        total_terms = sum(len(terms) for terms in protected.values())
        print(f"   Total:      {total_terms} across {len(protected)} categories")
        for cat, terms in protected.items():
            print(f"   {cat}: {len(terms)}")
        
        print(f"\n🗂️  Sections:")
        remove_count = sum(len(v) for v in sections.get('remove', {}).values())
        preserve_count = len(sections.get('preserve', []))
        print(f"   Remove:     {remove_count} section markers")
        print(f"   Preserve:   {preserve_count} section markers")
        
        print(f"\n🔍 PII Patterns:")
        print(f"   Email:      {len(pii.get('email', {}))}")
        print(f"   Phone:      {len(pii.get('phone', {}).get('patterns', []))}")
        print(f"   Social:     {len(pii.get('social', {}).get('patterns', []))}")
        print(f"   Demographics: {len(pii.get('demographics', {}))}")
        
        print(f"\n🔧 Text Healing:")
        total_rules = (
            len(healing.get('suffix_patterns', {})) +
            len(healing.get('prefix_patterns', {})) +
            len(healing.get('common_words', {}))
        )
        print(f"   Total rules: {total_rules}")
        
        print("\n" + "=" * 80)
        print(f"Config location: {self.config_dir.absolute()}")
        print("=" * 80 + "\n")
    
    def _save_json(self, path: Path, data: dict) -> None:
        """Save JSON with pretty formatting"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


# ============================================================================
# CLI INTERFACE
# ============================================================================

def create_parser() -> argparse.ArgumentParser:
    """Create argument parser"""
    parser = argparse.ArgumentParser(
        description="Universal CV Redaction Pipeline - Configuration Driven",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process CVs
  %(prog)s resume/ final_output/
  %(prog)s resume/ final_output/ --debug
  
  # Add new data
  %(prog)s add-city "Boston"
  %(prog)s add-state "California"
  %(prog)s add-term "tensorflow"
  %(prog)s add-healing "administr at ion" "administration"
  
  # View configurations
  %(prog)s list-cities
  %(prog)s list-terms
  %(prog)s list-config

Config files auto-created in ./config/ on first run
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Process command (default)
    process_parser = subparsers.add_parser('process', help='Process CVs (default)')
    process_parser.add_argument('input_dir', nargs='?', default='resume',
                                help='Input directory with PDFs (default: resume)')
    process_parser.add_argument('output_dir', nargs='?', default='final_output',
                                help='Output directory for redacted text (default: final_output)')
    process_parser.add_argument('--debug', action='store_true',
                                help='Enable debug output')
    process_parser.add_argument('--config-dir', default='config',
                                help='Config directory (default: config)')
    
    # Add location commands
    add_city = subparsers.add_parser('add-city', help='Add a city')
    add_city.add_argument('city', help='City name')
    
    add_state = subparsers.add_parser('add-state', help='Add a state')
    add_state.add_argument('state', help='State name')
    
    add_country = subparsers.add_parser('add-country', help='Add a country')
    add_country.add_argument('country', help='Country name')
    
    # Add term command
    add_term = subparsers.add_parser('add-term', help='Add protected technical term')
    add_term.add_argument('term', help='Term to protect')
    add_term.add_argument('--category', default='technical_terms',
                          help='Category (default: technical_terms)')
    
    # Add healing command
    add_healing = subparsers.add_parser('add-healing', help='Add text healing rule')
    add_healing.add_argument('broken', help='Broken pattern (e.g., "administr at ion")')
    add_healing.add_argument('fixed', help='Fixed word (e.g., "administration")')
    
    # List commands
    subparsers.add_parser('list-cities', help='List all cities')
    subparsers.add_parser('list-states', help='List all states')
    subparsers.add_parser('list-countries', help='List all countries')
    
    list_terms = subparsers.add_parser('list-terms', help='List protected terms')
    list_terms.add_argument('--category', help='Filter by category')
    
    subparsers.add_parser('list-healing', help='List text healing rules')
    subparsers.add_parser('list-config', help='Show configuration summary')
    
    return parser


def show_welcome():
    """Show welcome banner"""
    print("\n" + "=" * 80)
    print("🎯 UNIVERSAL CV REDACTION PIPELINE")
    print("=" * 80)
    print("Configuration-driven • Zero hardcoded data • Easy to extend")
    print("=" * 80 + "\n")


def main():
    """Main entry point"""
    parser = create_parser()
    
    # Handle no arguments or positional args (default to process)
    if len(sys.argv) == 1:
        show_welcome()
        parser.print_help()
        return 0
    
    # If first arg is a directory or looks like a path, treat as process command
    if (len(sys.argv) > 1 and 
        not sys.argv[1].startswith('-') and 
        sys.argv[1] not in ['add-city', 'add-state', 'add-country', 'add-term', 
                            'add-healing', 'list-cities', 'list-states', 
                            'list-countries', 'list-terms', 'list-healing', 
                            'list-config', 'process']):
        sys.argv.insert(1, 'process')
    
    args = parser.parse_args()
    
    config_dir = getattr(args, 'config_dir', 'config')
    config_manager = ConfigManager(config_dir)
    
    # Route commands
    if args.command == 'process' or args.command is None:
        show_welcome()
        input_dir = getattr(args, 'input_dir', 'resume')
        output_dir = getattr(args, 'output_dir', 'final_output')
        debug = getattr(args, 'debug', False)
        
        logger.info(f"Input:  {input_dir}")
        logger.info(f"Output: {output_dir}")
        logger.info(f"Debug:  {debug}")
        logger.info(f"Config: {config_dir}")
        print()
        
        orchestrator = PipelineOrchestrator(debug=debug, config_dir=config_dir)
        orchestrator.process_directory(input_dir, output_dir)
    
    elif args.command == 'add-city':
        config_manager.add_city(args.city)
    
    elif args.command == 'add-state':
        config_manager.add_state(args.state)
    
    elif args.command == 'add-country':
        config_manager.add_country(args.country)
    
    elif args.command == 'add-term':
        config_manager.add_term(args.term, args.category)
    
    elif args.command == 'add-healing':
        config_manager.add_healing_rule(args.broken, args.fixed)
    
    elif args.command == 'list-cities':
        config_manager.list_cities()
    
    elif args.command == 'list-states':
        config_manager.list_states()
    
    elif args.command == 'list-countries':
        config_manager.list_countries()
    
    elif args.command == 'list-terms':
        config_manager.list_terms(getattr(args, 'category', None))
    
    elif args.command == 'list-healing':
        config_manager.list_healing_rules()
    
    elif args.command == 'list-config':
        config_manager.show_config_summary()
    
    else:
        parser.print_help()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
