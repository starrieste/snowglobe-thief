# utils.py
# a bunch of utility functions that help with loading images, and spritesheets

import pygame
import os

from pygame.locals import *

BASE_IMG_PATH = 'data/images/'

# load single image
def load_image(path, colorkey=(0, 0, 0)):
    path = BASE_IMG_PATH + path if not path.startswith("*") else path.replace("*", "")
    img = pygame.image.load(path).convert()
    img.set_colorkey(colorkey)
    return img

# load all images in a directory
def load_images(path):
    images = []
    for img_name in sorted(os.listdir(BASE_IMG_PATH + path)):
        images.append(load_image(path + '/' + img_name))
    return images

# gets a part of an image, used for spritesheet
def clip(surf,x,y,x_size,y_size):
    handle_surf = surf.copy()
    clipR = pygame.Rect(x,y,x_size,y_size)
    handle_surf.set_clip(clipR)
    image = surf.subsurface(handle_surf.get_clip())
    return image.copy()

# swaps colors... THIS IS THE FUNCTION I ACCIDENTALLY DELETED D:
def swap_color(img,old_c,new_c):
    img.set_colorkey(old_c)
    surf = img.copy()
    surf.fill(new_c)
    surf.blit(img,(0,0))
    return surf

# loads an entire spritesheet...
# I don't have the time to go into depth,
# but it uses colors to tell where images begin and end
def load_spritesheet(spritesheet, colorkey=(0, 0, 0), two_d=False):
    rows = []
    sprites = []
    for y in range(spritesheet.get_height()):
        c = spritesheet.get_at((0,y))
        c = (c[0],c[1],c[2])
        if c == (255, 255, 0):
            rows.append(y)
    for row in rows:
        row_content = []
        for x in range(spritesheet.get_width()):
            c = spritesheet.get_at((x,row))
            c = (c[0],c[1],c[2])
            if c == (255,0,255):
                x2 = 0
                while True:
                    x2 += 1
                    c = spritesheet.get_at((x+x2,row))
                    c = (c[0],c[1],c[2])
                    if c == (0,255,255):
                        break
                y2 = 0
                while True:
                    y2 += 1
                    c = spritesheet.get_at((x,row+y2))
                    c = (c[0],c[1],c[2])
                    if c == (0,255,255):
                        break
                img = clip(spritesheet,x+1,row+1,x2-1,y2-1)
                img.set_colorkey(colorkey)
                row_content.append(img)
        sprites.append(row_content)
    if not two_d:
        one_d = []
        for row in sprites:
            for sprite in row:
                one_d.append(sprite)
        return one_d
    return sprites
