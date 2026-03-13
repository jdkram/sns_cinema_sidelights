cmake_minimum_required(VERSION 3.7)
project(star_shadow)

set(CMAKE_CXX_STANDARD 11)

#Lib for PWM board - depends on wiringPi lib
set(SOURCES pca9685/src/pca9685.c)

include(src/CMakeLists.txt)

# wiringPi headers are not in the default include path if wiringPi was built from source
# without `make install`. Search standard paths then the Pi's source-build tree.
find_path(WIRINGPI_INCLUDE wiringPi.h
    PATHS /usr/local/include /usr/include /home/pi/wiringPi/wiringPi)
if(WIRINGPI_INCLUDE)
    include_directories(${WIRINGPI_INCLUDE})
endif()

add_executable(main ${SOURCES})

#wiringPi lib for button presses and i2c
target_link_libraries(main wiringPi)