""" Made By John Moore, 8-26-2023.

A board is a matrix of tiles or cells. Each row and column and sub-block is treated as a group.
When solved, each group must contain exactly one occurance of the symbol choices 1-9."""

from sdk_config import CHOICES, UNKNOWN, ROOT
from sdk_config import NROWS, NCOLS, NBLOCKS

import enum
from typing import List, Sequence, Set 
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# ---------------------
# The events for MVC 
# ---------------------

class Event(object):
    """ Abstract base class for all events, 
    both for MVC and for other purposes."""

    pass

class Listener(object):
    """Abstract base class for listeners. 
    Subclass this for making useful notifications."""

    def __init__(self) -> None:
        pass

    def notify(self, event):
        """ The 'notify' method of the base class must 
        be overridden in concrete classes."""
        
        raise NotImplementedError("You must override Listener.notify")

# ---------------------
# Events and Listeners for Tile Objects
# ---------------------

class EventKind(enum.Enum):
    TileChanged = 1
    TileGuessed = 2

class TileEvent(Event):
    """ Abstract base class for things that happen to tiles. 
    We always indicate the tile. Concrete subclasses indicate 
    the nature of this event."""

    def __init__(self, tile: 'Tile', kind: EventKind):
        self.tile = tile
        self.kind = kind

    def __str__(self):
        "Printed representation of the event."
        return f"{repr(self.tile)}"
    
class TileListener(Listener):
    def notify(self, event: TileEvent):
        raise NotImplementedError(
            "TileListener Subclass needs to override notify(TileEvent)") 

class Listenable:
    """ Objects to which listeners (like a view component) Can be attached."""

    def __init__(self):
        self.listeners = [ ]

    def add_listener(self, listener):
        self.listeners.append(listener)
    
    def notify_all(self, event):
        for listener in self.listeners:
            listener.notify(event)


# ---------------------
# The Tile Class
# ---------------------

class Tile(Listenable):
    """One Tile on the Sudoku Grid. 
    Public attributes (read-only): value, 
    which will be either UNKNOWN or CHOICES; candidates, 
    which will be a set drawn from CHOICES. If value is an element of
    CHOICES,then candidates will be the singleton containing
    value.  If candidates is empty, then no tile value can
    be consistent with other tile values in the grid.
    value is a public read-only attribute; change it
    only through the access method set_value or indirectly 
    through method remove_candidates. """

    def __init__(self, row: int, col: int, value=UNKNOWN):
        super().__init__()
        assert value == UNKNOWN or value in CHOICES
        self.row = row
        self.col = col
        self.set_value(value)

    def set_value(self, value: str):
        if value in CHOICES:
            self.value = value
            self.candidates = {value}
        else:
            self.value = UNKNOWN
            self.candidates = set(CHOICES)
        self.notify_all(TileEvent(self, EventKind.TileChanged))

    def __str__(self):
        return f'{self.value}'
    
    def __repr__(self):
        return f"Tile({self.row}, {self.col}, \'{self.value}\')"
    
    def could_be(self, value:str) -> bool:
        """True if this tile could be value."""
        return value in self.candidates
    
# ---------------------
# The Board Class
# ---------------------

class Board(object):
    """A Board has a 9 * 9 Matrix of tiles."""

    def __init__(self):
        """The empty board."""
        ### Row and Column Structure: Each row contains columns

        self.tiles: List[List[Tile]] = [ ]
        for row in range(NROWS):
            cols = [ ]
            for col in range(NCOLS):
                cols.append(Tile(row, col))
            self.tiles.append(cols)

        #Now we build the groups, by calling another function
        self.build_groups()
    
    def set_tiles(self, tile_values: Sequence[Sequence[str]]):
        """Set the tile values to a list of lists or a list of strings."""

        for row_num in range(NROWS):
            for col_num in range(NCOLS):
                tile = self.tiles[row_num][col_num]
                tile.set_value(tile_values[row_num][col_num])

    def __str__(self):
        """In sadman sudoku format"""
        row_syms = []
        for row in self.tiles:
            values = [tile.value for tile in row]
            row_syms.append("".join(values))
        return "\n".join(row_syms)
    
    def build_groups(self):
        "Build the groups that must contain all choices."
       
        self.groups = [ ]

        #builds all the column groups
        for col_idx in range(NCOLS):
            col_group = [ ]
            for row_idx in range(NROWS):
                col_group.append(self.tiles[row_idx][col_idx])
            self.groups.append(col_group)

        #builds all row groups
        for row_idx in range(NROWS):
            row_group = [ ]
            for col_idx in range(NCOLS):
                row_group.append(self.tiles[row_idx][col_idx])
            self.groups.append(row_group)

        #builds block groups

        for block_column_idx in range(ROOT):
            for block_row_idx in range(ROOT):
                block_group = [ ]
                for row_idx in range(ROOT):
                    for col_idx in range(ROOT):
                        b_row_step = (block_row_idx * 3) + (row_idx)
                        b_col_step = (block_column_idx * 3) + (col_idx)
                        block_group.append(self.tiles[b_row_step][b_col_step])
                self.groups.append(block_group)


        

    

