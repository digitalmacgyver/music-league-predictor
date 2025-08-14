#!/bin/bash
# Convenience script to activate the virtual environment

echo "Activating Music League virtual environment..."
source venv/bin/activate
echo "Virtual environment activated. Python is now: $(which python)"
echo "To deactivate, type 'deactivate'"