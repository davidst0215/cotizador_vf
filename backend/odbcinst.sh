#!/usr/bin/env sh
set -eu

# find first match for a pattern across common lib dirs
find_first() {
  pattern=$1
  shift
  for dir in "$@"; do
    if [ -d "$dir" ]; then
      find "$dir" -type f -name "$pattern" 2>/dev/null | head -n 1 && return 0
      find "$dir" -type l -name "$pattern" 2>/dev/null | head -n 1 && return 0
    fi
  done
  return 1
}

# FreeTDS
if lib=$(find_first 'libtdsodbc*.so*' /usr/lib /usr/lib64 /lib /lib64); then
  odbcinst -i -d -f /dev/stdin <<EOF
[FreeTDS]
Description=FreeTDS Driver for MS SQL and Sybase
Driver=$lib
FileUsage=1
EOF
fi

# PostgreSQL
if lib=$(find_first 'psqlodbcw.so*' /usr/lib /usr/lib64 /lib /lib64); then
  odbcinst -i -d -f /dev/stdin <<EOF
[PostgreSQL]
Description=ODBC Driver for PostgreSQL
Driver=$lib
Threading=2
UsageCount=1
SafeSrc=1
FileUsage=1
EOF
fi
