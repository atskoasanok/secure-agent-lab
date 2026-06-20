# Copyright (c) 2026 MyCompany LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import re
import sys

def main():
    try:
        # Load the tool invocation context from stdin
        context = json.load(sys.stdin)

        # Get tool name and arguments
        tool_name = context.get("tool_name", "")
        tool_args = context.get("tool_args", {})

        # We specifically inspect run_command
        if tool_name == "run_command" or "CommandLine" in tool_args:
            command_line = tool_args.get("CommandLine", "")

            # Pattern to match rm with dangerous flags (like -rf, -fr, -r -f) targeting root / or /*
            # E.g. rm -rf /, rm -fr /etc, rm --recursive --force /
            rm_pattern = re.compile(
                r"\brm\s+-(?:[a-zA-Z]*[rf][a-zA-Z]*\s+)+(?:/|\*|/\*)", re.IGNORECASE
            )
            # Simple check for direct rm -rf / substring or variation
            if "rm " in command_line:
                normalized_cmd = re.sub(r"\s+", " ", command_line)
                if any(x in normalized_cmd for x in ["rm -rf /", "rm -fr /", "rm -r -f /", "rm -f -r /"]):
                    print("BLOCKED: Destructive command detected.", file=sys.stderr)
                    sys.exit(1)

            if rm_pattern.search(command_line):
                print("BLOCKED: Destructive command detected (rm matching root targets).", file=sys.stderr)
                sys.exit(1)

            # Block mkfs commands that can format disks
            if "mkfs" in command_line:
                print("BLOCKED: Destructive command detected (mkfs).", file=sys.stderr)
                sys.exit(1)

            # Block dd write commands targeting disks
            if "dd " in command_line and ("of=/dev/" in command_line or "of=/" in command_line):
                print("BLOCKED: Destructive command detected (dd write).", file=sys.stderr)
                sys.exit(1)

        print("APPROVED: Command validation passed.")
        sys.exit(0)
    except Exception as e:
        print(f"Validation error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
