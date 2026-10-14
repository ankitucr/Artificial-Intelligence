class IntervalTree:
    def __init__(self, intervals):
        self.intervals = sorted(intervals, key=lambda x: x[0])

    def query(self, start, end):
        overlapping_intervals = []
        for interval in self.intervals:
            if start <= interval[1] and end >= interval[0]:
                overlapping_intervals.append(interval)
        return overlapping_intervals

def interval_tree_query(intervals, start, end):
    tree = IntervalTree(intervals)
    return tree.query(start, end)