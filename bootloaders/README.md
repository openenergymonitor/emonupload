# Flash ATmega328 bootloader via ISP using PlatfomIO:

```
$ ~/.platformio/packages/tool-avrdude/avrdude -C ~/.platformio/packages/tool-avrdude/avrdude.conf -v -patmega328p -cstk500v2 -Pusb -Uflash:w:bootloaders/optiboot_atmega328.hex:i -Ulock:w:0x0F:m 
```
