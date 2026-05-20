# Mac:
## Transfer install script to the Pi

```shell
cd ~/Documents/GitHub/GTach && scp install.sh root@gtach.local:/opt/gtach/
```

## Build and transfer GTach to the Pi

```shell
cd ~/Documents/GitHub/GTach && ./build.sh && scp dist/*.whl root@gtach.local:/tmp/
```

## Transfer GTach log back to the Mac from the Pi

```shell
cd ~/Documents/GitHub/GTach && scp root@gtach.local:/opt/gtach/gtach-simbt.log ~/Documents/GitHub/GTach/
```

# Pi:

## Install GTach on the Pi

```shell
cd /opt/gtach && /opt/gtach/install.sh /tmp/gtach-0.2.42-py3-none-any.whl
```

## Run GTach on the Pi

```shell
cd /opt/gtach
gtach --debug 2>&1 | tee /opt/gtach/gtach-debug_PI.log
```

### or
```shell
gtach --transport simbt --debug 2>&1 | tee /opt/gtach/gtach-simbt.log
```
