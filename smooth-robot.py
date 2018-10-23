#!/usr/bin/python

## Smooth Robot.
## Version 0.9
## Christophe Foyer - 2016

##                                ............                
##                              -.            ..`             
##                             :                .-            
##                            -/-`   --.`        .-           
##                            s/:/   +::/+.       :           
##                            +--:   :--.         :           
##                           :``+``.:` `       `..:           
##                           :  .....          .:::           
##                           : //::/+.- `-    ./:/-           
##                           s-.----..:/-:  -..:-.            
##                          `/+.     :-+./-.. `:              
##                          `:+/.``-:+ / /+`   :              
##                          ./-:/``/-+`/.//`   ..`            
##                          .:.-/ `:-/ / /--    ``..```       
##                          ::``/ ..`: - - o`       ```...`   
##                         .-.  :`:  ` ` ` +          `` ``-. 
##                 ``````..:`   `:-    . . :     ```..``    ``
##              `..``````  -.    /         :.....```          
##            `-.          `-    :         :                  
##           `-           `-.    :        -`                  
##           :          ...      -:      `:`            ```   
##           :       `..`       -.`:      `..         .`/+-   
##          `:    ...`        .-   `-        -.       .//..   
##        ...`....           -.     `-        `-`    -`       
##     `..                  -`       .-         ....-:...     
##    -`                  `-          .-                `...  
##   :                   ..            `-                     
##  :                   -.              `-                     

import sys
import os
import re
from time import sleep
import nxt
import tty, termios

"""
this script relies on my "scokets" script for the socket server from
which it gets its instructions, I will probably include it but it is
very simple and can easily be replaced with any kind of script that
can send the required commands to the robot.
"""

from sockets import socketServer

"""
also going to need threads and queues so the socket server and the rest
of the script can function simultaneously and still exchange data.
"""
from threading import Thread
from multiprocessing import Queue

import nxt.locator
from nxt.motor import *
from nxt.sensor import *

"""
My first time using objects, and I must say, they're
very nice.
"""

class Robot(object):

    def __init__(self, brick):

        self.brick = brick

        """
        Ports A and B are for the left and right motors respecively,
        and port C is for the camera. The sensors are setup in this
        order: light sensor on port 1, "follower" sensor (mindsumo
        sensor which can do simple tracking of objets right in front
        of it) on port 2, touch on port 3, and ultrasonic on port 4
        """

        self.lmotor = Motor(brick, PORT_A)
        self.rmotor = Motor(brick, PORT_B)
        self.cmotor = Motor(brick, PORT_C)
        self.light = Light(brick, PORT_1)
        self.follower = Light(brick, PORT_2)
        self.touch = Touch(brick, PORT_3)
        self.ultrasonic = Ultrasonic(brick, PORT_4)

    def roll(self, left, right):
        '''
        Non-blocking function for modifying power to servos.
        The servos will continue to operate at these power
        levels until told to do otherwise. Values are given
        as percentages of full power, so torque will change
        as the battery loses charge. A negative value will
        reverse the rotation of the respective servo.
        For example, to spin on the spot, clockwise and at
        full power, do

            self.roll(100, -100)

        '''
        self.lmotor.run(left)
        self.rmotor.run(right)

    def halt(self):
        
        '''
        Stops and then holds both servos steady for
        0.2 seconds, then cuts power to both servos.
        '''
        
        self.lmotor.brake()
        self.rmotor.brake() 
        sleep(0.2)
        self.lmotor.idle()
        self.rmotor.idle()

    def pan(self, camera):

        self.cmotor.run(camera)

def commsServer():
    global queueMessages
    global queueCommands
    while True:
            #check if the robot is trying to get a message back
            if not queueMessages.empty():
                message = queueMessages.get_nowait()
            else:
                message = 'received'
            print "waiting for data"
            data = socketServer(3210, message)
            print data
            queueCommands.put(data)
    print "comms server is switching off"
    return

print 'starting socket server'

#starting commsServer thread with data queues.
queueCommands = Queue()
queueMessages = Queue()
commsServerThread = Thread(target=commsServer, args=())
commsServerThread.start()

brick = nxt.locator.find_one_brick()
robot = Robot(brick)

#power modifier (percentage)
power = 80

#turn light sensor led on
robot.light.set_illuminated(True)

#main loop (maybe I should put it in a thread... eh!...)
while True:
    """
    you might need to tweek the sign for power to match
    your robot configuration, I think my motors are facing
    the wrong way but on the right sides, which is why the
    power for "Forwards" is negative.
    """
    if not queueCommands.empty():
        print 'getting commands'
        cmd = queueCommands.get()
    else:
        cmd = 'None'

    print 'mainloop:', cmd

    if cmd == "Forwards":
        robot.roll(-power, -power)
        print "moving", cmd
        time.sleep(0.3)
    elif cmd == "Backwards":
        robot.roll(power, power)
        print "moving", cmd
        time.sleep(0.3)
    elif cmd == "Left":
        robot.roll(power, -power)
        print "moving", cmd
        time.sleep(0.3)
    elif cmd == "Right":
        robot.roll(-power, power)
        print "moving", cmd
        time.sleep(0.3)
    elif cmd == "None":
        robot.halt()
        
    else:
        """
        Either no movement command is sent by the user (robot stops)
        or it is a command where the robot takes control and the robot
        will pause to transition to an automatic mode.
        """
        sleep(0.2)
        robot.halt()
        if cmd[0] == "power":
            power = cmd[1]
        elif cmd == "Park":
            #this just follows a black line on my white carpet
            print 'attempting automatic maneuver'
            while True:
                if not queueCommands.empty():
                    cmd = queueCommands.get_nowait()
                else:
                    cmd = "None"
                if robot.touch.is_pressed() or cmd == "Park":
                    robot.halt()
                    break
                if robot.light.get_sample() < 350:
                    robot.roll(-80,0)
                else:
                    robot.roll(0,-80)
        elif cmd == "Roam":
            """
            I have to make sure this can be interupted.
            This is going to be fairly complex, going to have to find and
            recognize the charging station, all avoid obstacles, and
            positioning itself for the final manuever. Then it will also
            have to check it's indeed charging by recognizing a flashing
            LED on the dock. This function will also have to be called on
            if the robot is not charging and the internt cuts off (so it
            can get back to it's charging station without assistance)

            This is going to be though.
                  |
            also, | this is my initial reaction when coding this,
                  v we'll see if I can get past just typing this.
            """
            pass
