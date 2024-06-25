from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.statistics.traces.log import case_statistics
from pm4py.algo.discovery.inductive import algorithm as inductive_miner
from pm4py.visualization.process_tree import visualizer as pt_vis_factory
from pm4py.algo.filtering.log.variants import variants_filter
from naive_approach import ensure_trace_replayable_on_process_tree

log_path = "C:/Users/dschuste/Documents/event_logs/road_traffic_fine_management/log.xes"
log = xes_importer.apply(log_path)

variants_count = case_statistics.get_variant_statistics(log)
variants_count = sorted(variants_count, key=lambda x: x["count"], reverse=True)

print("number of variants: ", variants_count)

most_frequent_trace_log = variants_filter.apply(log, [variants_count[0]["variant"]])

tree = inductive_miner.apply_tree(most_frequent_trace_log)
gviz = pt_vis_factory.apply(tree, parameters={"format": "svg"})
pt_vis_factory.view(gviz)

for trace in log:
    readable_trace = ""
    for e in trace:
        readable_trace += e["concept:name"] + ", "
    print(readable_trace)
    tree = ensure_trace_replayable_on_process_tree(trace, tree)
    gviz = pt_vis_factory.apply(tree, parameters={"format": "svg"})
    pt_vis_factory.view(gviz)
