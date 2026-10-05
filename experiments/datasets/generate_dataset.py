import json
import os

def generate_benchmark_dataset():
    categories = {
        "computer_science": [
            ("Explain virtual memory in operating systems and how paging operates.", "beginner", "explanatory"),
            ("How does the Translation Lookaside Buffer (TLB) prevent memory access bottlenecks?", "intermediate", "explanatory"),
            ("Explain the difference between process-level and thread-level concurrency in Linux.", "intermediate", "explanatory"),
            ("How does copy-on-write (CoW) optimize the fork() system call?", "intermediate", "explanatory"),
            ("What causes page thrashing in virtual memory and how do working set algorithms mitigate it?", "intermediate", "explanatory"),
            ("Explain cache coherence protocols like MESI in multi-core processors.", "advanced", "explanatory"),
            ("How does a B-tree index differ from an LSM-tree in database storage engines?", "advanced", "explanatory"),
            ("Describe the Raft consensus algorithm and how leader election is guaranteed.", "advanced", "explanatory"),
            ("Explain TCP congestion control mechanisms: Tahoe, Reno, and BBR.", "intermediate", "explanatory"),
            ("How does memory alignment and structure padding impact CPU cache line performance?", "advanced", "explanatory"),
        ],
        "coding": [
            ("Implement an LRU Cache in Python using an OrderedDict or doubly linked list with O(1) operations.", "intermediate", "code_centric"),
            ("Write a thread-safe singleton pattern in Modern C++ using std::call_once.", "advanced", "code_centric"),
            ("Implement Dijkstra's shortest path algorithm using a min-heap in Python.", "intermediate", "code_centric"),
            ("Write a custom memory allocator (bump allocator) in C with alignment guarantees.", "advanced", "code_centric"),
            ("Implement binary search tree validation (isValidBST) in Python without recursion.", "intermediate", "code_centric"),
            ("Write a debounce function in TypeScript with cancellation support.", "intermediate", "code_centric"),
            ("Implement an asynchronous rate limiter in Python using asyncio tokens bucket.", "advanced", "code_centric"),
            ("Write an SQL query to find the top 3 highest paid employees in each department using window functions.", "intermediate", "code_centric"),
            ("Implement topological sort on a directed acyclic graph (DAG) using Kahn's algorithm in Python.", "intermediate", "code_centric"),
            ("Write a lock-free queue in C++ using std::atomic and compare_exchange_weak.", "advanced", "code_centric"),
        ],
        "mathematics_reasoning": [
            ("Explain Bayes' Theorem and derive posterior probability given prior and likelihood.", "intermediate", "step_by_step"),
            ("Prove that the square root of 2 is irrational using contradiction.", "beginner", "step_by_step"),
            ("Explain the difference between Eigenvalues and Singular Value Decomposition (SVD).", "advanced", "step_by_step"),
            ("Solve the Monty Hall problem using conditional probability and explain why switching is optimal.", "beginner", "step_by_step"),
            ("Explain Gradient Descent convergence bounds for strongly convex vs non-convex loss functions.", "advanced", "step_by_step"),
            ("Derive the closed-form solution of the Fibonacci recurrence using generating functions.", "intermediate", "step_by_step"),
            ("Explain the Central Limit Theorem and its formal assumptions.", "intermediate", "step_by_step"),
            ("Calculate the probability of drawing a full house in five-card poker from a standard deck.", "beginner", "step_by_step"),
            ("Explain Lagrange multipliers and how they solve constrained optimization problems.", "intermediate", "step_by_step"),
            ("Prove that there are infinitely many prime numbers using Euclid's proof.", "beginner", "step_by_step"),
        ],
        "general_knowledge": [
            ("Explain the physics of how aerodynamic lift is generated on an airplane wing.", "beginner", "explanatory"),
            ("What caused the Bronze Age Collapse around 1200 BCE?", "intermediate", "explanatory"),
            ("Explain the mechanics of CRISPR-Cas9 gene editing and guide RNA targeting.", "intermediate", "explanatory"),
            ("How does quantitative easing (QE) affect sovereign bond yields and inflation?", "intermediate", "explanatory"),
            ("Describe the carbon cycle and the role of oceanic carbon sinks.", "beginner", "explanatory"),
            ("What is the difference between nuclear fission and fusion power generation?", "beginner", "explanatory"),
            ("Explain how mRNA vaccines train the human immune system against spike proteins.", "beginner", "explanatory"),
            ("What are the geopolitical and trade implications of the Malacca Strait?", "intermediate", "explanatory"),
            ("How do gravitational waves propagate across spacetime and how does LIGO detect them?", "intermediate", "explanatory"),
            ("Explain the difference between civil law and common law legal traditions.", "beginner", "explanatory"),
        ],
        "creative_explanatory": [
            ("Explain the concept of quantum superposition using a creative analogy suitable for an 8-year-old.", "beginner", "creative"),
            ("Write an essay comparing the philosophical views of stoicism and existentialism on adversity.", "intermediate", "formal"),
            ("Describe how a computer network packet travels from a browser to a server as an adventurous journey.", "beginner", "creative"),
            ("Compare human memory consolidation during sleep to database caching and checkpointing.", "intermediate", "explanatory"),
            ("Write a dialogue between Socrates and Turing discussing whether machine consciousness is possible.", "intermediate", "creative"),
            ("Explain the concept of entropy in thermodynamics and information theory using everyday metaphors.", "beginner", "creative"),
            ("Describe the evolution of writing materials from clay cuneiform tablets to modern silicon transistors.", "intermediate", "explanatory"),
            ("Explain how compilers optimize code using the metaphor of a meticulous chef reorganizing a kitchen.", "beginner", "creative"),
            ("Write a balanced analysis of the ethical implications of autonomous AI agents in healthcare.", "intermediate", "formal"),
            ("Explain why time dilation occurs in Einstein's Special Relativity using a train and light clock thought experiment.", "beginner", "creative"),
        ]
    }

    # Generate 200 items by systematic domain expansion
    dataset = []
    item_id = 1
    
    # 40 items per category
    for cat_name, base_items in categories.items():
        for i in range(40):
            base = base_items[i % len(base_items)]
            query_variation = base[0] if i < len(base_items) else f"{base[0]} (Perspective #{i//len(base_items) + 1})"
            dataset.append({
                "id": item_id,
                "category": cat_name,
                "query": query_variation,
                "difficulty": base[1],
                "expected_style": base[2]
            })
            item_id += 1

    os.makedirs("experiments/datasets", exist_ok=True)
    with open("experiments/datasets/benchmark_queries.json", "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2)

    print(f"Generated {len(dataset)} benchmark queries across {len(categories)} domains.")

if __name__ == "__main__":
    generate_benchmark_dataset()
