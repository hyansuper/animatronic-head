# ref: 
# https://blog.miguelgrinberg.com/post/video-streaming-with-flask
# https://blog.miguelgrinberg.com/post/flask-video-streaming-revisited
# https://hackaday.io/project/25092-zerobot-raspberry-pi-zero-fpv-robot
from flask import Flask, render_template, Response
from flask_socketio import SocketIO
from picamera import PiCamera
from time import sleep
import face_recognition
from base_camera import BaseCamera
import numpy as np
from io import BytesIO
from PIL import Image, ImageDraw
import an
from scipy.spatial import distance as dist
from random import randrange
#from datetime import datetime

resolution = (160, 128)
center = (resolution[0]/2, resolution[1]/2)

def mouth_aspect_ratio(top_lip, bottom_lip):
    return dist.euclidean(top_lip[9], bottom_lip[9])/dist.euclidean(top_lip[0], top_lip[6])

def eye_aspect_radio(eye):
    return (dist.euclidean(eye[1],eye[5])+dist.euclidean(eye[2],eye[4]))/dist.euclidean(eye[0],eye[3])

class Camera(BaseCamera):
    stream = True
    manual = False
    @classmethod
    def frames(cls):
        # for faster response, set resolution to (160,128)
        output = np.empty((resolution[1], resolution[0], 3), dtype=np.uint8)
        with PiCamera(resolution="{}x{}".format(resolution[0], resolution[1]), framerate=24) as cam:
            #cam.led = False # turn off the led on cam
            cam.vflip = True
            #let cam warm up
            sleep(2)
            stream = BytesIO()
            for _ in cam.capture_continuous(output, 'rgb', use_video_port=True):
                pil_img = Image.fromarray(output)                
                if not cls.manual:
                    if randrange(3)<1:
                        an.blink()
                    face_landmarks_list = face_recognition.face_landmarks(output)
                    draw = ImageDraw.Draw(pil_img)
                    for face_landmarks in face_landmarks_list:
                        for pts in face_landmarks.values():
                            draw.polygon(pts)     
                        nose_tip = face_landmarks['nose_bridge'][3]
                        x = (nose_tip[0]-center[0])/resolution[0]
                        an.look(x, (center[1]-nose_tip[1])/resolution[1])
                        mar = mouth_aspect_ratio(face_landmarks['top_lip'], face_landmarks['bottom_lip'])                        
                        if mar < .1:
                            mar = 0
                        elif mar > .5:
                            mar = .5
                        an.astonish(mar/.5)
                        #print("mouth_aspect_ratio: {}".format(mar))
                        #if an.following:
                        if abs(x) < .2:
                            x = 0
                        y = an.eye_frame.angle/90
                        if abs(y) < .2:
                            y = 0
                        an.follow_once(x, y)                        
                        break
                    
                else:#manual mode
                    pass
                    #if an.following:

                if cls.stream:
                    # convert to jpeg format and stream it to the web
                    pil_img.save(stream, format='JPEG')
                    stream.seek(0)
                    yield stream.read()
                    # reset stream for next frame
                    stream.seek(0)
                    stream.truncate()

app = Flask(__name__)
socketio = SocketIO(app, async_mode='threading')
ns='/socket'

def gen(camera):
    while True:
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + camera.get_frame() + b'\r\n')

@app.route('/')
def index():
    return render_template('Touch.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen(Camera()),mimetype='multipart/x-mixed-replace; boundary=frame')

@socketio.on('connect', namespace=ns)
def on_connect():
    print('A user connected')

@socketio.on('eye', namespace=ns)
def on_eye(msx,msy):
    if Camera.manual:
        try:
            an.left_eye.angle = an.right_eye.angle = msx*40
        except an.ServoError as err:
            print(err)
        try:
            an.eye_frame.angle = msy*45
        except an.ServoError as err:
            print(err)

@socketio.on('neck', namespace=ns)
def on_neck(msx,msy):
    if Camera.manual:
        try:
            an.neck.angle = an.neck.angle*.9 + msy*.1*an.neck.l.angle_upper
        except an.ServoError as err:
            print(err)
        try:
            an.shoulder.angle = an.shoulder.angle*.9 + msx*.1*an.shoulder.angle_upper
        except an.ServoError as err:
            print(err)

@socketio.on('stream', namespace=ns)
def on_stream(toggle):
    Camera.stream = toggle==1

@socketio.on('manual', namespace=ns)
def on_manual(toggle):
    Camera.manual = toggle==1
    an.off()

@socketio.on('blink', namespace=ns)
def on_blink(toggle):
    if Camera.manual:
        an.blink()

@socketio.on('cmd', namespace=ns)
def on_cmd(cmd):
    if Camera.manual:
        if cmd==1:
            for i in range(2):
                an.left_eyelid(50)
                an.right_eyelid(0)
                sleep(.3)
                an.right_eyelid(50)
                an.left_eyelid(0)
                sleep(.3)
            an.eyelids(0)
            sleep(.3)
            an.eyelids(50)
            an.eyes((-30,30),0)
            an.mouth(90)


@socketio.on('talk', namespace=ns)
def on_blink(toggle):
    if Camera.manual:
        an.talk()

@socketio.on('reboot', namespace=ns)
def on_reboot(toggle):
    from subprocess import check_call
    check_call(['sudo', 'reboot'])

@socketio.on('power', namespace=ns)
def on_power(toggle):
    from subprocess import check_call
    check_call(['sudo', 'poweroff'])

@socketio.on('disconnect', namespace=ns)
def on_disconnect():
    print('A user disconnected')


if __name__ == '__main__':
    an.activate()
    an.off()
    print('start running web')
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)