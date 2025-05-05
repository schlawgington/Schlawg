import numpy as np
import matplotlib.pyplot as plt

def mandelbrot(c, iter):
    z = 0
    for i in range(iter):
        z = z**2 + c
        if abs(z) > 2:
            return i
    return iter

def generator(xmin, xmax, width, ymin, ymax, height, iter):
    xval = np.linspace(xmin, xmax, width)
    yval = np.linspace(ymin, ymax, height)
    mandelbrotset = np.zeros((width, height))

    for i, x in enumerate(xval):
        for j, y in enumerate(yval):
            mandelbrotset[i,j] = mandelbrot(complex(x, y), iter)

    return mandelbrotset

def plotter(settt):
    plt.imshow(settt, extent=[-2, 1.5, -1.5, 1.5], cmap='inferno')
    plt.colorbar()
    plt.show()

width, height = 800, 600
max_iter = 100
data = generator(-2, 1, width, -1.5, 1.5, height, max_iter)
plotter(data)