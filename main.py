# Curiosity-Catcher version 0.1
# Last Debug : N/A
# Release ID : N/A

# Last modification : 2023/12/3;8:14 AM

# Code formatted by Black provided from Microsoft


"""
TODO list:
    [1] - Add LDR query to gather the pin configuration. -> DONE
    [2] - Edit dock string in Catcher().__init__(). -> DONE
    [3] - Edit start operation option in CLI. -> DONE
    [4] - Edit and test the parser function. -> DONE
    [5] - Edit Dict <-> Json mechanism. -> DONE
    [6] - Add comments and Dock strings for rest of the code [HIGH PRIORITY] [TODO]
    [7] - Use database instead of class variables. [HIGH PRIORITY] | [REFACTOR] [TODO]
    [8] - Add AllowPiezoPWM and UseWindowsNotification conditions into Catcher class [BUG]
    [9] - REDEFINE THE CLASSES AND DATA TRANSITION AND USER CONFIG FILE MECHANISM. [BUG]
"""

#  --------------------------- IMPORTS

from warnings import catch_warnings,WarningMessage
from pyfirmata import util, Arduino
from numpy import mean, abs
from os import system
from time import sleep
from win10toast import ToastNotifier as notif
from ctypes import windll

from pyautoguiٔٔ import hotkey
from datetime import datetime as dt
from json import dumps, loads
import webbrowser
import os


#  --------------------------- MAIN CLASS


class Catcher:
    def __init__(
        self,
        port: str = "com4",
        ldrPin: str = "a:0:i",
        piezoPin: str = "d:9:p",
        piezoBeep: bool = True,
        saveLog: bool = True,
        logFileName: str = "log",
        blockUserInput: bool = True,
    ) -> None:
        # useWindowsNotification: bool = True,
        """_summary_

        Args:
            port (str, optional): _description_. Defaults to "com4".
            ldrPin (_type_, optional): _description_. Defaults to "a:0:i".
            piezoPin (_type_, optional): _description_. Defaults to "d:9:p".
            piezoBeep (bool, optional): _description_. Defaults to True.
            saveLog (bool, optional): _description_. Defaults to True.
            logFileName (str, optional): _description_. Defaults to "log".
            blockUserInput (bool, optional): _description_. Defaults to True.
        """

        # initializing port and board!
        self.port: str = port
        self.board: object = Arduino(self.port)

        # LDR configurations
        self.ldrPin: str = ldrPin
        self.ldr_sensor = self.board.get_pin(self.ldrPin)
        self.ldr_sensor_value: float = 0

        # Piezo configuration
        self.piezo = self.board.get_pin(piezoPin)
        self.piezo_beep: bool = piezoBeep

        # Initial value
        self.mean_init_values: float = 0
        self.get_init_values_token: int = (
            1  # allows the program to get the init value for just one time.
        )

        # Warning triggers
        self.trigger_level: int = 0
        self.block_trigger: bool = False

        # Block user input
        self.block_user_input: bool = blockUserInput

        # Suspect activity counter
        self.suspect_activity_ID: int = 0

        # Windows notification permission
        # self.use_windows_notification: bool = useWindowsNotification

        # Log file
        self.save_log: bool = saveLog
        self.log_file_name: str = logFileName

        # Starting the engine
        util.Iterator(board=self.board).start()
        sleep(1)

    def sensorRead(self) -> float:
        """
        Gets LDR value from Arduino from specified pin

        Returns:
            float: read LDR value
        """
        return self.ldr_sensor.read()

    def getInitialValues(self) -> None:
        """Calculates mean of 500 read LDR values to determine desk/env values"""
        init_values: list = []
        [init_values.append(self.sensorRead()) for _ in range(500)]
        self.init_mean_values = mean(init_values)

    def calculator(self, currentValue: float) -> bool:
        match self.get_init_values_token:
            case 0:
                mean_value: float = self.init_mean_values
                if mean_value == 0:
                    pass
                else:
                    if (abs(currentValue - mean_value) / mean_value) * 100 > 5:
                        return True
                return False
            case 1:
                self.getInitialValues()
                self.get_init_values_token = 0
                return False

    def piezoTone(self, PWMDutyCycle=float):
        """Simple piezo tone"""
        self.piezo.write(PWMDutyCycle)

    def piezoNoTone(self):
        """Simple piezo noTone"""
        self.piezo.write(0)

    def userEvacuationTime(self):
        """This gives the user time to leave the table with suitable notification without interfering with the results."""
        notif().show_toast(
            title="Developer",
            msg="You have only 10 seconds to evacuate",
            duration=10,
        )
        if self.piezo_beep:
            self.piezoTone(PWMDutyCycle=0.5)
            self.board.pass_time(t=1)
            self.piezoNoTone()
        print("System is ONLINE")

    def getLastSuspectActivityID(self):
        with open("id.txt", "r") as id_file:
            ID = id_file.read()
            id_file.close()
        self.suspect_activity_ID = ID

    def logNewSuspectActivityID(self):
        with open("id.txt", "w") as id_file:
            id_file.write(self.suspect_activity_ID)
            id_file.close()

    def logger(self) -> None:
        """Saves activities into a file"""
        with open(f"{self.log_file_name}.log", "+a") as log:
            log.write(
                f"ID : {self.suspect_activity_ID}, level : {self.trigger_level}, msg : New suspected activity recorded at : {dt.now()}\n"
            )
            log.close()

    def blockInput(self, Bool: bool) -> None:
        """
        Blocks mouse and keyboard input, Instantly defuses with (Ctrl + Alt + Del)

        Args:
            Bool (bool): _description_
        """
        windll.user32.BlockInput(Bool)

    def triggerWarningLevel1(self) -> None:
        """Blocks user input + warns him/her! with a notification level 1"""
        self.blockInput(self.block_user_input)
        # hotkey("win", "d")
        # notif().show_toast(
        #     title="Developer",
        #     msg="Access Denied, get out of here! |  دسترسی غیر مجاز، از سیستم دور شوید",
        #     duration=10,
        # )
        print(" Denied access level 1 : Warning Level 1 has triggered. ")

    def triggerWarningLevel2(self) -> None:
        """Shows final warning about locking the workstation"""
        notif().show_toast(
            title="Developer",
            msg=" This is your last warn to get out of the monitor sight ",
            duration=10,
        )
        print(" Denied access level 2 : Warning Level 2 has triggered. ")

    def lockWorkStation(self) -> None:
        """Locks computer while real operator unlock the machine"""
        print(" Locking the workstation ")
        system(command="Rundll32.exe user32.dll,LockWorkStation")
        self.blockInput(False)
        print(" Workstation locked ")

    def inspector(self) -> None:
        """Drives and handles all of the events"""
        self.userEvacuationTime()
        while True:
            if self.calculator(currentValue=self.sensorRead()):
                self.trigger_level += 1
                self.suspect_activity_ID += 1
                self.block_trigger = False
                if self.save_log:
                    self.logger()

            if self.block_trigger == False:
                match self.trigger_level:
                    case 0:
                        pass
                    case 1:
                        self.triggerWarningLevel1()
                        self.block_trigger = True
                        print(" Warning level 1 is active ")

                        sleep(0.5)
                    case 2:
                        self.triggerWarningLevel2()
                        self.block_trigger = True
                        print(" Warning level 2 is active ")
                        sleep(0.5)
                    case 3:
                        self.lockWorkStation()
                        self.block_trigger = True
                        self.board.exit()  # type: ignore
                        break


class UserInterface:
    def __init__(self) -> None:
        self.userConfig: dict = {
            "BoardPort": str,
            "LDRPinConfig": str,
            "PiezoInitialBeep": bool,
            "PiezoPinConfig": str,
            "PiezoAllowPWM": bool,
            "PiezoPWMValue": float | None,
            "BlockUserInput": bool,
            "UseWindowsNotification": bool,
            "SaveActivityLogs": bool,
            "LogFileName": str,
        }

    class InitialConfig:
        def __init__(self) -> None:
            self.userConfig: dict = UserInterface().userConfig

        def portQuery(self):
            self.userConfig["BoardPort"] = input(
                " Enter the board port COM X (e.g. com3) > "
            )

        def LDRPinConfigQuery(self):
            query: str = input(" Enter attached analog pin to the LDR > ")
            self.userConfig["LDRPinConfig"] = f"a:{query}:i"

        def piezoInitBeepQuery(self):
            query: str = input(" Would you like to setup piezo initial beep? (Y/n) >  ")
            self.userConfig["PiezoInitialBeep"] = (
                True if query.lower() == "y" else False
            )

        def piezoPinConfigQuery(self):
            if self.userConfig["PiezoInitialBeep"]:
                print(" \n Note : If you want to use PWM enter Arduino PWM pin\n ")
                print(
                    ' Pin configuration options : \n   1 | PWM\n   2 | Binary \n If you are not about to use Piezo enter "skip" to config later from saved config file'
                )
                while True:
                    selection: str = input(" Enter your selection > ")
                    match selection:
                        case "1":
                            self.userConfig[
                                "PiezoPinConfig"
                            ] = "{type}:{pin}:{IO}".format(
                                type="d", pin=input(" Enter PWM pin > "), IO="p"
                            )
                            try:
                                pwm_value: float = float(
                                    input(
                                        " Enter PWM value as a float number in range from 0 to 1 (e.g. 0.52) > "
                                    )
                                )
                                if 0 <= pwm_value <= 1:
                                    pass
                                else:
                                    print(" Entered value is out of range. ")
                            except:
                                print(
                                    " Input Value Error : invalid input, please try again. "
                                )
                            self.userConfig["PiezoPWMValue"] = pwm_value
                            self.userConfig["PiezoAllowPWM"] = True
                            break
                        case "2":
                            self.userConfig[
                                "PiezoPinConfig"
                            ] = "{type}:{pin}:{IO}".format(
                                type="d", pin=input(" Enter Digital pin > "), IO="o"
                            )
                            self.userConfig["PiezoAllowPWM"] = False
                            break
                        case "skip":
                            print(" Pin configuration has skipped ")
                            break
                        case _:
                            print(" Input Error : INVALID_SELECTION ")

        # def piezoPWMQuery(self):
        #     self.userConfig["PiezoPWM"] = (
        #         input(" Enter Duty Cycle as a float number in range of 0 to 1 > ")
        #         if self.userConfig["PiezoAllowPWM"] == True
        #         else None
        #     )

        def blockUserInputQuery(self):
            self.userConfig["BlockUserInput"] = (
                True
                if input(
                    " Would you like to block user input after suspicious activity?  (Y/n) > "
                ).lower()
                == "y"
                else False
            )

        def useWindowsNotificationQuery(self):
            self.userConfig["UseWindowsNotification"] = (
                True
                if input(
                    " Would you like to use Windows Notification? (Y/n) > "
                ).lower()
                == "y"
                else False
            )

        def saveLogQuery(self):
            self.userConfig["SaveActivityLogs"] = (
                True
                if input(" Would you like to save the activity logs? (Y/n) >  ").lower()
                == "y"
                else False
            )
            if self.userConfig["SaveActivityLogs"] == True:
                query: str = input(
                    " Choose a file name otherwise press enter to set as default (log) > "
                )
                if query != "":
                    self.userConfig["LogFileName"] = query
                else:
                    self.userConfig["LogFileName"] = "log"

        def saveUserConfigFile(self):
            file_name: str = input(
                " Configuration file has been compiled, Enter a file name to save > "
            )
            # format: str = input(" Enter file format (preferred *.txt) > ")
            with open(f"{file_name}.json", "w") as file:
                # config = deepcopy(self.userConfig)
                file.write(dumps(self.userConfig))
                file.close()
            print(
                f' User config " {file_name}.json " saved successfully. \n you can use this next time for faster setup.'
            )

        def saveUserConfigQuery(self):
            self.saveUserConfigFile() if input(
                " Would you like to save this configuration for future ? (Y/n) >  "
            ).lower() == "y" else None

        def glue(self):
            self.portQuery()
            self.LDRPinConfigQuery()

            self.piezoInitBeepQuery()
            self.piezoPinConfigQuery()
            # self.piezoPWMQuery()

            self.blockUserInputQuery()

            self.useWindowsNotificationQuery()

            self.saveLogQuery()

            self.saveUserConfigFile()
            # print(self.userConfig)
            # input("enter")

        def loadUserConfigFile(self):  # TODO : add parser
            dir: str = input(" Enter file directory or drag then drop here > ")
            with open(dir, "r") as file:
                user_config: str = file.read()
                file.close()
            self.userConfig = loads(user_config)

    class CLI:
        def __init__(self) -> None:
            self.userConfig: dict = UserInterface().userConfig

        def greeting(self):
            print(
                " *** Welcome to Curiosity-Catcher version 0.1 - This program is under GNU/GPL-V3 license ***\n"
            )

        def installDependencies(self):
            system(command=r"pip3 install -r requirements.txt")

        def menu(self):
            return input(
                "Main menu :\n  [1] Setup a new user config \n  [2] Load from existing file \n  [3] Use program defaults \n  [4] Install dependencies using pip3 \n  [5] Go to the GitHub repo \n  [0] Exit \n\n > "
            )

        def menu2(self):
            return input(
                "Main menu :\n   [1] Start operation\n   [2] Setup a user configuration file\n   [3] Install dependencies via pip3\n   [4] Go to this project's GitHub repo\n   [0] Exit\n\n > "
            )

        def start(self):
            selection: str = input(
                "Operation menu :\n  [1] Load user config file\n   [2] Setup a new user configuration file\n   [3] Use program default config (Developer default)  \n\n > "
            )
            match selection:
                case "1":
                    self.userConfig = (
                        UserInterface().InitialConfig().loadUserConfigFile()
                    )
                    config = self.userConfig
                    Catcher(
                        port=config["BoardPort"],
                        ldrPin=config["LDRPinConfig"],
                        piezoBeep=config["PiezoInitialBeep"],
                        piezoPin=config["PiezoPinConfig"],
                        blockUserInput=config["BlockUserInput"],
                        logFileName=config["LogFileName"],
                    ).inspector()
                case "2":
                    UserInterface().InitialConfig().glue()
                    Catcher(
                        port=config["BoardPort"],
                        ldrPin=config["LDRPinConfig"],
                        piezoBeep=config["PiezoInitialBeep"],
                        piezoPin=config["PiezoPinConfig"],
                        blockUserInput=config["BlockUserInput"],
                        logFileName=config["LogFileName"],
                    ).inspector()
                case "3":
                    Catcher.inspector()

        def runMenu(self):
            self.greeting()
            while KeyboardInterrupt:
                match self.menu2():
                    case "1":
                        self.start()
                    case "2":
                        UserInterface().InitialConfig().glue()
                        self.userConfig = UserInterface().userConfig  # TODO
                    case "3":
                        self.installDependencies()
                    case "4":
                        print(
                            " Just a moment you are going to this project repository "
                        )
                        sleep(3)
                        webbrowser.open(
                            url="https://github.com/ilaItayad3h/Curiosity-Catcher"
                        )
                    case "0":
                        exit(0)


#  --------------------------- RUN
if __name__ == "__main__":
    UserInterface().CLI().runMenu()

# end of code
