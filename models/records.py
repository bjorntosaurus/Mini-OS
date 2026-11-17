"""Plain data records shared by algorithms and GUI."""
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class Process:
    pid: str
    arrival: int
    burst: int
    priority: int = 0


@dataclass
class Slice:
    pid: Optional[str]          # None = CPU idle
    start: int
    end: int


@dataclass
class ProcMetrics:
    pid: str
    arrival: int
    burst: int
    start: int                   # first time on CPU
    finish: int                  # completion time
    turnaround: int
    waiting: int
    response: int


@dataclass
class ScheduleResult:
    algorithm: str
    slices: List[Slice]
    metrics: List[ProcMetrics]
    avg_waiting: float
    avg_turnaround: float
    cpu_busy: float              # 0..1
    throughput: float
    makespan: int
    order: List[str]


@dataclass
class SafetyStep:
    pid: str
    work_before: Tuple[int, ...]
    work_after: Tuple[int, ...]


@dataclass
class SafetyResult:
    safe: bool
    sequence: List[int]
    steps: List[SafetyStep]
    unfinished: List[int]
    need: List[List[int]]


@dataclass
class RequestResult:
    granted: bool
    reason: str
    safety: Optional[SafetyResult]


@dataclass
class Translation:
    status: str                  # ok | page_fault | invalid
    message: str
    page: Optional[int] = None
    offset: Optional[int] = None
    frame: Optional[int] = None
    physical: Optional[int] = None


@dataclass
class ReplStep:
    index: int
    page: int
    frames: List[Optional[int]]
    fault: bool
    evicted: Optional[int]
    slot: Optional[int]          # frame slot written (None on hit)


@dataclass
class ReplResult:
    algorithm: str
    steps: List[ReplStep]
    faults: int
    hits: int
    fault_ratio: float
    hit_ratio: float
    final_queue: List[int]
    queue_labels: Tuple[str, str]


@dataclass
class Segment:
    seg_id: int
    name: str
    base: int
    limit: int
    perms: str = "READ / WRITE"


@dataclass
class SegTranslation:
    valid: bool
    message: str
    segment: Optional[Segment] = None
    offset: Optional[int] = None
    physical: Optional[int] = None


@dataclass
class BlockReport:
    index: int
    size: int
    processes: List[int]         # indexes of processes placed here
    used: int
    internal: int                # wasted inside an allocated block (fixed mode)
    free: int                    # unallocated memory left in this block


@dataclass
class FragResult:
    strategy: str
    mode: str
    blocks: List[BlockReport]
    assignment: List[Optional[int]]   # process index -> block index
    unallocated: List[int]
    total_memory: int
    used: int
    internal: int
    free_total: int
    external: int
    largest_free: int


@dataclass
class DiskResult:
    algorithm: str
    path: List[int]              # every head position visited, starting with the head
    order: List[int]             # requests in service order
    seeks: List[int]             # head movement attributed to each serviced request
    total: int
    average: float
    kinds: List[str] = field(default_factory=list)   # per path point: B waypoint, S service, J jump, JS jump+service


@dataclass
class Program:
    name: str
    memory: int
    cpu_time: int
    io_wait: float = 0.5         # probability a resident program is blocked on I/O in any tick
    resources: int = 0
    arrival: int = 0


@dataclass
class SimResult:
    states: List[List[str]]      # per program: one char per tick
    mem_used: List[int]
    res_used: List[int]
    cpu_busy: List[bool]
    admitted_at: List[Optional[int]]
    finish: List[Optional[int]]
    ticks: int
    cpu_utilization: float
    avg_memory_util: float
    peak_memory: int
    max_degree: int
    avg_turnaround: float
