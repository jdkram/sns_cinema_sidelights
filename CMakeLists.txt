cmake_minimum_required(VERSION 3.7)
project(star_shadow)

set(CMAKE_CXX_STANDARD 11)

#Lib for PWM board - depends on wiringPi lib
set(SOURCES pca9685/src/pca9685.c)

include(src/CMakeLists.txt)

add_executable(main ${SOURCES})

#wiringPi lib for button presses and i2c
target_link_libraries(main wiringPi)