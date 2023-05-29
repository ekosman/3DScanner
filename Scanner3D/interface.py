"""Interface for 3D Scanner."""

from enum import Enum
from typing import Union

from serial import Serial


class SpeedMode(Enum):
    """Speed modes."""

    NORMAL: str = "normal"
    FAST: str = "fast"

    def speed(self) -> int:
        """Speed value represented by the speed mode."""
        if self == SpeedMode.NORMAL:
            return "25"

        if self == SpeedMode.FAST:
            return "50"

        return 0


class Mode(Enum):
    """Run modes."""

    QUEUE: str = "queue"
    SINGLE: str = "single"


class Direction(Enum):
    """Directions in which the scanner can move."""

    UP = "up"
    DOWN = "down"
    FORWARD = "forward"
    BACKWARD = "backward"


class Scanner:
    """Communication interface with the scanner.

    Args:
        port (int): Port to which the scanner is connected.
        baudrate (int): Baudrate of the connection. Defaults to 9600.
    """

    def __init__(self, port: str, baudrate: int = 9600) -> None:
        self._baudrate = baudrate
        self._port = port
        self._connection = Serial()
        self._connection.port = port
        self._connection.baudrate = baudrate
        self._connection.open()

    @property
    def baudrate(self) -> int:
        """Baudrate of the connection."""
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
        self._connection.write(action)

    @staticmethod
    def generate_command_for_specs(mode: Mode, direction: Direction, steps: int, speed: Union[SpeedMode, int]):
        """Generates a command from the specified values.

        Args:
            mode (Mode): Operation mode. Possible values are `queue` | `queue`.
            direction (Direction): Direction of the command.
            steps (int): How many steps to perform.
            speed (Union[SpeedMode, int]): Speed of the command,

        Returns:
            _type_: _description_
        """
        command = [mode.value, direction.value, str(steps)]
        if isinstance(speed, SpeedMode):
            command.append(speed.speed())
        else:
            command.append(str(speed))

        command = "_".join(command)
        command = bytes(command, "utf-8")
        return command
