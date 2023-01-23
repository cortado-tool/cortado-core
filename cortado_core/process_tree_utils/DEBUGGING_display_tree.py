from pm4py.objects.log.obj import Event, Trace
from pm4py.objects.process_tree.utils.generic import parse as pt_parse
import pm4py.visualization.process_tree.visualizer as tree_vis

from pm4py.algo.conformance.alignments.process_tree.variants import search_graph_pt as tree_alignment

if __name__ == "__main__":
    t = pt_parse(
        "->( 'Create Fine', X( tau, 'Send Fine' ), X( tau, 'Payment' ), X( tau, 'Send Fine' ), X( tau, ->( X( tau, +( 'Send Fine', *( ->( X( tau, 'Send Fine' ), *( +( ->( X( tau, +( X( tau, 'Insert Date Appeal to Prefecture' ), X( tau, +( X( tau ), X( tau, 'Insert Fine Notification' ) ) ) ) ), X( tau, 'Appeal to Judge' ), X( tau, *( X( 'Notify Result Appeal to Offender', 'Send Appeal to Prefecture', 'Receive Result Appeal from Prefecture', 'Send for Credit Collection', tau ), tau ) ) ), X( +( *( tau, 'Payment' ), 'Add penalty' ), tau ) ), tau ) ), tau ) ) ), X( tau, 'Payment' ) ) ) )")
    print(t)
    tree_vis.view(tree_vis.apply(t, parameters={"format": "svg"}))
    activities = ['Create Fine', 'Send Fine', 'Insert Fine Notification', 'Insert Date Appeal to Prefecture',
                  'Add penalty', 'Send Appeal to Prefecture', 'Receive Result Appeal from Prefecture',
                  'Notify Result Appeal to Offender', 'Appeal to Judge', 'Payment', 'Payment']
    trace = Trace()
    for a in activities:
        e = Event()
        e["concept:name"] = a
        trace.append(e)

    # n, i, f = pt_to_net(t, variant=pt_to_net_variants.TO_PETRI_NET_TRANSITION_BORDERED)
    # align = alignment(trace, n, i, f)
    # print(align)

    tree_align = tree_alignment.apply(trace, t)
    print(tree_align)
