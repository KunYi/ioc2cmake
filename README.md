# ioc2cmake

This is a small Python tool that allows building STM32CubeMX generated firmware with CMake. It parses STM32CubeMX `*.ioc` project files and generates CMake variables containing the appropriate settings for the microcontroller (include paths, compiler flags, etc.).

It can also generate a `c_cpp_properties.json` config file for VScode, containing the relevant include paths & compiler definitions to run VScode as IDE for the firmware project.

### How it works

`ioc2cmake` is called at configuration stage from within the CMake script. It spits out a list of `key=value` pairs on stdout, which are captured by the CMake script and saved in variables. These variables are then used to configure the firmware build.

Since the STM32 MCU type, include paths etc. are not hardcoded in the `CMakeLists.txt` but generated at configure stage, firmware can be ported to different MCUs without changing the CMake script, and the CMake script can be reused on firmwares targeting other STM32 MCUs.

### Usage
Call `ioc2cmake` from the CMake script like this:
```
execute_process(COMMAND ${CMAKE_SOURCE_DIR}/ioc2cmake.py
    ${CMAKE_SOURCE_DIR}             # Path to source tree
    ${CMAKE_SOURCE_DIR}/TDLAS.ioc   # Path to CubeMX config file
    -s ${CMAKE_SOURCE_DIR}/app      # Extra source folder
    -i ${CMAKE_SOURCE_DIR}/app      # Extra include folder
    -t /opt/gcc-arm-none-eabi-7-2017-q4-major   # Toolchain location
    -v                              # Create vscode properties file
    OUTPUT_VARIABLE ConfigContents)
```
It needs the path to the source tree, path to the CubeMX `*.ioc` project file and the path to the toolchain file. It assumes the regular CubeMX generated source structure. Additional source and include directories can be added with `-s` and `-i` switches, respectively. (I like to put my written source files in other directories than the autogenerated ones, for better clarity).

There is an example `CMakeLists.txt` in the repository demonstrating the use of `ioc2cmake`.

The firmware build can be set up like a regular CMake build.

### Caveats

I only use the CubeMX LL drivers, so this is not tested against a project structure using HAL drivers.  
For Cortex-M7 MCUs, at the moment it always assumes a double-precision FPU, but there are M7's which have single precision only.  
This is tested on a STM32F767xx MCU (NUCLEO-F767ZI board). Not tested on other MCUs yet.


Feedback and contributions welcome.
