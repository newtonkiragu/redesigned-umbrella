"""
    Based on: https://gist.github.com/xjcl/8ce64008710128f3a076
    Modified by PedroLopes and ShanYuanTeng for Intro to HCI class but credit remains with author

    HOW TO SETUP:
    Start the python game: >python3 pong-audio.py

    HOW TO PLAY: 
    Well.. use your auditory interface. 
    p.s.: Player 1 controls the left paddle: UP (W) DOWN (S) <- change this to auditory interface
          Player 2controls the right paddle: UP (O) DOWN (L)
    
    HOW TO QUIT: 
    Say "quit". 
    
    HOW TO INSTALL:
    Follow class wiki. 
    p.s.: this needs 10x10 image in the same directory: "white_square.png".
"""
#native imports
import math
import random
import pyglet
import sys
from playsound import playsound
from gtts import gTTS 
import pyttsx3
# speech recognition library
# -------------------------------------#
# threading so that listenting to speech would not block the whole program
import threading
# speech recognition (default using google, requiring internet)
import speech_recognition as sr
# -------------------------------------#

# pitch & volume detection
# -------------------------------------#
import aubio
import numpy as num
import pyaudio
import wave
# -------------------------------------#

quit = False
debug = 1

# pitch & volume detection
# -------------------------------------#
# PyAudio object.
p = pyaudio.PyAudio()
# Open stream.
stream = p.open(format=pyaudio.paFloat32,
    channels=1, rate=44100, input=True,
    frames_per_buffer=1024)
# Aubio's pitch detection.
pDetection = aubio.pitch("default", 2048,
    2048//2, 44100)
# Set unit.
pDetection.set_unit("Hz")
pDetection.set_silence(-40)
# -------------------------------------#

# keeping score of points:
p1_score = 0
p2_score = 0

#play some fun sounds?
def hit():
    playsound('hit.wav', False)

hit()
# speech recognition functions using google api
# -------------------------------------#
def listen_to_speech():
    global quit
    while not quit:
        # obtain audio from the microphone
        r = sr.Recognizer()
        with sr.Microphone() as source:
            print("[speech recognition] Say something!")
            audio = r.listen(source)
        # recognize speech using Google Speech Recognition
        try:
            # for testing purposes, we're just using the default API key
            # to use another API key, use `r.recognize_google(audio, key="GOOGLE_SPEECH_RECOGNITION_API_KEY")`
            # instead of `r.recognize_google(audio)`
            recog_results = r.recognize_google(audio)
            print("[speech recognition] Google Speech Recognition thinks you said \"" + recog_results + "\"")
            # if recognizing quit and exit then exit the program
            if recog_results == "quit" or recog_results == "exit":
                quit = True
            if recog_results == "up":
                p1.y -= self.speed
                p1.last_movements.append(-self.speed) 
        except sr.UnknownValueError:
            print("[speech recognition] Google Speech Recognition could not understand audio")
        except sr.RequestError as e:
            print("[speech recognition] Could not request results from Google Speech Recognition service; {0}".format(e))
# -------------------------------------#

# pitch & volume detection
# -------------------------------------#
def sense_microphone():
    global quit
    while not quit:
        data = stream.read(1024,exception_on_overflow=False)
        samples = num.fromstring(data,
            dtype=aubio.float_type)

        # Compute the pitch of the microphone input
        pitch = pDetection(samples)[0]
        # Compute the energy (volume) of the mic input
        volume = num.sum(samples**2)/len(samples)
        # Format the volume output so that at most
        # it has six decimal numbers.
        volume = "{:.6f}".format(volume)

        # uncomment these lines if you want pitch or volume
        print("p"+str(pitch))
        print("v"+str(volume))
# -------------------------------------#


class Ball(object):

    def __init__(self):
        self.debug = 0
        self.TO_SIDE = 5
        self.x = 50.0 + self.TO_SIDE
        self.y = float( random.randint(0, 450) )
        self.x_old = self.x  # coordinates in the last frame
        self.y_old = self.y
        self.vec_x = 2**0.5 / 2  # sqrt(2)/2
        self.vec_y = random.choice([-1, 1]) * 2**0.5 / 2

class Player(object):

    def __init__(self, NUMBER, screen_WIDTH=800):
        """NUMBER must be 0 (left player) or 1 (right player)."""
        self.NUMBER = NUMBER
        self.x = 50.0 + (screen_WIDTH - 100) * NUMBER
        self.y = 50.0
        self.last_movements = [0]*4  # short movement history
                                     # used for bounce calculation
        self.up_key, self.down_key = None, None
        if NUMBER == 0:
            self.up_key = pyglet.window.key.W
            self.down_key = pyglet.window.key.S
        elif NUMBER == 1:
            self.up_key = pyglet.window.key.O
            self.down_key = pyglet.window.key.L


class Model(object):
    """Model of the entire game. Has two players and one ball."""

    def __init__(self, DIMENSIONS=(800, 450)):
        """DIMENSIONS is a tuple (WIDTH, HEIGHT) of the field."""
        # OBJECTS
        WIDTH = DIMENSIONS[0]
        self.players = [Player(0, WIDTH), Player(1, WIDTH)]
        self.ball = Ball()
        # DATA
        self.pressed_keys = set()  # set has no duplicates
        self.quit_key = pyglet.window.key.Q
        self.speed = 6  # in pixels per frame
        self.ball_speed = self.speed #* 2.5
        self.WIDTH, self.HEIGHT = DIMENSIONS
        # STATE VARS
        self.paused = False
        self.i = 0  # "frame count" for debug

    def reset_ball(self, who_scored):
        """Place the ball anew on the loser's side."""
        if debug: print(str(who_scored)+" scored. reset.")
        self.ball.y = float( random.randint(0, self.HEIGHT) )
        self.ball.vec_y = random.choice([-1, 1]) * 2**0.5 / 2
        if who_scored == 0:
            self.ball.x = self.WIDTH - 50.0 - self.ball.TO_SIDE
            self.ball.vec_x = - 2**0.5 / 2
        elif who_scored == 1:
            self.ball.x = 50.0 + self.ball.TO_SIDE
            self.ball.vec_x = + 2**0.5 / 2
        elif who_scored == "debug":
            self.ball.x = 70  # in paddle atm -> usage: hold f
            self.ball.y = self.ball.debug
            self.ball.vec_x = -1
            self.ball.vec_y = 0
            self.ball.debug += 0.2
            if self.ball.debug > 100:
                self.ball.debug = 0

    def check_if_oob_top_bottom(self):
        """Called by update_ball to recalc. a ball above/below the screen."""
        # bounces. if -- bounce on top of screen. elif -- bounce on bottom.
        b = self.ball
        if b.y - b.TO_SIDE < 0:
            illegal_movement = 0 - (b.y - b.TO_SIDE)
            b.y = 0 + b.TO_SIDE + illegal_movement
            b.vec_y *= -1
        elif b.y + b.TO_SIDE > self.HEIGHT:
            illegal_movement = self.HEIGHT - (b.y + b.TO_SIDE)
            b.y = self.HEIGHT - b.TO_SIDE + illegal_movement
            b.vec_y *= -1

    def check_if_oob_sides(self):
        global p2_score, p1_score
        """Called by update_ball to reset a ball left/right of the screen."""
        b = self.ball
        if b.x + b.TO_SIDE < 0:  # leave on left
            self.reset_ball(1)
            p2_score+=1
        elif b.x - b.TO_SIDE > self.WIDTH:  # leave on right
            p1_score+=1
            self.reset_ball(0)

    def check_if_paddled(self): 
        """Called by update_ball to recalc. a ball hit with a player paddle."""
        b = self.ball
        p0, p1 = self.players[0], self.players[1]
        angle = math.acos(b.vec_y)  
        factor = random.randint(5, 15)  
        cross0 = (b.x < p0.x + 2*b.TO_SIDE) and (b.x_old >= p0.x + 2*b.TO_SIDE)
        cross1 = (b.x > p1.x - 2*b.TO_SIDE) and (b.x_old <= p1.x - 2*b.TO_SIDE)
        if cross0 and -25 < b.y - p0.y < 25:
            playhit = threading.Thread(target=hit(), args=())
            playhit.start()
            hit()
            if debug: print("hit at "+str(self.i))
            illegal_movement = p0.x + 2*b.TO_SIDE - b.x
            b.x = p0.x + 2*b.TO_SIDE + illegal_movement
            angle -= sum(p0.last_movements) / factor / self.ball_speed
            b.vec_y = math.cos(angle)
            b.vec_x = (1**2 - b.vec_y**2) ** 0.5
        elif cross1 and -25 < b.y - p1.y < 25:
            playhit = threading.Thread(target=hit(), args=())
            playhit.start()
            hit()
            if debug: print("hit at "+str(self.i))
            illegal_movement = p1.x - 2*b.TO_SIDE - b.x
            b.x = p1.x - 2*b.TO_SIDE + illegal_movement
            angle -= sum(p1.last_movements) / factor / self.ball_speed
            b.vec_y = math.cos(angle)
            b.vec_x = - (1**2 - b.vec_y**2) ** 0.5


# -------------- Ball position: you can find it here -------
    def update_ball(self):
        """
            Update ball position with post-collision detection.
            I.e. Let the ball move out of bounds and calculate
            where it should have been within bounds.

            When bouncing off a paddle, take player velocity into
            consideration as well. Add a small factor of random too.
        """
        self.i += 2  # "debug"
        b = self.ball
        b.x_old, b.y_old = b.x, b.y
        b.x += b.vec_x * self.ball_speed 
        b.y += b.vec_y * self.ball_speed
        self.check_if_oob_top_bottom()  # oob: out of bounds
        self.check_if_oob_sides()
        self.check_if_paddled()


    def update(self):
        """Work through all pressed keys, update and call update_ball."""
        pks = self.pressed_keys
        if quit:
            sys.exit(1)
        if self.quit_key in pks:
            exit(0)
        if pyglet.window.key.R in pks and debug:
            self.reset_ball(1)
        if pyglet.window.key.F in pks and debug:
            self.reset_ball("debug")

        # -------------- If you want to change paddle position, change it here
        # player 1: the user controls the left player by W/S but you should change it to VOICE input
        p1 = self.players[0]
        p1.last_movements.pop(0)
	#listen_to_speech()
        if p1.up_key in pks and p1.down_key not in pks: #change this to voice input
            p1.y -= self.speed
            p1.last_movements.append(-self.speed)
        elif p1.up_key not in pks and p1.down_key in pks: #change this to voice input
            p1.y += self.speed
            p1.last_movements.append(+self.speed)
        else:
            # notice how we popped from _place_ zero,
            # but append _a number_ zero here. it's not the same.
            p1.last_movements.append(0)
           
        # ----------------- DO NOT CHANGE BELOW ----------------
        # player 2: the other user controls the right player by O/L
        p2 = self.players[1]
        p2.last_movements.pop(0)
        if p2.up_key in pks and p2.down_key not in pks: #change this to voice input
            p2.y -= self.speed
            p2.last_movements.append(-self.speed)
        elif p2.up_key not in pks and p2.down_key in pks: #change this to voice input
            p2.y += self.speed
            p2.last_movements.append(+self.speed)
        else:
            # notice how we popped from _place_ zero,
            # but append _a number_ zero here. it's not the same.
            p2.last_movements.append(0)

        self.update_ball()
        label.text = str(p1_score)+':'+str(p2_score)

class Controller(object):

    def __init__(self, model):
        self.m = model

    def on_key_press(self, symbol, modifiers):
        # `a |= b`: mathematical or. add to set a if in set a or b.
        # equivalent to `a = a | b`.
        # XXX p0 holds down both keys => p1 controls break  # PYGLET!? D:
        self.m.pressed_keys |= set([symbol])

    def on_key_release(self, symbol, modifiers):
        if symbol in self.m.pressed_keys:
            self.m.pressed_keys.remove(symbol)

    def update(self):
        self.m.update()


class View(object):

    def __init__(self, window, model):
        self.w = window
        self.m = model
        # ------------------ IMAGES --------------------#
        # "white_square.png" is a 10x10 white image
        lplayer = pyglet.resource.image("white_square.png")
        self.player_spr = pyglet.sprite.Sprite(lplayer)

    def redraw(self):
        # ------------------ PLAYERS --------------------#
        TO_SIDE = self.m.ball.TO_SIDE
        for p in self.m.players:
            self.player_spr.x = p.x//1 - TO_SIDE
            # oh god! pyglet's (0, 0) is bottom right! madness.
            self.player_spr.y = self.w.height - (p.y//1 + TO_SIDE)
            self.player_spr.draw()  # these 3 lines: pretend-paddle
            self.player_spr.y -= 2*TO_SIDE; self.player_spr.draw()
            self.player_spr.y += 4*TO_SIDE; self.player_spr.draw()
        # ------------------ BALL --------------------#
        self.player_spr.x = self.m.ball.x//1 - TO_SIDE
        self.player_spr.y = self.w.height - (self.m.ball.y//1 + TO_SIDE)
        self.player_spr.draw()


class Window(pyglet.window.Window):

    def __init__(self, *args, **kwargs):
        DIM = (800, 450)  # DIMENSIONS
        super(Window, self).__init__(width=DIM[0], height=DIM[1],
                                     *args, **kwargs)
        # ------------------ MVC --------------------#
        the_window = self
        self.model = Model(DIM)
        self.view = View(the_window, self.model)
        self.controller = Controller(self.model)
        # ------------------ CLOCK --------------------#
        fps = 30.0
        pyglet.clock.schedule_interval(self.update, 1.0/fps)
        #pyglet.clock.set_fps_limit(fps)

    def on_key_release(self, symbol, modifiers):
        self.controller.on_key_release(symbol, modifiers)

    def on_key_press(self, symbol, modifiers):
        self.controller.on_key_press(symbol, modifiers)

    def update(self, *args, **kwargs):
        # XXX make more efficient (save last position, draw black square
        # over that and the new square, don't redraw _entire_ frame.)
        self.clear()
        self.controller.update()
        self.view.redraw()


window = Window()
label = pyglet.text.Label(str(p1_score)+':'+str(p2_score),
                      font_name='Times New Roman',
                      font_size=36,
                      x=window.width//2, y=window.height//2,
                      anchor_x='center', anchor_y='center')
@window.event
def on_draw():
    #window.clear()
    label.draw()

# speech recognition thread
# -------------------------------------#
# start a thread to listen to speech
speech_thread = threading.Thread(target=listen_to_speech, args=())
speech_thread.start()
# -------------------------------------#

# pitch & volume detection
# -------------------------------------#
# start a thread to detect pitch and volume
microphone_thread = threading.Thread(target=sense_microphone, args=())
microphone_thread.start()
# -------------------------------------#

if debug: print("init window...")
if debug: print("done! init app...")
pyglet.app.run()


