#!/bin/bash
# wait-for-mysql.sh

set -e

host="$1"
port="$2"
shift 2
cmd="$@"

until mysql -h"$host" -P"$port" -u"${MYSQL_USER:-content_agent}" -p"${MYSQL_PASSWORD:-content123}" -e "SELECT 1;" > /dev/null 2>&1; do
  >&2 echo "MySQL is unavailable - sleeping"
  sleep 1
done

>&2 echo "MySQL is up - executing command"
exec $cmd