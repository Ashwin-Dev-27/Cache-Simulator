# 💾 Visual Cache Memory Simulator

### A Python-based tool to visualize Direct & Associative Mapping

This project is a command-line interface (CLI) tool that simulates how a CPU interacts with Cache Memory. It helps visualize the concepts of **Cache Hits**, **Cache Misses**, and memory replacement policies (LRU/FIFO) without needing complex hardware description languages.

---

## 🧐 What is this?

In Computer Organization, understanding how data moves between main RAM and the high-speed Cache is critical. This simulator allows users to input memory addresses and observe how they are mapped to specific cache blocks.

**Key Concepts Demonstrated:**
* **Direct Mapping:** Each block of main memory maps to exactly one cache line.
* **Set Associative Mapping:** A hybrid approach balancing speed and flexibility.
* **Replacement Algorithms:** Implementing Least Recently Used (LRU) to decide which data to evict.

---

## 🛠️ Tech Stack

* **Language:** Python 3.x
* **Core Logic:** Object-Oriented Programming (Classes for `CacheBlock`, `Memory`, `CPU`)
* **Interface:** Command Line / Text-Based UI

---

## ⚙️ How It Works

1.  **Configuration:** The user sets the Cache Size, Block Size, and Mapping Technique.
2.  **Request:** The user (acting as the CPU) requests a specific memory address (e.g., `0x1A4`).
3.  **Process:**
    * The simulator splits the address into **Tag**, **Index**, and **Offset**.
    * It checks the specific Index in the cache.
    * **HIT:** If the Tags match, data is retrieved instantly.
    * **MISS:** If not, the simulator fetches data from "Main Memory" and updates the cache.

---

## 🚀 How to Run

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/Ashwin-Dev-27/Cache-Simulator.git](https://github.com/Ashwin-Dev-27/Cache-Simulator.git)
    ```
2.  **Run the script:**
    ```bash
    python main.py
    ```
3.  **Follow the prompts** to simulate memory access patterns.

---

### 📝 Author
**Ashwin Kumar**
*B.Tech Computer Science*
