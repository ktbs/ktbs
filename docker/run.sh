#!/bin/sh

echo "cleaning old semaphores"
rm /dev/shm/sem.*

# ensure kTBS install is up-to-date
pip install -e /src
pip install `grep GitPython /src/requirements.d/dev.txt`
echo "kTBS is up-to-date, now starting"

# then run kTBS
exec ktbs -c /app/app.conf
