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

import RPIO
from plumbing import Actor


RADIO_PIN = 2
BUZZ_PIN  = 3

ROTARY_PINS = [4, 14]

SELECT_PIN = 23
BACK_PIN = 18

BANDSW_PIN = 17

BKLT = 24
RPIO.setup(BKLT, RPIO.OUT)
RPIO.output(BKLT, True)



class ClockSwitches(Actor):
    def rotary_setup(self):
        self.rotary_state = [0, 0]
        self.left_home_towards = 99
        
        for pin in ROTARY_PINS:
            RPIO.add_interrupt_callback(pin, self.rotary_callback, edge='both', pull_up_down=RPIO.PUD_DOWN)
    
    def rotary_callback(self, pin, value):
        pin = ROTARY_PINS.index(pin)
        self.rotary_state[pin] = value
        value_other = self.rotary_state[1 - pin]
        
        if value == 1 and value_other == 0: # left Home rotary_position
            self.left_home_towards = pin
            print('left Home rotary_position towards %d' % pin)
        
        elif value == value_other == 0: # returned to Home rotary_position
            if self.left_home_towards == (1 - pin):
                print('returned via %d' % pin)
                self.source.as_input('direction', dy=(1, -1)[pin], kinetic='inst')
            
            self.left_home_towards = 99 #indeterminate
    
    def button_setup(self):
        for pin in [SELECT_PIN, BACK_PIN]:
            RPIO.add_interrupt_callback(pin, self.button_callback, edge='both', pull_up_down=RPIO.PUD_UP)
    
    def button_callback(self, pin, value):
        kinetic = 'in' if value else 'out'
        func = 'select' if pin == SELECT_PIN else 'escape'
        
        self.source.as_input(func, kinetic=kinetic)
    
    def _as_set_source(self, source):
        self.source = source
    
    def _loop(self):
        self._wait_next_event(only=['set_source'])
        
        self.rotary_setup()
        self.button_setup()
        
        RPIO.wait_for_interrupts()
    
    