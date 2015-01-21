# This file is part of bling.

# Bling is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Bling is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Bling.  If not, see <http://www.gnu.org/licenses/>.

import bling_core
import bling_uikit
import pygame

global alarm_backend

class AlarmBackend:
    def __init__(self):
        "Load everything from the crontab and elsewhere"
    
    def set_alarm(self, days=[1, 2, 3, 4, 5], type="analog", hrs=0, mins=0):
        # type = "off", "analog" or "digital"
        if type == "digital":
            print("Alarm: digital for days %s: %02d:%02d" % (str(days), hrs, mins))
        else:
            print("Alarm: %s for days %s" % (type, str(days)))
    
    def get_alarm(self, day):
        # returns a one- or three-item tuple: (type, [ mins, hrs ])
        "blah"

class TimeChooser(bling_core.Client):
    def _setup(self, graf_props, notifier=None, title="Choose time:"):
        self.notifier = notifier
        self.title = title
        
        self.hours = 7
        self.minutes = 0
        self.mode = 0
        
        self.small_font = pygame.freetype.Font("chicago.bdf")
        self.large_font = pygame.freetype.Font("chicago.ttf", 36)
        self.small_font.origin = self.large_font.origin = True
        self.small_font.antialiased = self.large_font.antialiased = False
        
        lg_rect = self.large_font.get_rect("12")
        self.min_x_pos = 80 # graf_props[0] // 2
        self.min_hour_gap = 20
        self.y_gap = (graf_props[1] - lg_rect[1]) // 2 + 7
        self.lg_origin = self.y_gap + lg_rect[1]
        
        ampm_rect = self.small_font.get_rect("am")
        self.ampm_x = self.min_x_pos - self.min_hour_gap - lg_rect[2] - 0 - ampm_rect[2]
        self.pm_origin = self.y_gap + 7
        self.am_origin = self.pm_origin + 10
    
    def _event(self, event):
        if event == "up" or event == "down":
            if self.mode == 1:
                if event == "up" and self.minutes < 55:
                    self.minutes += 5
                if event == "down" and self.minutes > 0:
                    self.minutes -= 5
                return True
                
            elif self.mode == 0:
                if event == "up" and self.hours < 23:
                    self.hours += 1
                if event == "down" and self.hours > 0:
                    self.hours -= 1
                return True
        
        elif event == "ok":
            if self.mode == 0:
                self.mode = 1
                return True
                
            elif self.mode == 1:
                if self.notifier != None:
                    self.notifier(self.hours, self.minutes)
                self.parent_server.remove_client(self)
                return False
        
        elif event == "back":
            if self.mode == 1:
                self.mode = 0
                return True
                
            elif self.mode == 0:
                self.parent_server.remove_client(self)
                return None
        
        else:
            return None
    
    def __draw_arrow(self, surface, x, y, s=1):
        sz = 3
        pygame.draw.line(surface, (0,0,0), (x-sz, y), (x, y+sz*s), 2)
        pygame.draw.line(surface, (0,0,0), (x+sz, y), (x, y+sz*s), 2)
    
    def _draw_frame(self, buffer, is_initial):
        bc = (255, 255, 255)
        tc = (0, 0, 0)
        
        if is_initial:
            buffer.fill(bc)
            
            title = self.title.upper()
            title_width = self.small_font.get_rect(title)[2]
            title_pos = ((self.width - title_width) // 2, 9)
            self.small_font.render_to(buffer, title_pos, title, fgcolor=tc, bgcolor=bc)
            
            pygame.draw.line(buffer, tc, (0, 10), (self.width, 10))
        
        else:
            buffer.fill(bc, rect=(0, 11, self.width, self.height - 11))
        
        show_ampm = True
        
        if self.hours == 0:
            draw_hours = "12"
        elif self.hours <= 12:
            draw_hours = str(self.hours)
        elif self.hours <= 23:
            draw_hours = str(self.hours - 12)
        
        draw_minutes = str(self.minutes).zfill(2)
        
        if show_ampm and self.hours >= 13:
            self.small_font.render_to(buffer, (self.ampm_x, self.pm_origin), "pm", fgcolor=tc, bgcolor=bc)
        elif show_ampm and self.hours <= 12:
            self.small_font.render_to(buffer, (self.ampm_x, self.am_origin), "am", fgcolor=tc, bgcolor=bc)
        
        hour_rect = self.large_font.get_rect(draw_hours)
        hour_pos = (self.min_x_pos - self.min_hour_gap - hour_rect[2], self.lg_origin)
        self.large_font.render_to(buffer, hour_pos, draw_hours, fgcolor=tc, bgcolor=bc)
        # buffer.blit(source=no, dest=(64 - no.get_width(), 20))
        
        min_pos = (self.min_x_pos, self.lg_origin)
        self.large_font.render_to(buffer, min_pos, draw_minutes, fgcolor=tc, bgcolor=bc)
        # buffer.blit(source=no, dest=(64, 20))
        
        if self.mode == 0:
            if self.hours < 23:
                self.__draw_arrow(buffer, 50, 22, -1)
            if self.hours > 0:
                self.__draw_arrow(buffer, 50, 54, 1)
        elif self.mode == 1:
            if self.minutes < 55:
                self.__draw_arrow(buffer, 103, 22, -1)
            if self.minutes > 0:
                self.__draw_arrow(buffer, 103, 54, 1)


class AlarmsMenu(bling_uikit.ProtoMenu):
    def _setup(self, graf_props):
        spc = "  "
        day_tuples = [
            ("every day", "Every day>",  "Daily alarm:"),
            ("weekdays",  "Weekdays>",   "Weekday alarm:"),
            ("weekends",  "Weekends>",   "Weekend alarm:"),
            ("monday",    "Monday>",     "Monday alarm:"),
            ("tuesday",   "Tuesday>",    "Tuesday alarm:"),
            ("wednesday", "Wednesday>",  "Wednesday alarm:"),
            ("thursday",  "Thursday>",   "Thursday alarm:"),
            ("friday",    "Friday>",     "Friday alarm:"),
            ("saturday",  "Saturday>",   "Saturday alarm:"),
            ("sunday",    "Sunday>",     "Sunday alarm:"),
        ]
        
        def create_alarmtypemenu_spawner_for_day(day):
            def alarmtypemenu_spawner(server):
                server.add_client(AlarmTypeMenu(graf_props = graf_props, day = day))
            return alarmtypemenu_spawner
        
        items = []
        for day_tuple in day_tuples:
            (day, menu_string, junk) = day_tuple
            alarmtypemenu_spawner = create_alarmtypemenu_spawner_for_day(day)
            items.append((menu_string, alarmtypemenu_spawner))
        
        bling_uikit.ProtoMenu._setup(self, graf_props, items=items, title="Alarms")


class AlarmTypeMenu(bling_uikit.ProtoMenu):
    def _setup(self, graf_props, day):
        day_to_title_and_day_numbers = {
            "every day": ("Daily alarm:",      range(0, 7)),
            "weekdays":  ("Weekday alarm:",    range(0, 5)),
            "weekends":  ("Weekend alarm:",    range(5, 7)),
            "monday":    ("Monday alarm:",     0),
            "tuesday":   ("Tuesday alarm:",    1),
            "wednesday": ("Wednesday alarm:",  2),
            "thursday":  ("Thursday alarm:",   3),
            "friday":    ("Friday alarm:",     4),
            "saturday":  ("Saturday alarm:",   5),
            "sunday":    ("Sunday alarm:",     6),
        }
        title, day_numbers = day_to_title_and_day_numbers[day]
        
        items = []
        
        def timechooser_action(hrs, mins):
            alarm_backend.set_alarm(days = day_numbers, type = "digital", hrs = hrs, mins = mins)
        def timechooser_spawner(server):
            timechooser = TimeChooser(graf_props=graf_props, notifier=timechooser_action, title=title)
            server.add_client(timechooser)
        items.append(("Set digital alarm>", timechooser_spawner))
        
        def use_analog_alarm(server):
            alarm_backend.set_alarm(days = day_numbers, type = "analog")
            server.remove_client(self)
        items.append(("Use analog alarm", use_analog_alarm))
        
        def disable_alarm(server):
            alarm_backend.set_alarm(days = day_numbers, type = "off")
            server.remove_client(self)
        items.append(("Disable alarm", disable_alarm))
        
        bling_uikit.ProtoMenu._setup(self, graf_props, items=items, title=title)
    
    def _event(self, event):
        if event == "covered":
            self.parent_server.remove_client(self, anim_duration_ms=0)
            return False
        else:
            return bling_uikit.ProtoMenu._event(self, event)
