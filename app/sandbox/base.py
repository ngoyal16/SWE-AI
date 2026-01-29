from abc import ABC, abstractmethod
from typing import List

class Sandbox(ABC):
    @abstractmethod
    def setup(self):
        """Initializes the sandbox environment."""
        pass

    @abstractmethod
    def teardown(self):
        """Cleans up the sandbox environment."""
        pass

    @abstractmethod
    def run_command(self, command: str, cwd: str = None) -> str:
        """Runs a shell command in the sandbox."""
        pass

    @abstractmethod
    def read_file(self, filepath: str) -> str:
        """Reads content from a file in the sandbox."""
        pass

    @abstractmethod
    def write_file(self, filepath: str, content: str) -> str:
        """Writes content to a file in the sandbox."""
        pass

    @abstractmethod
    def list_files(self, path: str) -> str:
        """Lists files in a directory in the sandbox."""
        pass

    @abstractmethod
    def get_root_path(self) -> str:
        """Returns the root path of the workspace inside the sandbox."""
        pass
