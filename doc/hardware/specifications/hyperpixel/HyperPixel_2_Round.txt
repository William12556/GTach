Source: https://shop.pimoroni.com/products/hyperpixel-round?variant=39381081882707

A perfectly round, high-resolution, high-speed 2.1" touchscreen display for Raspberry Pi.

HyperPixel 2.1 Round has all the great features of our other HyperPixels - crisp, brilliant IPS display, touchscreen, and high-speed DPI interface—it's just rounder! You can use it with any Raspberry Pi with a 40 pin header* but it works particularly nicely with the Pi Zero footprint - we've designed it so you can mount one neatly behind it, so you can't see the Pi when you look at it from the front.

This version of HyperPixel would be great for custom interfaces and control panels - mounted on a wall it would make a really neat, minimalist smart home controller or a stylish 'what's playing' display for your sound system. Everything is pre-soldered and ready to go (assuming that your Pi has pin headers attached).

The images of the displays on this page are not renders - they're real photos of the display!

* Note that standoffs and booster headers are not included with Hyperpixel Round - scroll down or check out the extras tabs for some links. You will need a booster header if you want to use Hyperpixel Round with a full size Pi!

Hyperpixel Round is not fully compatible with recent versions of Raspberry Pi OS, scroll down to the software section for more info.

Features
High-speed DPI interface
2.1" IPS (wide viewing angle, 175°) display
480x480 pixels, minus the corners (~229 PPI)
18-bit colour (262,144 colours)
60 FPS frame rate
Active area: 53.28 x 53.28mm
Display drivers baked into Raspberry Pi OS (touch currently not supported)
Capacitive touchscreen (with Python library)
Compatible with all 40-pin header Raspberry Pi models
HyperPixel 2.1 Round uses a high-speed DPI interface, allowing it to shift 5x more pixel data than the usual SPI interface that these small Pi displays normally use. It has a 60 FPS frame rate and a resolution of approximately 229 pixels per inch (480x480px) on its 2.1" display. The display can show 18-bits of colour (262,144 colours).

The touchscreen is capacitive touch, that's more sensitive and responsive to touch than a resistive touch display, and it's capable of multi-touch!**

Attaching Hyperpixel Round to your Pi
Hyperpixel Round will work with any 40-pin version of the Pi, including Pi Zero and Pi Zero W. If you're using it with a full-size Pi then you'll need a booster header to raise it up over the Pi's USB ports and extended standoffs if you'd like to bolt it in place. If you're using a Pi Zero or Pi Zero W you won't need a booster header, but you might like to pick up these special short standoffs that will let you attach everything securely together in an extra slim package.

If you're using standoffs to fasten your Hyperpixel and your Pi together, just screw them into the posts on the underside of the HyperPixel PCB and then secure with screws through the mounting holes on your Pi.

Please note: when installing HyperPixel 2.1 Round onto your Pi make sure not to press down on the screen surface. We recommend putting the screen face down on a soft surface and gently wiggling the Pi to mate with the extended header (or GPIO header). If you need to remove your Hyperpixel, take care not to pull on the edges of the glass display - it's best to hold on to the round PCB. As the glass edges of this display overhang the PCB they're quite exposed, so it's worth being extra careful with them.

Software
If you're using a recent version of Raspberry Pi OS (Bullseye or later) then you'll need to use the built in kernel drivers - just add the following line to the end of your boot/firmware/config.txt (and then reboot):

dtoverlay=vc4-kms-dpi-hyperpixel2r

You will need to have I2C disabled (sudo raspi-config nonint do_i2c 1).

If you need to rotate the display you can do this using Pi OS's 'Screen Configuration' utility. Note that the kernel drivers for Round do not include touch support.

⚠ The screen backlight will not automatically turn off when you shut down / power off your Pi. We'd suggest unplugging the power cable from your Pi (or turning off your power supply at the socket) when you're not using it to ensure longevity of the backlight.

Legacy display drivers and Python touch drivers can be found here:

HyperPixel 2.0" Round Drivers for Raspberry Pi 4
HyperPixel 2" Round Touch Driver
Notes
Dimensions: 71.80 x 71.80 x 10.8mm (WxHxD, depth includes header and display). With a Pi Zero attached with short standoffs, the total depth is 17mm.
Dimensional drawing
Pinout
HyperPixel uses basically all of the GPIO pins to communicate with the Pi (including the standard I2C pins) so it's not generally possible to use it with other HATs and devices that connect via the GPIO.