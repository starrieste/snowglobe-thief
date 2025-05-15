# main.py
# where the whole game is ran

import pygame
import sys
import time
import random

from data.scripts.utils import *
from data.scripts.entities import *
from data.scripts.tilemap import *
from data.scripts.text import *
from data.scripts.animation import *

class Game:
    def __init__(self):
        pygame.init()

        pygame.display.set_caption("Snowglobe Thief")
        self.type = "game"

        self.DS = (960, 720) # display size
        self.CS = (160, 120) # canvas size

        self.display = pygame.display.set_mode(self.DS)
        self.canvas = pygame.Surface(self.CS)

        self.fps = 60
        self.clock = pygame.time.Clock()

        # storing images for retrieval
        self.assets = {
            "snow": (load_spritesheet(load_image("tiles/foreground/snow.png")), ["tile", "autotile", "physics"]),
            # "snow_bg": (load_spritesheet(load_image("tiles/background/snow_bg.png")), ["tile", "autotile"]),

            "spawners": (load_images("tiles/spawners"), ["tile"]),

            "spike-0": (load_image("animations/spike!/0.png"), []),
            "spike-1": (load_image("animations/spike!/1.png"), []),
            "spike-2": (load_image("animations/spike!/2.png"), []),
            "spike-3": (load_image("animations/spike!/3.png"), []),

            "player!idle": (Animation(load_images("animations/player!idle"), img_dur=6, anim_offset=[-3, -5]), []),
            "player!run": (Animation(load_images("animations/player!run"), img_dur=4, anim_offset=[-3, -5]), []),
            "player!rising": (Animation(load_images("animations/player!rising"), img_dur=6, anim_offset=[-3, -5]), []),
            "player!falling": (Animation(load_images("animations/player!falling"), img_dur=6, anim_offset=[-3, -5]), []),
            "player!wall_slide": (Animation(load_images("animations/player!wall_slide"), img_dur=15, anim_offset=[-2, -5]), []),
            "particle!dash": (Animation(load_images("animations/particle!dash"), loop=False), []),
            "particle!death": (Animation(load_images("animations/particle!death"), loop=False), []),
            "particle!impact": (Animation(load_images("animations/particle!impact"), loop=False), []),
            "particle!wall_impact": (Animation(load_images("animations/particle!wall_impact"), loop=False), []),

            "elf!idle": (Animation(load_images("animations/elf!idle"), img_dur=25, anim_offset=[-2, -3]),[]),
            "elf!run": (Animation(load_images("animations/elf!run"), img_dur=4, anim_offset=[-2, -3]),[]),
            "particle!confused": (Animation(load_images("animations/particle!confused"), loop=False, img_dur=25), []),
            "particle!spotted": (Animation(load_images("animations/particle!spotted"), loop=False, img_dur=25), []),

            "door!idle": (Animation(load_images("animations/door!idle")), []),
            "sign!idle": (Animation(load_images("animations/sign!idle")), []),
            "snowglobe!idle": (Animation(load_images("animations/snowglobe!idle"), img_dur=25), []),
            "particle!obtain": (Animation(load_images("animations/particle!obtain"), loop=False), []),
            "particle!guide": (Animation(load_images("animations/particle!guide")), []),

            "font": (load_image("font.png"), []),
            "background": (load_image("background.png"), [])
        }

        self.player = Player(self, (0, 0),(5, 13))
        self.exit = Door(self, (0, 0))

        # lists that help me keep track of the sprites on the screen, so I can render and update them
        self.snowglobes = []
        self.spikes = []
        self.elves = []
        self.particles = []
        
        self.cam_speed = 12 # LOWER = FASTER

        self.tilemap = Tilemap(self)

        # OKAY SO I HAVE SCREENSHAKE HERE BUT I DIDN'T USE IT AT ALL.
        self.screenshake = 0

        # tells us how far the camera has moved along the world
        self.scroll = [0, 0]
        self.scroll[0] += (self.player.rect().centerx - self.canvas.get_width()/2 - self.scroll[0])
        self.scroll[1] += (self.player.rect().centery - self.canvas.get_height()/2 - self.scroll[1])

        self.game_text = []
        self.interacting = False
        self.keys = set() # keep track of keys

        self.death_flag = False # keep track of if player died
        self.death_timer = 0

        self.level = 0
        try: self.loadLevel(self.level)
        except FileNotFoundError:
            print(f"Level {self.level} not found.")

    def loadLevel(self, map_id): # load a level, and everything in it using a .json file
        self.player.air_time = 0
        self.player.jumps = 1
        self.player.wall_cling = 0

        self.player.holding_globe = False
        self.death_flag = False
        self.spawned_death_anim = False

        self.tilemap.load("data/maps/" + str(map_id) + ".json")

        self.spikes = []
        self.snowglobes = []
        self.elves = []
        self.particles = []
        self.game_text = []

        # a bunch of texts and a particle, for LEVEL SPECIFIC stuff
        if map_id == 0:
            self.particles.append(Particle(self, [0,0], "guide"))
            text1 = text(self.assets["font"][0], desiredText="You can dash through enemies!", scale=4, color=(255, 255, 255))
            renderPos = (5, self.DS[1] - text1.get_height()*2 - 2)
            self.game_text.append([text1, renderPos, 2147483647]) # you can technically wait this out but whatever
        if map_id == 7: #len(os.listdir("data/maps"))-1:
            text1 = text(self.assets["font"][0], desiredText="This is the end, thanks for playing!", scale=4, color=(255, 255, 255))
            renderPos = (5, self.DS[1] - text1.get_height() - 2)
            self.game_text.append([text1, renderPos, 2147483647]) # you can technically wait this out but whatever

        # the spawners essentially tell me to make new entities, or to move the player or exit
        for spawner in self.tilemap.extract("spawners"):
            if spawner["part"] == 0:
                self.player.pos = spawner["pos"]
            if 1 <= spawner["part"] <= 4:
                self.spikes.append(Spike(self, spawner["pos"], spawner["part"]))
            if spawner["part"] == 5:
                self.snowglobes.append(Snowglobe(self, spawner["pos"]))
            if spawner["part"] == 6:
                self.exit = Door(self, spawner["pos"])
            if spawner["part"] == 7:
                self.elves.append(Elf(self, spawner["pos"]))
            if spawner["part"] == 8:
                self.elves.append(Elf(self, spawner["pos"], flip=True))
        
    def handleEvents(self): # self explanatory
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            # I added a bunch of options but only told the player about one set of keys...
            # I dunno, too lazy to make a better guide screen.
            if event.type == pygame.KEYDOWN:
                self.keys.add(event.key)
                # Movement
                if event.key in [pygame.K_a, pygame.K_LEFT]:
                    self.player.lateral_movement[0] = True
                if event.key in [pygame.K_d, pygame.K_RIGHT]:
                    self.player.lateral_movement[1] = True
                if event.key in [pygame.K_SPACE, pygame.K_w, pygame.K_UP]:
                    self.player.jump()
                if event.key in [pygame.K_LSHIFT, pygame.K_RSHIFT]:
                    self.player.dash()

                # Other
                if event.key in [pygame.K_e]:
                    self.interacting = True
                
            if event.type == pygame.KEYUP:
                if event.key in self.keys: self.keys.remove(event.key)

                # Movement
                if event.key in [pygame.K_a, pygame.K_LEFT]:
                    self.player.lateral_movement[0] = False
                if event.key in [pygame.K_d, pygame.K_RIGHT]:
                    self.player.lateral_movement[1] = False
                if event.key in [pygame.K_SPACE, pygame.K_w, pygame.K_UP]:
                    self.player.vary_jump()

                # Other
                if event.key in [pygame.K_e]: # technically i don't even need this self.interacting variable, but too lazy to change it now.
                    self.interacting = False

    def render(self): # drawing stuff to screen
        self.canvas.blit(self.assets["background"][0], (0,0))
        self.scroll[0] += (self.player.rect().centerx - self.canvas.get_width()/2 - self.scroll[0]) / self.cam_speed
        self.scroll[1] += (self.player.rect().centery - self.canvas.get_height()/2 - self.scroll[1]) / self.cam_speed
        render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

        for group in [self.snowglobes, self.spikes]:
            for entity in group:
                entity.render(self.canvas, render_scroll)
            
        for elf in self.elves:
            elf.render(self.canvas, render_scroll)
        
        self.exit.render(self.canvas, offset=render_scroll)
        self.tilemap.render(self.canvas, offset=render_scroll)

        for particle in self.particles:
            particle.render(self.canvas, offset=render_scroll)

        if not self.death_flag: self.player.render(self.canvas, offset=render_scroll)

        # PLAYER HITBOX
        # pygame.draw.rect(self.canvas, (255, 255, 0), (self.player.pos[0] - render_scroll[0], self.player.pos[1] - render_scroll[1], self.player.size[0], self.player.size[1]))

        screenshake_offset = (random.random() * self.screenshake - self.screenshake / 2, random.random() * self.screenshake - self.screenshake / 2)
        self.display.blit(pygame.transform.scale(self.canvas,self.display.get_size()), screenshake_offset)

        for tex in self.game_text:
            self.display.blit(tex[0], tex[1])
            tex[2] -= 1
            if tex[2] <= 0: self.game_text.remove(tex)

    def update(self): # updating entities' positions and properties
        self.screenshake = max(0, self.screenshake - 1) # unused
        self.death_timer = max(0, self.death_timer - 1)

        for group in [self.snowglobes, self.spikes]:
            for entity in group:
                entity.update()
            
        for elf in self.elves:
            elf.update(self.tilemap)

        for particle in self.particles:
            particle.update()
            if particle.animation.done:
                self.particles.remove(particle)

        self.exit.update()
        self.player.update(self.tilemap)
    
        if self.player.pos[1] >= 200: self.death_flag = True

        # make death particle
        if self.death_flag and not self.spawned_death_anim:
            self.particles.append(Particle(self, (self.player.pos[0] - 16, self.player.pos[1] - 16), "death"))
            self.spawned_death_anim = True

        # if dead and the death particle is gone, then transition
        if self.death_flag and self.death_timer == 0:
            flag = False
            for particle in self.particles:
                if particle.img_name == "death":
                    flag = True
            if not flag:
                self.death_timer = 60 # make sure we don't crash by dying infinitely
                self.transition(text(self.assets["font"][0], desiredText="", color=(255, 255, 255), scale=5), 0, advance=True)
                self.death_flag = False

    def transition(self, showText, wait_time, advance=False): # used to cut between levels, and deaths
        curtain_text = showText
        dtss = curtain_text.get_size()
        
        curtain = pygame.Surface(self.display.get_size())
        curtain.fill((1, 1, 1))
        curtain_y = 250
        y = - self.DS[1] - curtain_y
        stage = 1

        self.player.lateral_movement = [0, 0]
        self.player.jump_buffer = 0
        self.player.velocity[1] = 0
        
        while True:
            self.clock.tick(self.fps)

            self.screenshake = max(0, self.screenshake - 1)
            self.death_timer = max(0, self.death_timer - 1)

            for group in [self.snowglobes, self.spikes]:
                for entity in group:
                    entity.update()
                
            for elf in self.elves:
                elf.update(self.tilemap)

            for particle in self.particles:
                particle.update()
                if particle.animation.done:
                    self.particles.remove(particle)

            self.exit.update()
            self.player.update(self.tilemap)

            self.render()

            now = time.time()
            
            # transition curtain
            self.display.blit(pygame.transform.scale(self.canvas, self.display.get_size()), (0, 0))
            pPoints = [(0, y - curtain_y - 50), (self.DS[0]/2, y - 50),(self.DS[0], y - curtain_y - 50), (self.DS[0], self.DS[1] + y + 50), (self.DS[0]/2, self.DS[1] + y + curtain_y + 50), (0, self.DS[1] + y + 50)]
            pygame.draw.polygon(self.display, (0, 0, 0), pPoints)
            self.display.blit(curtain_text, (self.DS[0]/2 - dtss[0]/2, self.DS[1]/2 + y - dtss[1]/2 - 50))

            pygame.display.update()

            if stage == 1:
                y += self.DS[1]/10
                if y >= 0:
                    stage = 2
                    begin = time.time()
            if stage == 2: # FULLY COVERED
                if advance: self.loadLevel(self.level)
                if now - begin > wait_time:
                    stage = 3
            if stage == 3:
                y += self.DS[1]/10
                if y >= self.DS[1]:
                    return
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

    def run(self):
        while True:
            self.clock.tick(self.fps)

            self.update()
            self.render()
            self.handleEvents()

            pygame.display.update()

if __name__ == "__main__":
    Game().run()
else: game_assets = Game().assets