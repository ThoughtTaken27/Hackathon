#!/bin/sh
# Run a hook script with whichever Python 3 exists (python3, python or py).
# If none works, exit 0 so a missing Python never blocks anyone's session.
dir=$(dirname "$0")
for p in python3 python py; do
  if command -v "$p" >/dev/null 2>&1 && "$p" -c "import sys; sys.exit(sys.version_info < (3, 8))" >/dev/null 2>&1; then
    exec "$p" "$dir/$1"
  fi
done
exit 0
