"""The discrete event timeline - ADR 012's load-bearing decision.

One event loop from day one, even while only DPS is read out of it: mana,
tank survivability and healing are later readouts of the same timeline,
and retrofitting a timeline is a rewrite.

Time is INTEGER MILLISECONDS. Floats drift and make event order depend on
accumulated rounding; the game server itself ticks in ms. Determinism rule:
events at the same timestamp fire in scheduling order (a monotonic sequence
number breaks ties), so a run is exactly reproducible from its seed.
"""

import heapq


class TimelineError(Exception):
    pass


class Timeline(object):
    def __init__(self):
        self._heap = []
        self._seq = 0
        self.now_ms = 0

    def schedule(self, at_ms, callback):
        """Schedule callback() to fire at at_ms (absolute, integer ms)."""
        if not isinstance(at_ms, int):
            raise TimelineError(
                "event time %r is not an integer millisecond" % (at_ms,))
        if at_ms < self.now_ms:
            raise TimelineError(
                "event scheduled at %d ms, in the past of %d ms"
                % (at_ms, self.now_ms))
        heapq.heappush(self._heap, (at_ms, self._seq, callback))
        self._seq += 1

    def schedule_in(self, delay_ms, callback):
        self.schedule(self.now_ms + delay_ms, callback)

    def run_until(self, end_ms):
        """Fire events in order until end_ms (exclusive). Events scheduled
        at exactly end_ms do not fire - the fight is over."""
        while self._heap and self._heap[0][0] < end_ms:
            at_ms, _seq, callback = heapq.heappop(self._heap)
            self.now_ms = at_ms
            callback()
        self.now_ms = end_ms
