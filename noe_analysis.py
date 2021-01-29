from en_masse import *
from restraint_pair_classification import *
from noe_proportions_plotting import *
from noe_tiers import *

def classify_shift(cs_sigma, outlier_sigma):
    """
    Classify the chemical shift depending on the number of standard deviations
    that define an outlier.

    Keyword arguments:
    cs_sigma -- the Z-score of an atom
    outlier_sigma -- the number of standard deviations from mean that make an
        atom's chemical shift an outlier
    Returns:
    'upfield' -- if the shift is upfield by more than outlier_sigma standard 
        deviations
    'downfield' -- if the shift is downfield by more than outlier_sigma 
        standard deviations
    'non_outlier' -- if the shift is within outlier_sigma standard deviations
        of the mean
    """
    if cs_sigma <= -1 * outlier_sigma:
        return 'upfield'
    elif cs_sigma >= outlier_sigma:
        return 'downfield'
    elif abs(cs_sigma) < outlier_sigma:
        return 'non_outlier'

def results_a(proteins_dict, exceptions_map_entries):
    """
    The first stage of printing out the results. Prints
    exceptions_map_entries in more readable format; prints the number of
    entries that had restraints successfully added; prints the number of
    amide-aromatic pairs with at least one NOE between them.

    Keyword arguments:
    proteins_dict -- dict organized by pdb_id and bmrb_id of all succesfully
        created Protein instances
    exceptions_map_entries -- dict organized by pdb_id and bmrb_id of all 
        exceptions raised from failures to add restraints
    """
    print("A:")
    exceptions_by_reason = {}
    for pdb_id in exceptions_map_entries:
        for bmrb_id in exceptions_map_entries[pdb_id]:
            reason = exceptions_map_entries[pdb_id][bmrb_id]
            if reason not in exceptions_by_reason:
                exceptions_by_reason[reason] = 0
            exceptions_by_reason[reason] += 1
    for reason in exceptions_by_reason:
        num = exceptions_by_reason[reason]
        print("  ", reason, ":", num)
    num_entries = 0
    num_pairs = 0
    for pdb_id in proteins_dict:
        for bmrb_id in proteins_dict[pdb_id]:
            num_entries += 1
            protein = proteins_dict[pdb_id][bmrb_id]
            pairs_dict = protein.pairs_dict
            for atom_amide in pairs_dict:
                for res_index_aroma in pairs_dict[atom_amide]:
                    num_pairs += 1
    print("  ", "NUM ENTRIES WITH USABLE RESTRAINTS:    ", num_entries)
    print("  ", "NUM AMIDE-AROMATIC PAIRS WITH A RESTRAINT:    ", num_pairs)

def results_b(proteins_dict):
    """
    The second stage of printing out the results. Prunes undefined pairs from
    each protein.pairs_dict. Prints the number of amide-aromatic pairs with at
    least one defined restraint between them.

    Keyword arguments:
    proteins_dict -- dict organized by pdb_id and bmrb_id of all successfully
        created Protein instances
    """
    print("B:")
    num_pairs = 0
    for pdb_id in proteins_dict:
        for bmrb_id in proteins_dict[pdb_id]:
            protein = proteins_dict[pdb_id][bmrb_id]
            protein.prune_undefined_pairs()
            pairs_dict = protein.pairs_dict
            for atom_amide in pairs_dict:
                for res_index_aroma in pairs_dict[atom_amide]:
                    atoms_aroma = pairs_dict[atom_amide][res_index_aroma]
                    if len(atoms_aroma) != 0:
                        num_pairs += 1
    print(
        "  ", "NUM AMIDE_AROMATIC PAIRS WITH A DEFINED RESTRAINT:    ", num_pairs
    )

def results_c(proteins_dict, outlier_sigma):
    """
    The third and final stage of printing out the results. Classifies all
    amide-aromatic pairs with at least one defined restraint using 
    get_confidence_tier(). Prints out results in readable format.

    Keyword arguments:
    proteins_dict -- dict organized by pdb_id and bmrb_id of all successfully
        created Protein instances
    outlier_sigma -- the number of standard deviations from mean that make an
        atom's chemical shift an outlier
    """
    conf_tiers = {
        'upfield': {
            'high': {'HIS': [], 'TRP': [], 'PHE': [], 'TYR': []},
            'intermediate': {'HIS': [], 'TRP': [], 'PHE': [], 'TYR': []},
            'low': {'HIS': [], 'TRP': [], 'PHE': [], 'TYR': []}, 
            'none': {'HIS': [], 'TRP': [], 'PHE': [], 'TYR': []}
        },
        'downfield': {
            'high': {'HIS': [], 'TRP': [], 'PHE': [], 'TYR': []},
            'intermediate': {'HIS': [], 'TRP': [], 'PHE': [], 'TYR': []},
            'low': {'HIS': [], 'TRP': [], 'PHE': [], 'TYR': []}, 
            'none': {'HIS': [], 'TRP': [], 'PHE': [], 'TYR': []}
        },
        'non_outlier': {
            'high': {'HIS': [], 'TRP': [], 'PHE': [], 'TYR': []},
            'intermediate': {'HIS': [], 'TRP': [], 'PHE': [], 'TYR': []},
            'low': {'HIS': [], 'TRP': [], 'PHE': [], 'TYR': []}, 
            'none': {'HIS': [], 'TRP': [], 'PHE': [], 'TYR': []}
        },
    }
    for pdb_id in proteins_dict:
        for bmrb_id in proteins_dict[pdb_id]:
            protein = proteins_dict[pdb_id][bmrb_id]
            protein.prune_undefined_pairs()
            pairs_dict = protein.pairs_dict
            for atom_amide in pairs_dict:
                for res_index in pairs_dict[atom_amide]:
                    atoms_aroma = pairs_dict[atom_amide][res_index]
                    atoms_aroma = [atom[0] for atom in atoms_aroma] #removing tags
                    if len(atoms_aroma) > 0:
                        conf_tier, label_aroma = get_confidence_tier(
                            atoms_aroma
                        )
                        shift_class = classify_shift(
                            atom_amide.cs_sigma, outlier_sigma
                        )
                        conf_tiers[shift_class][conf_tier][label_aroma].append(
                            [pdb_id, bmrb_id, atom_amide, atoms_aroma]
                        )


    print("C:")
    for shift_class in conf_tiers:
        print(f"  {shift_class}:")
        for conf_tier in conf_tiers[shift_class]:
            print(f"    {conf_tier}:")
            for res_label in conf_tiers[shift_class][conf_tier]:
                atoms_list = conf_tiers[shift_class][conf_tier][res_label]
                num = len(atoms_list)
                print(f"      {res_label}:  {num}")

    pairs_info_list = conf_tiers['downfield']['high']['HIS']
    for pair_info in pairs_info_list:
        pdb_id = pair_info[0]
        bmrb_id = pair_info[1]
        atom_amide = pair_info[2]
        atom_aroma = pair_info[3][0]
        print(
            pdb_id, bmrb_id, atom_amide.res_index, atom_amide.res_label, 
            atom_aroma.res_index, atom_aroma.res_label)

def print_result_stages(
    outlier_sigma, build_anyway=False
    ):
    """
    Generates dict of all proteins with BMRB and PDB entries, analyzes 
    restraint data, and prints out major results.

    Keyword arguments:
    outlier_sigma -- the number of standard deviations from mean that make an
        atom's chemical shift an outlier
    build_anyway -- default False; if True, proteins will be built even if a 
        json build file is present in ./proteins
    """
    entries_dict = get_all_entries()
    proteins_dict, exceptions_map_entries = get_proteins_dict_multi(
        entries_dict, build_anyway
    )
    reasons_dict = {}
    for pdb_id in proteins_dict:
        for bmrb_id in proteins_dict[pdb_id]:
            protein = proteins_dict[pdb_id][bmrb_id]
            exceptions_map = protein.exceptions_map_residues
            for res_index in exceptions_map:
                reason = exceptions_map[res_index]
                if reason not in reasons_dict:
                    reasons_dict[reason] = 0
                reasons_dict[reason] += 1
    print(reasons_dict)
    for pdb_id in proteins_dict:
        for bmrb_id in proteins_dict[pdb_id]:
            protein = proteins_dict[pdb_id][bmrb_id]
            exceptions_map = protein.exceptions_map_restraints
            for res_index in exceptions_map:
                reason = exceptions_map[res_index]
                if reason not in reasons_dict:
                    reasons_dict[reason] = 0
                reasons_dict[reason] += 1
    print(reasons_dict)


    results_a(proteins_dict, exceptions_map_entries)
    results_b(proteins_dict)
    results_c(proteins_dict, outlier_sigma)
