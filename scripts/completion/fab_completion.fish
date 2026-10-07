# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

# This script is provided as a sample to demonstrate how to enable fab tab completion. Users are solely responsible for reviewing, testing, and executing this script in their environment.
# To enable tab completion for `fab` command, save this script as ~/.config/fish/completions/fab.fish. Then restart your terminal to apply changes.
# Saving it in the completions directory also replaces the completions that fish ships for an unrelated `fab` command (Python Fabric).
register-python-argcomplete --shell fish fab | source