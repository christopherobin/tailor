#!/usr/bin/env python
from __future__ import print_function

import argparse
import re
import sys
from subprocess import check_output

def wmctrl(*options, **kwargs):
    options = list(options)
    options.insert(0, 'wmctrl')
    return check_output(options, **kwargs)

def screen_layout():
    screens = []
    for line in check_output(['xrandr']).decode('utf-8').split('\n'):
        if ' connected ' in line:
            info = line.split()[2].split('+')
            res = info[0].split('x')
            screens.append({ 'x': int(info[1]), 'y': int(info[2]), 'w': int(res[0]), 'h': int(res[1])})
    return screens

def window_geometry(window):
    geo = {}
    prog = re.compile('^  (?P<key>[^:]+): (?P<value>.*)$')
    tslt = {'Absolute upper-left X': 'x', 'Absolute upper-left Y': 'y', 'Width': 'w', 'Height': 'h'}
    for line in check_output(['xwininfo', '-id', window, '-stats']).decode('utf-8').split('\n'):
        res = prog.match(line)
        if res and res.group('key') in tslt:
            geo[tslt[res.group('key')]] = int(res.group('value').strip())
    return geo


def desktop(window):
    # get general screen layout
    screens = screen_layout()

    # locate screen where the window is located
    geo = window_geometry(window)

    target = None
    for screen in screens:
        if geo['x'] >= screen['x'] and geo['y'] >= screen['y'] \
                and geo['x'] < (screen['x'] + screen['w']) \
                and geo['y'] < (screen['y'] + screen['h']):
            target = screen

    if not target:
        print('Could not find target screen, aborting ...')
        sys.exit(2)

    # fix height (for example panels on KDE or Gnome)
    work_area = None
    for line in wmctrl('-d').decode('utf-8').split('\n'):
        info = list(filter(None, line.split('  ')))
        if info and info[1].startswith('* '):
            work_area = dict(zip(['w', 'h'], map(int, info[3].split(' ')[2].split('x'))))

    if work_area:
        target['h'] = work_area['h']

    return target

def current():
    return check_output(['xprop', '-root', '32x', '\t$0', '_NET_ACTIVE_WINDOW']).decode('utf-8').split()[1]

def tailor(direction):
    window = current()

    if direction == 'F':
        wmctrl('-i', '-r', window, '-b', 'add,maximized_horz,maximized_vert')
        return

    # retrieve desktop geometry
    geometry = desktop(window)

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
        geometry['y'] += geometry['h']
    elif direction == 'S':
        geometry['h'] /= 2
        geometry['y'] += geometry['h']
    elif direction == 'SE':
        geometry['w'] /= 2
        geometry['h'] /= 2
        geometry['x'] += geometry['w']
        geometry['y'] += geometry['h']
    elif direction == 'E':
        geometry['w'] /= 2
        geometry['x'] += geometry['w']
    elif direction == 'NE':
        geometry['w'] /= 2
        geometry['h'] /= 2
        geometry['x'] += geometry['w']

    mvarg = '0,%d,%d,%d,%d' % (geometry['x'], geometry['y'], geometry['w'], geometry['h'])

    wmctrl('-i', '-r', window, '-b', 'remove,maximized_horz,maximized_vert')
    wmctrl('-i', '-r', window, '-e', mvarg)

if __name__ == '__main__':
    import sys

    parser = argparse.ArgumentParser(prog='Taylor', description='Resize the current window')
    parser.add_argument('direction', choices=['N', 'NW', 'W', 'SW', 'S', 'SE', 'E', 'NE', 'F'])
    args = parser.parse_args(map(lambda x: x.upper(), sys.argv[1:]))

    try:
        tailor(args.direction)
    except FileNotFoundError as e:
        print(e)
        print('\nMake sure that wmctrl and xprop are available on your system')

