from lxml import etree
from cortado_core.utils.split_graph import SequenceGroup, ParallelGroup, LeafGroup


def create_valid_element_name(name: str) -> str:
    """
    Create a valid XML element name by replacing invalid characters.
    """
    valid_name = []
    for c in name:
        if c.isalnum() or c in ["_", "-", "."]:
            valid_name.append(c)
        else:
            valid_name.append("_")
    return "".join(valid_name)


def build_variant(variant: SequenceGroup) -> etree.Element:
    return build_sequence_group(variant)


def build_sequence_group(node: SequenceGroup) -> etree.Element:
    sequence = etree.Element("sequence")

    for child in node:
        ctype = type(child)
        if ctype is LeafGroup:
            etree.SubElement(sequence, create_valid_element_name(child[0]))
        elif ctype is ParallelGroup:
            sequence.append(build_parallel_group(child))
        else:
            raise ValueError(f"Unknown group type in sequence: {ctype}")

    return sequence


def build_parallel_group(node: ParallelGroup) -> etree.Element:
    parallel = etree.Element("parallel")

    for child in node:
        ctype = type(child)
        if ctype is LeafGroup:
            etree.SubElement(parallel, create_valid_element_name(child[0]))
        elif ctype is SequenceGroup:
            parallel.append(build_sequence_group(child))
        else:
            raise ValueError(f"Unknown group type in parallel: {ctype}")

    return parallel
