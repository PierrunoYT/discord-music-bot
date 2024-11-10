import json
import pickle
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Tuple

@dataclass
class QueuedSong:
    title: str
    url: str
    duration: int
    artist: str

class QueueManager:
    def __init__(self, save_file: str = 'queue_state.json'):
        self.save_file = Path(save_file)
        self.save_file.touch(exist_ok=True)

    def save_queue(self, current_song: Optional[QueuedSong], queue: List[QueuedSong]) -> None:
        """Save the current queue state to file"""
        state = {
            'current_song': vars(current_song) if current_song else None,
            'queue': [vars(song) for song in queue]
        }
        with open(self.save_file, 'w') as f:
            json.dump(state, f)

    def load_queue(self) -> Tuple[Optional[QueuedSong], List[QueuedSong]]:
        """Load the queue state from file"""
        try:
            with open(self.save_file, 'r') as f:
                state = json.load(f)
                current_song = QueuedSong(**state['current_song']) if state['current_song'] else None
                queue = [QueuedSong(**song) for song in state['queue']]
                return current_song, queue
        except (json.JSONDecodeError, FileNotFoundError):
            return None, []
