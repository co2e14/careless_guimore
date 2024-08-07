WARNINGS := -Wall $(WARNINGS)
CC = g++
CFLAGS := -g
CFLAGS := $(CFLAGS) $(WARNINGS) -std=c++20
LFLAGS := $(LFLAGS)   
SOURCES = $(wildcard *.cpp)
EXECUTABLES = $(SOURCES:.cpp=.exe)

all: $(EXECUTABLES)


$(EXECUTABLES): %.exe: %.cpp
	$(CC) $(CFLAGS) $< -o $@ $(LFLAGS)

clean::
	- rm -f *.exe