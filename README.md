# animatronic-head

[video](https://www.bilibili.com/video/av50975243/)

![](image.png)

## Hardware:
* Raspberry Pi Zero W
* Adafruit 16-channel servo controller
* 996 servo X3
* 9g plastic servo X8
* RPi camera

## Software

Python code for my 3d printed animatronic head

### Dependency:
    pip install numpy scipy Pillow flask flask-socketio face_recognition

### test:
    python an.py

### application:
    python web.py<br>
    then visit <rpi_ip_address>:5000

code in web.py is remixed from [miguelgrinberg/flask-video-streaming](https://github.com/miguelgrinberg/flask-video-streaming) and [CoretechR/ZeroBot](https://github.com/CoretechR/ZeroBot)
