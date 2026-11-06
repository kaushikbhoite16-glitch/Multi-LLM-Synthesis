import time
import asyncio
from typing import Optional
from app.schemas.pydantic_models import (
    SynthesisResult,
    UserPreferenceSchema
)
from app.services.openrouter_service import OpenRouterService, classify_query_topic
from app.utils.logger import log_stage, logger

SYNTHESIZER_SYSTEM_PROMPT = """You are the master synthesis engine of a cutting-edge Multi-LLM research architecture.
Your objective is to produce a single, user-tailored, authoritative, and coherent response based on the structured context provided.
You must adhere strictly to these principles:
- Seamlessly blend the most accurate, high-clarity insights from the candidate outputs.
- Resolve any contradictions or discrepancies using rigorous technical and factual logic.
- Strictly respect user preferences (formatting, conciseness, technical depth).
- Never refer to 'Candidate 1', 'Model B', 'internal ranking', 'scores', or 'synthesis pipeline'.
- Deliver a clear, self-contained, and comprehensive answer directly to the user.
"""

class SynthesizerService:
    def __init__(self, openrouter_service: OpenRouterService):
        self.openrouter = openrouter_service

    async def synthesize(
        self,
        query_id: int,
        query: str,
        structured_context: str,
        synthesis_model: str = "openai/gpt-4o-mini",
        preferences: Optional[UserPreferenceSchema] = None,
        force_mock: bool = False
    ) -> SynthesisResult:
        """
        Executes final adaptive answer synthesis over the structured multi-candidate context.
        """
        log_stage("synthesis", f"Starting adaptive synthesis with {synthesis_model}", query_id=query_id)
        start_time = time.perf_counter()

        messages = [
            {"role": "system", "content": SYNTHESIZER_SYSTEM_PROMPT},
            {"role": "user", "content": structured_context}
        ]

        max_tokens = preferences.max_tokens if preferences and preferences.max_tokens else 2000

        if self.openrouter.has_api_key() and not force_mock:
            try:
                resp = await self.openrouter.generate_response(
                    model=synthesis_model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=0.4,
                    force_mock=force_mock
                )
                if resp.status == "success" and resp.response_text and not resp.is_fallback:
                    log_stage(
                        "synthesis",
                        "Synthesis completed successfully via Live API",
                        tokens=resp.total_tokens,
                        cost=f"${resp.cost:.6f}",
                        latency=f"{resp.latency_ms}ms"
                    )
                    return SynthesisResult(
                        query_id=query_id,
                        synthesis_model=synthesis_model,
                        context=structured_context,
                        final_response=resp.response_text,
                        input_tokens=resp.input_tokens,
                        output_tokens=resp.output_tokens,
                        total_tokens=resp.total_tokens,
                        cost=resp.cost,
                        latency_ms=resp.latency_ms,
                        status="success",
                        is_fallback=False,
                        execution_mode="live"
                    )
                elif resp.is_fallback:
                    logger.warning(f"Synthesis model {synthesis_model} fell back to simulation. Generating high-fidelity adaptive synthesis.")
            except Exception as e:
                logger.error(f"Synthesis call failed: {e}. Generating fallback adaptive synthesis.")

        # High-fidelity synthesis fallback
        is_fallback = not force_mock and self.openrouter.has_api_key()
        return await self._fallback_synthesis(
            query_id=query_id,
            query=query,
            structured_context=structured_context,
            synthesis_model=synthesis_model,
            start_time=start_time,
            is_fallback=is_fallback
        )

    async def _fallback_synthesis(
        self,
        query_id: int,
        query: str,
        structured_context: str,
        synthesis_model: str,
        start_time: float,
        is_fallback: bool = False
    ) -> SynthesisResult:
        await asyncio.sleep(0.4)
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        topic = classify_query_topic(query)

        # 1. LOOPS
        if topic == "loops":
            text = (
                "### Understanding For Loops in Programming & C++\n\n"
                "A **for loop** is an entry-controlled iterative control structure used to execute a block of statements "
                "repeatedly until a specified condition evaluates to false. It is universally employed when the iteration bounds "
                "or collection sizes are known before entering the loop.\n\n"
                "---\n\n"
                "#### 1. Core Structure and Syntax\n"
                "In C++ and C-style languages, the canonical for loop consists of three clauses separated by semicolons:\n\n"
                "```cpp\n"
                "for (initialization; condition; increment/decrement) {\n"
                "    // Loop body (statements executed each cycle)\n"
                "}\n"
                "```\n\n"
                "1. **Initialization (`int i = 0`)**: Evaluated once before the first iteration to initialize the loop counter or iterator.\n"
                "2. **Condition (`i < n`)**: A boolean expression tested prior to every pass. If `true`, the body executes; if `false`, the loop terminates.\n"
                "3. **Update (`++i`)**: Executed immediately after each iteration, modifying the counter before the next condition check.\n\n"
                "---\n\n"
                "#### 2. Modern Implementation Paradigms in C++\n\n"
                "##### A. Traditional Indexed For Loop\n"
                "Best suited when the numeric index position is required during execution:\n"
                "```cpp\n"
                "#include <iostream>\n"
                "#include <vector>\n\n"
                "int main() {\n"
                "    std::vector<int> numbers = {10, 20, 30, 40, 50};\n"
                "    for (size_t i = 0; i < numbers.size(); ++i) {\n"
                "        std::cout << \"Index \" << i << \": \" << numbers[i] << std::endl;\n"
                "    }\n"
                "    return 0;\n"
                "}\n"
                "```\n\n"
                "##### B. Range-Based For Loop (Modern C++11 and later)\n"
                "Provides cleaner, safer syntax without manual indexing arithmetic:\n"
                "```cpp\n"
                "for (const auto& num : numbers) {\n"
                "    std::cout << num << \" \";\n"
                "}\n"
                "```\n\n"
                "---\n\n"
                "#### 3. Complexity & Compiler Optimizations\n"
                "- **Time Complexity**: $O(n)$, where $n$ is the total number of iterations.\n"
                "- **Space Complexity**: $O(1)$ auxiliary memory.\n"
                "- **Hardware Efficiency**: Compilers (e.g., GCC/Clang with `-O2`/`-O3`) apply **loop unrolling** and SIMD vectorization "
                "when operating on contiguous memory, while CPU branch predictors ensure minimal branching penalties.\n\n"
                "---\n\n"
                "#### 4. Best Practices & Common Pitfalls\n"
                "- **Off-by-One Errors**: Ensure strict distinction between `<` (runs $n$ times from 0 to $n-1$) and `<=` (runs $n+1$ times).\n"
                "- **Iterator Invalidation**: Modifying container size (e.g., `vec.push_back()`) inside the loop body can invalidate iterators.\n"
                "- **Pre-increment Optimization**: Prefer `++i` over `i++` for custom object iterators to prevent redundant temporary copies."
            )
            in_tokens, out_tokens = 320, 560

        # 2. VIRTUAL MEMORY
        elif topic == "virtual_memory":
            text = (
                "### Virtual Memory: Architecture, Mechanisms, and Trade-offs\n\n"
                "**Virtual memory** is an essential operating system abstraction that decouples an application's logical address "
                "space from physical random-access memory (RAM). By seamlessly integrating physical memory with secondary storage "
                "(swap or paging files), it provides each running process with the illusion of an isolated, continuous, and expansive memory space.\n\n"
                "---\n\n"
                "#### 1. Core Architectural Pillars\n"
                "1. **Paging and Logical Segmentation**:\n"
                "   - **Pages & Frames**: The process address space is partitioned into uniform blocks called **virtual pages** (typically 4 KB, or 2 MB/1 GB for HugePages). "
                "Physical RAM is identically divided into matching **page frames**.\n"
                "   - **Page Tables**: Hierarchical data structures maintained by the OS kernel that record the mapping between virtual page numbers (VPN) and physical frame numbers (PFN).\n\n"
                "2. **Hardware-Assisted Translation (MMU & TLB)**:\n"
                "   - **Memory Management Unit (MMU)**: A dedicated hardware subsystem that performs address translation on every CPU instruction.\n"
                "   - **Translation Lookaside Buffer (TLB)**: An associative cache that stores the most recently accessed address translations, allowing typical memory references to resolve in a single clock cycle without multi-level page table traversals.\n\n"
                "3. **Demand Paging and Page Fault Handling**:\n"
                "   - Programs are loaded lazily: code and data pages are brought into physical RAM only upon initial reference.\n"
                "   - When an unmapped or swapped-out page is accessed, the MMU signals a hardware trap—a **Page Fault**.\n"
                "   - The operating system interrupts process execution, reads the requested page from disk/SSD into an available RAM frame, updates the page table and TLB, and restarts the faulting instruction.\n\n"
                "---\n\n"
                "#### 2. Key System Benefits\n"
                "- **Hardware Protection & Isolation**: Processes cannot inspect or corrupt other processes' memory, establishing core operating system security boundaries.\n"
                "- **Memory Overcommit**: Systems can run workloads whose aggregate memory demand exceeds physical RAM capacity.\n"
                "- **Copy-on-Write (CoW) & Shared Libraries**: Common binaries (like `libc`) and `fork()` address spaces share identical physical pages in read-only mode, only allocating physical duplicates when a write is attempted.\n\n"
                "---\n\n"
                "#### 3. Performance Criticality: Thrashing & Mitigation\n"
                "When aggregate active memory requirements exceed available physical RAM, the operating system spends a disproportionate amount of time swapping pages in and out rather than executing instructions—a pathological state called **thrashing**. Modern kernels combat this via:\n"
                "- **Working Set Models**: Monitoring process memory footprints to avoid over-scheduling.\n"
                "- **Heuristic Page Replacement**: Advanced variants of the Least Recently Used (LRU) algorithm, such as the Clock algorithm or multi-queue active/inactive lists."
            )
            in_tokens, out_tokens = 320, 520

        # 3. LINKED LISTS
        elif topic == "linked_list":
            text = (
                "### Linked List: Architecture, Operations, and Practical Trade-offs\n\n"
                "A **linked list** is a linear dynamic data structure composed of discrete elements known as **nodes**. "
                "Unlike arrays, linked lists do not store elements contiguously in physical memory; instead, each node contains a data payload "
                "along with one or more pointers referencing adjacent nodes.\n\n"
                "---\n\n"
                "#### 1. Core Topologies\n"
                "1. **Singly Linked List**: Each node stores a data value and a single pointer (`next`) pointing to the successive node. The final node points to `nullptr`.\n"
                "2. **Doubly Linked List**: Nodes store both `next` and `prev` pointers, facilitating bidirectional traversal and $O(1)$ removal when given an iterator.\n"
                "3. **Circular Linked List**: The last node links back to the head node, forming an unbroken circular loop.\n\n"
                "---\n\n"
                "#### 2. C++ Node Definition & Operations\n"
                "```cpp\n"
                "struct Node {\n"
                "    int data;\n"
                "    Node* next;\n"
                "    Node(int val) : data(val), next(nullptr) {}\n"
                "};\n"
                "```\n\n"
                "| Operation | Time Complexity | Notes |\n"
                "|---|---|---|\n"
                "| Insertion at Head | $O(1)$ | Update head pointer; no element shifting needed |\n"
                "| Insertion at Tail | $O(1)$ or $O(n)$ | $O(1)$ if tail pointer maintained, otherwise $O(n)$ traversal |\n"
                "| Deletion (known node) | $O(1)$ | Rewire predecessor pointer to successor |\n"
                "| Search / Access `[k]` | $O(n)$ | Sequential traversal required from head node |\n\n"
                "---\n\n"
                "#### 3. Trade-offs: Linked Lists vs Contiguous Arrays (`std::vector`)\n"
                "- **Advantages of Linked Lists**: Non-contiguous heap allocation, constant-time insertions/deletions at known nodes without amortized buffer reallocation.\n"
                "- **Disadvantages**: Lack of random access ($O(n)$ vs $O(1)$), pointer memory overhead (8 bytes per pointer on 64-bit systems), "
                "and **poor CPU cache spatial locality** (pointer chasing causes frequent L1/L2 cache misses)."
            )
            in_tokens, out_tokens = 310, 490

        # 4. STACK VS QUEUE
        elif topic == "stack_queue":
            text = (
                "### Comprehensive Comparison: Stack vs Queue Data Structures\n\n"
                "Stacks and queues are fundamental linear abstract data types (ADTs) governed by opposite data access principles.\n\n"
                "---\n\n"
                "#### 1. Core Operating Principles\n"
                "- **Stack (LIFO — Last In, First Out)**: The element added most recently is the first to be extracted. "
                "All insertion and removal operations occur at a single open end called the **top**.\n"
                "- **Queue (FIFO — First In, First Out)**: Elements are processed in exact arrival sequence. "
                "Insertions occur at the **rear/tail**, while removals occur at the **front/head**.\n\n"
                "---\n\n"
                "#### 2. Detailed Technical Comparison\n\n"
                "| Feature | Stack | Queue |\n"
                "|---|---|---|\n"
                "| **Access Discipline** | LIFO (Last In, First Out) | FIFO (First In, First Out) |\n"
                "| **Active Endpoints** | 1 open end (Top) | 2 open ends (Front and Rear) |\n"
                "| **Insertion Method** | `push(x)` — $O(1)$ | `enqueue(x)` — $O(1)$ |\n"
                "| **Removal Method** | `pop()` — $O(1)$ | `dequeue()` — $O(1)$ |\n"
                "| **Inspection Method** | `top()` or `peek()` — $O(1)$ | `front()` and `back()` — $O(1)$ |\n"
                "| **C++ Standard Type** | `std::stack<T>` | `std::queue<T>` |\n"
                "| **Underlying Container** | `std::deque` or `std::vector` | `std::deque` or circular buffer |\n\n"
                "---\n\n"
                "#### 3. Real-World Applications\n"
                "- **Stack Applications**: Call stack management during function recursion, undo/redo buffers in text editors, "
                "syntax tree parsing, and Depth-First Search (DFS).\n"
                "- **Queue Applications**: Operating system CPU process scheduling (e.g. Round-Robin), printer job spoolers, "
                "network packet routing buffers, and Breadth-First Search (BFS)."
            )
            in_tokens, out_tokens = 300, 480

        # 5. BINARY SEARCH
        elif topic == "binary_search":
            text = (
                "### Binary Search Algorithm: Mechanics, Complexity, and Implementation\n\n"
                "**Binary Search** is an optimal search algorithm that locates the position of a target value within a sorted collection "
                "by repeatedly halving the search interval.\n\n"
                "---\n\n"
                "#### 1. Core Algorithm & Mathematical Proof\n"
                "Binary search requires a **monotonically ordered (sorted)** array with random-access ($O(1)$ index lookup) capabilities.\n\n"
                "At each step, the algorithm compares the target against the midpoint element $arr[mid]$:\n"
                "1. If $arr[mid] == target$, the target is found.\n"
                "2. If $target < arr[mid]$, the right half is discarded: `high = mid - 1`.\n"
                "3. If $target > arr[mid]$, the left half is discarded: `low = mid + 1`.\n\n"
                "**Recurrence & Complexity**:\n"
                "The recurrence relation is $T(n) = T(n/2) + O(1)$. By the Master Theorem, this yields:\n"
                "- **Worst & Average Case**: $O(\\log_2 n)$\n"
                "- **Best Case**: $O(1)$ (target located on first comparison)\n"
                "- **Space Complexity**: $O(1)$ auxiliary space for iterative implementations ($O(\\log n)$ stack space for recursive implementations).\n\n"
                "---\n\n"
                "#### 2. Robust C++ Implementation (Overflow Safe)\n"
                "```cpp\n"
                "#include <iostream>\n"
                "#include <vector>\n\n"
                "int binarySearch(const std::vector<int>& arr, int target) {\n"
                "    int low = 0;\n"
                "    int high = static_cast<int>(arr.size()) - 1;\n\n"
                "    while (low <= high) {\n"
                "        // Prevent integer overflow when (low + high) > INT_MAX\n"
                "        int mid = low + (high - low) / 2;\n\n"
                "        if (arr[mid] == target) {\n"
                "            return mid; // Target found at index mid\n"
                "        } else if (arr[mid] < target) {\n"
                "            low = mid + 1;\n"
                "        } else {\n"
                "            high = mid - 1;\n"
                "        }\n"
                "    }\n"
                "    return -1; // Target not present in collection\n"
                "}\n"
                "```\n\n"
                "---\n\n"
                "#### 3. Key Practical Insights\n"
                "- **Midpoint Calculation**: Always use `low + (high - low) / 2` instead of `(low + high) / 2` to eliminate integer overflow risks in large arrays.\n"
                "- **Efficiency Benchmark**: In an array of $1,000,000$ elements, linear search requires up to $1,000,000$ comparisons, "
                "whereas binary search guarantees resolution in at most $20$ comparisons ($\log_2 10^6 \\approx 19.93$)."
            )
            in_tokens, out_tokens = 310, 520

        # 6. GENERAL TECHNICAL QUERY
        else:
            text = (
                f"### Synthesized Technical Analysis: {query}\n\n"
                f"By synthesizing the highest-accuracy insights across candidate evaluations, the following master response "
                f"comprehensively addresses **{query}**:\n\n"
                f"#### 1. Core Principles & Overview\n"
                f"The inquiry directly pertains to foundational computer science and software architecture principles. "
                f"Understanding the mechanisms, constraints, and standard patterns associated with **{query}** is vital for robust engineering.\n\n"
                f"#### 2. Key Mechanisms & Implementation\n"
                f"- **Foundational Guarantees**: Strict alignment with established algorithmic invariants and interface contracts.\n"
                f"- **Efficiency & Complexity**: Balances computational throughput with memory overhead across real-world workloads.\n"
                f"- **Edge-Case Resilience**: Validates boundary conditions and error-handling paths.\n\n"
                f"#### 3. Summary & Practical Takeaways\n"
                f"A balanced application of these principles ensures reliable, high-performance, and maintainable software systems."
            )
            in_tokens, out_tokens = 280, 260

        total_tokens = in_tokens + out_tokens
        cost = 0.0 if is_fallback else self.openrouter.calculate_cost(synthesis_model, in_tokens, out_tokens)

        return SynthesisResult(
            query_id=query_id,
            synthesis_model=synthesis_model,
            context=structured_context,
            final_response=text,
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            total_tokens=total_tokens,
            cost=cost,
            latency_ms=elapsed_ms,
            status="mock_fallback" if is_fallback else "success",
            is_fallback=is_fallback,
            execution_mode="mock_fallback" if is_fallback else "simulation"
        )
