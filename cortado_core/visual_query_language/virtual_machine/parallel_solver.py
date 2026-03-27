import copy
import queue
from typing import Deque, List
from collections import deque
from dataclasses import dataclass
from cortado_core.utils.split_graph import (
    Group,
    OptionalGroup,
    ParallelGroup,
    SequenceGroup,
    LoopGroup,
    LeafGroup,
    FallthroughGroup,
    WildcardGroup,
    AnythingGroup,
    ChoiceGroup,
    StartGroup,
    EndGroup,
)
from cortado_core.visual_query_language.matching_functions import match as match_fn


@dataclass
class SolvingRun:
    queue: Deque
    assigned: List[bool]
    num_anythings: int
    variant: ParallelGroup
    num_attempts: int = 0

    def __str__(self):
        return f"{[element.__class__.__name__ for element in self.queue]} | Assigned: {self.assigned} | Num Anythings: {self.num_anythings}"


class ParallelSolver:
    def __init__(self, query: ParallelGroup, lazy: bool):
        self.query = query
        self.query_length = query.list_length()

        # If query containts a sequence create a vm for it
        self.sequence_vm = None
        self.queue = deque()
        for element in query:
            etype = type(element)
            if etype in (LeafGroup, FallthroughGroup, AnythingGroup, SequenceGroup):
                # Match these mandatory first so in case of backtracking we dont have to try them again
                self.queue.appendleft(element)
            else:
                self.queue.append(element)

            # Find sequence group
            if etype is OptionalGroup:
                element = element[0]
                etype = type(element)

            if etype is SequenceGroup:
                assert (
                    self.sequence_vm is None
                ), "ParallelSolver supports only a single SequenceGroup"
                # pylint: disable=import-outside-toplevel - prevents circular import
                from cortado_core.visual_query_language.virtual_machine.vm import (
                    compile_vm,
                )

                self.sequence_vm = compile_vm(
                    SequenceGroup([StartGroup()] + element[:] + [EndGroup()]), lazy
                )

    def match(self, variant: ParallelGroup) -> bool:
        assigned = [False] * variant.list_length()

        return self.match_next(SolvingRun(copy.copy(self.queue), assigned, 0, variant))

    def match_next(self, run: SolvingRun) -> bool:
        if not run.queue:
            if run.num_anythings == 0:
                return all(run.assigned)
            return run.assigned.count(False) - run.num_anythings >= 0

        run.num_attempts += 1
        assert (
            run.num_attempts < 100000
        ), "Too many attempts in ParallelSolver, possible infinite loop"

        element = run.queue.popleft()
        etype = type(element)

        if etype is LoopGroup:
            if self.match_loop(element, run):
                return True

        elif etype is OptionalGroup:
            if self.match_optional(element, run):
                return True

        elif etype in (LeafGroup, FallthroughGroup):
            # These elements match exactly their counterpart in the variant
            # We only need to find the first unassigned element that matches
            if self.match_exact(element, run):
                return True

        elif etype in (WildcardGroup, ChoiceGroup):
            # These elements can match multiple various elements in the variant
            # We need to try all possible matches so we do not "steal" matches from later elements
            if self.match_various(element, run):
                return True

        elif etype is SequenceGroup:
            if self.match_sequence(run):
                return True

        elif etype is AnythingGroup:
            # Anything matches at least one unassigned element
            run.num_anythings += 1
            if self.match_next(run):
                return True
            run.num_anythings -= 1  # Backtrack

        else:
            raise TypeError(f"Unsupported group type in ParallelSolver: {etype}")

        # Backtrack
        run.queue.appendleft(element)
        return False

    def match_exact(self, element: Group, run: SolvingRun) -> bool:
        for i, _val in enumerate(run.assigned):
            if _val:
                continue

            variant_element = run.variant[i]
            if match_fn(element, variant_element):
                run.assigned[i] = True
                if self.match_next(run):
                    return True
                run.assigned[i] = False  # Backtrack
                break
        return False

    def match_various(self, element: Group, run: SolvingRun) -> bool:
        for i, _val in enumerate(run.assigned):
            if _val:
                continue

            variant_element = run.variant[i]
            if match_fn(element, variant_element):
                run.assigned[i] = True
                if self.match_next(run):
                    return True
                run.assigned[i] = False  # Backtrack
        return False

    def match_loop(self, loop: LoopGroup, run: SolvingRun) -> bool:
        assert (
            loop.list_length() == 1
        ), "LoopGroup in ParallelSolver should contain a single element"
        loop_body = loop[0]

        # MIN repetitions
        for _ in range(loop.min_count):
            run.queue.appendleft(loop_body)

        if self.match_next(run):
            return True

        # MAX repetitions
        if loop.max_count is not None:
            optional_reps = loop.max_count - loop.min_count
            for _ in range(optional_reps):
                run.queue.appendleft(loop_body)
                if self.match_next(run):
                    return True

            # Backtrack
            for _ in range(optional_reps):
                run.queue.popleft()

        else:
            # Unlimited repetitions
            reps = 0
            while True:
                reps += 1
                run.queue.appendleft(loop_body)
                if self.match_next(run):
                    return True

                # No more room for additional repetitions
                if len(run.queue) > len(run.assigned):
                    break

            # Backtrack
            for _ in range(reps):
                run.queue.popleft()

        # Backtrack
        for _ in range(loop.min_count):
            run.queue.popleft()

        return False

    def match_optional(self, optional: OptionalGroup, run: SolvingRun) -> bool:
        assert (
            optional.list_length() == 1
        ), "OptionalGroup in ParallelSolver should contain a single element"
        optional_body = optional[0]

        # First try: include the optional body
        run.queue.appendleft(optional_body)
        if self.match_next(run):
            return True

        # Second try: exclude the optional body
        run.queue.popleft()
        return self.match_next(run)

    def match_sequence(self, run: SolvingRun) -> bool:
        assert self.sequence_vm is not None, "No sequence VM available for matching"

        for i, assigned in enumerate(run.assigned):
            if assigned:
                continue

            if not isinstance(run.variant[i], SequenceGroup):
                continue

            variant_element = run.variant[i]
            if self.sequence_vm.run(variant_element):
                run.assigned[i] = True
                if self.match_next(run):
                    return True
                run.assigned[i] = False  # Backtrack
            break  # There will be only one sequence in parallel group

        return False
