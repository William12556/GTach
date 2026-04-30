# Mac:
## Transfer install script to the Pi
scp install.sh root@gtach.local:/opt/gtach/

## Build and transfer GTach to the Pi
./build.sh && scp dist/gtach-0.2.2-py3-none-any.whl root@gtach.local:/tmp/

## Transfer GTach log back to the Mac from the Pi
scp root@gtach.local:/opt/gtach/gtach-debug_PI.log ~/Documents/GitHub/GTach/

# Pi:

## Install GTach on the Pi
/opt/gtach/install.sh /tmp/gtach-0.2.2-py3-none-any.whl

## Run GTach on the Pi
gtach --debug 2>&1 | tee /opt/gtach/gtach-debug_PI.log
