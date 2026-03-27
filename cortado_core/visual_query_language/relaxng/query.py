from cortado_core.utils.split_graph import (
    SequenceGroup,
    ParallelGroup,
    LeafGroup,
    LoopGroup,
    OptionalGroup,
    ChoiceGroup,
    WildcardGroup,
    AnythingGroup,
    StartGroup,
    EndGroup,
    FallthroughGroup,
    Group,
)
from lxml import etree
from typing import List


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


def build_query(query: SequenceGroup) -> etree.RelaxNG:
    grammar = etree.Element("grammar", xmlns="http://relaxng.org/ns/structure/1.0")
    grammar.append(build_anything_pattern())

    query = SequenceGroup(lst=query.copy())

    if type(query[0]) is not StartGroup:
        query.insert(0, OptionalGroup(lst=[AnythingGroup()]))
    else:
        query.pop(0)

    if type(query[-1]) is not EndGroup:
        query.append(OptionalGroup(lst=[AnythingGroup()]))
    else:
        query.pop()

    start = etree.SubElement(grammar, "start")
    start.append(build_sequence_group(query))

    s = etree.tostring(grammar)
    return etree.RelaxNG(etree.fromstring(s))


def build_anything_pattern() -> etree.Element:
    return etree.fromstring(
        '<define name="anything_pattern"><oneOrMore><element><anyName /><zeroOrMore><ref name="anything_pattern" /></zeroOrMore></element></oneOrMore></define>'
    )


def build_sequence_group(node: SequenceGroup) -> etree.Element:
    sequence = etree.Element("element", name="sequence")
    sequence.extend(build_elements(node, flat_sequence=True))
    return sequence


def build_parallel_group(node: ParallelGroup) -> etree.Element:
    parallel = etree.Element("element", name="parallel")
    interleave = etree.SubElement(parallel, "interleave")
    interleave.extend(build_elements(node, flat_sequence=False))
    return parallel


def build_optional_group(node: OptionalGroup, flat_sequence: bool) -> etree.Element:
    assert node.list_length() == 1, "OptionalGroup must have exactly one child"

    optional = etree.Element("optional")
    for element in build_elements(node, flat_sequence):
        optional.append(element)

    return optional


def build_choice_group(node: ChoiceGroup) -> etree.Element:
    choice = etree.Element("choice")

    for child in node:
        if type(child) is not LeafGroup:
            raise ValueError("ChoiceGroup children must be LeafGroups")

        elem = etree.SubElement(
            choice, "element", name=create_valid_element_name(child[0])
        )
        etree.SubElement(elem, "empty")

    return choice


def build_wildcard_group(node: WildcardGroup) -> etree.Element:
    element = etree.Element("element")
    etree.SubElement(element, "anyName")
    etree.SubElement(element, "empty")
    return element


def build_leaf_group(node: LeafGroup) -> etree.Element:
    element = etree.Element("element", name=create_valid_element_name(node[0]))
    etree.SubElement(element, "empty")
    return element


def build_loop_group(node: LoopGroup, flat_sequence: bool) -> List[etree.Element]:
    assert node.list_length() == 1, "LoopGroup must have exactly one child"
    elements = []

    min = 1
    if node.min_count is not None:
        min = max(1, node.min_count)

    for _ in range(min):
        elements.extend(build_elements(node, flat_sequence))

    if node.max_count is not None:
        max_count = max(node.max_count, min)
        optional_count = max_count - min
        for _ in range(optional_count):
            optional = etree.Element("optional")
            optional.extend(build_elements(node, flat_sequence))
            elements.append(optional)

    else:
        loop = etree.Element("zeroOrMore")
        loop.extend(build_elements(node, flat_sequence))

    return elements


def build_anything_group(node: AnythingGroup) -> etree.Element:
    return etree.Element("ref", name="anything_pattern")


def build_elements(node: Group, flat_sequence: bool) -> List[etree.Element]:
    elements = []

    for child in node:
        ctype = type(child)
        if ctype is SequenceGroup:
            if flat_sequence:
                elements.extend(build_elements(child, flat_sequence=True))
            else:
                elements.append(build_sequence_group(child))

        elif ctype is ParallelGroup:
            elements.append(build_parallel_group(child))

        elif ctype is LeafGroup:
            elements.append(build_leaf_group(child))

        elif ctype is OptionalGroup:
            elements.append(build_optional_group(child, flat_sequence))

        elif ctype is ChoiceGroup:
            elements.append(build_choice_group(child))

        elif ctype is WildcardGroup:
            elements.append(build_wildcard_group(child))

        elif ctype is LoopGroup:
            elements.extend(build_loop_group(child, flat_sequence))

        elif ctype is AnythingGroup:
            elements.append(build_anything_group(child))

        elif ctype is FallthroughGroup:
            continue  # TODO: implement FallthroughGroup handling

        elif ctype is StartGroup or ctype is EndGroup:
            raise TypeError(f"{ctype.__name__} should not appear in the query tree")

        else:
            raise TypeError(f"Unknown node type: {ctype}")

    return elements
