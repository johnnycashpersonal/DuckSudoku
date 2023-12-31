""" Made By John Moore, 8-26-2023.

A board is a matrix of tiles or cells. Each row and column and sub-block is treated as a group.
When solved, each group must contain exactly one occurance of the symbol choices 1-9."""

from sdk_config import CHOICES, UNKNOWN, ROOT
from sdk_config import NROWS, NCOLS, NBLOCKS

import enum
import time
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

    def remove_candidates(self, used_values: Set[str]) -> bool:
        """The used values cannot be a value of this unknown tile.
        We remove those possibilities from the list of candidates.
        If there is exactly one candidate left, we set the
        value of the tile.
        Returns:  True means we eliminated at least one candidate,
        False means nothing changed (none of the 'used_values' was
        in our candidates set)."""
        new_candidates = self.candidates.difference(used_values)
        if new_candidates == self.candidates:
            # didn't remove any candidates
            return False
        self.candidates = new_candidates
        if len(self.candidates) == 1:
            self.set_value(new_candidates.pop())
        self.notify_all(TileEvent(self, EventKind.TileChanged))
        return True
    
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

    # This next method checks for board consistency across groups

    def is_consistent(self) -> bool:
        for group in self.groups:
            used_symbols = []
            for tile in group:
                if tile.value in CHOICES:
                    if tile.value in used_symbols:
                        return False
                    else:
                        used_symbols.append(tile.value)
        return True

    def naked_single(self) -> bool:
        """Eliminate Candidates and Check for sole remaining possibilities.
        Return Value true means we crossed off at least one candidate.
        Return Value False means we made no progress."""
        print(f'Entering naked_single method at time {time.localtime()}')

        progress = False

        for group in self.groups:
            #  get the set of symbols used in that group
            group_symbols = set()
            
            for tile in group:
                #This is a good place to check for invalid boards. 
                if tile.value in CHOICES:
                    group_symbols.add(tile.value)

            # Eliminate symbols from candidate sets of unknown tiles in groups

            for tile in group:
                remove_result = tile.remove_candidates(group_symbols)

                if remove_result == True:
                    progress = True

        return progress
    
    # my hidden single method - IE the "this must contain some certain value as there's nowhere else to put it"
    def hidden_single(self):
        print(f'entering hidden_single method time: {time.localtime()}')
        for group in self.groups: # each group of tiles in the groups definition
            leftovers = set(CHOICES)  #start with all choices
            
            for tile in group:
                #remove candidates if value is in group
                if tile.value in leftovers:
                    leftovers.remove(tile.value)
        
                for other_tile in group:
                    if other_tile is not tile:
                        other_tile.candidates.discard(tile.value)

            for value in leftovers:
                #count unknown tiles in a group
                candidate_tiles = [tile for tile in group if tile.value == UNKNOWN]

                # Count occurrences of this value as a candidate in the group
                count = sum(1 for tile in candidate_tiles if value in tile.candidates)
                        
                # If it appears only once, set that tile's value to the candidate
                if count == 1:
                    for tile in candidate_tiles:
                        if value in tile.candidates:
                            tile.value = value
                            tile.candidates = {value}
    
    def min_choice_tile(self) -> Tile:
        print(f'finding a tile with minimum possibilities... time: {time.localtime()}')
        min_tile = None  # Initialize with None to indicate no tile has been found yet
        min_candidates = float('inf')  # Initialize with infinity for comparison

        for row in self.tiles:
            for tile in row:
                # We are only interested in tiles with value UNKNOWN
                if tile.value == UNKNOWN:
                    num_candidates = len(tile.candidates)
                    
                    if num_candidates < min_candidates:
                        min_candidates = num_candidates
                        min_tile = tile

        # At this point, min_tile will hold the tile with the fewest candidates
        # If no such tile exists, min_tile will still be None
        return min_tile
    
    #Saving and restoring our state when we make a mistake and have to backtrack

    def __str__(self) -> str:
        """In Sadman Sudoku format"""
        return "\n".join(self.as_list())


    def as_list(self) -> List[str]:
        """Tile values in a format compatible with 
        set_tiles.
        """
        row_syms = [ ]
        for row in self.tiles:
            values = [tile.value for tile in row]
            row_syms.append("".join(values))
        return row_syms

    def is_complete(self) -> bool:
        
        for group in self.groups:
            for tile in group:
                if tile.value in set(CHOICES):
                    continue
                else:
                    return False
        return True
                            
    def propagate(self):
        """Repeat solution tactics until we
        don't make any progress, whether or not
        the board is solved.
        """
        progress = True
        while progress:
            progress = self.naked_single()
            print(self.__str__())
            self.hidden_single()
        return True
    
    def solve(self) -> bool: # should have been 'ultimate_nuclear_fraud_cooker' but I call solve above
        print(f'Solving... time: {time.localtime()}')
        # Step 1: Propagate constraints
        self.propagate()

        # Step 2: Check if the board is solved
        if self.is_complete():
            return True

        # Check for inconsistency
        if not self.is_consistent():
            return False

        # Step 3: Save the current state for backtracking
        saved_state = self.as_list()

        # Step 4: Select a tile with the minimum number of candidates
        min_tile = self.min_choice_tile()

        if min_tile is None:
            return False  # No tile to choose, so it's inconsistent

        # Step 5: Try each candidate value for the tile
        for candidate in min_tile.candidates:
            min_tile.set_value(candidate)

            # Step 5.1: Recursively try to solve with the new value
            if self.solve():
               return True

            else: # Step 5.2: Restore to saved state if the guess was wrong
                self.set_tiles(saved_state)

        # If we get here, none of the candidates worked
        return False