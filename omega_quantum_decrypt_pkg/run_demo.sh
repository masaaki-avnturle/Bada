#!/bin/sh
# Run the full Jones/Burau/Shor decryption demo and the test suite.
set -e
ROOT=$(cd "$(dirname "$0")" && pwd)
cd "$ROOT"

echo "############################################################"
echo "# omega_quantum_decrypt : Jones x Burau x Shor pipeline"
echo "############################################################"

echo
echo "--- 1. Jones polynomial of the trefoil (sigma_1^3) ---"
python3 -m omega_qdecrypt.cli jones "2: 1 1 1"

echo
echo "--- 2. Inverse-matrix (Burau) cipher, invertibility test ---"
python3 -m omega_qdecrypt.cli invmat "3: 1 2 1 2 1 2"

echo
echo "--- 3. Full end-to-end decrypt of an 'encrypted USB stick' ---"
python3 -m omega_qdecrypt.cli demo "3: 1 1 1"

echo
echo "--- 4. Test suite ---"
python3 tests/test_all.py
