"""
Abstract capture backend base class
"""
from abc import ABC, abstractmethod


class CaptureBackend(ABC):

    @abstractmethod
    def get_ffmpeg_input_args(self) -> list:
        """
        Return the list of ffmpeg arguments for input source.
        Example: ["-f", "x11grab", "-video_size", "1280x720", "-i", ":0"]
        """

    def validate(self) -> bool:
        """
        Optional: validate that the backend is usable on this system.
        Returns True if available, False otherwise.
        """
        return True
