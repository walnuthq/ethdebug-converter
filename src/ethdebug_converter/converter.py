"""
Converter from Solidity compiler output to Ethdebug format.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from .parser import SourceMapParser, SourceMapping, parse_bytecode_to_instructions


class EthdebugConverter:
    """Converts Solidity compiler output to Ethdebug format."""
    
    def __init__(self, solc_json_path: Path):
        """Initialize converter with path to Solidity compiler JSON output."""
        self.solc_json_path = solc_json_path
        self.solc_data: Dict[str, Any] = {}
        self.source_list: List[str] = []
        
    def load(self) -> bool:
        """Load and validate Solidity compiler JSON."""
        try:
            with open(self.solc_json_path, 'r') as f:
                self.solc_data = json.load(f)
            
            # Get source file list
            self.source_list = self.solc_data.get('sourceList', [])
            if not self.source_list and 'sources' in self.solc_data:
                # Try alternative format
                self.source_list = list(self.solc_data['sources'].keys())
                
            return True
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error loading file: {e}")
            return False
    
    def convert(self, contract_name: Optional[str] = None, 
                environment: str = "create") -> Dict[str, Any]:
        """
        Convert to Ethdebug format.
        
        Args:
            contract_name: Specific contract to convert, or None for first found
            environment: "create" for deployment or "runtime" for runtime
        """
        if not self.solc_data:
            return {}
        
        contracts = self.solc_data.get('contracts', {})
        if not contracts:
            return {}
        
        # Find the contract
        contract_key = None
        contract_data = None
        
        if contract_name:
            # Look for specific contract
            for key, data in contracts.items():
                if key.endswith(f":{contract_name}"):
                    contract_key = key
                    contract_data = data
                    break
        else:
            # Use first contract found
            contract_key = list(contracts.keys())[0]
            contract_data = contracts[contract_key]
        
        if not contract_data:
            return {}
        
        # Extract contract name from key (format: "filename:ContractName")
        actual_contract_name = contract_key.split(':')[-1] if ':' in contract_key else contract_key
        
        # Get bytecode and source map based on environment
        if environment == "runtime":
            bytecode = contract_data.get('bin-runtime', contract_data.get('bin', ''))
            srcmap = contract_data.get('srcmap-runtime', '')
        else:
            bytecode = contract_data.get('bin', '')
            srcmap = contract_data.get('srcmap', '')
        
        if not bytecode or not srcmap:
            return {}
        
        # Parse bytecode into instructions
        instructions_list = parse_bytecode_to_instructions(bytecode)
        
        # Parse source mappings
        parser = SourceMapParser(srcmap)
        mappings = parser.parse()
        
        # Build Ethdebug format
        ethdebug_data = {
            "version": 1,
            "format": "ethdebug",
            "environment": environment,
            "contract": {
                "name": actual_contract_name,
                "bytecode": bytecode if not bytecode.startswith('0x') else bytecode[2:]
            },
            "sources": self._build_sources(),
            "instructions": self._build_instructions(instructions_list, mappings)
        }
        
        return ethdebug_data
    
    def _build_sources(self) -> List[Dict[str, Any]]:
        """Build sources array for Ethdebug format."""
        sources = []
        for idx, source_file in enumerate(self.source_list):
            sources.append({
                "id": idx,
                "path": source_file,
                "content": self._get_source_content(source_file)
            })
        return sources
    
    def _get_source_content(self, source_file: str) -> Optional[str]:
        """Try to read source file content if available."""
        # Try to read from relative path
        source_path = self.solc_json_path.parent / source_file
        if source_path.exists():
            try:
                with open(source_path, 'r') as f:
                    return f.read()
            except Exception:
                pass
        
        # Check if content is embedded in JSON
        if 'sources' in self.solc_data and source_file in self.solc_data['sources']:
            source_data = self.solc_data['sources'][source_file]
            if 'content' in source_data:
                return source_data['content']
        
        return None
    
    def _build_instructions(self, instructions: List[Tuple[int, str]], 
                           mappings: List[SourceMapping]) -> List[Dict[str, Any]]:
        """Build instructions array with context for Ethdebug format."""
        ethdebug_instructions = []
        
        for idx, (pc, opcode_bytes) in enumerate(instructions):
            instruction = {
                "pc": pc,
                "opcode": opcode_bytes[:2],  # First byte is the opcode
                "bytes": opcode_bytes
            }
            
            # Add context if we have a corresponding source mapping
            if idx < len(mappings):
                mapping = mappings[idx]
                context = self._build_context(mapping)
                if context:
                    instruction["context"] = context
            
            ethdebug_instructions.append(instruction)
        
        return ethdebug_instructions
    
    def _build_context(self, mapping: SourceMapping) -> Optional[Dict[str, Any]]:
        """Build context object from source mapping."""
        if not mapping.has_source_location():
            return None
        
        context = {
            "code": {
                "source": {
                    "id": mapping.file_index,
                    "range": {
                        "start": mapping.start,
                        "length": mapping.length
                    }
                }
            }
        }
        
        # Add jump info if available
        if mapping.jump_type:
            context["code"]["jump"] = mapping.jump_type
            
        # Add modifier depth if available
        if mapping.modifier_depth is not None and mapping.modifier_depth > 0:
            context["code"]["modifierDepth"] = mapping.modifier_depth
        
        return context
    
    def save(self, output_path: Path, ethdebug_data: Dict[str, Any]) -> bool:
        """Save Ethdebug format data to file."""
        try:
            with open(output_path, 'w') as f:
                json.dump(ethdebug_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving file: {e}")
            return False
