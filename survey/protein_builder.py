from k_file_maker import *
from k_file_reader import *
from noes_builder import *
from typing import Union, Dict, List, Tuple

import json
import os
import os.path

def get_protein(
    pdb_id: str, bmrb_id: str, build_anyway: bool = False
) -> Union[Protein, str]:
    """ 
    Generate a Protein object for the input IDs. Build it from BMRB and PDB
    entries if it hasn't already been built or if build_anyway=True.

    Keyword arguments:
    pdb_id -- str of the PDB ID for the entry
    bmrb_id -- str of the BMRB ID for the entry
    Returns:
    protein -- Protein object if successful, an exception from build_protein()
        otherwise
    """
    filename = os.path.join("proteins", f"{pdb_id}_{bmrb_id}.json")
    try:
        if os.path.exists(filename):
            if build_anyway: # to rebuild the protein from scratch
                protein = build_protein(pdb_id, bmrb_id)
            else: # otherwise it can just be loaded from a dumpfile
                protein = load_protein(pdb_id, bmrb_id)
        else:
            protein = build_protein(pdb_id, bmrb_id)
        if isinstance(protein, Protein):
            dump_protein(protein) # store locally so we don't have to rebuild everytime
            ####protein = load_protein(pdb_id, bmrb_id)
        else:
            with open(filename, 'w') as dumpfile:
                json.dump(protein, dumpfile) # even store exceptions locally
    except Exception as err:
        protein = str(err)
        with open(filename, 'w') as dumpfile:
            json.dump(protein, dumpfile)

    


    return protein

def build_protein(pdb_id: str, bmrb_id: str) -> Union[Protein, str]:
    """
    Create a Protein object with amides, aromatic protons, chemical shifts,
    and NOE restraints if possible. Otherwise return an appropriate exception.

    Keyword arguments:
    pdb_id -- str of the PDB ID
    bmrb_id -- str of the BMRB ID
    Returns
    protein -- either a Protein object or an exception raised by 
        make_protein_from_file() or add_restraints()
    """

    ring_current_object = RingCurrentEffect(pdb_id, bmrb_id)
    k_file_path = ring_current_object.calculate_ring_current_effects(
        pdb_id, bmrb_id
    ) # make k-file from Kumaran's code, and return the path
    protein = make_protein_from_file(k_file_path) # build a Protein from k-file

    if isinstance(protein, Protein):
        protein = add_restraints(protein)
    return protein

def dump_protein(protein: Protein):
    """Dump protein to file."""
    dump_dict = protein.dump()
    filename = os.path.join("proteins", f"{protein.pdb_id}_{protein.bmrb_id}.json")
    with open(filename, 'w') as dumpfile:
        json.dump(dump_dict, dumpfile)

def load_protein(pdb_id: str, bmrb_id: str) -> Union[Protein, str]:
    """Load protein from file."""
    filename = os.path.join("proteins", f"{pdb_id}_{bmrb_id}.json")
    with open(filename, 'r') as dumpfile:
        dump_dict = json.load(dumpfile)
    if isinstance(dump_dict, str):
        return dump_dict #there is a one line exception rather than a dumped Protein
    else:
        protein = Protein.load(dump_dict)
        return protein
