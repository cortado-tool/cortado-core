from typing import List
from enum import Enum
from itertools import chain

from cortado_core.utils.split_graph import (
    AnythingGroup,
    Group,
    LeafGroup,
    StartGroup,
    EndGroup,
    SequenceGroup,
    ParallelGroup,
    FallthroughGroup,
    OptionalGroup,
    WildcardGroup,
    ChoiceGroup,
    LoopGroup,
)
from cortado_core.visual_query_language.matching_functions import match
from cortado_core.visual_query_language.virtual_machine.parallel_solver import (
    ParallelSolver,
)


class Instruction(Enum):
    MATCH_LEAF = 0
    MATCH_NODE = 1
    MATCH_PARALLEL = 2
    READ_LEAF = 3
    READ_ANY = 4
    JUMP = 5
    SPLIT = 6
    ACCEPT = 7


class ThreadResult(Enum):
    SUSPENDED = 0
    ACCEPTED = 1
    KILLED = 2


class VM:
    def __init__(
        self,
        prog: List[int],
        has_start,
        has_end: bool,
    ):
        self.prog = prog
        self.has_start = has_start
        self.has_end = has_end
        self.lazy = False

    def run(self, variant: SequenceGroup) -> bool:
        if self.lazy:
            return self.run_lazy(variant)

        # Bring types into local scope for performance
        tLeafGroup = LeafGroup
        tParallelGroup = ParallelGroup
        match_node = match
        has_start = self.has_start
        has_end = self.has_end
        prog = self.prog

        visited = [-1] * len(self.prog)
        clist = [0]
        nlist = []

        for idx, el in enumerate(chain(variant, [None])):
            etype = type(el)
            is_leaf = etype is tLeafGroup
            is_parallel = etype is tParallelGroup
            for pc in clist:
                while True:
                    instruction = prog[pc]

                    # Prevent multiple threads in same state for same input position (stop epsilon loops)
                    visited[pc] = idx

                    # read instruction
                    if instruction < 5:
                        # Instruction.MATCH_LEAF:
                        if instruction == 0:
                            if not is_leaf:
                                break
                            if prog[pc + 1][0] != el[0]:
                                break
                            pc += 2

                        # Instruction.READ_ANY:
                        elif instruction == 4:
                            pc += 1

                        # Instruction.MATCH_NODE:
                        elif instruction == 1:
                            if not match_node(prog[pc + 1], el):
                                break
                            pc += 2

                        # Instruction.READ_LEAF:
                        elif instruction == 3:
                            if not is_leaf:
                                break
                            pc += 1

                        # Instruction.MATCH_PARALLEL:
                        elif instruction == 2:
                            if not is_parallel:
                                break
                            if not prog[pc + 1].match(el):
                                break
                            pc += 2

                        # Check for duplicate threads in next input
                        if visited[pc] != idx + 1:
                            nlist.append(pc)
                        break

                    # control flow instruction
                    else:
                        # Instruction.SPLIT:
                        if instruction == 6:
                            new_thread1 = pc + prog[pc + 1]
                            new_thread2 = pc + prog[pc + 2]
                            if visited[new_thread2] != idx:
                                # pylint: disable=modified-iterating-list
                                clist.append(new_thread2)
                            if visited[new_thread1] != idx:
                                pc = new_thread1
                            else:
                                break

                        # Instruction.JUMP:
                        elif instruction == 5:
                            new_pos = pc + prog[pc + 1]
                            if visited[new_pos] == idx:
                                break
                            pc = new_pos

                        # Instruction.ACCEPT:
                        elif instruction == 7:
                            if has_end and el is not None:
                                break
                            return True

            if not has_start:
                nlist.append(0)

            elif not nlist:
                return False

            clist, nlist = nlist, clist
            nlist = []
        return False

    def run_lazy(self, variant: SequenceGroup) -> bool:
        # Bring types into local scope for performance
        tLeafGroup = LeafGroup
        tParallelGroup = ParallelGroup
        match_node = match
        has_start = self.has_start
        has_end = self.has_end
        prog = self.prog

        clist = [(0, -1, -1)]  # (pc, lazy_qnode, lazy_vnode)
        nlist = []

        for idx, el in enumerate(chain(variant, [None])):
            visited = set()
            for pc, lazy_qnode, lazy_vnode in clist:
                etype = type(el)
                is_leaf = etype is tLeafGroup
                is_parallel = etype is tParallelGroup
                while True:
                    instruction = prog[pc]

                    # Prevent multiple threads in same state for same input position (stop epsilon loops)
                    state = (pc, lazy_qnode, lazy_vnode)
                    if state in visited:
                        break
                    visited.add(state)

                    # read instruction
                    if instruction < 5:
                        # Instruction.MATCH_LEAF:
                        if instruction == 0:
                            if not is_leaf:
                                break
                            if prog[pc + 1][0] != el[0]:
                                break
                            pc += 2

                        # Instruction.READ_ANY:
                        elif instruction == 4:
                            pc += 1

                        # Instruction.MATCH_NODE:
                        elif instruction == 1:
                            if not match_node(prog[pc + 1], el):
                                break
                            pc += 2

                        # Instruction.READ_LEAF:
                        elif instruction == 3:
                            if not is_leaf:
                                break

                            pc += 1

                        # Instruction.MATCH_PARALLEL:
                        elif instruction == 2:
                            if not is_parallel:
                                break

                            # We currently save only one lazy parallel (the last one)
                            if lazy_qnode > -1:
                                if not prog[lazy_qnode].match(variant[lazy_vnode]):
                                    break

                            # Save current parallel as lazy for later checking
                            # Were only use int numbers for faster hashing in the visited set
                            lazy_qnode, lazy_vnode = (pc + 1, idx)
                            pc += 2

                        nlist.append((pc, lazy_qnode, lazy_vnode))
                        break

                    # control flow instruction
                    else:
                        # Instruction.SPLIT:
                        if instruction == 6:
                            # pylint: disable=modified-iterating-list
                            clist.append((pc + prog[pc + 2], lazy_qnode, lazy_vnode))
                            pc += prog[pc + 1]

                        # Instruction.JUMP:
                        elif instruction == 5:
                            offset = prog[pc + 1]
                            pc += offset

                        # Instruction.ACCEPT:
                        elif instruction == 7:
                            if has_end and el is not None:
                                break

                            # If any parallel was lazy, check it now
                            if lazy_qnode > -1:
                                if not prog[lazy_qnode].match(variant[lazy_vnode]):
                                    break

                            return True

            if not has_start:
                # Take any element as a potential start
                nlist.append((0, -1, -1))

            elif not nlist:
                return False

            clist, nlist = nlist, clist
            nlist = []
        return False

    def print_prog(self):
        pc = 0
        while pc < len(self.prog):
            instruction = Instruction(self.prog[pc])
            print(f"{pc}: {instruction.name}", end=" ")
            match instruction:
                case Instruction.MATCH_LEAF | Instruction.MATCH_NODE:
                    print(self.prog[pc + 1])
                    pc += 2
                case Instruction.MATCH_PARALLEL:
                    node_index = self.prog[pc + 1]
                    print(f"{node_index} (ParallelSolver)")
                    pc += 2
                case Instruction.JUMP:
                    offset = self.prog[pc + 1]
                    print(f"{pc + offset}")
                    pc += 2
                case Instruction.SPLIT:
                    offset1 = self.prog[pc + 1]
                    offset2 = self.prog[pc + 2]
                    print(f"{pc + offset1} , {pc + offset2}")
                    pc += 3
                case _:
                    print()
                    pc += 1


def compile_vm(query: SequenceGroup, lazy: bool) -> VM:
    compiler = VMCompiler()
    compiler.compile(query, lazy)
    return compiler.vm


class VMCompiler:
    def __init__(self):
        self.vm = VM([], False, False)

    def compile(self, query: SequenceGroup, lazy: bool) -> List[int]:
        self.vm.has_start = isinstance(query[0], StartGroup)
        self.vm.has_end = isinstance(query[-1], EndGroup)
        self.vm.lazy = lazy

        if self.vm.has_start:
            query = SequenceGroup(query[1:])

        if self.vm.has_end:
            query = SequenceGroup(query[:-1])

        prog = self.compile_seq(query)
        prog.append(Instruction.ACCEPT.value)

        self.vm.prog = prog

    def compile_group(self, group: Group) -> List[int]:
        etype = type(group)
        if etype is LeafGroup:
            return self.compile_leaf(group)

        elif etype is FallthroughGroup:
            return self.compile_fallthrough(group)

        elif etype is OptionalGroup:
            return self.compile_optional(group)

        elif etype is SequenceGroup:
            return self.compile_seq(group)

        elif etype is ParallelGroup:
            return self.compile_parallel(group)

        elif etype is WildcardGroup:
            return self.compile_wildcard()

        elif etype is AnythingGroup:
            return self.compile_anything()

        elif etype is ChoiceGroup:
            return self.compile_choice(group)

        elif etype is LoopGroup:
            return self.compile_loop(group)

        elif etype is StartGroup or etype is EndGroup:
            raise ValueError(f"{etype} should be handled outside of VM compilation")

        else:
            raise TypeError(f"Unsupported group type: {etype}")

    def compile_seq(self, seq: SequenceGroup) -> List[int]:
        prog = []

        seq_len = seq.list_length()
        for i, element in enumerate(seq):
            if i == seq_len - 1 and isinstance(element, AnythingGroup):
                # Optimize trailing AnythingGroup
                prog.extend([Instruction.READ_ANY.value, Instruction.ACCEPT.value])
                break
            prog.extend(self.compile_group(element))

        return prog

    def compile_leaf(self, leaf: LeafGroup) -> List[int]:
        return [Instruction.MATCH_LEAF.value, leaf]

    def compile_fallthrough(self, fallthrough: FallthroughGroup) -> List[int]:
        return [Instruction.MATCH_NODE.value, fallthrough]

    def compile_optional(self, optional: OptionalGroup) -> List[int]:
        assert (
            optional.list_length() == 1
        ), "OptionalGroup with multiple children not supported yet"
        child_prog = self.compile_group(optional[0])
        prog = [Instruction.SPLIT.value, 3, len(child_prog) + 3]
        prog.extend(child_prog)
        return prog

    def compile_parallel(self, parallel: ParallelGroup) -> List[int]:
        return [
            Instruction.MATCH_PARALLEL.value,
            ParallelSolver(parallel, lazy=self.vm.lazy),
        ]

    def compile_wildcard(self) -> List[int]:
        return [Instruction.READ_LEAF.value]

    def compile_choice(self, choice: ChoiceGroup) -> List[int]:
        return [Instruction.MATCH_NODE.value, choice]

    def compile_loop(self, loop: LoopGroup) -> List[int]:
        assert (
            loop.list_length() == 1
        ), "LoopGroup with multiple children not supported yet"
        child_prog = self.compile_group(loop[0])

        # Minimum count part
        min_prog = child_prog * loop.min_count

        if loop.max_count is None:
            # Unbounded loop part
            loop_prog = [Instruction.SPLIT.value, 3, len(child_prog) + 5]
            loop_prog.extend(child_prog)
            loop_prog.extend([Instruction.JUMP.value, -len(loop_prog)])
            return min_prog + loop_prog

        optional_count = loop.max_count - loop.min_count
        if optional_count == 0:
            return min_prog

        # Bounded unrolling of the loop
        max_prog = []
        for i in range(optional_count, 0, -1):
            max_prog.extend([Instruction.SPLIT.value, 3, i * (3 + len(child_prog))])
            max_prog.extend(child_prog)

        return min_prog + max_prog

    def compile_anything(self) -> List[int]:
        return [
            Instruction.READ_ANY.value,
            Instruction.SPLIT.value,
            3,
            -1,
        ]
