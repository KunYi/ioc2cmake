#!/usr/bin/python3

import argparse
import os
import json


def loadIOC(filename):
    conf = {}
    with open(filename) as f:
        while True:
            line = f.readline().strip()
            if not line:
                break
            if line[0] == '#':
                continue
            vals = line.split('=', 2)
            if len(vals) < 2:
                continue
            conf[vals[0]] = vals[1]
    return conf


def getCore(mcuName):
    coreTable = {
        "STM32F0": "cortex-m0",
        "STM32F1": "cortex-m3",
        "STM32F2": "cortex-m3",
        "STM32F3": "cortex-m4",
        "STM32F4": "cortex-m4",
        "STM32F7": "cortex-m7",
        "STM32H7": "cortex-m7",
        "STM32L0": "cortex-m0",
        "STM32L1": "cortex-m3",
        "STM32L4": "cortex-m4",
    }
    for key, value in coreTable.items():
        if mcuName.startswith(key):
            return value


def getFpu(mcuName):
    # TODO in case of m7 core, check if it has single or double precision fpu
    fpuTable = {
        "cortex-m0": None,
        "cortex-m3": None,
        "cortex-m4": "fpv4-sp-d16",
        "cortex-m7": "fpv5-d16"
    }
    for key, value in fpuTable.items():
        if getCore(mcuName) == key:
            return value


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create CMake and vscode config files from CubeMX .ioc project file")
    parser.add_argument("srcPath", help="Source path")
    parser.add_argument("iocFile", help="CubeMX .ioc project file")
    parser.add_argument("-s", help="additional source folder", action="append")
    parser.add_argument("-i", help="additional include folder", action="append")
    parser.add_argument("-v", help="enable vscode properties setup", action="store_true")
    parser.add_argument("-t", help="toolchain location")
    args = parser.parse_args()

    iocConf = loadIOC(args.iocFile)

    cmakeConf = {
        "CUBEMX_PROJNAME": iocConf["ProjectManager.ProjectName"],
        "CUBEMX_MCUFAMILY": iocConf["Mcu.Family"] + "xx",
        "CUBEMX_MCUNAME": iocConf["Mcu.Name"],
        "CUBEMX_MCULINE": iocConf["Mcu.Name"][0:9] + "xx",
        "CUBEMX_LDFILE": iocConf["Mcu.Name"] + "_FLASH.ld",
        "CUBEMX_CPUTYPE": getCore(iocConf["Mcu.Family"]),
        "CUBEMX_TOOLCHAIN": args.t
    }

    cmakeConf["CUBEMX_STARTUPFILE"] = \
        os.path.join(args.srcPath,
                     "startup_" + cmakeConf["CUBEMX_MCULINE"].lower() + ".s")

    core = getCore(iocConf["Mcu.Family"])
    mcuFlags = f"-mcpu={core} -mthumb"

    fpu = getFpu(iocConf["Mcu.Family"])
    mcuFlags += f" -mfpu={fpu} -mfloat-abi=hard" \
                if fpu is not None else " -mfloat-abi=soft"

    cmakeConf["CUBEMX_MCUFLAGS"] = mcuFlags

    cdefs = [
        "USE_FULL_LL_DRIVER",
        f"HSE_VALUE={iocConf['RCC.HSE_VALUE']}",
        f"HSI_VALUE={iocConf['RCC.HSI_VALUE']}",
        f"LSI_VALUE={iocConf['RCC.LSI_VALUE']}",
        cmakeConf["CUBEMX_MCULINE"]
    ]
    cmakeConf["CUBEMX_CDEFS"] = "\n".join([f"-D{cdef}" for cdef in cdefs])

    cmsisDir = os.path.join(args.srcPath, "Drivers", "CMSIS")
    deviceDir = os.path.join(cmsisDir,
                             "Device", "ST", cmakeConf["CUBEMX_MCUFAMILY"])
    halDir = os.path.join(args.srcPath,
                          "Drivers", cmakeConf["CUBEMX_MCUFAMILY"] + "_HAL_Driver")

    sourceDirs = [
        os.path.join(args.srcPath, "Src"),
#       os.path.join(deviceDir, "Source"),
        os.path.join(halDir, "Src"),
    ]
    if args.s:
        sourceDirs += args.s
    cmakeConf["CUBEMX_SOURCEDIRS"] = "\n".join(sourceDirs + args.s)

    includeDirs = [
        os.path.join(args.srcPath, "Inc"),
        os.path.join(cmsisDir, "Include"),
        os.path.join(deviceDir, "Include"),
        os.path.join(halDir, "Inc"),
    ]
    if args.i:
        includeDirs += args.i
    cmakeConf["CUBEMX_INCLUDEDIRS"] = "\n".join(includeDirs)

    for key, value in cmakeConf.items():
        print(f"{key}={value};", end="")

    if args.v:
        # Create vscode properties
        vscodeSetup = {
            "configurations": [
                {
                    "name": "Linux",
                    "includePath": [
                        os.path.join("${workspaceFolder}", i)
                        for i in includeDirs
                    ],
                    "defines": cdefs,
                    "compilerPath":
                        os.path.join(args.t, "bin/arm-none-eabi-gcc"),
                    "cStandard": "c11",
                    "intelliSenseMode": "clang-x64"
                }
            ],
            "version": 4
        }
        os.makedirs(os.path.join(args.srcPath, ".vscode"), exist_ok=True)
        with open(os.path.join(args.srcPath, ".vscode", "c_cpp_properties.json"),
                  'w') as outfile:
            json.dump(vscodeSetup, outfile, sort_keys=True, indent=4)
