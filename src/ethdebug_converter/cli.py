#!/usr/bin/env python3
"""
CLI for Ethdebug Converter
"""

import argparse
import sys
import json
from pathlib import Path
from .converter import EthdebugConverter


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Convert Solidity source mappings to Ethdebug format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ethdebug-converter contract.json -o contract_ethdebug.json
  ethdebug-converter contract.json --contract MyContract --runtime
  ethdebug-converter contract.json --format json | jq .
        """
    )
    
    parser.add_argument(
        'input',
        type=str,
        help='Path to Solidity compiler JSON output (from solc --combined-json)'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        help='Output file path (default: stdout)'
    )
    
    parser.add_argument(
        '-c', '--contract',
        type=str,
        help='Specific contract name to convert (default: first found)'
    )
    
    parser.add_argument(
        '--runtime',
        action='store_true',
        help='Convert runtime bytecode instead of deployment bytecode'
    )
    
    parser.add_argument(
        '--format',
        choices=['json', 'pretty'],
        default='pretty',
        help='Output format (default: pretty)'
    )
    
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate output with ethdebug-stats after conversion'
    )
    
    args = parser.parse_args()
    
    # Create converter
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file '{input_path}' not found", file=sys.stderr)
        sys.exit(1)
    
    converter = EthdebugConverter(input_path)
    
    # Load input data
    if not converter.load():
        print("Error: Failed to load Solidity compiler output", file=sys.stderr)
        sys.exit(1)
    
    # Convert to Ethdebug format
    environment = "runtime" if args.runtime else "create"
    ethdebug_data = converter.convert(
        contract_name=args.contract,
        environment=environment
    )
    
    if not ethdebug_data:
        print("Error: Failed to convert to Ethdebug format", file=sys.stderr)
        sys.exit(1)
    
    # Output result
    if args.output:
        output_path = Path(args.output)
        if converter.save(output_path, ethdebug_data):
            print(f"Successfully converted to: {output_path}")
            
            # Optionally validate with ethdebug-stats
            if args.validate:
                try:
                    from ethdebug_stats import EthdebugAnalyzer
                    analyzer = EthdebugAnalyzer(output_path)
                    if analyzer.load():
                        stats = analyzer.analyze()
                        print("\n" + analyzer.format_output('text'))
                except ImportError:
                    print("\nNote: Install ethdebug-stats to validate output", file=sys.stderr)
        else:
            print("Error: Failed to save output", file=sys.stderr)
            sys.exit(1)
    else:
        # Output to stdout
        if args.format == 'pretty':
            print(json.dumps(ethdebug_data, indent=2))
        else:
            print(json.dumps(ethdebug_data))


if __name__ == '__main__':
    main()
