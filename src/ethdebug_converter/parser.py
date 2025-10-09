"""
Source mapping parser for Solidity compiler output.

Parses the compressed source mapping format used by the Solidity compiler.
Format: s:l:f:j:m
  s - start offset in source file
  l - length of source range
  f - source file index
  j - jump type ("-" for regular, "i" for into, "o" for out)
  m - modifier depth
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class SourceMapping:
    """Represents a single source mapping entry."""
    start: Optional[int] = None
    length: Optional[int] = None
    file_index: Optional[int] = None
    jump_type: Optional[str] = None
    modifier_depth: Optional[int] = None
    
    def has_source_location(self) -> bool:
        """Check if this mapping has valid source location info."""
        return (self.start is not None and 
                self.length is not None and 
                self.file_index is not None and
                self.file_index >= 0)


class SourceMapParser:
    """Parser for Solidity source mappings."""
    
    def __init__(self, srcmap: str):
        """Initialize parser with source mapping string."""
        self.srcmap = srcmap
        self.mappings: List[SourceMapping] = []
        
    def parse(self) -> List[SourceMapping]:
        """Parse the compressed source mapping string."""
        if not self.srcmap:
            return []
            
        entries = self.srcmap.split(';')
        
        # Previous values for compressed format
        prev_start = None
        prev_length = None
        prev_file = None
        prev_jump = None
        prev_modifier = None
        
        for entry in entries:
            if not entry:
                # Empty entry means use all previous values
                mapping = SourceMapping(
                    start=prev_start,
                    length=prev_length,
                    file_index=prev_file,
                    jump_type=prev_jump,
                    modifier_depth=prev_modifier
                )
            else:
                parts = entry.split(':')
                
                # Parse each component, using previous if empty
                start = self._parse_int(parts[0] if len(parts) > 0 else '') 
                if start is not None:
                    prev_start = start
                else:
                    start = prev_start
                    
                length = self._parse_int(parts[1] if len(parts) > 1 else '')
                if length is not None:
                    prev_length = length
                else:
                    length = prev_length
                    
                file_idx = self._parse_int(parts[2] if len(parts) > 2 else '')
                if file_idx is not None:
                    prev_file = file_idx
                else:
                    file_idx = prev_file
                    
                jump = parts[3] if len(parts) > 3 and parts[3] else None
                if jump is not None:
                    prev_jump = jump
                else:
                    jump = prev_jump
                    
                modifier = self._parse_int(parts[4] if len(parts) > 4 else '')
                if modifier is not None:
                    prev_modifier = modifier
                else:
                    modifier = prev_modifier
                
                mapping = SourceMapping(
                    start=start,
                    length=length,
                    file_index=file_idx,
                    jump_type=jump,
                    modifier_depth=modifier
                )
            
            self.mappings.append(mapping)
            
        return self.mappings
    
    def _parse_int(self, value: str) -> Optional[int]:
        """Parse integer value from string, handling empty and -1 values."""
        if not value or value == '':
            return None
        try:
            val = int(value)
            return val if val >= 0 else None
        except ValueError:
            return None


def parse_bytecode_to_instructions(bytecode: str) -> List[Tuple[int, str]]:
    """
    Parse bytecode into instruction offsets and opcodes.
    Returns list of (pc, opcode_bytes) tuples.
    """
    if bytecode.startswith('0x'):
        bytecode = bytecode[2:]
    
    instructions = []
    pc = 0
    i = 0
    
    while i < len(bytecode):
        # Get opcode
        if i + 2 <= len(bytecode):
            opcode_hex = bytecode[i:i+2]
            opcode = int(opcode_hex, 16)
            
            # Check if it's a PUSH instruction (0x60 to 0x7f)
            if 0x60 <= opcode <= 0x7f:
                # PUSH1 to PUSH32
                push_bytes = opcode - 0x5f
                end_idx = i + 2 + (push_bytes * 2)
                if end_idx <= len(bytecode):
                    instruction_bytes = bytecode[i:end_idx]
                else:
                    instruction_bytes = bytecode[i:]
                instructions.append((pc, instruction_bytes))
                pc += 1 + push_bytes
                i = end_idx
            else:
                # Regular instruction
                instructions.append((pc, opcode_hex))
                pc += 1
                i += 2
        else:
            break
            
    return instructions
