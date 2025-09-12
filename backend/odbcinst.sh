LIBTDS=$(find /lib /usr/lib -type l -name 'libtdsodbc*.so*' 2>/dev/null)
odbcinst -i -d -f /dev/stdin <<EOF
[FreeTDS]
Description = FreeTDS Driver for MS SQL and Sybase
Driver = $LIBTDS
FileUsage = 1
EOF
