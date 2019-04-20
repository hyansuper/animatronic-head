from __future__ import division
from time import sleep
import Adafruit_PCA9685
from threading import Thread
from random import uniform

class ServoError(Exception):
    def __init__(s,value):
        s.value = value
    def __str__(s):
        return repr(s.value)

class Servo:
    servo_min = 150
    servo_max = 600
    servo_mid = (servo_max + servo_min)//2
    servo_45 = (servo_max - servo_min)/(180/45)
    servo_30 = (servo_max - servo_min)/(180/30)
    servo_40 = (servo_max - servo_min)/(180/40)
    servo_k = (servo_max - servo_min)/180
    pwm = None
    
    @classmethod
    def turn_off_all(cl):
        cl.pwm.set_all_pwm(0,0)        
    def __init__(s,ch,angle_lower,angle_upper,pulse_min,pulse_max):
        s.channel = ch
        s.pulse_min = pulse_min
        s.pulse_max = pulse_max
        s.angle_upper = angle_upper
        s.angle_lower = angle_lower
        s.k = (pulse_max - pulse_min)/(angle_upper - angle_lower)
        s._angle = None        
    def off(s):
        s.pwm.set_pwm(s.channel,0,0)      
    @property
    def angle(s):
        return s._angle
    def angle_to_pulse(s,a):
        p = int(s.k*(a-s.angle_lower)+s.pulse_min)
        if a <= s.angle_upper and a >= s.angle_lower and p>=s.servo_min and p<=s.servo_max:
            return p
        else:
            return None
    @angle.setter
    def angle(s,a):        
        p = s.angle_to_pulse(a)
        if p:
            s._angle = a
            s.pwm.set_pwm(s.channel,0,p)
        else:
            raise ServoError('Channel {}: angle or pulse out of range'.format(s.channel))
    def __call__(s,a):
        s.angle = a
        
Servo.pwm = Adafruit_PCA9685.PCA9685()
Servo.pwm.set_pwm_freq(60)

left_eye = Servo(0,-40,40,Servo.servo_mid-Servo.servo_40,Servo.servo_mid+Servo.servo_40)
right_eye = Servo(4,-40,40,Servo.servo_mid-Servo.servo_40,Servo.servo_mid+Servo.servo_40)
left_eyelid = Servo(1,0,90,Servo.servo_mid-Servo.servo_45+20,Servo.servo_mid+Servo.servo_45+20)
right_eyelid = Servo(5,0,90,Servo.servo_mid+Servo.servo_45,Servo.servo_mid-Servo.servo_45)
left_brow = Servo(2,-30,30,Servo.servo_mid-Servo.servo_30,Servo.servo_mid+Servo.servo_30)
right_brow = Servo(6,-30,30,Servo.servo_mid+Servo.servo_30,Servo.servo_mid-Servo.servo_30)
eye_frame = Servo(8,-45,45,Servo.servo_mid+Servo.servo_45,Servo.servo_mid-Servo.servo_45)
mouth = Servo(9,0,60,Servo.servo_mid-Servo.servo_45-50,Servo.servo_mid+200)

neck_left = Servo(12,-30,30,Servo.servo_mid-Servo.servo_30,Servo.servo_mid+Servo.servo_30)
neck_right = Servo(13,-30,30,Servo.servo_mid+Servo.servo_30,Servo.servo_mid-Servo.servo_30)
shoulder = Servo(14,-45,45,Servo.servo_mid-Servo.servo_45,Servo.servo_mid+Servo.servo_45)

class ServoPair:
    def __init__(s,l,r):
        s.l = l
        s.r = r
    def off(s):
        s.l.off()
        s.r.off()
    @property
    def angle(s):
        return (s.r.angle+s.l.angle)/2
    @angle.setter
    def angle(s,a):
        if type(a)==tuple and len(a)==2:
            s.l.angle = a[0]
            s.r.angle = a[1]
        else:
            s.l.angle = s.r.angle = a
    def __call__(s,*a):
        if len(a)==1:
            s.angle = a[0]
        else:
            s.angle = a

neck = ServoPair(neck_left, neck_right)
eyes = ServoPair(ServoPair(left_eye, right_eye), eye_frame)
eyelids = ServoPair(left_eyelid, right_eyelid)
brows = ServoPair(left_brow, right_brow)

def off():
    Servo.turn_off_all()
    
def blink():
    ra = right_eyelid.angle
    la = left_eyelid.angle
    right_eyelid.angle = left_eyelid.angle = 0
    sleep(.3)
    right_eyelid.angle = ra
    left_eyelid.angle = la
    sleep(.3)

def talk():
    mouth.angle = 45
    sleep(.3)
    mouth.angle = 0
    sleep(.3)
    
def deactivate():    
    stop_blinking()
    stop_following()
    try:
        steps = 25
        lel = (0-left_eyelid.angle)/steps
        rel = (0-right_eyelid.angle)/steps
        le = (0-left_eye.angle)/steps
        re = (0-right_eye.angle)/steps
        m = (0-mouth.angle)/steps
        ef = (-45-eye_frame.angle)/steps
        sh = (0-shoulder.angle)/steps
        nl = (0-neck_left.angle)/steps
        nr = (0-neck_right.angle)/steps
        bl = (0-left_brow.angle)/steps
        br = (0-right_brow.angle)/steps
        for i in range(steps):
            sleep(.5/steps)
            left_eyelid.angle += lel
            right_eyelid.angle += rel
            left_eye.angle += le
            right_eye.angle += re
            mouth.angle += m
            eye_frame.angle += ef
            shoulder.angle += sh
            neck_left.angle += nl
            neck_right.angle += nr
            right_brow.angle += br
            left_brow.angle += bl
    finally:
        off()
    print('deactivated')

def activate():
    shoulder(0)
    neck(10)
    sleep(.3)
    mouth(0)
    brows(0)
    eyes(0)
    eyelids(50)
    sleep(.3)
    blink()    
    #off()

def look(x,y):# x,y is off set from camera center in percentage 
    try:
        if x>.05 or x<-.05:
            right_eye.angle = left_eye.angle = x*(right_eye.angle_upper-right_eye.angle_lower)            
        if y>.1 or y<-.1:
            eye_frame.angle += y*60
    except ServoError as err:
        print(err)

# mouth openess
def astonish(percent):
    try:
        mouth.angle = (mouth.angle_upper-mouth.angle_lower)*percent + mouth.angle_lower
    except ServoError as err:
        print(err)
    

blinking = False
_blinking_thread = None
def _blinking_runnable():    
    while blinking:
        sleep(uniform(0.3,6))
        blink()

_x, _y = 0, 0
def follow(x,y):
    global _x, _y
    _x, _y = x, y
def follow_once(x,y):
    try:
        shoulder.angle += x*3
    except ServoError as err:
        print(err)
    try:
        neck.angle += y*3
    except ServoError as err:
        print(err)

following = False
_following_thread = None

def _following_runnable():
    while following:
        sleep(.2)
        follow_once(_x, _y)


def start_blinking():
    print('start blinking thread')
    global _blinking_thread,blinking
    blinking = True
    _blinking_thread = Thread(target=_blinking_runnable)
    _blinking_thread.start()

def stop_blinking():    
    global _blinking_thread,blinking
    if _blinking_thread:
        blinking = False
        _blinking_thread.join()
        _blinking_thread = None
        print('stoped blinking thread')        

def start_following():
    global following,_following_thread
    following = True
    _following_thread = Thread(target=_following_runnable)
    _following_thread.start()

def stop_following():
    global following,_following_thread
    if _following_thread:
        following = False
        _following_thread.join()
        _following_thread = None
        off()

def expression(exp):
    def _ex(a):
        eyelids(a[0])
        eyes(a[1])
        brows(a[2])
        mouth(a[3])    
    _ex(expression.codes[exp])
expression.codes = {
    'happy':[40,(0,-10),0,30],
    'tired':[40,0,0,45],
    'angry':[60,0,30,0],
    'shocked':[90,0,-15,60],
    'sad':[50,(0,-30),-30,0],
    'retarded':[(40,55),((20,-30),0),10,50],
    'cross-eye':[60,((-30,30),0),0,0],
    'thinking':[(40,50),(-25,45),(15,10),0],
    'despise':[40,(25,-25),15,0]
}

import atexit
atexit.register(deactivate)

if __name__=='__main__':
    activate()
    off()
    for e in expression.codes.keys():
        sleep(1)
        expression(e)
    sleep(1)
    off()
