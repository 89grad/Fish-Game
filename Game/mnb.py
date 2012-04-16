#
#   Copyright 2012 89grad GmbH
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
#
#   Game Engine
#
#   Fish Installation for Muesumsnacht Bern 2012
#   Author: Christian Cueni <christian.cueni@89grad.ch>
#   Based on examples that come with cocos2D
#
import sys
import os
import math
import random
import socket
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


from pyglet import image, font
from pyglet.gl import *
from pyglet.window import key

from cocos.director import director
from cocos.layer import Layer
from cocos.scene import Scene
from cocos.sprite import Sprite
from cocos.scenes.transitions import ZoomTransition

import cocos.euclid as eu
import cocos.actions as ac

from cocos.path import Bezier
import cocos

#Messages for the user
START_MSG = "Press space or wave!"
END_MSG = "They got you!"

FONT = "Fredoka One" #http://www.google.com/webfonts/specimen/Fredoka+One

#communication with kinect
SO_ADDR = "EVENT_SERVER_IP"
SO_PORT = 8000
MSGLEN = 1024

#fish constatns
NO_FISH = 10
RANDOM_MOVE = 50

#player constants
ENERGY_DRAIN = 5
ENERGY_MAX = 100.0

#based on some trial an error
MOVEMENT_INC = 15 #player 
FLUID_R = 0.001


#----- Actions ---------

#Performs a Bezier move and aligns the target on the movement's tangent
class RotatingBezier(ac.Bezier):
    def __init__(self, bezier, duration, forward=True):
        super(RotatingBezier, self).__init__(bezier, duration, forward)
        
    def update(self,t):
        if self.forward:
            p = self.bezier.at(t)
        else:
            p = self.bezier.at(1-t)
            
        #calculates the angle between the current and the last point and
        #changes the angle of the sprite accordingly
        p1 = self.target.position
        p2 = self.start_position + eu.Point2(*p)
        
        self.target.position = p2
        self.target.rotation = (360*math.atan2(p2[0]-p1[0], p2[1]-p1[1])/(math.pi*2)+0)
        


#----- Sprites -----
 
#Well, the player
class Player(cocos.sprite.Sprite):
    
    def __init__(self, img):
        super(Player, self).__init__(img)

        #a circle is assumed as image
        #set radius to the picture's with times the player's scale factor
        self.radius = img.get_image_data().width/2*self.scale

        #check size of picutre, maybe
        self.energy = ENERGY_MAX

        #velocity vector
        self.v = eu.Vector2(0.0, 0.0)


#Some fish class
class Fish(cocos.sprite.Sprite):

    def __init__(self, img, scale=1):
        super(Fish, self).__init__(img)

        self.scale = scale

        #velocity is related to size
        #basically a linear equation that is based on trial an error
        self.v = -(45/0.4)*(scale-0.1)+90

        self.length = img.frames[0].image.get_image_data().width/2*self.scale

        #keep the 2nd handle as vector
        self.bc = eu.Vector2(0.0,0.0)

        #states:
        # 0: free
        # 1: onfollow
        # 2: follow
        # 3: eat
        self.state = 0

    
    #performs a move on a bezier curve
    def bezier_move(self, endpoint, duration):
        """
        calculate the position of the endpoint handles
        the end handle must be in the 2nd or 3rd quadrant of the fish's local coord system
        used in order to control the fish's movement a wee bit
        1. calculate angle between starting- and endpoint
        2. get a rotation matrix & rotate some random handles (limted to quadrant 2 & 3 of the fish)
        3. move the handles in a coord-system where (0,0) is the starting point
        """

        angle = math.atan2(endpoint.y,endpoint.x)
        end_handles_matrix = eu.Matrix3.new_rotate(angle)
        handle2_x = random.randint(-150,50)
        handle2_y = random.randint(50,150)

        relative_handle2 = end_handles_matrix*eu.Vector2(handle2_x, handle2_y)
        #the (0,0) of the handles is the fish's starting position
        handle2_x = endpoint.x-relative_handle2.x
        handle2_y = endpoint.y-relative_handle2.y
        
        curve = Bezier((0,0), (endpoint.x, endpoint.y),self.bc, (handle2_x,handle2_y))

        self.b = eu.Point2(endpoint.x,endpoint.y)
        self.bc = relative_handle2

        rb = RotatingBezier(curve, duration)
        self.do(rb)


    #standard move, when the fish is not near the player
    def free_move(self, direction=None):
        global game_height, game_width

        self.state = 0

        #direction makes the fish swim in the general direction of the player
        #if no direction is given the fish are allowed to swim freely about
        if direction is None:
        #will be used as random boundaries for end position
            lower_x_rand = lower_y_rand = -300
            upper_x_rand = upper_y_rand = 300
             
            #check where where the fish is, if it's somewhere near the corner limit the movement
            if(self.x < game_width/5):
                lower_x_rand = 0
                upper_x_rand = game_width
            elif(self.x > (game_width-(game_width/5))):
                upper_x_rand = game_width
                lower_x_rand = -game_width
             
            if(self.y < game_height/5):
                lower_y_rand = 0
                upper_y_rand = game_height
            elif(self.y > (game_height-(game_height/5))):
                upper_y_rand = 0
                lower_y_rand = -game_height
     
            #calculate delta-x and -y, check if we're out of bounds
            #add the delta value to the vector that points to the player
            fish_dx = random.randint(lower_x_rand,upper_x_rand)
             
            if(fish_dx+self.x > game_width):
                fish_dx = game_width-self.x
            elif(fish_dx+self.x < 0):
                fish_dx = 0
     
            fish_dy = random.randint(lower_y_rand,upper_y_rand)
     
            if(fish_dy+self.y > game_height):
                dy = game_height-self.y
            elif(fish_dy+self.y < 0):
                dy = 0

        #otherwise move the fish in the general direction of the player
        #some random values are added in order to have some diversity among the fish
        else:
            rand_factor = float(random.randint(5,12))/10
            fish_vector = rand_factor*direction
    
    
            #will be used as random numbers that get added to the endposition of the movement
            lower_x_rand = lower_y_rand = int(-direction.magnitude()*0.4)
            upper_x_rand = upper_y_rand = int(direction.magnitude()*0.4)
            
            dx = random.randint(lower_x_rand,upper_x_rand)
            fish_dx = dx + fish_vector.x
    
            dy = random.randint(lower_y_rand,upper_y_rand)
            fish_dy = dy + fish_vector.y

        self.bezier_move(eu.Vector2(fish_dx, fish_dy), random.randint(2,5))

    #scares the fish away to some random position
    def escape_move(self):
        global game_height, game_width

        random_pos = eu.Vector2(random.randint(-game_width,game_width), random.randint(-game_height,game_height))
        self.bezier_move(random_pos,float(random.randint(6,12))/10)


    #this move is used to make the fish swim straight at the player
    def on_follow_move(self, direction):

        self.state = 1
        #determine a random point (ok, there are some constraints) that is closer to the player as endpoint
        #get a random angle
        #create a rotating matrix with the angle
        angle = random.randint(-45,45)
        rotation_matrix = eu.Matrix3.new_rotate(2*math.pi*(angle/360))

        #multiply the vector pointing from the fish to the player by 0.2 to 0.5
        #and rotate it with the random angle
        #this vector points towards the movement's endpoint
        v_p2 = (float(random.randint(2,5))/10)*direction
        v_rotated = rotation_matrix*v_p2

        #get the vector pointing from the endpoint to the player
        #is used for the endpoints handles
        v_p2_handle = -(direction - v_rotated)

        curve = Bezier((0,0), (v_rotated.x, v_rotated.y),self.bc*0.5, (v_p2_handle.x+v_rotated.x,v_p2_handle.y+v_rotated.y))
        self.bc = direction

        rb = RotatingBezier(curve, 1)
        self.do(rb)


    #follows the player
    def follow_move(self, v_direction, dt):

        self.state = 2

        #update the old endpoint handle
        #this results in a smooth movement away from the player if we go back to state 0
        self.bc = v_direction

        #get vector that points to the player and move along it
        v_distance = dt*self.v*v_direction.normalized()
        self.position = (v_distance.x + self.x, v_distance.y + self.y)
        self.rotation = (360*math.atan2(v_direction.x, v_direction.y)/(math.pi*2)+0)
        
    


#------ Layers ----------

#A layer that contains the fish
class FishLayer(cocos.layer.Layer):
    
    def __init__(self):

        global game_height, game_width

        super(FishLayer, self).__init__()
        
        random.seed()
        
        #init fishes and add them to the layer
        for i in range(NO_FISH):
            images = [pyglet.resource.image('fish0.png'), pyglet.resource.image('fish1.png'), pyglet.resource.image('fish2.png'),pyglet.resource.image('fish3.png'),
                      pyglet.resource.image('fish4.png'), pyglet.resource.image('fish3.png'), pyglet.resource.image('fish2.png'), pyglet.resource.image('fish1.png'),
                      pyglet.resource.image('fish0.png')]
            fishes = pyglet.image.Animation.from_image_sequence(images, 0.1)
            fish = Fish(fishes, float(random.randint(1,6))/10) #get random scale factor between 0.1 and 0.6

            self.add(fish,2.0)
            fish.position = random.randint(0,game_width),random.randint(0,game_height)

        self.schedule(self.update)


    def update(self, dt):

        for node in self.get_children():
            
            #perform actions for a fish
            #in this case it can move freely around the screen
            if(node.__class__.__name__ == "Fish" and not(node.are_actions_running())):
                node.free_move()



#the actual game, extends the FishLayer
class FishGame(FishLayer):

    #used for keybord & mouse input
    is_event_handler = True
    
    def __init__(self, semi_transparent_layer, fn_show_message=None):
        super(FishGame, self).__init__()

        #assign callback for gameover message
        self.fn_show_message = fn_show_message

        self.semi_t_layer = semi_transparent_layer
        self.player_image = pyglet.resource.image('player.png')
        self.player = None

    def start_game(self):
        global game_height, game_width

        self.semi_t_layer.visible = False

        #init a new player and add it to the game
        self.player = Player(self.player_image)
        self.player.position = (game_width/2,game_height/2)
        self.add(self.player)


    def update(self, dt):

        global socket_mgr, game_width, game_height, use_kinect

        escape = False

        if use_kinect:
            #poll position from kinect
            socket_mgr.send('get\n')
            input = socket_mgr.receive()
    
            #extract the status and positions from the response
            #status <x vector> <y vector> <Event if any>
            match_obj = re.match(r'status (-?\d\.\d*) (-?\d\.\d*)\s?(.*)', input)
            if match_obj:
                x_factor = float(match_obj.group(1))
                y_factor = float(match_obj.group(2))
                #player makes a splash
                status = match_obj.group(3)
                if status == "Forward":
                    #self.do(cocos.actions.grid3d_actions.Ripple3D( grid=(32,24), radius=400, waves=5,
                    #                    center=(self.player.x, self.player.y), duration=1, amplitude=20))
                    escape = True
    
               
                self.player.v.x += x_factor*MOVEMENT_INC
                self.player.v.y += y_factor*MOVEMENT_INC        


        #loop thru all objects on the layer
        for node in self.get_children():
            
            #perform actions for a fish if we have a player
            if(self.player and node.__class__.__name__ == "Fish"):
                #get distance to player
                v_player_fish = eu.Vector2((self.player.x-node.x),  (self.player.y-node.y))
                distance_to_player = v_player_fish.magnitude()
                #make close fish swim away if the player makes a splash
                if escape:
                    if(distance_to_player < 200):
                        node.stop()
                        node.escape_move()
                #only do new actions if the fish is currently not performing one
                elif not(node.are_actions_running()):
                    #triggers follow mode for fish
                    if(distance_to_player < 150):
                        #check if we're coming from free-movement
                        #in this case the fish must first do an adujsment movement
                        #before it can go into follow mode
                        if(node.state == 0):
                            node.on_follow_move(v_player_fish)
                        else:
                            #if the fish is too close there is no need to move it
                            #drain the players energy if we touching it
                            if(not distance_to_player <= self.player.radius*self.player.scale):
                                node.follow_move(v_player_fish, dt)
                                #maybe a collision model here!!!!!!!!
                                if(not distance_to_player > (self.player.radius*self.player.scale + node.length)):
                                    self.player.energy = self.player.energy - dt*ENERGY_DRAIN
                            else:
                                self.player.energy = self.player.energy - dt*ENERGY_DRAIN
                            
                    else:
                        node.free_move(v_player_fish)
                

            #player stuff
            elif(node.__class__.__name__ == "Player"):

                #apply some kind of friction (based on trial and error) to the player's movement
                #then calculate its new position
                node.v = node.v - node.v.normalized()*node.v.magnitude()*node.v.magnitude()*FLUID_R
                node.position = node.position + node.v*dt

                #keep player in bounds
                if(node.x < 0):
                    node.x = 0
                if(node.x > game_width):
                    node.x = game_width
                if(node.y < 0):
                    node.y = 0
                if(node.y > game_height):
                    node.y = game_height

                #maybe collision model here
                #if the player runs out of energy, stop the game
                if(node.energy < 0):
                    self.pause_scheduler()
                    self.semi_t_layer.visible = True
                    self.fn_show_message(END_MSG, self.end_game)

                #decrease the radius in some proportional fashion to the energy level
                new_scale = (0.7/ENERGY_MAX)*node.energy + 0.3
                self.player.scale = new_scale


    def end_game(self):
        global info_scene
        self.player.kill()
        self.player = None
        director.replace(ZoomTransition(info_scene,1.25))      


    #handles mouse events
    #def on_mouse_motion (self, x, y, dx, dy):
       #This function is called when the mouse is moved over the app.
       #(x, y) are the physical coordinates of the mouse
       #(dx, dy) is the distance vector covered by the mouse pointer since the
       #    last call.
    #   self.player.position =  (x, y)
    #   return True


    #handles key events
    def on_key_press(self, k ,m ):
        if k == key.LEFT:
            self.player.v.x -= MOVEMENT_INC
        elif k == key.RIGHT:
            self.player.v.x += MOVEMENT_INC
        elif k == key.UP:
            self.player.v.y += MOVEMENT_INC
        elif k == key.DOWN:
            self.player.v.y -= MOVEMENT_INC
        if k == key.ESCAPE:
            #exit()
            self.pause_scheduler()
            self.semi_t_layer.visible = True
            self.fn_show_message(END_MSG, self.end_game)
        elif k == key.SPACE:
            #shy fish away, just copy paste from above, some refactoring is needed :)
            for node in self.get_children():
            
                #perform actions for a fish if we have a player
                if(self.player and node.__class__.__name__ == "Fish"):
                    #get distance to player
                    v_player_fish = eu.Vector2((self.player.x-node.x),  (self.player.y-node.y))
                    distance_to_player = v_player_fish.magnitude()
                    #make close fish swim away if the player makes a splash
                    if(distance_to_player < 200):
                        node.stop()
                        node.escape_move()
        
        return True
    


#the start screen with all the information
class InfoLayer(cocos.layer.Layer):
    
    #uncomment if you want to use the mouse as input device
    is_event_handler = True

    def __init__(self, fn_start_game=None):
        super(InfoLayer, self).__init__()

        self.fn_start_game = fn_start_game

        self.title = cocos.text.Label(START_MSG,font_name=FONT, font_size=32, anchor_x='center',anchor_y='center')
        self.title.position = (game_width/2, game_height/2-75)
        self.add(self.title)

        self.schedule(self.update)
    
    #this polling part is not that nice
    def update(self, dt):
        global game_scene, socket_mgr, use_kinect
        
        if use_kinect and socket_mgr:
            socket_mgr.send('get\n')
            response = socket_mgr.receive()
            if 'Wave' in response:
                self.fn_start_game()
                director.replace(ZoomTransition(game_scene,1.25))

    
    #handles key events
    def on_key_press( self, k , m ):
        global game_scene
        if k == key.SPACE:
            self.fn_start_game()
            director.replace(ZoomTransition(game_scene,1.25))
        if k == key.ESCAPE:
            exit()

        return True
    


#displays a game over message on screen
#plus our logo
class MessageLayer(cocos.layer.Layer):

    def __init__(self):
        super(MessageLayer, self).__init__()

    def show_message(self, message, callback):

        self.message = cocos.text.Label(message,font_name=FONT,font_size=32, anchor_x='center',anchor_y='center')
        self.message.position = (game_width/2, game_height+100)

        actions = (
            ac.Show() + ac.Accelerate(ac.MoveBy( (0,-game_height/2.0-100), duration=0.5)) +
            ac.Delay(1) +
            ac.Accelerate(ac.MoveBy( (0,-game_height/2.0-100), duration=0.5)) +
            ac.Hide()+
            ac.CallFunc(callback)
            )

        self.add(self.message)
        self.message.do(actions)



class SocketManager():

    def __init__(self, sock=None):
        if sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = sock

    def connect(self, addr):
        self.sock.connect(addr)

    def send(self, msg):
        self.sock.send(msg)

    def receive(self):
        return self.sock.recv(MSGLEN)

if __name__ == "__main__":


    #get input mode, if keyword keyboard (actually any keyword) the the player can use either keyboard or mouse
    if len(sys.argv) > 1:
        use_kinect = False
    else:
        #open a socket to a event server
        #if we cannot open a socket, fall back to keyboard
        try:
            socket_mgr = SocketManager()
            socket_mgr.connect((SO_ADDR, SO_PORT))
            use_kinect = True
        except:
            use_kinect = False
    
    # director init takes the same arguments as pyglet.window
    #cocos.director.director.init(fullscreen=True)
    cocos.director.director.init(width=1024, height=700)
    game_width = cocos.director.director.get_window_size()[0]
    game_height = cocos.director.director.get_window_size()[1]
    cocos.director.director.set_show_FPS(True)

    #GameScene and Layer
    message_layer = MessageLayer()
    semi_transparent_layer = cocos.layer.util_layers.ColorLayer(0,37,68,100)
    game_layer = FishGame(semi_transparent_layer, fn_show_message=message_layer.show_message)
    game_scene = cocos.scene.Scene(cocos.layer.util_layers.ColorLayer(0,37,68,255), game_layer, semi_transparent_layer, message_layer)

    #Main & Info Scene
    ten = cocos.sprite.Sprite(pyglet.resource.image('title.png'))
    ten.position = (game_width/2, game_height/2)

    game_scene.add(message_layer)

    info_layer = InfoLayer(fn_start_game=game_layer.start_game)
    info_fish_layer = FishLayer()
    info_fish_layer.add(ten,1.0)
    info_scene = cocos.scene.Scene(cocos.layer.util_layers.ColorLayer(0,37,68,255), info_fish_layer,
                                   cocos.layer.util_layers.ColorLayer(0,37,68,120), info_layer)

    info_fish_layer.do(ac.Repeat(cocos.actions.grid3d_actions.Ripple3D( grid=(32,24), radius=800, waves=5,
                                    center=(game_width/2+100,game_height/2+100), duration=8, amplitude=30)))

    # And now, start the application, starting with main_scene
    cocos.director.director.run(info_scene)
