import unittest
from cortado_core.process_tree_utils.reduction import *
from cortado_core.utils.start_and_end_activities import *
from pm4py.objects.process_tree.obj import ProcessTree
from pm4py.objects.process_tree.utils.generic import parse as pt_parse



class InsertArtficialActivitiesTest(unittest.TestCase):
    def test_Insert_Artificial_Start_End(self):

        t1 = pt_parse("+( ->('A','B','A', X('D', 'C') ) )")
        t1_expected = pt_parse("->('" + ARTIFICIAL_START_ACTIVITY_NAME + "', + (->('A','B','A', X('D', 'C') ) ),'" + ARTIFICIAL_END_ACTIVITY_NAME + "')")

        self.assertEqual(add_artificial_start_and_end_to_pt(t1), t1_expected)
                
    def test_Insert_and_Remove_Artificial_Start_End(self):
        t1 = pt_parse("+ (->('A','B','A', X('D', 'C')))")
        t1_expected = pt_parse("->('A','B','A', X('D', 'C'))")
        t1_arti = add_artificial_start_and_end_to_pt(t1)

        self.assertEqual(t1_expected, remove_artificial_start_and_end_activity_leaves_from_pt(t1_arti))

        t2: ProcessTree = pt_parse(
        "+ (->('A','" + ARTIFICIAL_END_ACTIVITY_NAME + "','A', '" + ARTIFICIAL_START_ACTIVITY_NAME + "'),'C'))"
        )

        t2_arti =  add_artificial_start_and_end_to_pt(t2)
        t2_expected = pt_parse("+(->('A','A'),'C')")

        self.assertEqual(remove_artificial_start_and_end_activity_leaves_from_pt(t2_arti), t2_expected)

    def test_Insert_Artificial_Start_End_to_Log(self):
 
        L = EventLog()

        e1 = Event()
        e1["concept:name"] = "A"
        e2 = Event()
        e2["concept:name"] = "B"
        e3 = Event()
        e3["concept:name"] = "C"
        e4 = Event()
        e4["concept:name"] = "D"
        e5 = Event()
        e5["concept:name"] = "A"
        e6 = Event()
        e6["concept:name"] = "B"
        e7 = Event()
        e7["concept:name"] = "E"
        e8 = Event()
        e8["concept:name"] = "F"

        t = Trace()
        t.append(e1)
        t.append(e2)
        t.append(e3)
        t.append(e4)
        t.append(e5)
        t.append(e6)
        t.append(e7)
        t.append(e8)
        L.append(t)

        t1 = Trace()
        t1.append(e1)
        t1.append(e2)
        t1.append(e2)
        t1.append(e3)
        t1.append(e4)
        t1.append(e4)
        t1.append(e4)
        t1.append(e5)
        t1.append(e6)
        t1.append(e7)
        t1.append(e8)
        L.append(t1)


        t2 = Trace()
        t2.append(e1)
        t2.append(e2)
        t2.append(e2)
        t2.append(e3)
        t2.append(e4)
        t2.append(e5)
        t2.append(e6)
        t2.append(e7)
        t2.append(e8)
        L.append(t2)

       

        New_Log  = add_artificial_start_and_end_activity_to_Log(L, inplace = False)

        self.assertEqual(L,L)
        self.assertNotEqual(L, New_Log)

        add_artificial_start_and_end_activity_to_Log(L, inplace = True)
        self.assertEqual(L, New_Log)

        t_compare = Trace()
        t_compare.append(Event({DEFAULT_TRACEID_KEY: ARTIFICIAL_START_ACTIVITY_NAME}))
        t_compare.append(e1)
        t_compare.append(e2)
        t_compare.append(e2)
        t_compare.append(e3)
        t_compare.append(e4)
        t_compare.append(e4)
        t_compare.append(e4)
        t_compare.append(e5)
        t_compare.append(e6)
        t_compare.append(e7)
        t_compare.append(e8)
        t_compare.append(Event({DEFAULT_TRACEID_KEY: ARTIFICIAL_END_ACTIVITY_NAME}))

        self.assertEqual(t_compare, add_artificial_start_and_end_activity_to_trace(t1))




        

