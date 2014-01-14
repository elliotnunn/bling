#include <stdlib.h>
#include <bcm2835.h>

// extern int init();
// extern void deinit();
// extern void fling_buffer(char *buffer);

#define CS_PIN 2
#define RST_PIN 3
#define A0_PIN 4
#define CLK_PIN 27
#define SI_PIN 17


#define set_pin(pin, val) bcm2835_gpio_write(pin, val)

#define lcd_byte(byte)                                          \
for (int which_lcd_bit=0; which_lcd_bit<8; which_lcd_bit++) {   \
	set_pin(CLK_PIN, LOW);                                      \
	set_pin(SI_PIN, ((byte) << which_lcd_bit) & 0x80);          \
	set_pin(CLK_PIN, HIGH);                                     \
}

#define lcd_transfer_data(byte, is_data) lcd_byte(byte);

#define lcd_jump(page, col) {             \
	char page_cmd = page | 0xb0;          \
	char col_high = (col >> 4) | 0x10;    \
	char col_low = col & 0x0f;            \
	lcd_byte(page_cmd);                   \
	lcd_byte(col_high);                   \
	lcd_byte(col_low);                    \
}


#define PAGE_COUNT 8
#define COL_COUNT 128


// int main(int argc, char **argv) {
// 	
// 	if (init() == 0) {
// 		return 1;
// 	}
// 	
// 	srand(time(NULL));
// 	char buf_frame[8448];
// 	
// 	// create a gradient
// 	for (int i=0; i<8448; i++) {
// 		buf_frame[i] = rand() & 0xff;
// 	}
// 	
// 	fling_buffer(buf_frame);
// 	
// 	return 0;
// }


void fling_buffer(char *buffer) {
	// buffer must be 132x64 = 8448 chars
	
	// char buf_rand[8448*65];
	// // populate the random pixel buffer
	// for (int i=0; i<8448*65; i++) {
	// 	buf_rand[i] = rand() & 0xff;
	// }
			
	// // create a gradient
	// for (int y=0; y<64; y++) {
	// 	for (char x=0; x<132; x++) {
	// 		buffer[132*y+x] = x;
	// 	}
	// }
	
	// for (int y=0; y<64; y++) {
	// 	for (int x=0; x<132; x++) {
	// 		printf("%02x ", buffer[y*132 + x]);
	// 	}
	// 	printf("\n");
	// }
	// 
	// return;
	
	set_pin(CS_PIN, LOW); // "Listen up!"
	
	char lcd_pages[PAGE_COUNT * COL_COUNT];
	char page_content;
	int buf_offset, lcd_offset;
	//int rand_offset;
	
	//rand_offset = rand() & 63;

	for (char page=0; page<PAGE_COUNT; page++) {
		set_pin(A0_PIN, LOW);
		lcd_jump(page, 4); // jump to the first column of this page
		
		set_pin(A0_PIN, HIGH); // prepare for data!
		for (char col=0; col<COL_COUNT; col++) {		
			page_content = 0;
			
			for (char bit=0; bit<8; bit++) {
				buf_offset = page*COL_COUNT*8 + col + bit*COL_COUNT;
				page_content >>= 1;
				page_content |= buffer[buf_offset] & 0x80;
			} // bit
			
			lcd_byte(page_content);
		} // col
	} // page
	
	set_pin(CS_PIN, HIGH); // or it won't respond later?
}


int init() {
	if (bcm2835_init() == 0) {
		return 0;
	}
	
	// all five pins are for 'riting
	bcm2835_gpio_fsel(CS_PIN,  BCM2835_GPIO_FSEL_OUTP);
	bcm2835_gpio_fsel(RST_PIN, BCM2835_GPIO_FSEL_OUTP);
	bcm2835_gpio_fsel(A0_PIN,  BCM2835_GPIO_FSEL_OUTP);
	bcm2835_gpio_fsel(CLK_PIN, BCM2835_GPIO_FSEL_OUTP);
	bcm2835_gpio_fsel(SI_PIN,  BCM2835_GPIO_FSEL_OUTP);
	
	set_pin(CS_PIN, LOW); // we only ever need to set this once
	set_pin(RST_PIN, LOW); set_pin(RST_PIN, HIGH);
	set_pin(A0_PIN, LOW); // command mode
	
    lcd_byte(0xe2); // reset
    lcd_byte(0xa3); // set lcd voltage bias to 1/9 (a2) or 1/7 (a3)
    lcd_byte(0xa1); // set col sequence to rightwards (a0) or leftwards (a1)
    lcd_byte(0xc0); // set com output scan direction to downwards (c0) or upwards (c8)
    lcd_byte(0xa4); // display all points: on (a4) or off (a5)
    lcd_byte(0xa7); // set display normal (a6) or reverse (a7)
    lcd_byte(0x2f); // set internal power supp mode (0x28 | 3 bits)
    lcd_byte(0x40); // set first display line (0x40 | 6 bits)
    lcd_byte(0x22); // set resistor ratio (0x20 | 3 bits)
    lcd_byte(0x81); // command to set electronic volume mode
    lcd_byte(0x28); // continued: 6 bits
    lcd_byte(0xaf); // set display on (af) or off (ae)
	
	set_pin(CS_PIN, HIGH);
	
	return 1;
}


void deinit() {
	set_pin(CS_PIN, LOW);
	bcm2835_gpio_fsel(CS_PIN,  BCM2835_GPIO_FSEL_INPT);
	bcm2835_gpio_fsel(RST_PIN, BCM2835_GPIO_FSEL_INPT);
	bcm2835_gpio_fsel(A0_PIN,  BCM2835_GPIO_FSEL_INPT);
	bcm2835_gpio_fsel(CLK_PIN, BCM2835_GPIO_FSEL_INPT);
	bcm2835_gpio_fsel(SI_PIN,  BCM2835_GPIO_FSEL_INPT);
}


// 	srand(time(NULL));
// 	
// 	char page_cmd, col_high, col_low;
// 	
// 	// draws a simple test pattern
// 	if (0)
// 	{
// 		for (char page=0; page<8; page++) {
// 			set_pin(A0_PIN, LOW);
// 			lcd_jump(page, 0);
// 			set_pin(A0_PIN, HIGH);
// 			for (char col=0; col<132; col++) {
// 				lcd_byte(0x02);
// 			}
// 		}
// 		bcm2835_delay(1);
// 	}
// 	
// 	char buf_rand[8448*65];
// 	// populate the random pixel buffer
// 	for (int i=0; i<8448*65; i++) {
// 		buf_rand[i] = rand() & 0xff;
// 	}
// 	
// 	char buf_frame[8448], lcd_pages[1056];
// 	char page_content;
// 	int buf_offset, lcd_offset, rand_offset;
// 		
// 	// create a gradient
// 	for (int y=0; y<64; y++) {
// 		for (char x=0; x<132; x++) {
// 			buf_frame[132*y+x] = x;
// 		}
// 	}
// 	while (1)
// 	{
// 		
// 		buf_offset = 0;
// 		rand_offset = rand() & 63;
// 
// 		for (char page=0; page<8; page++) {
// 			set_pin(A0_PIN, LOW);
// 			lcd_jump(page, 0);
// 			set_pin(A0_PIN, HIGH); // prepare for data!
// 			for (char col=0; col<132; col++) {		
// 				page_content = 0;
// 				for (char bit=0; bit<8; bit++) {
// 					buf_offset = page*132*8 + bit*132 + col;
// 					page_content <<= 1;
// 					page_content |= (buf_frame[buf_offset] < buf_rand[rand_offset + buf_offset]);
// 				} // bit
// 				lcd_byte(page_content);
// 			} // col
// 		} // page
// 		
// 	}
// 	
// 	set_pin(CS_PIN, HIGH); // or it won't respond later?
