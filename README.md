# Ethdebug Converter

Convert old Solidity source mappings to the Ethdebug format.

## Installation

```bash
pip install -e .
```

## Usage

```bash
ethdebug-converter <solc-json-file> -o <output-file>
```

Example:
```bash
ethdebug-converter examples/Counter/0.8.0/output.json -o Counter_ethdebug.json
```

### Options

- `-o, --output`: Output file path (default: stdout)
- `-c, --contract`: Specific contract name to convert (default: first found)
- `--runtime`: Convert runtime bytecode instead of deployment bytecode
- `--format`: Output format - `json` or `pretty` (default: pretty)
- `--validate`: Validate output with ethdebug-stats after conversion (runs `ethdebug-stats` on the generated file)

## Input Format

The tool expects Solidity compiler output in combined JSON format generated with:
```bash
solc --combined-json abi,bin,srcmap,srcmap-runtime Contract.sol > output.json
```

## Output Format

Generates Ethdebug format JSON files compatible with ethdebug-stats analyzer.

## Examples

The `examples/` directory contains pre-generated Solidity compiler outputs for different versions. Here's how these files were generated:

### Prerequisites

First, you need to install `solc-select` to easily switch between Solidity compiler versions:

```bash
pip install solc-select
```

### Generating Compiler Output

1. Install the desired Solidity version:
```bash
solc-select install 0.7.0
```

2. Switch to that version:
```bash
solc-select use 0.7.0
```

3. Generate the combined JSON output:
```bash
solc --combined-json abi,bin,srcmap,srcmap-runtime TaxCalculator.sol > TaxCalculator_0.7.0.json
```

### Example Directory Structure

```
examples/
├── Counter/
│   ├── Counter.sol          # Source contract
│   ├── 0.5.0/
│   │   └── output.json      # Compiler output for Solidity 0.5.0
│   ├── 0.6.0/
│   │   └── output.json      # Compiler output for Solidity 0.6.0
│   ├── 0.7.0/
│   │   └── output.json      # Compiler output for Solidity 0.7.0
│   ├── 0.8.0/
│   │   └── output.json      # Compiler output for Solidity 0.8.0
│   └── 0.8.30/
│       └── output.json      # Compiler output for Solidity 0.8.30
└── TaxCalculator/
    ├── TaxCalculator.sol    # Source contract
    ├── 0.7.0/
    │   └── output.json
    ├── 0.8.0/
    │   └── output.json
    └── 0.8.30/
        └── output.json
```

### Converting Examples

To convert any of the example files to Ethdebug format:

```bash
# Convert Counter compiled with Solidity 0.8.0
ethdebug-converter examples/Counter/0.8.0/output.json -o Counter_0.8.0_ethdebug.json

# Convert TaxCalculator runtime bytecode
ethdebug-converter examples/TaxCalculator/0.7.0/output.json --runtime -o TaxCalculator_0.7.0_runtime_ethdebug.json

# Validate the output with ethdebug-stats
ethdebug-stats Counter_0.8.0_ethdebug.json --format text
```
