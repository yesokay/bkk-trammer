#!/usr/bin/env python

import pygame
import sys, time, os, requests

from pygame.locals import *
from datetime import datetime
# from pitftgpio import PiTFT_GPIO

# # These go in for PiTFT
# os.environ["SDL_FBDEV"] = "/dev/fb1"
# os.environ["SDL_MOUSEDEV"] = "/dev/input/touchscreen"
# os.environ["SDL_MOUSEDRV"] = "TSLIB"

pygame.init()
# pygame.mouse.set_visible(0) # hide cursor
fpsClock = pygame.time.Clock() # Lowers CPU load by setting max frame rate by "ticking"

screen = pygame.display.set_mode((320,240))
pygame.display.set_caption('Trammer')



''' Globals '''

# Schedule
minutes = 60 # Arrivals in the next X minutes
stop_id = 'BKK_F01343' # Zsil utca

updated_at = 0
schedule = []
next_text = None
later_text = None


# Colors
black = pygame.Color(0,0,0)
white = pygame.Color(255,255,255)
yellow = pygame.Color(255,211,0)
blue = pygame.Color(74,144,226)

# Resources
tram_icon = pygame.image.load('resources/icon-tram-32x32.png')
rounded_label = pygame.image.load('resources/rounded-label-42x32.png')
clock_font = pygame.font.Font('resources/OpenSans-Regular.ttf', 24)
label_font = pygame.font.Font('resources/OpenSans-Bold.ttf', 22)
next_font = pygame.font.Font('resources/OpenSans-Bold.ttf', 64)
later_font = pygame.font.Font('resources/OpenSans-Regular.ttf', 26)



''' Functions '''
def blit_clock():
    time_now = str(datetime.now().strftime('%H:%M'))

    clock_display = clock_font.render(time_now, True, white, black)
    clock_block = clock_display.get_rect()
    clock_block.bottomright = (310, 230)
    
    pygame.draw.rect(screen, black, (clock_block.right - 48, clock_block.top, 48, clock_block.height)) # prevent old text hangover
    screen.blit(clock_display, clock_block)


def blit_schedule():
    global schedule, next_text, later_text

    def mins_left(t):
        ml = int((t - time.time()) / 60)
        return str(ml)

    if not schedule:
        next_text = ''
        later_text = ''
    else:
        upnext = [mins_left(x) for x in schedule if x - time.time() > 45]
        next_text = upnext[0] + ' min'
        later_text = ', '.join(x + ' min' for x in upnext[1:3])

    next_display = next_font.render(next_text, True, white, black)
    next_block = next_display.get_rect()
    next_block.center = (160,80)

    later_display = later_font.render(later_text, True, white, black)
    later_block = later_display.get_rect()
    later_block.center = (160, 128)

    pygame.draw.rect(screen, black, (0, next_block.top, 320, later_block.bottom - next_block.top)) # prevent old text hangover
    screen.blit(next_display, next_block)
    screen.blit(later_display, later_block)



def check_schedule(minutes, stop_id):
    global updated_at, schedule

    def fetch_data():
        global updated_at, schedule

        api_data = get_schedule(duration = minutes, stop_id = stop_id)
        if not api_data:
            return

        del schedule[:]
        for arrival in api_data['data']['entry']['stopTimes']:
            if 'predictedArrivalTime' in arrival.keys():
                schedule.append(arrival['predictedArrivalTime'])
            else:
                schedule.append(arrival['departureTime'])

        updated_at = time.time()


    if not schedule:
        if time.time() - updated_at < 600:
            return
        else:
            fetch_data()
            return

    if schedule[0] - time.time() < 0:
        fetch_data()



def get_schedule(stop_id, duration = 30):
    p = { 'includeReferences': 'routes,trips,stops', # Knocked out: agencies
          'stopId': stop_id,
          'minutesBefore': 0,
          'minutesAfter': duration }

    r = requests.get('http://futar.bkk.hu/bkk-utvonaltervezo-api/ws/otp/api/where/arrivals-and-departures-for-stop.json', params = p)
    if r.status_code != 200:
        return None

    return r.json()


def get_weather():
    return (12, 'cloudy')


def draw_label(text, color):
    screen.blit(tram_icon, (10, 197)) # Should move this to the function too

    label_rect = pygame.Rect(48, 197, 42, 32)
    pygame.draw.rect(screen, color, label_rect)
    screen.blit(rounded_label, label_rect)

    label_display = label_font.render(text, True, black, color)
    label_block = label_display.get_rect()
    label_block.midtop = label_rect.midtop

    screen.blit(label_display, label_block)



''' Draw label '''
draw_label('2', yellow)


''' Main loop '''
while True:
    
    for event in pygame.event.get():
        if event.type == QUIT:
            sys.exit()

    p = pygame.key.get_pressed()
    if p[K_ESCAPE]:
        pygame.quit()
        sys.exit(0)

    # pitft = PiTFT_GPIO()
    # if pitft.Button3: # My GPIOs are quite fucked
    #     pygame.quit()
    #     sys.exit(0)

    blit_clock()
    check_schedule(minutes, stop_id)
    blit_schedule()

    pygame.display.update()
    fpsClock.tick(12)

