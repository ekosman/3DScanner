from enum import Enum
from time import sleep
from typing import Optional, Union

from serial import Serial


class SpeedMode(Enum):
    NORMAL: str = "normal"
    FAST: str = "fast"

    def speed(self) -> int:
        if self == SpeedMode.NORMAL:
            return "25"

        if self == SpeedMode.FAST:
            return "50"


class Mode(Enum):
    QUEUE: str = "queue"
    SINGLE: str = "single"


class Direction(Enum):
    UP = "up"
    DOWN = "down"
    FORWARD = "forward"
    BACKWARD = "backward"


class Scanner:
    BASE_SPEED: int = 25

    def __init__(self, port: str, baudrate: int = 9600) -> None:
        self._baudrate = baudrate
        self._port = port
        self._connection = Serial()
        self._connection.port = port
        self._connection.baudrate = baudrate
        self._connection.open()

    @property
    def baudrate(self) -> int:
        return self._baudrate

    @baudrate.setter
    def baudrate(self, value) -> None:
        self._baudrate = value

    @property
    def port(self) -> str:
        return self._port

    @port.setter
    def port(self, value) -> None:
        self._port = value

    def move(self, action) -> None:
        c = self._connection
        c.write(action)

    @staticmethod
    def generate_command_for_specs(mode: Mode, direction: Direction, steps: int, speed: Union[SpeedMode, int]):
        command = [mode.value, direction.value, str(steps)]
        if isinstance(speed, SpeedMode):
            command.append(speed.speed())
        else:
            command.append(str(speed))

        command = "_".join(command)
        command = bytes(command, "utf-8")
        return command
