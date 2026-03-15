import stim
from typing import Dict, Tuple, Literal

QubitType = Literal['data', 'x_stab', 'z_stab']

class LogicalQubit():
    x_offset:int = -1
    y_offset:int = -1
    d_x:int = 0
    d_y:int = 0
    physicalQubits: Dict[Tuple[int,int], QubitType] = {} #stores the qubits that make up this logical qubit {coordinate (x,y), qubitType}

    def __init__(self, x_offset:int, y_offset:int, d_x:int, d_z:int):
        self.physicalQubits = {}
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.d_x = d_x
        self.d_z = d_z

        if d_x%2 != 1  or d_z%2 !=1 or d_x < 0 or d_z < 0:
            raise ValueError(f'LogicalQubit must have odd distances greater than 0, but was given (d_x: {d_x}, d_z: {d_z})')

        #add data qubits
        for i in range(d_x):
            for j in range(d_z):
                x_coord = (2*i + 1) + x_offset
                y_coord = 2*j + 1 + y_offset
                self.physicalQubits[(x_coord, y_coord)] = 'data'
        
        #add inner stabelizers
        for i in range(2, 2*d_x, 2):
            for j in range(2, 2*d_z, 2):
                x_coord = i + x_offset
                y_coord = j + y_offset
                if (x_coord+y_coord)%4 == 0:
                    self.physicalQubits[(x_coord,y_coord)] = 'z_stab'
                else:
                    self.physicalQubits[(x_coord,y_coord)] = 'x_stab'
        
        #add boundry stabelizers (x stabelizers along top and bottom, z along right and left)
        for j in range(2, d_z*2-1,2): #adding Z stabelisers on far right or far left (alternating)
            if (j%4 == 0):
                x_coord = 0 + x_offset
            else:
                x_coord = d_x*2 + x_offset
            y_coord = j + y_offset
            self.physicalQubits[(x_coord,y_coord)] = 'z_stab'

        for i in range(2,d_x*2-1,2): #adding X stabelisers on far bottom or far top (alternating)
            if (i%4 == 0):
                y_coord = d_z*2 + y_offset
            else:
                y_coord = 0 + y_offset
            x_coord = i + x_offset
            self.physicalQubits[(x_coord,y_coord)] = 'x_stab'

    """
        gives the stim index for a coordinate pair for this logical qubit
    """
    def calcCoordIndex(self, coords:Tuple):
        index = coords[0] + (coords[1]//2)*(2*self.d_x+1)
        return index

    """
        displays the logical qubit on a lattice
    """
    def printLattice(self):
        width = 2*self.d_x + 1 + self.x_offset   #the x,y coords are flipped to be rows and columns
        height = 2*self.d_z + 1 + self.y_offset
        # 1. Initialize empty grid (rows are y, cols are x)
        grid = [['.' for _ in range(width)] for _ in range(height)]

        # 2. Populate the grid
        role_map = {'data': 'D', 'x_stab': 'X', 'z_stab': 'Z'} # Mapping role to a single character
        
        for coords, qubitType in self.physicalQubits.items():
            xCoord = coords[0]
            yCoord = coords[1]

            if 0 <= xCoord < width and 0 <= yCoord < height: # Make sure x, y are within bounds
                grid[yCoord][xCoord] = role_map.get(qubitType, '?')  #x & y are flipped so that it is cartesian rather than row column
        
        # 3. Print the grid
        for row in grid:
            print(" ".join(row))


    """
        returns a list of coordinates for a specific role (e.g. 'x_stab')
    """
    def getQubitsByRole(self, role: str):
        return [coord for coord, r in self.physicalQubits.items() if r == role]
    
    """
        returns the role of the qubit at the given location
    """
    def getRoleFromCoord(self, coord: Tuple):
        return self.physicalQubits.get(coord, None)
    
    """
        returns the 4 neighbors of a qubit at the given coords
    """
    def getNeighbors(self, coord: Tuple):
        x = coord[0]
        y = coord[1]
        
        if self.physicalQubits.get(coord, None) == None:
            raise ValueError(f'cannot get neighbors of nonexistant qubit. No qubit at ({x},{y})')

        candidates = [
            (x-1,y-1), (x-1,y+1), (x+1,y-1), (x+1,y+1)
        ]
        
        #filter candidates and only return ones that appear in the physical qubits of this logical qubit
        return [c for c in candidates if c in self.physicalQubits]


Lqubit = LogicalQubit(x_offset = 1, y_offset=0, d_x=3, d_z=3)
Lqubit.printLattice()

# class SCCircut():

# circuit = stim.Circuit("""
#     H 0
#     CNOT 0 1
#     M 0 1                   
# """)

# sampler = circuit.compile_sampler()

# samples = sampler.sample(shots=10)

# print("Results of 10 shots (Qubit 0, Qubit 1):")
# print(samples)

# circuit = stim.Circuit.generated(
#     "surface_code:rotated_memory_z",
#     distance=3,
#     rounds=10,
#     after_clifford_depolarization=0.001 # Adding 0.1% noise
# )

# print(circuit)
