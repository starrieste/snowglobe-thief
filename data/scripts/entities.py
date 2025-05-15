# entities.py
# where I keep all entities that will be processed and used in the game

import math
import random
import pygame

from data.scripts.text import *

class PhysicsEntity: # class with gravity
    def __init__(self, game, asset_id, pos, size=None):
        self.game = game
        self.asset_id = asset_id
        self.pos = list(pos)
        self.velocity = [0, 0]
        self.collisions = {"up": False, "down": False, "right": False, "left": False}

        self.action = ""
        self.set_action("idle")
        self.size = self.animation.images[0].get_size() if not size else size
        self.anim_offset = [0, 0]
        self.flip = False

        self.last_movement = [0, 0]
        self.gravity = 0.1

    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])

    def set_action(self, action):
        if action != self.action:
            self.action = action
            self.animation = self.game.assets[self.asset_id + "!" + self.action][0].copy()

    def update(self, tilemap, movement=(0, 0)):
        self.collisions = {"up": False, "down": False, "right": False, "left": False}

        frame_movement = ((movement[0] + self.velocity[0]), (movement[1] + self.velocity[1]))

        self.pos[0] += frame_movement[0]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[0] > 0:
                    entity_rect.right = rect.left
                    self.collisions["right"] = True
                if frame_movement[0] < 0:
                    entity_rect.left = rect.right
                    self.collisions["left"] = True
                self.pos[0] = entity_rect.x

        self.pos[1] += frame_movement[1]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[1] > 0:
                    entity_rect.bottom = rect.top
                    self.collisions["down"] = True
                if frame_movement[1] < 0:
                    entity_rect.top = rect.bottom
                    self.collisions["up"] = True
                self.pos[1] = entity_rect.y

        if movement[0] > 0:
            self.flip = False
        if movement[0] < 0:
            self.flip = True

        self.last_movement = movement

        self.velocity[1] = min(3, self.velocity[1] + self.gravity)

        if self.collisions["down"] or self.collisions["up"]:
            self.velocity[1] = 0

        self.animation.update()
        self.anim_offset = self.animation.anim_offset.copy()

        if self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0] - (0.1), 0)
        if self.velocity[0] < 0:
            self.velocity[0] = min(self.velocity[0] + (0.1), 0)

    def render(self, surf, offset=(0, 0)):
        render_pos = [self.pos[0] - offset[0] + self.anim_offset[0], self.pos[1] - offset[1] + self.anim_offset[1]]
        render_pos[0] = min(math.ceil(render_pos[0]), math.floor(render_pos[0]))
        render_pos[1] = min(math.ceil(render_pos[1]), math.floor(render_pos[1]))
        surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False), render_pos)

class Player(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, "player", pos, size)
        self.air_time = 0
        # these are some platformer tricks, used for better game feel
        # the jump buffer makes it so you can press jump before hitting the ground and you still jump
        self.jump_buffer = 0
        # jump effect makes it so you can vary how high the jump is
        self.jump_effect = False
        self.jumps = 1

        self.lateral_movement = [False, False] # running left and right


        self.wall_slide = 0
        self.slide_counter = 0 # keeps track of whether we're wallsliding

        self.holding_globe = False
        self.dashing = 0

    def update(self, tilemap):
        movement = ((self.lateral_movement[1] - self.lateral_movement[0]), 0)
        super().update(tilemap, movement=movement)

        if self.dashing > 0:
            self.dashing = max(0, self.dashing - 1)
        if self.dashing < 0:
            self.dashing = min(0, self.dashing + 1)

        if abs(self.dashing) > 50:
            self.velocity[0] = abs(self.dashing) / self.dashing * 5.5
            if abs(self.dashing) == 51:
                self.velocity[0] *= 0.05
            pvelocity = [abs(self.dashing) / self.dashing * random.random(), 0]
            self.game.particles.append(Particle(self.game, self.rect().center, "dash", pvelocity, frame=random.randint(0, 7)))

        if self.velocity[1] >= 0:
            self.jump_effect = False

        self.air_time += 1
        self.jump_buffer = max(0, self.jump_buffer - 1)

        if self.jump_buffer:
            self.jump(auto=True)

        if self.collisions["down"]:
            self.air_time = 0
            self.jumps = 1
        else:
            if self.air_time > 10:
                self.jumps = 0

        if (self.collisions['right'] or self.collisions['left']) and self.air_time > 4 and self.velocity[1] > 0:
            self.wall_slide += 1
            self.slide_counter += 1
            self.slide_counter %= 2

            if self.slide_counter == 1:
                self.velocity[1] = 1
            else:
                self.velocity[1] = 0

            if self.collisions['right']:
                self.flip = False
            else:
                self.flip = True
            self.set_action('wall_slide')
        else:
            self.wall_slide = 0

        if self.wall_slide < 1:
            self.slide_counter = 0
            if self.air_time > 4 and self.velocity[1] < 0:
                self.set_action("rising")
            elif self.air_time > 8 and self.velocity[1] > 0:
                self.set_action("falling")
            elif movement[0] != 0:
                self.set_action("run")
            else:
                self.set_action("idle")

    def render(self, surf, offset=(0, 0)):
        if abs(self.dashing) < 50: super().render(surf, offset=offset)

    def jump(self, auto=False) -> bool:
        condition = False
        for key in [pygame.K_SPACE, pygame.K_w, pygame.K_UP]:
            if key in self.game.keys: condition = True
        if self.wall_slide > 1 and condition:
            direction = 1 if self.last_movement[0] < 0 else -1
            self.velocity[0] = 2 * direction
            self.velocity[1] = -2
            self.jump_effect = True
            self.air_time = 5
            self.jumps = max(0, self.jumps - 1)
            if direction == 1:
                self.game.particles.append(Particle(self.game, (self.pos[0], self.pos[1] - 4), "wall_impact"))
            else:
                self.game.particles.append(Particle(self.game, (self.pos[0] - 3, self.pos[1] - 4), "wall_impact", flip=True))
            return True

        if self.jumps and condition:
            self.velocity[1] = -2.5
            self.jump_effect = True
            self.jumps -= 1
            self.air_time = 5
            self.game.particles.append(Particle(self.game, (self.pos[0] - 5, self.pos[1] + 5), "impact"))
            return True

        if not auto:
            self.jump_buffer = 13
        
        return False
    
    # reduce velocity to reduce jump height
    def vary_jump(self):
        if self.jump_effect == True:
            self.velocity[1] = max(-.5, self.velocity[1])
            self.jump_effect = False
    
    def dash(self):
        if not self.dashing:
            if self.flip:
                self.dashing = -60
            else:
                self.dashing = 60

class Elf(PhysicsEntity):
    def __init__(self, game, pos, flip=False):
        super().__init__(game, "elf", pos, size=(5, 11))
        self.lateral_movement = [False, False] # running left and right
        self.OG_flip = flip # make the elf face the way it was originally facing
        self.flip = flip
        self.vision_range = 80
        self.chasing = 0
        self.walk_tick = 0
        self.wait_tick = 0
        self.flip_count = 0

    def vision_rect(self): # what the elf can see, if the player hits this box the elf can see the player.
        return pygame.Rect(self.pos[0] - (self.vision_range-self.size[0])*self.flip, min(math.ceil((self.pos[1])-28), math.floor(self.pos[1])-28), self.vision_range, 50)

    def update(self, tilemap):
        self.walk_tick = (self.walk_tick + 1) % 2 # make elf walk slower than player
        movement = (self.lateral_movement[1] - self.lateral_movement[0], 0)
        super().update(tilemap, movement=movement if self.walk_tick else [0,0])

        if pygame.Rect.colliderect(self.game.player.rect(), self.rect()) and abs(self.game.player.dashing) < 50:
            self.game.death_flag = True

        if pygame.Rect.colliderect(self.game.player.rect(), self.vision_rect()):
            if self.chasing == 0 or self.chasing == 2:
                self.game.particles.append(Particle(self.game, (self.pos[0]-1, self.pos[1]-12), "spotted"))
            self.chasing = 1
        elif self.chasing == 1: # was chasing, but no longer in sight.
            self.game.particles.append(Particle(self.game, (self.pos[0]-1, self.pos[1]-12), "confused"))
            self.chasing = 2

        self.lateral_movement = [False, False]
        if self.chasing == 1:
            if self.game.player.pos[0] < self.pos[0]:
                self.lateral_movement[0] = True
                self.flip = True
            if self.game.player.pos[0] > self.pos[0]:
                self.lateral_movement[1] = True
                self.flip = False
        if self.chasing == 2:
            self.wait_tick = (self.wait_tick + 1) % 30
            if not self.wait_tick:
                self.flip = not self.flip
                self.flip_count += 1
                if self.flip_count == 4:
                    self.flip_count = 0
                    self.chasing = 0
                    self.flip = self.OG_flip

        # make sure the elf doesn't walk off the edge.
        tile_loc = (int(self.pos[0] // self.game.tilemap.tile_size), int(self.pos[1] // self.game.tilemap.tile_size))
        tile_loc2 = str(tile_loc[0]+1) + ";" + str(tile_loc[1]+2)
        if self.lateral_movement[0]: tile_loc2 = str(tile_loc[0]) + ";" + str(tile_loc[1]+2)

        a = self.game.player.pos
        b = self.pos
        if not (tile_loc2 in self.game.tilemap.tilemap and self.game.tilemap.tilemap[tile_loc2]["group"] in self.game.tilemap.PHYSICS_TILES) \
            and not ((a[0] - b[0])**2 + (a[1] - b[1])**2)**(1/2) < 20:
            self.lateral_movement = [False, False]

        if movement[0] != 0: self.set_action("run")
        else: self.set_action("idle")

    def render(self, surf, offset=(0, 0)):
        super().render(surf, offset=offset)
        rec = self.vision_rect()

        vision_surf = pygame.Surface(rec.size)
        vision_surf.fill((255,0,0))
        # UNCOMMENT TO SEE THE VISION BOX
        # surf.blit(vision_surf, ((rec.x - offset[0]), (rec.y - offset[1])))

# a class of entities that keep track of if they're touching player
class InteractEntity:
    def __init__(self, game, asset_id, pos, anim=True):
        self.game = game
        self.asset_id = asset_id
        self.pos = list(pos)
        if anim:
            self.action = ""
            self.set_action("idle")
            self.size = self.animation.images[0].get_size()
        
        self.anim_offset = [0, 0]
        self.colliding = False
        self.flip = False

    def rect(self):
        return pygame.Rect((self.pos[0]), (self.pos[1]), self.size[0], self.size[1])

    def set_action(self, action):
        if action != self.action:
            self.action = action
            self.animation = self.game.assets[self.asset_id + "!" + self.action][0].copy()

    def update(self):
        self.animation.update()
        self.anim_offset = self.animation.anim_offset.copy()
        
        if pygame.Rect.colliderect(self.game.player.rect(), self.rect()):
            self.colliding = True
        else:
            self.colliding = False

    def render(self, surf, offset=(0, 0)):
        surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False), (round(self.pos[0] - offset[0] + self.anim_offset[0]), round(self.pos[1] - offset[1] + self.anim_offset[1])))

# it was originally going to be a door but I opted for a portal since it fits the theme kinda?
class Door(InteractEntity):
    def __init__(self, game, pos):
        super().__init__(game, "door", pos)
        self.particles = []
        
    def update(self):
        super().update()
        
        if self.colliding and self.game.interacting == True:
            if self.game.player.holding_globe:
                self.game.interacting = False
                self.game.level = min(len(os.listdir("data/maps"))-1, self.game.level+1)
                self.game.transition(text(self.game.assets["font"][0], desiredText="", color=(255, 255, 255), scale=5), 0, advance=True)
            else:
                text1 = text(self.game.assets["font"][0], desiredText="Obtain the snowglobe first!", scale=4, color=(255, 255, 255))
                renderPos = (5, self.game.DS[1] - text1.get_height() - 2)
                self.game.game_text.append([text1, renderPos, 60])
    
    def render(self, surf, offset=(0, 0)):
        surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False), (self.pos[0] - offset[0] + self.anim_offset[0], self.pos[1] - offset[1] + self.anim_offset[1]))
        if self.colliding:
            text1 = text(self.game.assets["font"][0], desiredText="[E]", scale=4, color=(255, 255, 255))
            displayScale = (self.game.display.get_size()[0] / self.game.canvas.get_size()[0])
            renderPos = ((self.pos[0] - offset[0] + 0.5) * displayScale + text1.get_size()[0]/displayScale, (self.pos[1] - offset[1] - 8) * displayScale)
            self.game.game_text.append([text1, renderPos, 1])
        
# snowglobe entity
class Snowglobe(InteractEntity):
    def __init__(self, game, pos):
        super().__init__(game, "snowglobe", pos)
        self.collected = False
    def update(self):
        super().update()
        if self.colliding and not self.collected:
            self.collected = True
            self.game.player.holding_globe = True
            self.game.particles.append(Particle(self.game, (self.pos[0]-10, self.pos[1]-12), "obtain"))
    def render(self, surf, offset):
        if not self.collected:
            super().render(surf, offset)

# spikes that kill the player
class Spike:
    def __init__(self, game, pos, orientation):
        self.game = game
        self.pos = list(pos)
        
        self.anim_offset = [0, 0]
        self.flip = False

        self.image = self.game.assets["spike-"+str(orientation-1)][0].copy()
        self.size = self.image.get_size()

    def rect(self):
        return pygame.Rect((self.pos[0]), (self.pos[1]), self.size[0], self.size[1])

    def update(self):
        if pygame.Rect.colliderect(self.game.player.rect(), self.rect()):
            self.game.death_flag = True

    def render(self, surf, offset=(0, 0)):
        surf.blit(self.image, (self.pos[0] - offset[0], self.pos[1] - offset[1]))
        # pygame.draw.rect(surf, (0,255,255), (self.pos[0] - offset[0], self.pos[1] - offset[1], self.size[0], self.size[1]))

# this is a class with an animation, that can die if the animation is over.
# used for player jump particles, dash particles, death particles, obtaining snowglobe particles
# also used for guide screen
class Particle:
    def __init__(self, game, pos, img_name, vel=[0, 0], frame=0, flip=False):
        self.game = game
        self.pos = list(pos)
        self.animation = self.game.assets["particle!" + img_name][0].copy()
        self.animation.frame = frame
        self.size = self.animation.images[0].get_size()
        self.velocity = vel
        self.img_name = img_name
        self.flip = flip
    
    def update(self):
        self.animation.update()
        self.pos[0] += self.velocity[0]
        self.pos[1] += self.velocity[1]

    def render(self, surf, offset=(0, 0)):
        surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False), (self.pos[0] - offset[0], self.pos[1] - offset[1]))