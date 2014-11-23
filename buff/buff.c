#include <stdlib.h>
#include <stdio.h>
#include <bcm2835.h>

extern int init();
extern void deinit();
extern void fling_buffer(char *buffer);

#define PIN_CS_B 24  /* chip select, active low */
#define PIN_RST_B 17 /* reset, active low */
#define PIN_A0 22    /* register select, high=display, low=control */
#define PIN_SCLK 27  /* serial input clock */
#define PIN_SID 23   /* serial input data */
#define PINS {PIN_CS_B, PIN_RST_B, PIN_A0, PIN_SCLK, PIN_SID}

#define PAGE_COUNT 8
#define COL_COUNT 128
#define PIXEL_COUNT (PAGE_COUNT*COL_COUNT*8)
#define DITH_AMT 101
#define LEFT_OVERSCAN 4

#define send_byte(byte)                                                        \
for (int which_lcd_bit=0; which_lcd_bit<8; which_lcd_bit++) {                  \
	bcm2835_gpio_write(PIN_SID, ((byte) << which_lcd_bit) & 0x80);             \
	bcm2835_delayMicroseconds(1);       /* T[DSS] data setup time and */       \
	                                    /* T[WLS] SCLK low pulse width. */     \
	bcm2835_gpio_write(PIN_SCLK, HIGH); /* SCLK's rising edge separated. */    \
	bcm2835_delayMicroseconds(1);       /* T[DHS] data hold time and */        \
	                                    /* T[WHS] SCLK high pulse width. */    \
	bcm2835_gpio_write(PIN_SCLK, LOW);                                         \
} /* These also satisfy the hold and setup timings for A0 and CS_B. */

#define page_jump_cmd(page)        (page | 0xb0)
#define col_jump_cmd_high(col)     ((col >> 4) | 0x10)
#define col_jump_cmd_low(col)      (col & 0x0f)


int init()
{
	if (bcm2835_init() == 0) {
		return 0;
	}
	
	/* Init all pins: low output. "_B" is a convention meaning "active low". */
	/* PIN_CS_B unused; pulling it high could stop the LCD from listening. */
	uint8_t pins[] = PINS;
	for (int i=0; i<5; i++) {
		bcm2835_gpio_fsel(pins[i], BCM2835_GPIO_FSEL_OUTP);
		bcm2835_gpio_write(pins[i], LOW);
	}
	
	bcm2835_delayMicroseconds(1); /* RST_B low pulse width */
	bcm2835_gpio_write(PIN_RST_B, HIGH);
	bcm2835_delayMicroseconds(1); /* t[R]: reset time */
	
	send_byte(0xaf);   /*  1. display on (0xaf) or off (0xae)                 */
	//send_byte(0x40); /*  2. first display line (0x40 | 6 bits)              */
	send_byte(0xa1);   /*  8. LCD scan normal (0xa0) or reverse (0xa1)        */
	send_byte(0xa7);   /*  9. normal 1=white (0xa7) or reverse 1=black (0xa6) */
	//send_byte(0xa4); /* 10. every pixel black (0xa5) or not (0xa4)          */
	send_byte(0xa3);   /* 11. LCD voltage bias 1/9 (0xa2) or 1/7 (0xa3)       */
	//send_byte(0xe2); /* 14. reset, not inc memory or LCD power              */
	//send_byte(0xc0); /* 15. LCD scan downwards (0xc0) or upwards (0xc8)     */
	send_byte(0x2f);   /* 16. internal power supply mode:
	                      0x28 | 0x04 (internal voltage converter circuit)
	                           | 0x02 (internal voltage regulator circuit)
	                           | 0x01 (internal voltage follower circuit)     */
	send_byte(0x22);   /* 17. resistor ratio:
	                          0x20 | (3 bits) such that (1 + Rb/Ra) =
	                          3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.4          */
	send_byte(0x81);   /* 18. reference voltage (2 byte command)              */
	send_byte(47);     /*     low contrast (0) to high contrast (63)          */
	
	return 1;
}


void deinit()
{
	uint8_t pins[] = PINS;
	for (int i=0; i<5; i++) {
		bcm2835_gpio_write(pins[i], LOW);
		bcm2835_gpio_fsel(pins[i], BCM2835_GPIO_FSEL_INPT);
	}
}


/* one byte per pixel please ... we only use the most sig bit */
void fling_buffer(char *buffer)
{
	char page_content;
	int buf_offset;
	
	for (char page=0; page<PAGE_COUNT; page++) {
		/* only need to issue jump instructions once */
		/* because every display data increments the col counter */
		bcm2835_gpio_write(PIN_A0, LOW);
		send_byte(page_jump_cmd(page));
		send_byte(col_jump_cmd_high(LEFT_OVERSCAN));
		send_byte(col_jump_cmd_low(LEFT_OVERSCAN));
		
		//lcd_jump(page, 4); // jump to the "first" column of this page
		
		bcm2835_gpio_write(PIN_A0, HIGH); // prepare for data!
		for (char col=0; col<COL_COUNT; col++) {		
			page_content = 0;
			
			for (char bit=0; bit<8; bit++) {
				buf_offset = page*COL_COUNT*8 + col + bit*COL_COUNT;
				page_content >>= 1;
				page_content |= buffer[buf_offset] & 0x80;
			} // bit
			
			send_byte(page_content);
		} // col
	} // page
} // fling_buffer


/* World's Ugliest Test Pattern:
   A dithered horizontal gradient (dark on the left)
   with black lines along the top and right edges. */
int main(int argc, char **argv)
{
 	if (init() == 0) {
 		return 1;
 	}
	
	/* fill DITH_AMT screens' worth of memory with fuzz */
	char rand_buffer[PIXEL_COUNT*DITH_AMT];
	
	char rand_char;
	srand(0x12345678);
	for (int i=0; i<PIXEL_COUNT*DITH_AMT; i++) {
		rand_char = rand() & 0xff;
		/* I think this will allow for full white and full black?? */
		//rand_char = rand_char<128 ? rand_char : rand_char-1;
		rand_buffer[i] = rand_char;
	}
	
	/* do up a test pattern in glorious 8-bit monochrome */
	char pic_buffer[PIXEL_COUNT];
	
	for (int px=0; px<PIXEL_COUNT; px++) {
		if ((px < COL_COUNT) || (px%COL_COUNT == 127)) {
			pic_buffer[px] = 0;
		} else if (px >= COL_COUNT*63) {
			pic_buffer[px] = 255;
		} else {
			pic_buffer[px] = (px%COL_COUNT) * 2;
		}
	}
	
	char buffer[PIXEL_COUNT];
	
	int rand_offset = 0;
	for (int i=0; i<300; i++) {
		rand_offset += 5345; /* seriously just made this up */
		rand_offset %= PIXEL_COUNT * (DITH_AMT-1);
		
		for (int px=0; px<PIXEL_COUNT; px++) {
			buffer[px] = (rand_buffer[px+rand_offset] < pic_buffer[px]) << 7;
		}
		
		fling_buffer(buffer);
	}
 	
	deinit();
	return 0;
}
