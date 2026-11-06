import time
import httpx
import json
import asyncio
import re
from typing import Dict, Any, Optional, List, Tuple
from app.config import settings
from app.utils.logger import log_stage, logger
from app.schemas.pydantic_models import NormalizedResponse

# Standard pricing table per 1M tokens (input / output) for realistic cost calculations
MODEL_PRICING_CATALOG = {
    "google/gemini-2.0-flash-001": {"input": 0.10, "output": 0.40, "provider": "Google"},
    "google/gemini-2.5-flash": {"input": 0.075, "output": 0.30, "provider": "Google"},
    "google/gemini-flash-1.5": {"input": 0.075, "output": 0.30, "provider": "Google"},
    "openai/gpt-4o-mini": {"input": 0.15, "output": 0.60, "provider": "OpenAI"},
    "openai/gpt-4o": {"input": 2.50, "output": 10.00, "provider": "OpenAI"},
    "anthropic/claude-3-haiku": {"input": 0.25, "output": 1.25, "provider": "Anthropic"},
    "anthropic/claude-3.5-sonnet": {"input": 3.00, "output": 15.00, "provider": "Anthropic"},
    "meta-llama/llama-3.1-8b-instruct": {"input": 0.055, "output": 0.055, "provider": "Meta"},
    "meta-llama/llama-3.1-70b-instruct": {"input": 0.35, "output": 0.40, "provider": "Meta"},
    "mistralai/mistral-7b-instruct": {"input": 0.06, "output": 0.06, "provider": "MistralAI"},
    "deepseek/deepseek-chat": {"input": 0.14, "output": 0.28, "provider": "DeepSeek"}
}

def classify_query_topic(query: str) -> str:
    """Accurately classifies the technical query topic using word boundaries."""
    q = query.lower()
    
    # 1. Loops / Control flow / Programming language syntax
    if re.search(r"\b(for\s+loop|while\s+loop|do\s+while|loops?|iteration|iterating|iterator|control\s+flow)\b", q):
        return "loops"
    
    # 2. Operating Systems / Virtual Memory / Paging
    if re.search(r"\b(virtual\s+memory|paging|page\s+fault|page\s+table|mmu|tlb|thrashing|swap\s+space|operating\s+systems?)\b", q) or re.search(r"\b(os\s+memory|kernel\s+memory)\b", q):
        return "virtual_memory"
    
    # 3. Linked Lists
    if re.search(r"\b(linked\s+list|singly\s+linked|doubly\s+linked|circular\s+linked|nodes?\s+and\s+pointers?)\b", q):
        return "linked_list"
        
    # 4. Stack vs Queue / Stacks & Queues
    if re.search(r"\b(stacks?\s+and\s+queues?|stack\s+vs\s+queue|difference\s+between\s+stack\s+and\s+queue|lifo|fifo)\b", q) or (re.search(r"\bstack\b", q) and re.search(r"\bqueue\b", q)):
        return "stack_queue"
        
    # 5. Binary Search & Searching/Sorting
    if re.search(r"\b(binary\s+search|divide\s+and\s+conquer|time\s+complexity\s+of\s+binary\s+search|log\s*n|search\s+algorithm)\b", q):
        return "binary_search"

    # 6. Database / SQL / Transactions
    if re.search(r"\b(sql|nosql|database|acid|indexing|rdbms|b-tree|mongodb|postgres)\b", q):
        return "database"

    # 7. General Coding / Functions / OOP
    if re.search(r"\b(python|c\+\+|java|javascript|class|object|inheritance|polymorphism|recursion|pointer|interface)\b", q):
        return "general_coding"

    return "general"


class OpenRouterService:
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = settings.OPENROUTER_BASE_URL.rstrip("/")
        self.timeout = settings.REQUEST_TIMEOUT_SECONDS

    def has_api_key(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 5)

    def calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        pricing = MODEL_PRICING_CATALOG.get(model, {"input": 0.20, "output": 0.80})
        input_cost = (prompt_tokens / 1_000_000.0) * pricing["input"]
        output_cost = (completion_tokens / 1_000_000.0) * pricing["output"]
        return round(input_cost + output_cost, 6)

    def _extract_user_query(self, messages: List[Dict[str, str]]) -> str:
        """Extracts the underlying user query even if wrapped inside structured context."""
        raw_query = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                raw_query = m.get("content", "")
                break
        if not raw_query:
            return "General Technical Query"
        
        # Check if raw_query contains structured context with "USER QUERY" section
        if "USER QUERY" in raw_query:
            match = re.search(r"USER QUERY\s*\n=+\s*\n(.*?)\n=+", raw_query, re.DOTALL)
            if match:
                return match.group(1).strip()
            lines = raw_query.splitlines()
            for idx, line in enumerate(lines):
                if "USER QUERY" in line and idx + 2 < len(lines):
                    return lines[idx + 2].strip()
        return raw_query.strip()

    async def generate_response(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int = 1500,
        temperature: float = 0.7,
        response_id: int = 1,
        force_mock: bool = False
    ) -> NormalizedResponse:
        """
        Queries OpenRouter API for a given model with strict latency, token, and cost tracking.
        Falls back to realistic research simulation if API key is not configured or force_mock is True.
        """
        start_time = time.perf_counter()
        pricing_info = MODEL_PRICING_CATALOG.get(model, {"provider": model.split("/")[0] if "/" in model else "AI"})
        provider = pricing_info.get("provider", "OpenRouter")

        if not self.has_api_key() or force_mock or settings.MOCK_MODE:
            return await self._generate_mock_response(
                model=model,
                provider=provider,
                messages=messages,
                response_id=response_id,
                start_time=start_time,
                is_fallback=False
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "Multi-LLM Synthesis Research System",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        try:
            log_stage("model", f"{model} started")
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                elapsed_ms = int((time.perf_counter() - start_time) * 1000)

                if res.status_code != 200:
                    err_msg = f"HTTP {res.status_code}: {res.text[:200]}"
                    logger.error(f"OpenRouter call failed for {model}: {err_msg}")
                    # Detect expired API key, auth errors, credit exhaustion, or rate limits
                    is_auth_or_credit = (
                        res.status_code in (401, 402, 403, 429)
                        or "credit" in res.text.lower()
                        or "auth" in res.text.lower()
                        or "expired" in res.text.lower()
                    )
                    if is_auth_or_credit:
                        reason = "API key expired or invalid" if res.status_code == 401 else f"API returned {res.status_code}"
                        logger.warning(f"Falling back to high-fidelity mock response for {model} due to API limitation: {reason}")
                        return await self._generate_mock_response(
                            model=model,
                            provider=provider,
                            messages=messages,
                            response_id=response_id,
                            start_time=start_time,
                            is_fallback=True,
                            fallback_reason=f"OpenRouter HTTP {res.status_code}: {reason}"
                        )
                    return NormalizedResponse(
                        response_id=response_id,
                        model=model,
                        provider=provider,
                        response_text="",
                        status="error",
                        error_message=err_msg,
                        latency_ms=elapsed_ms,
                        is_fallback=False,
                        execution_mode="live"
                    )

                data = res.json()
                generation_id = data.get("id")
                choices = data.get("choices", [])
                response_text = choices[0]["message"]["content"] if choices else ""
                
                usage = data.get("usage", {})
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)
                total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)
                
                # Try getting actual cost from OpenRouter usage object or calculate
                cost = usage.get("total_cost")
                if cost is None:
                    cost = self.calculate_cost(model, prompt_tokens, completion_tokens)

                log_stage(
                    "model",
                    f"{model} completed",
                    tokens=total_tokens,
                    cost=f"${cost:.6f}",
                    latency=f"{elapsed_ms}ms"
                )

                return NormalizedResponse(
                    response_id=response_id,
                    model=model,
                    provider=provider,
                    response_text=response_text,
                    input_tokens=prompt_tokens,
                    output_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    cost=float(cost),
                    latency_ms=elapsed_ms,
                    status="success",
                    generation_id=generation_id,
                    is_fallback=False,
                    execution_mode="live"
                )

        except httpx.TimeoutException:
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error(f"Timeout querying {model} after {elapsed_ms}ms. Falling back to mock simulation.")
            return await self._generate_mock_response(
                model=model,
                provider=provider,
                messages=messages,
                response_id=response_id,
                start_time=start_time,
                is_fallback=True,
                fallback_reason=f"Request timed out after {elapsed_ms}ms"
            )
        except Exception as e:
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error(f"Exception querying {model}: {str(e)}. Falling back to mock simulation.")
            return await self._generate_mock_response(
                model=model,
                provider=provider,
                messages=messages,
                response_id=response_id,
                start_time=start_time,
                is_fallback=True,
                fallback_reason=str(e)
            )

    async def generate_parallel_responses(
        self,
        models: List[str],
        messages: List[Dict[str, str]],
        max_tokens: int = 1500,
        temperature: float = 0.7,
        force_mock: bool = False
    ) -> List[NormalizedResponse]:
        """
        Queries all candidate models asynchronously in parallel.
        Does not terminate if one model fails; records failures and collects all available.
        """
        tasks = [
            self.generate_response(
                model=m,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                response_id=idx + 1,
                force_mock=force_mock
            )
            for idx, m in enumerate(models)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=False)
        return results

    async def get_generation_usage(self, generation_id: str) -> Dict[str, Any]:
        """Queries OpenRouter generation endpoint for verified billing and token statistics"""
        if not self.has_api_key() or not generation_id or generation_id.startswith("mock-"):
            return {"status": "mock", "cost": 0.0, "tokens": 0}

        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(f"{self.base_url}/generation?id={generation_id}", headers=headers)
                if res.status_code == 200:
                    return res.json().get("data", {})
        except Exception as e:
            logger.warning(f"Could not retrieve generation usage for {generation_id}: {e}")
        return {}

    async def _generate_mock_response(
        self,
        model: str,
        provider: str,
        messages: List[Dict[str, str]],
        response_id: int,
        start_time: float,
        is_fallback: bool = False,
        fallback_reason: Optional[str] = None
    ) -> NormalizedResponse:
        """
        High-fidelity research simulator when OpenRouter key is not set or in testing mode.
        Generates domain-aware candidate perspectives with genuine variance and nuanced trade-offs.
        """
        import random
        simulated_delay = random.uniform(0.25, 0.60)
        await asyncio.sleep(simulated_delay)
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        user_query = self._extract_user_query(messages)

        # Generate differentiated responses reflecting model personalities
        text, in_tokens, out_tokens = self._synthesize_mock_model_text(model, user_query)
        total_tokens = in_tokens + out_tokens
        
        # When falling back or simulating, actual API expenditure is $0.00
        cost = 0.0 if is_fallback else self.calculate_cost(model, in_tokens, out_tokens)

        return NormalizedResponse(
            response_id=response_id,
            model=model,
            provider=provider,
            response_text=text,
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            total_tokens=total_tokens,
            cost=cost,
            latency_ms=elapsed_ms,
            status="mock_fallback" if is_fallback else "success",
            generation_id=f"mock-gen-{int(time.time())}-{response_id}",
            error_message=fallback_reason,
            is_fallback=is_fallback,
            execution_mode="mock_fallback" if is_fallback else "simulation"
        )

    def _synthesize_mock_model_text(self, model: str, query: str) -> Tuple[str, int, int]:
        m_lower = model.lower()
        topic = classify_query_topic(query)
        
        # =========================================================================
        # 1. LOOPS & CONTROL FLOW (e.g. for loop, while loop, iteration)
        # =========================================================================
        if topic == "loops":
            if "claude" in m_lower or "sonnet" in m_lower:
                text = (
                    f"### Architectural Analysis of Iteration & For Loops\n\n"
                    f"In modern programming languages like C++, a **for loop** is an entry-controlled repetition control structure "
                    f"designed to execute a designated block of code repeatedly while an invariant condition remains valid.\n\n"
                    f"#### 1. Anatomy and Execution Semantics\n"
                    f"The canonical three-clause construct consists of:\n"
                    f"- **Initialization**: Evaluated exactly once before the first iteration (e.g., `int i = 0`).\n"
                    f"- **Condition Guard**: Evaluated before each iteration. If `false`, the loop terminates immediately (e.g., `i < n`).\n"
                    f"- **Step / Update Expression**: Executed at the conclusion of each iteration (e.g., `++i`).\n\n"
                    f"#### 2. Modern C++ Paradigms\n"
                    f"1. **Traditional Indexed Loop**:\n"
                    f"```cpp\n"
                    f"for (size_t i = 0; i < vec.size(); ++i) {{\n"
                    f"    process(vec[i]);\n"
                    f"}}\n"
                    f"```\n"
                    f"2. **Range-Based For Loop (C++11/20)**:\n"
                    f"```cpp\n"
                    f"for (const auto& element : container) {{\n"
                    f"    process(element); // Zero index arithmetic overhead\n"
                    f"}}\n"
                    f"```\n\n"
                    f"#### 3. Compiler Optimization & Complexity\n"
                    f"- **Time Complexity**: $O(n)$ where $n$ represents iteration count.\n"
                    f"- **Space Complexity**: $O(1)$ auxiliary memory.\n"
                    f"- **Compiler Enhancements**: Compilers (GCC/Clang `-O3`) utilize **loop unrolling** and auto-vectorization (SIMD) "
                    f"to maximize instruction-level parallelism across CPU execution ports."
                )
                return text, 115, 340
            elif "gemini" in m_lower:
                text = (
                    f"**Understanding the For Loop in Programming**\n\n"
                    f"A **for loop** is a fundamental control flow statement used to iterate over a range of values or a sequence of elements.\n\n"
                    f"### Syntax Breakdown (C++ / C-style languages):\n"
                    f"```cpp\n"
                    f"for (initialization; condition; increment/decrement) {{\n"
                    f"    // Statements to execute repeatedly\n"
                    f"}}\n"
                    f"```\n\n"
                    f"### Execution Steps:\n"
                    f"1. **Initialization**: Sets up the loop counter (runs once).\n"
                    f"2. **Condition Check**: Evaluated before each run. If true, body executes; if false, loop ends.\n"
                    f"3. **Body Execution**: Runs the code inside the curly braces.\n"
                    f"4. **Update**: Modifies the counter, then re-checks the condition.\n\n"
                    f"### Practical Example:\n"
                    f"```cpp\n"
                    f"#include <iostream>\n\n"
                    f"int main() {{\n"
                    f"    for (int i = 1; i <= 5; ++i) {{\n"
                    f"        std::cout << \"Count: \" << i << std::endl;\n"
                    f"    }}\n"
                    f"    return 0;\n"
                    f"}}\n"
                    f"```\n\n"
                    f"**Key Advantage**: The loop variable, boundary condition, and increment logic are all unified in a single compact line, "
                    f"significantly reducing the risk of infinite loops compared to unstructured `while` loops."
                )
                return text, 100, 270
            elif "gpt-4o" in m_lower:
                text = (
                    f"A **for loop** is a programming construct that allows code to be executed repeatedly based on a condition. "
                    f"It is especially useful when the number of iterations is known before entering the loop.\n\n"
                    f"### How a For Loop Works in C++\n\n"
                    f"```cpp\n"
                    f"for (int i = 0; i < 5; i++) {{\n"
                    f"    std::cout << i << \" \";\n"
                    f"}}\n"
                    f"// Output: 0 1 2 3 4\n"
                    f"```\n\n"
                    f"### Core Components:\n"
                    f"- **Initialization (`int i = 0`)**: Creates and initializes the iteration index.\n"
                    f"- **Condition (`i < 5`)**: Tested prior to every cycle. Execution halts when this evaluates to false.\n"
                    f"- **Increment (`i++` or `++i`)**: Increments the index after each pass through the loop block.\n\n"
                    f"### Common Variants in C++:\n"
                    f"1. **Indexed Loops**: Direct index access (`arr[i]`), ideal when index position matters.\n"
                    f"2. **Range-based Loops**: `for (auto& item : collection)` introduced in C++11 for cleaner, safer traversals.\n"
                    f"3. **Infinite Loops**: `for (;;) {{ ... }}` which continues until an explicit `break` or `return`.\n\n"
                    f"### Best Practices & Pitfalls:\n"
                    f"- Beware of **off-by-one errors** (`<` vs `<=`).\n"
                    f"- Prefer pre-increment (`++i`) for non-primitive iterators to avoid unnecessary object copies.\n"
                    f"- Avoid mutating the collection size inside the loop body unless handling iterator invalidation carefully."
                )
                return text, 110, 290
            else:  # Llama or default
                text = (
                    f"A **for loop** provides deterministic iteration over sequences and counter ranges.\n\n"
                    f"```cpp\n"
                    f"for (int i = 0; i < N; ++i) {{\n"
                    f"    // executed N times\n"
                    f"}}\n"
                    f"```\n\n"
                    f"**Low-Level & Hardware Execution Details:**\n"
                    f"- At the machine level, the compiler generates a comparison (`cmp`) instruction followed by a conditional jump (`jl` / `jne`).\n"
                    f"- Modern CPUs employ branch predictors to predict loop continuation with over 99% accuracy until the final exit branch.\n"
                    f"- **Memory Locality**: Iterating over contiguous memory (e.g. `std::vector` or raw arrays) in a forward for-loop "
                    f"maximizes hardware L1/L2 cache prefetching line efficiency.\n"
                    f"- Time complexity is $O(n)$ with $O(1)$ memory consumption."
                )
                return text, 95, 210

        # =========================================================================
        # 2. VIRTUAL MEMORY & OPERATING SYSTEMS
        # =========================================================================
        elif topic == "virtual_memory":
            if "claude" in m_lower or "sonnet" in m_lower:
                text = (
                    "### Virtual Memory in Operating Systems\n\n"
                    "Virtual memory is a fundamental memory management technique that creates an illusion of a very large, "
                    "contiguous address space for each process, abstracting physical RAM and secondary storage (swap/paging space).\n\n"
                    "#### 1. Core Mechanisms\n"
                    "- **Paging & Virtual Addresses**: Memory is divided into fixed-size chunks called **pages** (typically 4 KB). "
                    "Physical memory is partitioned into matching **page frames**.\n"
                    "- **Memory Management Unit (MMU)**: A hardware component that translates virtual addresses to physical addresses "
                    "via page tables on every memory reference.\n"
                    "- **Translation Lookaside Buffer (TLB)**: A high-speed hardware cache for page table entries to minimize lookup latency.\n\n"
                    "#### 2. Key Benefits\n"
                    "- **Process Isolation & Security**: Each process runs in its own isolated address space, preventing unauthorized memory access.\n"
                    "- **Overcommitting Memory**: Allows programs larger than physical RAM to execute by swapping inactive pages to disk.\n"
                    "- **Shared Memory & Copy-on-Write (CoW)**: Facilitates efficient memory sharing (e.g., shared libraries, fork()).\n\n"
                    "#### 3. Page Faults & Thrashing\n"
                    "When a page is accessed that is not in physical RAM, an MMU exception triggers a **Page Fault**. "
                    "The OS kernel reads the page from disk into a frame. If physical memory is saturated and the system spends more time paging than computing, "
                    "it enters **thrashing**."
                )
                return text, 120, 310
            elif "gemini" in m_lower:
                text = (
                    "**Virtual Memory Overview**\n\n"
                    "Virtual memory separates the logical address space used by applications from the physical RAM installed in hardware. "
                    "Here is a breakdown of how it works:\n\n"
                    "1. **Address Translation**: The CPU generates virtual addresses, which the MMU translates into physical addresses using page tables.\n"
                    "2. **Paging System**: Modern operating systems divide memory into 4KB blocks (pages). Pages are mapped to physical page frames.\n"
                    "3. **Swap Space**: Secondary storage (SSD or HDD) acts as an extension of RAM. Rarely used pages are written to swap space.\n"
                    "4. **Benefits**:\n"
                    "   * Protection: Processes cannot overwrite each other's memory space.\n"
                    "   * Efficiency: Enables lazy loading (only code pages actively in use are brought into RAM).\n\n"
                    "*Common Issue*: Page thrashing occurs if too many processes compete for insufficient physical RAM."
                )
                return text, 110, 195
            elif "gpt-4o" in m_lower:
                text = (
                    "Virtual memory is an essential operating system abstraction that gives every running application the perception of having dedicated, "
                    "uninterrupted access to RAM.\n\n"
                    "**How It Operates:**\n"
                    "- **Virtual vs Physical Addresses**: Applications work strictly with virtual addresses. The hardware MMU (Memory Management Unit) "
                    "maps these to physical RAM addresses.\n"
                    "- **Page Table & TLB**: Translations are stored in hierarchical page tables. The TLB caches frequent mappings for single-cycle access.\n"
                    "- **Demand Paging**: When an instruction references an unmapped page, the CPU triggers a page fault interrupt. The OS fetches the block from disk.\n\n"
                    "**Significance:**\n"
                    "It ensures process protection, enables sharing of system libraries, and allows execution of massive software packages on constrained hardware."
                )
                return text, 115, 210
            else:  # Llama or default
                text = (
                    "Virtual memory is a memory management capability of an OS that uses hardware and software to allow a computer to compensate for physical memory shortages "
                    "by temporarily transferring data from random access memory (RAM) to disk storage.\n\n"
                    "- Pages are typically 4KB or 2MB/1GB (HugePages).\n"
                    "- Virtual addresses are converted to physical addresses by the MMU.\n"
                    "- Page replacement algorithms (e.g., LRU, Clock algorithm) determine which frame to evict when memory is full.\n"
                    "- Protection bits (Read, Write, Execute) prevent illegal operations and buffer overflows."
                )
                return text, 105, 160

        # =========================================================================
        # 3. LINKED LISTS
        # =========================================================================
        elif topic == "linked_list":
            if "claude" in m_lower or "sonnet" in m_lower:
                text = (
                    "### Structural Analysis: Linked Lists\n\n"
                    "A **linked list** is a fundamental dynamic data structure consisting of discrete nodes connected sequentially via pointers or references. "
                    "Unlike arrays, elements are not stored contiguously in physical memory.\n\n"
                    "#### 1. Core Topologies\n"
                    "- **Singly Linked List**: Each node contains a data payload and a single forward reference pointer (`next`).\n"
                    "- **Doubly Linked List**: Nodes maintain both forward (`next`) and backward (`prev`) pointers, facilitating bidirectional traversal.\n"
                    "- **Circular Linked List**: The terminal node references the head node, forming a continuous ring.\n\n"
                    "#### 2. Asymptotic Complexity Profiles\n"
                    "| Operation | Linked List | Array / std::vector |\n"
                    "|---|---|---|\n"
                    "| Insertion at Head | $O(1)$ | $O(n)$ |\n"
                    "| Insertion at Known Node | $O(1)$ | $O(n)$ |\n"
                    "| Random Access `get(k)` | $O(n)$ | $O(1)$ |\n"
                    "| Search | $O(n)$ | $O(n)$ or $O(\\log n)$ sorted |\n\n"
                    "#### 3. Architectural Trade-offs\n"
                    "- **Dynamic Sizing**: Allocates and deallocates memory on demand without costly amortized buffer resizes.\n"
                    "- **Memory & Cache Penalty**: Each node consumes pointer overhead (8 bytes on 64-bit systems). "
                    "Crucially, disparate heap allocations lead to high cache miss rates (pointer-chasing penalty) compared to cache-friendly contiguous arrays."
                )
                return text, 120, 310
            elif "gemini" in m_lower:
                text = (
                    "**Linked List: Concepts and Mechanics**\n\n"
                    "A linked list is a linear data structure where elements are not stored in adjacent memory locations. "
                    "Instead, elements are linked using pointers.\n\n"
                    "### Node Structure in C++:\n"
                    "```cpp\n"
                    "struct Node {\n"
                    "    int data;\n"
                    "    Node* next;\n"
                    "    Node(int val) : data(val), next(nullptr) {}\n"
                    "};\n"
                    "```\n\n"
                    "### Key Operations:\n"
                    "1. **Prepend (Insert at Head)**: $O(1)$ time. Set new node's next pointer to current head, update head.\n"
                    "2. **Append (Insert at Tail)**: $O(1)$ if tail pointer maintained, otherwise $O(n)$ traversal.\n"
                    "3. **Deletion**: $O(1)$ if the previous node is known; $O(n)$ if search is needed.\n"
                    "4. **Lookup**: $O(n)$ sequential traversal required.\n\n"
                    "**When to use**: Ideal for situations requiring frequent insertions and deletions without reallocation spikes, "
                    "or when the maximum dataset size cannot be predicted in advance."
                )
                return text, 105, 240
            elif "gpt-4o" in m_lower:
                text = (
                    "A **linked list** is a linear collection of data elements whose order is not given by their physical placement in memory. "
                    "Each element is stored in a **node** that points to the next node in sequence.\n\n"
                    "### How a Singly Linked List Works:\n"
                    "```\n"
                    "[ Head: 10 | next* ] -> [ 20 | next* ] -> [ 30 | nullptr ]\n"
                    "```\n\n"
                    "### C++ Implementation Example:\n"
                    "```cpp\n"
                    "#include <iostream>\n\n"
                    "struct Node {\n"
                    "    int data;\n"
                    "    Node* next;\n"
                    "};\n\n"
                    "void printList(Node* n) {\n"
                    "    while (n != nullptr) {\n"
                    "        std::cout << n->data << \" -> \";\n"
                    "        n = n->next;\n"
                    "    }\n"
                    "    std::cout << \"NULL\\n\";\n"
                    "}\n"
                    "```\n\n"
                    "### Comparison with Arrays:\n"
                    "- **Pros**: Easy insertion/deletion without shifting elements; no fixed capacity limitations.\n"
                    "- **Cons**: No direct index access (must traverse from head); extra memory per node for pointer storage."
                )
                return text, 110, 260
            else:  # Llama or default
                text = (
                    "A linked list is a pointer-linked data structure organizing nodes dynamically on the heap.\n\n"
                    "- **Memory Structure**: Individual heap allocations via `malloc` or `new`.\n"
                    "- **Time Complexity**: Insertion/deletion at ends is $O(1)$; indexing requires $O(n)$ linear traversal.\n"
                    "- **Hardware Considerations**: Pointer chasing degrades spatial locality in CPU cache lines. "
                    "On modern processors, an array of contiguous integers often beats a linked list even for mid-array insertions "
                    "due to SIMD `memmove` speed and L1 cache hits."
                )
                return text, 95, 180

        # =========================================================================
        # 4. STACK VS QUEUE
        # =========================================================================
        elif topic == "stack_queue":
            if "claude" in m_lower or "sonnet" in m_lower:
                text = (
                    "### Abstract Data Types: Stack vs Queue Comparative Analysis\n\n"
                    "Stacks and queues are fundamental linear abstract data types (ADTs) governed by distinct element access disciplines.\n\n"
                    "#### 1. Core Operating Principles\n"
                    "- **Stack (LIFO - Last In, First Out)**: The most recently inserted element is the first to be retrieved or removed. "
                    "All operations occur exclusively at one designated end—the **top**.\n"
                    "- **Queue (FIFO - First In, First Out)**: Elements are processed in the strict chronological order of arrival. "
                    "Insertion occurs at the **rear/tail**, while removal occurs at the **front/head**.\n\n"
                    "#### 2. Operations & Complexity\n"
                    "| Metric | Stack | Queue |\n"
                    "|---|---|---|\n"
                    "| Insert Operation | `push(x)` — $O(1)$ | `enqueue(x)` — $O(1)$ |\n"
                    "| Removal Operation | `pop()` — $O(1)$ | `dequeue()` — $O(1)$ |\n"
                    "| Inspection | `peek()` / `top()` — $O(1)$ | `front()` — $O(1)$ |\n"
                    "| Primary Access End | Single end (Top) | Dual ends (Front & Rear) |\n\n"
                    "#### 3. Canonical Applications\n"
                    "- **Stack Use Cases**: CPU function call stack frames, syntax parsing/bracket matching, undo/redo buffers, and Depth-First Search (DFS).\n"
                    "- **Queue Use Cases**: Operating system CPU/task scheduling (round-robin), IO request buffering, print spoolers, and Breadth-First Search (BFS)."
                )
                return text, 120, 310
            elif "gemini" in m_lower:
                text = (
                    "**Difference Between Stack and Queue**\n\n"
                    "Here is a direct comparison between stacks and queues:\n\n"
                    "| Feature | Stack | Queue |\n"
                    "|---|---|---|\n"
                    "| **Principle** | LIFO (Last-In, First-Out) | FIFO (First-In, First-Out) |\n"
                    "| **Endpoints** | 1 open end (Top) | 2 open ends (Front and Rear) |\n"
                    "| **Insert Method** | `push()` | `enqueue()` |\n"
                    "| **Delete Method** | `pop()` | `dequeue()` |\n"
                    "| **Inspection** | `top()` or `peek()` | `front()` and `back()` |\n"
                    "| **C++ STL Type** | `std::stack` | `std::queue` |\n\n"
                    "### Real-World Analogies:\n"
                    "- **Stack**: A stack of cafeteria plates—you add to the top and take from the top.\n"
                    "- **Queue**: A ticket line—the first customer in line is the first one served."
                )
                return text, 100, 220
            elif "gpt-4o" in m_lower:
                text = (
                    "Stacks and Queues are two essential linear data structures with opposite retrieval rules:\n\n"
                    "### 1. Stack (LIFO: Last In, First Out)\n"
                    "- Think of a stack of books: the last book placed on top is the first one removed.\n"
                    "- **Core Methods**: `push()` to add, `pop()` to remove from the top, `peek()` to view top.\n"
                    "- **C++ STL**: `#include <stack>` -> `std::stack<int> s;`\n"
                    "- **Examples**: Browser back-button history, function call execution stack, undo actions.\n\n"
                    "### 2. Queue (FIFO: First In, First Out)\n"
                    "- Think of a checkout queue: the person who arrives first gets served first.\n"
                    "- **Core Methods**: `enqueue()` (or `push()`) at the back, `dequeue()` (or `pop()`) from the front.\n"
                    "- **C++ STL**: `#include <queue>` -> `std::queue<int> q;`\n"
                    "- **Examples**: Printer task queues, thread pool work queues, web server request buffers.\n\n"
                    "### Summary\n"
                    "Both provide $O(1)$ constant time insertion and deletion, but differ fundamentally in order of processing."
                )
                return text, 110, 260
            else:  # Llama or default
                text = (
                    "**Stack vs Queue Implementation Mechanisms:**\n\n"
                    "- **Stack (LIFO)**: Implemented via dynamic array (`std::vector`) or linked list. "
                    "Only requires maintaining a single pointer/index to the top element. $O(1)$ operations.\n"
                    "- **Queue (FIFO)**: Implemented using a circular ring buffer or doubly linked list (`std::deque`). "
                    "Requires maintaining both read and write pointers (head and tail indices) to avoid $O(n)$ shifts on deletion.\n"
                    "- Both structures consume $O(n)$ space for $n$ elements."
                )
                return text, 95, 170

        # =========================================================================
        # 5. BINARY SEARCH & SEARCH ALGORITHMS
        # =========================================================================
        elif topic == "binary_search":
            if "claude" in m_lower or "sonnet" in m_lower:
                text = (
                    "### Binary Search: Algorithmic Foundations and Complexity\n\n"
                    "**Binary Search** is an optimal divide-and-conquer algorithm for locating a target value within a sorted collection.\n\n"
                    "#### 1. Mathematical Principle & Recurrence\n"
                    "Binary search maintains a search interval $[low, high]$. In each step, the midpoint $mid$ is examined. "
                    "Because elements are monotonically ordered, comparing the target against $arr[mid]$ eliminates exactly half the candidate search space.\n\n"
                    "The recurrence relation is:\n"
                    "$$T(n) = T(n/2) + O(1)$$\n"
                    "By the Master Theorem (Case 2 with $a=1, b=2$), the asymptotic time complexity solves strictly to:\n"
                    "- **Worst & Average Case**: $O(\\log_2 n)$\n"
                    "- **Best Case**: $O(1)$ (target located immediately at initial midpoint)\n"
                    "- **Space Complexity**: $O(1)$ auxiliary memory in iterative implementation ($O(\\log n)$ on recursion call stack).\n\n"
                    "#### 2. Overflow-Safe Implementation (C++)\n"
                    "```cpp\n"
                    "int binarySearch(const std::vector<int>& arr, int target) {\n"
                    "    int low = 0, high = static_cast<int>(arr.size()) - 1;\n"
                    "    while (low <= high) {\n"
                    "        // Avoid integer overflow: low + (high - low) / 2 instead of (low + high) / 2\n"
                    "        int mid = low + (high - low) / 2;\n"
                    "        if (arr[mid] == target) return mid;\n"
                    "        if (arr[mid] < target) low = mid + 1;\n"
                    "        else high = mid - 1;\n"
                    "    }\n"
                    "    return -1; // Target not found\n"
                    "}\n"
                    "```"
                )
                return text, 120, 330
            elif "gemini" in m_lower:
                text = (
                    "**Binary Search Algorithm and Time Complexity**\n\n"
                    "Binary search is an efficient search algorithm that works on sorted arrays by repeatedly halving the search space.\n\n"
                    "### How It Works:\n"
                    "1. Define search range: `low = 0`, `high = n - 1`.\n"
                    "2. Calculate the middle index: `mid = low + (high - low) / 2`.\n"
                    "3. If `arr[mid] == target`, target is found!\n"
                    "4. If `target > arr[mid]`, discard the left half (`low = mid + 1`).\n"
                    "5. If `target < arr[mid]`, discard the right half (`high = mid - 1`).\n"
                    "6. Repeat until `low > high`.\n\n"
                    "### Time & Space Complexity:\n"
                    "- **Worst Case**: $O(\\log n)$ (halving $n$ until 1 element remains requires $\\approx \\log_2 n$ steps).\n"
                    "- **Average Case**: $O(\\log n)$\n"
                    "- **Best Case**: $O(1)$ (target is at the midpoint on the first check).\n"
                    "- **Space Complexity**: $O(1)$ iterative, $O(\\log n)$ recursive.\n\n"
                    "*Prerequisite*: The collection **must** be sorted before binary search can be applied."
                )
                return text, 105, 250
            elif "gpt-4o" in m_lower:
                text = (
                    "**Binary search** is a fast search algorithm with a run-time complexity of $O(\\log n)$. "
                    "It works on the principle of divide and conquer, requiring the input array to be sorted.\n\n"
                    "### Step-by-Step Example:\n"
                    "Given `arr = [2, 5, 8, 12, 16, 23, 38, 56, 72, 91]`, search for `target = 23`:\n"
                    "1. `low = 0`, `high = 9`, `mid = 4` (`arr[4] = 16`). Since $23 > 16$, search right half (`low = 5`).\n"
                    "2. `low = 5`, `high = 9`, `mid = 7` (`arr[7] = 56`). Since $23 < 56$, search left half (`high = 6`).\n"
                    "3. `low = 5`, `high = 6`, `mid = 5` (`arr[5] = 23`). Match found! Return index 5.\n\n"
                    "### Complexity Analysis:\n"
                    "- **Linear Search**: $O(n)$ comparisons.\n"
                    "- **Binary Search**: $O(\\log_2 n)$ comparisons. For $1,000,000$ elements, linear search takes up to $1,000,000$ checks; "
                    "binary search takes at most $\\approx 20$ checks!\n\n"
                    "### Critical Implementation Note:\n"
                    "Use `int mid = low + (high - low) / 2;` rather than `(low + high) / 2` to prevent potential 32-bit signed integer overflow."
                )
                return text, 110, 270
            else:  # Llama or default
                text = (
                    "Binary search algorithm efficiency:\n\n"
                    "- **Asymptotic Complexity**: $O(\\log n)$ time, $O(1)$ space for iterative implementation.\n"
                    "- **Requirement**: Monotonically sorted dataset with random access $O(1)$ indexing.\n"
                    "- **Hardware Consideration**: While theoretically optimal for comparisons, binary search exhibits high branch misprediction rates "
                    "because branches are 50/50 probabilistic. Branchless binary search formulations can yield noticeable speedups on modern superscalar CPUs."
                )
                return text, 95, 170

        # =========================================================================
        # 6. DATABASE & TRANSACTIONS
        # =========================================================================
        elif topic == "database":
            text = (
                f"### Database Architecture and Data Systems Analysis\n\n"
                f"Addressing: **{query}**\n\n"
                f"1. **Core Architectural Foundations**: Relational (RDBMS) vs non-relational (NoSQL) storage models "
                f"prioritize different trade-offs across consistency, availability, and partition tolerance (CAP theorem).\n"
                f"2. **Transactional Integrity (ACID)**: Atomicity, Consistency, Isolation, and Durability ensure data reliability.\n"
                f"3. **Indexing & Retrieval**: B-Trees and LSM-Trees power fast index lookups with $O(\\log n)$ disk read complexity."
            )
            return text, 105, 180

        # =========================================================================
        # 7. GENERAL TECHNICAL QUERY (Dynamic query-aware synthesis)
        # =========================================================================
        else:
            text = (
                f"### Technical Analysis: {query}\n\n"
                f"Addressing the inquiry regarding: **{query}**\n\n"
                f"1. **Core Definition & Conceptual Framework**:\n"
                f"   The subject matter directly addresses fundamental principles in software design and computer science.\n\n"
                f"2. **Mechanics & Practical Implementation**:\n"
                f"   - Proper structural separation of concerns and clear interfaces.\n"
                f"   - Consideration of runtime efficiency, memory footprint, and edge cases.\n"
                f"   - Standard best practices and idiomatic usage patterns.\n\n"
                f"3. **Summary & Verification**:\n"
                f"   Understanding the structural guarantees and constraints of **{query}** ensures robust, scalable, and verifiable results."
            )
            return text, 100, 180
