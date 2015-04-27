#!/usr/bin/env python
from __future__ import print_function

import argparse
from subprocess import check_output

def wmctrl(*options, **kwargs):
    options = list(options)
    options.insert(0, 'wmctrl')
    return check_output(options, **kwargs)

def desktop():
    for line in wmctrl('-d').decode('utf-8').split('\n'):
        info = list(filter(None, line.split('  ')))
        if info and info[1].startswith('* '):
            return dict(zip(['w', 'h'], map(int, info[3].split(' ')[2].split('x'))))

def current():
    return check_output(['xprop', '-root', '32x', '\t$0', '_NET_ACTIVE_WINDOW']).decode('utf-8').split()[1]

def taylor(direction):
    desktop_geometry = desktop()
    geometry = {'g': 0, 'x': 0, 'y': 0, 'w': desktop_geometry['w'], 'h': desktop_geometry['h']}

    # compute geometry
    if direction == 'N':
        geometry['h'] /= 2
    elif direction == 'NW':
        geometry['w'] /= 2
        geometry['h'] /= 2
    elif direction == 'W':
        geometry['w'] /= 2
    elif direction == 'SW':
        geometry['h'] /= 2
        geometry['w'] /= 2
        geometry['y'] = geometry['h']
    elif direction == 'S':
        geometry['h'] /= 2
        geometry['y'] = geometry['h']
    elif direction == 'SE':
        geometry['w'] /= 2
        geometry['h'] /= 2
        geometry['x'] = geometry['w']
        geometry['y'] = geometry['h']
    elif direction == 'E':
        geometry['w'] /= 2
        geometry['x'] = geometry['w']
    elif direction == 'NE':
        geometry['w'] /= 2
        geometry['h'] /= 2
        geometry['x'] = geometry['w']

    mvarg = '%d,%d,%d,%d,%d' % (geometry['g'], geometry['x'], geometry['y'], geometry['w'], geometry['h'])

    wmctrl('-i', '-r', current(), '-b', 'remove,maximized_horz,maximized_vert')
    wmctrl('-i', '-r', current(), '-e', mvarg)

if __name__ == '__main__':
    import sys

    parser = argparse.ArgumentParser(prog='Taylor', description='Resize the current window')
    parser.add_argument('direction', choices=['N', 'NW', 'W', 'SW', 'S', 'SE', 'E', 'NE', 'F'])
    args = parser.parse_args(map(lambda x: x.upper(), sys.argv[1:]))

    try:
        taylor(args.direction)
    except FileNotFoundError as e:
        print(e)
        print('\nMake sure that wmctrl and xprop are available on your system')

