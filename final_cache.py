import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time

# --- CONFIGURATION ---
CACHE_SETS = 4
RAM_SIZE = 100 

# --- SIMULATION CONSTANTS ---
HIT_PENALTY = 1     # Cycles for a Cache Hit
MISS_PENALTY = 50   # Cycles for a RAM Fetch

# --- COLORS ---
BG_COLOR = "#1e272e"
CPU_COLOR = "#3498db"
CACHE_COLOR = "#2ecc71"
RAM_COLOR = "#e67e22"
BUS_OFF = "#576574"
BUS_ON_HIT = "#00ff00"
BUS_ON_MISS = "#ff3838"

# --- LOGIC CLASS ---
class CacheLogic:
    def __init__(self, mode="Direct Mapped"):
        self.mode = mode
        self.ways = 1 if mode == "Direct Mapped" else 2
        self.sets = [[{'tag': -1, 'last_used': 0} for _ in range(self.ways)] for _ in range(CACHE_SETS)]
        self.clock = 0
        self.hits = 0
        self.misses = 0
        self.total_cycles = 0
    
    def access(self, addr):
        self.clock += 1
        set_idx = addr % CACHE_SETS
        tag = addr // CACHE_SETS
        
        # Check Hit
        for way in range(self.ways):
            if self.sets[set_idx][way]['tag'] == tag:
                self.sets[set_idx][way]['last_used'] = self.clock
                self.hits += 1
                cost = HIT_PENALTY
                self.total_cycles += cost
                return "HIT", set_idx, way, cost

        # Handle Miss
        self.misses += 1
        cost = HIT_PENALTY + MISS_PENALTY 
        self.total_cycles += cost
        
        # LRU / Eviction Logic
        target_way = 0
        found_empty = False
        
        for way in range(self.ways):
            if self.sets[set_idx][way]['tag'] == -1:
                target_way = way
                found_empty = True
                break
        
        if not found_empty:
            min_lru = float('inf')
            for way in range(self.ways):
                if self.sets[set_idx][way]['last_used'] < min_lru:
                    min_lru = self.sets[set_idx][way]['last_used']
                    target_way = way
        
        self.sets[set_idx][target_way]['tag'] = tag
        self.sets[set_idx][target_way]['last_used'] = self.clock
        return "MISS", set_idx, target_way, cost

# --- GUI APP ---
class SystemSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("Processor-Memory Simulator (Log Memory Edition)")
        self.root.geometry("1400x850") 
        self.root.configure(bg=BG_COLOR)
        
        self.current_mode = "Direct Mapped"
        
        # --- SEPARATE LOGIC INSTANCES FOR EACH MODE ---
        # This keeps the cache state alive when you switch away
        self.logics = {
            "Direct Mapped": CacheLogic("Direct Mapped"),
            "2-Way Set Associative": CacheLogic("2-Way Set Associative")
        }
        
        # --- SEPARATE LOG DATA FOR EACH MODE ---
        # Stores list of tuples: (step_num, addr, status, cycles)
        self.log_memory = {
            "Direct Mapped": [],
            "2-Way Set Associative": []
        }
        
        # --- SEPARATE GRAPH DATA FOR EACH MODE ---
        self.graph_data_memory = {
             "Direct Mapped": [],
             "2-Way Set Associative": []
        }
        
        self.cache_rects = {}
        self.bus_lines = {}
        
        self.setup_main_layout()
        
    def setup_main_layout(self):
        # 1. Header Frame
        header = tk.Frame(self.root, bg="#2f3640", height=80)
        header.pack(fill=tk.X)
        
        # --- LEFT: Mode Selection ---
        tk.Label(header, text="Mode:", bg="#2f3640", fg="#bdc3c7", font=("Arial", 10)).pack(side=tk.LEFT, padx=(20, 5))
        self.mode_combo = ttk.Combobox(header, values=["Direct Mapped", "2-Way Set Associative"], state="readonly", width=22)
        self.mode_combo.current(0) 
        self.mode_combo.pack(side=tk.LEFT, padx=5)
        self.mode_combo.bind("<<ComboboxSelected>>", self.change_mode)

        # --- CENTER: Manual Input ---
        manual_frame = tk.Frame(header, bg="#2f3640", highlightbackground="#576574", highlightthickness=1)
        manual_frame.pack(side=tk.LEFT, padx=30)
        
        tk.Label(manual_frame, text="Manual Addr:", bg="#2f3640", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        self.addr_entry = tk.Entry(manual_frame, width=8, font=("Arial", 11))
        self.addr_entry.pack(side=tk.LEFT, padx=5)
        self.addr_entry.bind('<Return>', lambda event: self.run_manual()) 
        
        btn_go = tk.Button(manual_frame, text="GO", command=self.run_manual, bg="#2ecc71", fg="white", font=("Arial", 9, "bold"), width=4)
        btn_go.pack(side=tk.LEFT, padx=5)

        # --- RIGHT: Control Buttons ---
        btn_frame = tk.Frame(header, bg="#2f3640")
        btn_frame.pack(side=tk.RIGHT, padx=20)
        
        tk.Button(btn_frame, text="Run Trace (30 Ops)", command=self.run_demo, bg="#0984e3", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="View Analysis", command=self.show_results, bg="#e84393", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="RESET CURRENT", command=self.reset_current, bg="#c0392b", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)

        # 2. Split Content Area
        content_frame = tk.Frame(self.root, bg=BG_COLOR)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # LEFT: Animation Canvas
        self.canvas = tk.Canvas(content_frame, bg=BG_COLOR, highlightthickness=0, width=900)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # RIGHT: Log Table
        log_frame = tk.Frame(content_frame, bg="#353b48", width=350)
        log_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10)
        
        # Dynamic label that updates with mode name
        self.lbl_log_title = tk.Label(log_frame, text=f"Log: {self.current_mode}", font=("Arial", 12, "bold"), bg="#353b48", fg="white")
        self.lbl_log_title.pack(pady=5)
        
        columns = ("step", "addr", "result", "cycles")
        self.log_tree = ttk.Treeview(log_frame, columns=columns, show="headings", height=20)
        self.log_tree.heading("step", text="#")
        self.log_tree.column("step", width=35)
        self.log_tree.heading("addr", text="Addr")
        self.log_tree.column("addr", width=50)
        self.log_tree.heading("result", text="Status")
        self.log_tree.column("result", width=80)
        self.log_tree.heading("cycles", text="Time")
        self.log_tree.column("cycles", width=80)
        
        self.log_tree.pack(fill=tk.BOTH, expand=True)
        
        self.draw_architecture()
        
        # 3. Footer
        self.footer = tk.Label(self.root, text="System Ready.", font=("Consolas", 14), bg="#2f3640", fg="#f1c40f", pady=10)
        self.footer.pack(fill=tk.X, side=tk.BOTTOM)

    def change_mode(self, event):
        new_mode = self.mode_combo.get()
        if new_mode == self.current_mode:
            return

        self.current_mode = new_mode
        self.lbl_log_title.config(text=f"Log: {self.current_mode}")
        
        # 1. Redraw Architecture for new mode
        self.draw_architecture()
        
        # 2. RESTORE LOGS FOR THIS MODE
        # Clear table visuals first
        for i in self.log_tree.get_children():
            self.log_tree.delete(i)
            
        # Refill table from memory
        saved_logs = self.log_memory[self.current_mode]
        for row in saved_logs:
            self.log_tree.insert("", "end", values=row)
            
        # Scroll to bottom if logs exist
        if saved_logs:
            self.log_tree.yview_moveto(1)
        
        self.footer.config(text=f"Switched to {self.current_mode}. Logs Restored.", fg="white")

    def draw_architecture(self):
        self.canvas.delete("all")
        self.cache_rects = {} 
        
        w = 1000
        h = 600
        mid_y = h / 2
        
        # BLOCK 1: CPU
        self.canvas.create_rectangle(50, mid_y-80, 200, mid_y+80, fill=CPU_COLOR, width=3, outline="white")
        self.canvas.create_text(125, mid_y, text="CPU", font=("Arial", 20, "bold"), fill="white")
        
        # BLOCK 2: CACHE
        cache_x = 350
        box_width = 280 if self.current_mode == "2-Way Set Associative" else 150
        
        self.canvas.create_rectangle(cache_x, mid_y-150, cache_x+box_width, mid_y+150, fill="#2c3e50", width=3, outline=CACHE_COLOR)
        title = "L1 (Direct)" if self.current_mode == "Direct Mapped" else "L1 (2-Way)"
        self.canvas.create_text(cache_x+(box_width/2), mid_y-170, text=title, font=("Arial", 16, "bold"), fill=CACHE_COLOR)
        
        current_ways = 1 if self.current_mode == "Direct Mapped" else 2
        
        # DRAW BLOCKS BASED ON CURRENT LOGIC STATE
        # We fetch the actual state from self.logics[self.current_mode]
        current_logic = self.logics[self.current_mode]
        
        for s in range(CACHE_SETS):
            for way in range(current_ways):
                bx = cache_x + 20 + (way * 120)
                by = (mid_y - 120) + (s * 60)
                
                # Check if data exists in logic to color it
                tag_val = current_logic.sets[s][way]['tag']
                fill_color = "grey" if tag_val == -1 else CACHE_COLOR
                
                rect = self.canvas.create_rectangle(bx, by, bx+100, by+50, fill=fill_color, outline="white")
                if way == 0:
                    self.canvas.create_text(bx-15, by+25, text=f"{s}", fill="#bdc3c7", font=("Arial", 8))
                
                txt_val = "--" if tag_val == -1 else f"[{tag_val*CACHE_SETS + s}]" # Approximate addr reconstruction or just show tag
                txt = self.canvas.create_text(bx+50, by+25, text=txt_val, fill="white", font=("Courier", 10))
                self.cache_rects[(s, way)] = (rect, txt)
        
        # BLOCK 3: RAM
        ram_x = cache_x + box_width + 150
        self.canvas.create_rectangle(ram_x, mid_y-200, ram_x+150, mid_y+200, fill=RAM_COLOR, width=3, outline="white")
        self.canvas.create_text(ram_x+75, mid_y, text="RAM", font=("Arial", 20, "bold"), fill="white")
        
        # BUS LINES
        self.bus_lines['L1'] = self.canvas.create_line(200, mid_y, cache_x, mid_y, fill=BUS_OFF, width=8, arrow=tk.LAST)
        self.bus_lines['L2'] = self.canvas.create_line(cache_x+box_width, mid_y, ram_x, mid_y, fill=BUS_OFF, width=8, arrow=tk.LAST)

    def run_manual(self):
        val = self.addr_entry.get()
        if not val.strip().isdigit():
            messagebox.showerror("Error", "Please enter a valid integer address")
            return
        
        addr = int(val)
        self.addr_entry.delete(0, tk.END) 
        
        # Use logic specific to current mode
        logic = self.logics[self.current_mode]
        status, s, w, cost = logic.access(addr)
        
        # 1. Update Memory
        step_num = len(self.log_memory[self.current_mode]) + 1
        log_entry = (step_num, addr, status, f"{cost} cyc")
        self.log_memory[self.current_mode].append(log_entry)
        
        # 2. Update Graph Data Memory
        self.graph_data_memory[self.current_mode].append(logic.total_cycles)
        
        # 3. Update Visual Table
        self.log_tree.insert("", "end", values=log_entry)
        self.log_tree.yview_moveto(1)
        
        self.animate_flow(addr, status, s, w)

    def run_demo(self):
        loop_pattern = [0, 4, 0, 4, 8, 12, 8, 0, 1, 5] 
        trace = loop_pattern * 3 
        
        # Auto-Clear ONLY for this mode before running new demo
        self.reset_current()
        
        logic = self.logics[self.current_mode]
            
        def step(i):
            if i < len(trace):
                addr = trace[i]
                status, s, w, cost = logic.access(addr)
                
                step_num = len(self.log_memory[self.current_mode]) + 1
                log_entry = (step_num, addr, status, f"{cost} cyc")
                
                # Update Memory & Visuals
                self.log_memory[self.current_mode].append(log_entry)
                self.graph_data_memory[self.current_mode].append(logic.total_cycles)
                
                self.log_tree.insert("", "end", values=log_entry)
                self.log_tree.yview_moveto(1) 
                
                self.animate_flow(addr, status, s, w)
                
                self.root.after(200, lambda: step(i+1))
            else:
                self.footer.config(text="Processing Complete. Data Saved.", fg="#2ecc71")
        
        step(0)

    def animate_flow(self, addr, status, s, w):
        self.canvas.itemconfig(self.bus_lines['L1'], fill="yellow") 
        self.root.update()
        
        rect, txt_obj = self.cache_rects[(s, w)]
        
        if status == "HIT":
            self.canvas.itemconfig(self.bus_lines['L1'], fill=BUS_ON_HIT)
            self.canvas.itemconfig(rect, fill=CACHE_COLOR)
            self.footer.config(text=f"HIT! Address {addr} found in Set {s}.", fg=CACHE_COLOR)
            
        elif status == "MISS":
            self.canvas.itemconfig(self.bus_lines['L1'], fill=BUS_ON_MISS)
            self.root.update()
            time.sleep(0.05) 
            
            self.footer.config(text="Fetching from RAM...", fg=RAM_COLOR)
            self.canvas.itemconfig(self.bus_lines['L2'], fill=RAM_COLOR)
            self.root.update()
            time.sleep(0.1) 
            
            self.canvas.itemconfig(self.bus_lines['L2'], fill=BUS_OFF)
            self.canvas.itemconfig(self.bus_lines['L1'], fill=BUS_ON_HIT)
            self.canvas.itemconfig(rect, fill=BUS_ON_MISS)
            # Update text on the block to show new data
            self.canvas.itemconfig(txt_obj, text=f"[{addr}]")
            self.footer.config(text=f"Data Loaded.", fg="white")

        self.root.after(200, lambda: self.reset_bus_colors(rect))

    def reset_bus_colors(self, rect_obj):
        self.canvas.itemconfig(self.bus_lines['L1'], fill=BUS_OFF)
        self.canvas.itemconfig(self.bus_lines['L2'], fill=BUS_OFF)
        # Keep it green if it has data (simple visual persistence)
        # In a complex sim we'd check state, but here we just revert to "filled" color
        # logic check:
        tag_val = self.logics[self.current_mode].sets[0][0]['tag'] # just a dummy check? no.
        # Simple reset to CACHE_COLOR is safer visually for "filled" blocks
        self.canvas.itemconfig(rect_obj, fill=CACHE_COLOR) 

    def reset_current(self):
        # 1. Reset Logic Instance
        self.logics[self.current_mode] = CacheLogic(self.current_mode)
        
        # 2. Clear Memory Lists
        self.log_memory[self.current_mode] = []
        self.graph_data_memory[self.current_mode] = []
        
        # 3. Clear Visual Table
        for i in self.log_tree.get_children(): self.log_tree.delete(i)
        
        # 4. Redraw Architecture (to clear filled blocks)
        self.draw_architecture()
        
        self.footer.config(text=f"{self.current_mode} Reset.", fg="white")

    def show_results(self):
        # Fetch logic objects to get stats
        dm_logic = self.logics["Direct Mapped"]
        sa_logic = self.logics["2-Way Set Associative"]
        
        # Check if they have run at all (total_cycles > 0)
        has_dm = dm_logic.total_cycles > 0
        has_sa = sa_logic.total_cycles > 0
        
        if not has_dm and not has_sa:
            messagebox.showwarning("No Data", "Run simulation first (Auto or Manual).")
            return
            
        res_win = tk.Toplevel(self.root)
        res_win.title("Comprehensive Analysis Report")
        res_win.geometry("1100x700")
        
        # --- LEFT SIDE: TEXT REPORT ---
        report_frame = tk.Frame(res_win, bg="#f1f2f6", width=300)
        report_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=10, pady=10)
        
        lbl_title = tk.Label(report_frame, text="PERFORMANCE REPORT", font=("Arial", 14, "bold"), bg="#f1f2f6")
        lbl_title.pack(pady=10)
        
        def create_stat_block(title, logic_obj):
            if logic_obj.total_cycles == 0: return
            total = logic_obj.hits + logic_obj.misses
            if total == 0: return
            h_ratio = (logic_obj.hits/total)*100
            m_ratio = (logic_obj.misses/total)*100
            
            text = f"""
            {title.upper()}
            -----------------------
            Total Instructions: {total}
            Hits: {logic_obj.hits}
            Misses: {logic_obj.misses}
            
            Hit Ratio:  {h_ratio:.1f}%
            Miss Ratio: {m_ratio:.1f}%
            
            TOTAL ACCESS TIME: 
            {logic_obj.total_cycles} Cycles
            """
            lbl = tk.Label(report_frame, text=text, justify=tk.LEFT, font=("Courier", 10), bg="white", relief="solid", borderwidth=1)
            lbl.pack(fill=tk.X, pady=10, padx=5)

        if has_dm: create_stat_block("Direct Mapped", dm_logic)
        if has_sa: create_stat_block("2-Way Associative", sa_logic)
        
        if has_dm and has_sa:
            t1 = dm_logic.total_cycles
            t2 = sa_logic.total_cycles
            saved = t1 - t2
            percent = (saved / t1) * 100
            
            comp_text = f"""
            FINAL VERDICT:
            -----------------------
            Time Saved: {saved} Cycles
            Speed Improvement: {percent:.1f}%
            """
            lbl_res = tk.Label(report_frame, text=comp_text, justify=tk.LEFT, font=("Arial", 11, "bold"), bg="#2ecc71", fg="white")
            lbl_res.pack(fill=tk.X, pady=20, padx=5)
        
        # --- RIGHT SIDE: GRAPHS ---
        graph_frame = tk.Frame(res_win)
        graph_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6, 6))
        plt.subplots_adjust(hspace=0.4)
        
        modes = []
        ratios = []
        colors = []
        
        if has_dm:
            modes.append("Direct")
            total = dm_logic.hits + dm_logic.misses
            ratios.append((dm_logic.hits / total) * 100)
            colors.append("#ff4757") 
        if has_sa:
            modes.append("2-Way")
            total = sa_logic.hits + sa_logic.misses
            ratios.append((sa_logic.hits / total) * 100)
            colors.append("#2ed573") 
            
        ax1.bar(modes, ratios, color=colors)
        ax1.set_title("Hit Ratio Comparison (Higher is Better)")
        ax1.set_ylabel("Hit %")
        ax1.set_ylim(0, 100)
        
        # Graph 2 needs historical data
        dm_history = self.graph_data_memory["Direct Mapped"]
        sa_history = self.graph_data_memory["2-Way Set Associative"]

        if dm_history:
            ax2.plot(range(len(dm_history)), dm_history, label="Direct Mapped", color="red", linewidth=2)
        if sa_history:
            ax2.plot(range(len(sa_history)), sa_history, label="2-Way Assoc", color="green", linewidth=2)
            
        ax2.set_title("Cumulative Latency (Lower is Better)")
        ax2.set_xlabel("Instructions Processed")
        ax2.set_ylabel("Total Cycles Spent")
        ax2.legend()
        ax2.grid(True)
        
        canvas = FigureCanvasTkAgg(fig, master=graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = SystemSimulator(root)
    root.mainloop()