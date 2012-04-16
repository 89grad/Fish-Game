# Interactive Fish

This is a project we did at [89grad](http://www.89grad.ch) for the [Night of Museums 2012 in Bern](http://www.museumsnacht-bern.ch).
We developed an interactive game that allowed visitors to control a circle of light that is hunted by a swarm of fish.
Fish that get close enough to the circle, start to eat it and in turn diminishes the player's energy.

A [video of the installation](http://www.youtube.com/watch?v=v7GTQomqFMk) and a short basic technical description of the fish movements can be found on our
[blog](http://www.89grad.ch/2012/04/museumsnacht-tech/) (sorry, German only).

## Components

The whole game can be split into three parts:

* User input via Kinect
* Event server
* Game engine

### User input

An adapted version of the OpenNI/NITE framework's TrackPad sample is used as user input. Install OpenNI/NITE by following these steps:

1. Obtain the framework from [OpenNI/NITE](http://www.openni.org)
2. Follow the steps on [20 paper cups](http://www.20papercups.net/programming/kinect-on-ubuntu-with-openni/)'s howto

Even though the howto on [20 paper cups](http://www.20papercups.net/programming/kinect-on-ubuntu-with-openni/) is very good, there
are some small things that may be valuable knowing:

* The directory names in the howto may differ from OpenNI's actual names. In most cases the required files can be found in a subdirectory.
* Step 2: The downloaded files are not executable. As such you need to make them executable with chmod.
* Same goes for step 3: Kinect Sensor Module. Also don't use the boilerbots' sensor (as mentioned in many howtos), instead use the [avin2](https://github.com/avin2/SensorKinect) sensor.

For the actual compilation of our source code do the following:

1. Copy the Fishly directory to the same diretory as the OpenNI examples
2. In Fishly's main.cpp replace *EVENT_SERVER_IP* with the EventServer's IP on line 574
3. From within the Fishly directory run make
4. The executable can be found in the sample code's x64-Release directory

### Event server

The event server receives the user input from Fishly. As in the TrackPad example the position of the hand is maped into a grid of 5x9
tiles. If the player pushes forward i.e. presses a tile, this event is also forwarded to the event server. The server takes the input
and converts the position of the hand to a vector (the centre tile is the (0,0) position) that will be passed along to the game engine.
The following format is used:

    status <x vector component> <y vector component> <Event, optional>

To start the event server just type

    python kinetadapt.py

It will listen on port 8000 for incoming events.

### Game Engine

The game engine is based on [Cocos2D](http://cocos2d.org), a game framework written in Python.

#### Installation

The game only depends on the cocos2d package, that can be obtained from [code.google.com](http://code.google.com/p/los-cocos/downloads/list)
or installed with `easy_install`

In mnb.py, change *SO_ADDR* = '127.0.0.1' to the EventServer's address (next time we do less static coding :) )

### Game

The game can be played either with the Kinect or a keyboard.

#### Kinect

To play the game with the Kinect, the EventServer must be started first. Then start the Kinect part
     
     ./Fishly

and finally the game
     
     python mnb.py

If the EventServer is running and you still want to use the keyboard as input start the game with
     python mnb.py key

If you use the Kinect as input, you need to wave to start the game. The circle of light will follow the movement of your hand: If
you move your hand up the circle goes upwards and so on. If you push towards the sensor you can shy the fish away.

#### Keyboard

If you just want to play the game without the Kinect, you don't have to care about the EventServer and User Input section and can just type

     python mnb.py

The game can also be controlled with the arrow keys. To shy the fish away, press the space key.

## Licensing

The game engine's and the event server's code are licensed under the Apache v2.0 licence, while the Fishly code is based on Primsense's copyrighted example code.