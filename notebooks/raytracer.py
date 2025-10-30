"""
MIT License

Copyright (c) 2017 Cyrille Rossant

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import numpy as np
from PIL import Image  # Addition by @ianthomas23 for JupyterCon 2025 subshell talk

class RayTracer:
    def __init__(self, width=400, height=300):
        self.w = width
        self.h = height
        self.rgb = np.zeros((self.h, self.w, 3))
        #self.rgba = np.zeros((self.h, self.w), dtype=np.uint32)

        # List of objects.
        self.color_plane0 = 1. * np.ones(3)
        self.color_plane1 = 0. * np.ones(3)
        self.scene = [
            self.add_sphere([.75, .1, 1.], .6, [0., 0., 1.]),
            self.add_sphere([-.75, .1, 2.25], .6, [.5, .223, .5]),
            self.add_sphere([-2.75, .1, 3.5], .6, [1., .572, .184]),
            self.add_plane([0., -.5, 0.], [0., 1., 0.]),
        ]

        # Light position and color.
        self.L = np.array([5., 5., -10.])
        self.color_light = np.ones(3)

        # Default light and material parameters.
        self.ambient = .05
        self.diffuse_c = 1.
        self.specular_c = 1.
        self.specular_k = 50

        self.O = np.array([0., 0.35, -1.])  # Camera.
        self.Q = np.array([0., 0., 0.])  # Camera pointing to.

        self.depth_max = 5  # Maximum number of light reflections.
        self.col = np.zeros(3)  # Current color.

        r = float(self.w) / self.h
        # Screen coordinates: x0, y0, x1, y1.
        self.S = (-1., -1. / r + .25, 1., 1. / r + .25)

        self.completed = False

    def normalize(self, x):
        x /= np.linalg.norm(x)
        return x

    def intersect_plane(self, O, D, P, N):
        # Return the distance from O to the intersection of the ray (O, D) with the
        # plane (P, N), or +inf if there is no intersection.
        # O and P are 3D points, D and N (normal) are normalized vectors.
        denom = np.dot(D, N)
        if np.abs(denom) < 1e-6:
            return np.inf
        d = np.dot(P - O, N) / denom
        if d < 0:
            return np.inf
        return d

    def intersect_sphere(self, O, D, S, R):
        # Return the distance from O to the intersection of the ray (O, D) with the
        # sphere (S, R), or +inf if there is no intersection.
        # O and S are 3D points, D (direction) is a normalized vector, R is a scalar.
        a = np.dot(D, D)
        OS = O - S
        b = 2 * np.dot(D, OS)
        c = np.dot(OS, OS) - R * R
        disc = b * b - 4 * a * c
        if disc > 0:
            distSqrt = np.sqrt(disc)
            q = (-b - distSqrt) / 2.0 if b < 0 else (-b + distSqrt) / 2.0
            t0 = q / a
            t1 = c / q
            t0, t1 = min(t0, t1), max(t0, t1)
            if t1 >= 0:
                return t1 if t0 < 0 else t0
        return np.inf

    def intersect(self, O, D, obj):
        if obj['type'] == 'plane':
            return self.intersect_plane(O, D, obj['position'], obj['normal'])
        elif obj['type'] == 'sphere':
            return self.intersect_sphere(O, D, obj['position'], obj['radius'])

    def get_normal(self, obj, M):
        # Find normal.
        if obj['type'] == 'sphere':
            N = self.normalize(M - obj['position'])
        elif obj['type'] == 'plane':
            N = obj['normal']
        return N

    def get_color(self, obj, M):
        color = obj['color']
        if not hasattr(color, '__len__'):
            color = color(M)
        return color

    def trace_ray(self, rayO, rayD):
        # Find first point of intersection with the scene.
        t = np.inf
        for i, obj in enumerate(self.scene):
            t_obj = self.intersect(rayO, rayD, obj)
            if t_obj < t:
                t, obj_idx = t_obj, i
        # Return None if the ray does not intersect any object.
        if t == np.inf:
            return
        # Find the object.
        obj = self.scene[obj_idx]
        # Find the point of intersection on the object.
        M = rayO + rayD * t
        # Find properties of the object.
        N = self.get_normal(obj, M)
        color = self.get_color(obj, M)
        toL = self.normalize(self.L - M)
        toO = self.normalize(self.O - M)
        # Shadow: find if the point is shadowed or not.
        l = [self.intersect(M + N * .0001, toL, obj_sh)
                for k, obj_sh in enumerate(self.scene) if k != obj_idx]
        if l and min(l) < np.inf:
            return
        # Start computing the color.
        col_ray = self.ambient
        # Lambert shading (diffuse).
        col_ray += obj.get('diffuse_c', self.diffuse_c) * max(np.dot(N, toL), 0) * color
        # Blinn-Phong shading (specular).
        col_ray += obj.get('specular_c', self.specular_c) * max(np.dot(N, self.normalize(toL + toO)), 0) ** self.specular_k * self.color_light
        return obj, M, N, col_ray

    def add_sphere(self, position, radius, color):
        return dict(type='sphere', position=np.array(position),
            radius=np.array(radius), color=np.array(color), reflection=.5)

    def add_plane(self, position, normal):
        return dict(type='plane', position=np.array(position),
            normal=np.array(normal),
            color=lambda M: (self.color_plane0
                if (int(M[0] * 2) % 2) == (int(M[2] * 2) % 2) else self.color_plane1),
            diffuse_c=.75, specular_c=.5, reflection=.25)

    def reset(self):
        self.completed = False
        self.rgb.fill(0)

    def single_pixel(self, i, j):
        x = self.S[0] + (self.S[2] - self.S[0])*i / (self.w-1)
        y = self.S[1] + (self.S[3] - self.S[1])*j / (self.h-1)
        self.col[:] = 0
        self.Q[:2] = (x, y)
        D = self.normalize(self.Q - self.O)
        depth = 0
        rayO, rayD = self.O, D
        reflection = 1.
        # Loop through initial and secondary rays.
        while depth < self.depth_max:
            traced = self.trace_ray(rayO, rayD)
            if not traced:
                break
            obj, M, N, col_ray = traced
            # Reflection: create a new ray.
            rayO, rayD = M + N * .0001, self.normalize(rayD - 2 * np.dot(rayD, N) * N)
            depth += 1
            self.col += reflection * col_ray
            reflection *= obj.get('reflection', 1.)
        rgb_float = np.clip(self.col, 0, 1)
        self.rgb[self.h - j - 1, i] = rgb_float

        #rgb = (rgb_float*255).astype(np.uint8)
        #self.rgba[j, i] = (255 << 24) | (rgb[2] << 16) | (rgb[1] << 8) | (rgb[0])

    def run_scan(self):
        self.completed = False
        self.rgb.fill(0)
        for i in range(self.w):
            for j in range(self.h):
                self.single_pixel(i, j)
        self.completed = True

    def run_random(self):
        self.completed = False
        self.rgb.fill(0)
        i, j = np.meshgrid(np.arange(self.w), np.arange(self.h))
        ijs = np.column_stack((i.ravel(), j.ravel()))
        rng = np.random.default_rng(2184)
        rng.shuffle(ijs)
        for i, j in ijs:
            self.single_pixel(i, j)
        self.completed = True

    # Addition by @ianthomas23 for JupyterCon 2025 subshell talk
    def as_image(self):
        return Image.fromarray((self.rgb*255).astype(np.uint8))
