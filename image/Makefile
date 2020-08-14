
all:
	gcc -o driver driver.c

%:%.c
	gcc -o $@ $<
	mv $@ driver

clean:
	rm -f driver
