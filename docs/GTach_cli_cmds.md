# Mac:
## Transfer install script to the Pi

```shell
cd ~/Documents/GitHub/GTach && scp install.sh root@gtach.local:/opt/gtach/
```

## Build and transfer GTach to the Pi

```shell
cd ~/Documents/GitHub/GTach && ./build.sh && scp dist/*.whl root@gtach.local:/tmp/
```

or

```shell
cd /Users/williamwatson/Documents/GitHub/GTach && ./build.sh && scp dist/gtach-0.2.58-py3-none-any.whl root@gtach.local:/tmp/ && ssh root@gtach.local '/opt/gtach/install.sh /tmp/gtach-0.2.58-py3-none-any.whl'
```

## Transfer GTach log back to the Mac from the Pi

```shell
cd ~/Documents/GitHub/GTach && scp root@gtach.local:/opt/gtach/gtach-debug.log ~/Documents/GitHub/GTach/
```

# Transfer ELM327 logs back to the Mac from the emulator

```shell
cd ~/Documents/GitHub/GTach && scp root@ELM327-Emulator.local:/opt/elm327/elm.log ~/Documents/GitHub/GTach/
```

```shell
cd ~/Documents/GitHub/GTach && scp root@ELM327-Emulator.local:/opt/elm327/bt-server.log ~/Documents/GitHub/GTach/
```

# Pi:

## Install GTach on the Pi

```shell
cd /opt/gtach && /opt/gtach/install.sh /tmp/gtach-0.2.51-py3-none-any.whl
```

## Run GTach on the Pi

```shell
cd /opt/gtach && gtach --transport rfcomm --debug 2>&1 | tee /opt/gtach/gtach-debug.log
```

### or simulate
```shell
cd /opt/gtach &&  gtach --transport simbt --debug 2>&1 | tee /opt/gtach/gtach-simbt.log
```
