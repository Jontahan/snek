import random
import sys
from collections import deque
from gym import spaces
import numpy as np
import gym
import pygame as pg
import itertools

class Snek(gym.Env):
    NOP, LEFT, RIGHT, UP, DOWN = range(5)
    COLOR_BKG = (24, 24, 24)
    COLOR_FOOD = (140, 24, 24)

    def __init__(self, render_enabled=False):
        self.width = 9
        self.height = 9
        self.scale = 16
        self.player = Player(self, (self.width // 2, self.height // 2))
        self.steps = 0
        self.timeout = 500
        self.render_enabled = render_enabled

        free_pos = list(filter(lambda pos: pos not in self.player.tail, itertools.product(range(self.width), repeat=2)))
        self.wrap = False
        self.food = Food(random.choice(free_pos))
        self.action_space = spaces.Discrete(5)
        self.observation_space = spaces.Box(low=0, high=1, shape=(3,self.width,self.height), dtype=np.uint8)
        self.framerate = 10
        
        if self.render_enabled:
            pg.init()
            pg.display.set_caption('Snek')
            self.screen = pg.display.set_mode((self.width * self.scale, self.height * self.scale))
            self.clock = pg.time.Clock()

    def step(self, action):
        state = self.init_state()
        reward = 0
        done = False
        info = {}

        # Pygame event handling (resolves some crashing)
        if self.render_enabled:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    sys.exit()
            pg.event.pump()

        if action == Snek.LEFT and self.player.dir != Player.DIR_RIGHT:
            self.player.dir = Player.DIR_LEFT
        if action == Snek.RIGHT and self.player.dir != Player.DIR_LEFT:
            self.player.dir = Player.DIR_RIGHT
        if action == Snek.UP and self.player.dir != Player.DIR_DOWN:
            self.player.dir = Player.DIR_UP
        if action == Snek.DOWN and self.player.dir != Player.DIR_UP:
            self.player.dir = Player.DIR_DOWN

        survive = self.player.tick()
        if self.player.pos_x == self.food.pos_x and self.player.pos_y == self.food.pos_y:
            self.player.len += 1
            
            free_pos = list(filter(lambda pos: pos not in self.player.tail, itertools.product(range(self.width), repeat=2)))   
        
            self.food.pos_x, self.food.pos_y = random.choice(free_pos)

            reward = 1

        state[0][self.player.pos_x][self.player.pos_y] = 1
        for pos in self.player.tail:
            state[1][pos[0]][pos[1]] = 1
        state[2][self.food.pos_x][self.food.pos_y] = 1
        
        # Death
        if (self.player.pos_x, self.player.pos_y) in list(self.player.tail)[1:]:
            reward = -1
            done = True
        
        if not survive:
            reward = -1
            done = True
        
        self.steps += 1
        if self.steps >= self.timeout:
            self.steps = 0
            done = True
        
        return state, reward, done, info

    def render(self, mode='human'):
        # Background
        pg.draw.rect(self.screen, Snek.COLOR_BKG,
                     (0, 0, self.width * self.scale, self.height * self.scale))

        for i, pos in enumerate(self.player.tail):
            pg.draw.rect(self.screen, (24, 160 - i * (80 / len(self.player.tail)), 24), (self.scale * pos[0], self.scale * pos[1], self.scale, self.scale))
            
            if i == 0:
                self.draw_face(pos)
                
        pg.draw.rect(self.screen, Snek.COLOR_FOOD, (self.scale * self.food.pos_x, self.scale * self.food.pos_y, self.scale, self.scale))
        pg.display.flip()
        self.clock.tick(int(self.framerate))

    def draw_face(self, pos):
        unit = self.scale / 6
        if self.player.dir == Player.DIR_LEFT:
            pg.draw.rect(self.screen, (0, 0, 0), (self.scale * pos[0] + unit, self.scale * pos[1] + unit, unit, unit))
            pg.draw.rect(self.screen, (0, 0, 0), (self.scale * pos[0] + unit, self.scale * pos[1] + unit * 4, unit, unit))
            
        if self.player.dir == Player.DIR_RIGHT:
            pg.draw.rect(self.screen, (0, 0, 0), (self.scale * pos[0] + unit * 4, self.scale * pos[1] + unit, unit, unit))
            pg.draw.rect(self.screen, (0, 0, 0), (self.scale * pos[0] + unit * 4, self.scale * pos[1] + unit * 4, unit, unit))
            
        if self.player.dir == Player.DIR_UP:
            pg.draw.rect(self.screen, (0, 0, 0), (self.scale * pos[0] + unit, self.scale * pos[1] + unit, unit, unit))
            pg.draw.rect(self.screen, (0, 0, 0), (self.scale * pos[0] + unit * 4, self.scale * pos[1] + unit, unit, unit))
            
        if self.player.dir == Player.DIR_DOWN:
            pg.draw.rect(self.screen, (0, 0, 0), (self.scale * pos[0] + unit, self.scale * pos[1] + unit * 4, unit, unit))
            pg.draw.rect(self.screen, (0, 0, 0), (self.scale * pos[0] + unit * 4, self.scale * pos[1] + unit * 4, unit, unit))

    def init_state(self):
        state = np.array([
            np.zeros((self.width, self.height)), # Head
            np.zeros((self.width, self.height)), # Body
            np.zeros((self.width, self.height))  # Food
        ])
        return state

    def reset(self):
        self.steps = 0
        self.player = Player(self, (self.width // 2, self.height // 2))
        free_pos = list(filter(lambda pos: pos not in self.player.tail, itertools.product(range(self.width), repeat=2)))
        self.food = Food(random.choice(free_pos))
        return self.init_state()

class Player:
    DIR_LEFT, DIR_RIGHT, DIR_UP, DIR_DOWN = range(4)

    def __init__(self, env, start_pos):
        self.pos_x, self.pos_y = start_pos
        self.dir = Player.DIR_DOWN
        self.tail = deque([start_pos])
        self.len = 1
        self.env = env

    def tick(self):
        survive = True
        if self.dir == Player.DIR_LEFT:
            if not self.env.wrap and self.pos_x - 1 < 0:
                survive = False 
            self.pos_x = (self.pos_x - 1) % self.env.width
        if self.dir == Player.DIR_RIGHT:
            if not self.env.wrap and self.pos_x + 1 >= self.env.width:
                survive = False 
            self.pos_x = (self.pos_x + 1) % self.env.width
        if self.dir == Player.DIR_UP:
            if not self.env.wrap and self.pos_y - 1 < 0:
                survive = False 
            self.pos_y = (self.pos_y - 1) % self.env.height
        if self.dir == Player.DIR_DOWN:
            if not self.env.wrap and self.pos_y + 1 >= self.env.height:
                survive = False 
            self.pos_y = (self.pos_y + 1) % self.env.height

        if len(self.tail) >= self.len:
            self.tail.pop()
        self.tail.appendleft((self.pos_x, self.pos_y))

        return survive

class Food:
    def __init__(self, pos):
        self.pos_x, self.pos_y = pos
