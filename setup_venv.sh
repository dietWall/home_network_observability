#!/bin/bash
# Setup script for Ansible Molecule project
# Creates virtual environment and installs dependencies

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/venv"

echo "=== Creating virtual environment ==="
python3 -m venv "${VENV_DIR}"

echo ""
echo "=== Activating virtual environment ==="
source "${VENV_DIR}/bin/activate"

echo ""
echo "=== Installing dependencies ==="
pip install --upgrade pip
if [ -f "${SCRIPT_DIR}/requirements.txt" ]; then
    echo "Installing from requirements.txt..."
    pip install -r "${SCRIPT_DIR}/requirements.txt"
else
    echo "No requirements.txt found, installing core dependencies..."
    pip install molecule molecule-docker
fi

echo ""
echo "=== Installing Galaxy collections ==="
if [ -f "${SCRIPT_DIR}/requirements.yml" ]; then
    ansible-galaxy install -r "${SCRIPT_DIR}/requirements.yml"
else
    echo "No requirements.yml found, skipping Galaxy collections"
fi

echo ""
echo "=== Setup complete! ==="
echo ""
echo "To run tests, use:"
echo "  molecule converge -s default        # Localhost scenario"
echo "  molecule converge -s ubuntu         # Docker container scenario"
echo "  molecule converge -s ubuntu26_ssh   # SSH-based role testing"
echo "There is also a convinience script, which runs all playbooks in the right order"
echo "  ./ansible_template/run_molecule_scenarios.py"
