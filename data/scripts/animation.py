# animation.py
# a class that stores images used in an independent animation
# it helps with figuring out which image to display in an animation
# NOT WRITTEN BY ME

from .utils import *

class Animation:
    def __init__(self, images, img_dur=5, anim_offset=[0, 0], loop=True):
        self.images = images
        self.img_duration = img_dur
        self.loop = loop
        self.done = False
        self.frame = 0
        self.anim_offset = anim_offset

    def copy(self):
        return Animation(self.images, self.img_duration, self.anim_offset, self.loop)

    def update(self):
        if self.loop:
            self.frame = (self.frame + 1) % (self.img_duration * len(self.images))
        else:
            self.frame = min(self.frame + 1, self.img_duration * len(self.images) - 1)
            if self.frame >= self.img_duration * len(self.images) - 1:
                self.done = True

    def img(self):
        cf = self.frame / self.img_duration
        cf = int(cf % (len(self.images)))
        return self.images[cf]