import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import numpy as np
import heapq
import random
import math
import threading
from queue import Queue
import time

class SmartCourierSimulator:
    def __init__(self, master):
        self.master = master
        self.master.title("Ultra-Fast Courier Simulator")
        self.master.geometry("1000x800")
        
        # Constants
        self.DIRECTIONS = {
            0: "Up",    # North
            90: "Right", # East
            180: "Down", # South
            270: "Left"  # West
        }
        
        # Colors
        self.ROAD_COLOR_RANGE = ((90, 90, 90), (150, 150, 150))
        self.SOURCE_COLOR = "#4CAF50"  # Green flag (source)
        self.DESTINATION_COLOR = "#F44336"  # Red flag (destination)
        self.COURIER_COLOR = "#2196F3"  # Blue courier
        self.PATH_COLOR = "#9C27B0"  # Purple path
        
        # Sizes
        self.COURIER_SIZE = 20
        self.FLAG_SIZE = 12
        self.PATH_WIDTH = 3
        
        # Initialize UI
        self.setup_ui()
        
        # Game state
        self.reset_state()
        
        # Thread-safe queue for GUI updates
        self.gui_queue = Queue()
        
        # Performance tracking
        self.last_frame_time = time.time()
        self.frame_count = 0
        self.fps = 0
        
        # Start checking the queue
        self.check_queue()
    
    def setup_ui(self):
        """Initialize UI components"""
        # Control Panel
        self.control_frame = tk.Frame(self.master, bg="#f0f0f0", padx=10, pady=10)
        self.control_frame.pack(fill=tk.X)
        
        # Buttons
        self.load_btn = tk.Button(
            self.control_frame, 
            text="Load Map", 
            command=self.load_map,
            bg="#607D8B", fg="white"
        )
        self.load_btn.pack(side=tk.LEFT, padx=5)
        
        self.random_btn = tk.Button(
            self.control_frame,
            text="Random Positions",
            command=lambda: threading.Thread(target=self.place_flags_threaded, daemon=True).start(),
            bg="#795548", fg="white"
        )
        self.random_btn.pack(side=tk.LEFT, padx=5)
        
        self.start_btn = tk.Button(
            self.control_frame,
            text="Start Delivery",
            command=lambda: threading.Thread(target=self.start_delivery_threaded, daemon=True).start(),
            bg="#4CAF50", fg="white"
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = tk.Button(
            self.control_frame,
            text="Stop",
            command=self.stop_delivery,
            bg="#F44336", fg="white"
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Speed Control
        self.speed_label = tk.Label(self.control_frame, text="Speed:", bg="#f0f0f0")
        self.speed_label.pack(side=tk.LEFT, padx=(20, 5))
        
        self.speed_scale = tk.Scale(
            self.control_frame,
            from_=1, to=30,
            orient=tk.HORIZONTAL,
            bg="#f0f0f0"
        )
        self.speed_scale.set(10)  # Default to medium speed
        self.speed_scale.pack(side=tk.LEFT)
        
        # Status Bar
        self.status_frame = tk.Frame(self.master, bg="#333", height=30)
        self.status_frame.pack(fill=tk.X)
        
        self.status_label = tk.Label(
            self.status_frame,
            text="Status: Ready to load map | FPS: 0",
            fg="white",
            bg="#333"
        )
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        # Main Canvas
        self.canvas = tk.Canvas(
            self.master,
            width=900,
            height=700,
            bg="#333"
        )
        self.canvas.pack(pady=(0, 10))
    
    def check_queue(self):
        """Check for GUI updates from threads and calculate FPS"""
        try:
            while True:
                task = self.gui_queue.get_nowait()
                task()
        except:
            pass
        
        # Calculate FPS
        self.frame_count += 1
        current_time = time.time()
        if current_time - self.last_frame_time >= 1.0:
            self.fps = self.frame_count
            self.frame_count = 0
            self.last_frame_time = current_time
            self.update_fps()
            
        self.master.after(10, self.check_queue)
    
    def update_fps(self):
        """Update FPS display in status bar"""
        current_text = self.status_label.cget("text")
        if "FPS:" in current_text:
            current_text = current_text.split("| FPS:")[0].strip()
        self.status_label.config(text=f"{current_text} | FPS: {self.fps}")
    
    def reset_state(self):
        """Reset game state"""
        self.image = None
        self.image_tk = None
        self.image_path = None
        self.map_array = None
        self.original_size = None
        
        self.source = None
        self.destination = None
        self.courier = None
        self.courier_angle = 90  # Start facing right
        self.target_angle = 90   # For smooth rotation
        self.has_package = False
        self.path = []
        self.delivery_in_progress = False
        self.road_pixels = []
        self.road_set = set()
        self.animation_id = None
        self.rotation_id = None
        self.current_step = 0
        self.prev_pos = None
        self.interp_pos = None
        self.interp_factor = 0.3  # Smoother movement interpolation
        self.smooth_angle = 90    # For extra smooth rotation
    
    def stop_delivery(self):
        """Stop the current delivery"""
        if self.animation_id:
            self.master.after_cancel(self.animation_id)
            self.animation_id = None
        if self.rotation_id:
            self.master.after_cancel(self.rotation_id)
            self.rotation_id = None
        self.delivery_in_progress = False
        self.gui_queue.put(lambda: self.update_status("Delivery stopped"))
    
    def load_map(self):
        """Load and validate map image"""
        if self.delivery_in_progress:
            return
            
        file_path = filedialog.askopenfilename(
            title="Select Map Image",
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg")]
        )
        
        if not file_path:
            return
            
        try:
            img = Image.open(file_path).convert("RGB")
            width, height = img.size
            
            if not (1000 <= width <= 1500) or not (700 <= height <= 1000):
                messagebox.showerror(
                    "Invalid Map Size",
                    f"Map must be 1000-1500px wide and 700-1000px tall.\n"
                    f"Your map is {width}x{height}px."
                )
                return
                
            self.image_path = file_path
            self.original_size = (width, height)
            self.map_array = np.array(img)
            
            img.thumbnail((900, 700), Image.LANCZOS)
            self.image = img
            self.image_tk = ImageTk.PhotoImage(self.image)
            
            self.road_pixels = self.get_road_pixels()
            self.road_set = set(self.road_pixels)
            
            if len(self.road_pixels) < 10:
                messagebox.showwarning(
                    "Few Road Pixels",
                    f"Only found {len(self.road_pixels)} road pixels.\n"
                    "The map may not have enough navigable area."
                )
            
            self.gui_queue.put(lambda: self.canvas.delete("all"))
            self.gui_queue.put(lambda: self.canvas.config(width=self.image.width, height=self.image.height))
            self.gui_queue.put(lambda: self.canvas.create_image(0, 0, anchor=tk.NW, image=self.image_tk))
            
            self.gui_queue.put(lambda: self.update_status(f"Map loaded: {width}x{height} | Road pixels: {len(self.road_pixels)}"))
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {str(e)}")
            self.reset_state()
    
    def get_road_pixels(self):
        """Return list of road pixel coordinates (y, x)"""
        if self.map_array is None:
            return []
            
        min_rgb, max_rgb = self.ROAD_COLOR_RANGE
        
        # Vectorized operation for better performance
        road_mask = (
            (self.map_array[:,:,0] >= min_rgb[0]) & (self.map_array[:,:,0] <= max_rgb[0]) &
            (self.map_array[:,:,1] >= min_rgb[1]) & (self.map_array[:,:,1] <= max_rgb[1]) &
            (self.map_array[:,:,2] >= min_rgb[2]) & (self.map_array[:,:,2] <= max_rgb[2])
        )
        
        return list(zip(*np.where(road_mask)))
    
    def place_flags_threaded(self):
        """Threaded version of place_flags"""
        if self.delivery_in_progress:
            return
            
        if not self.road_pixels:
            self.gui_queue.put(lambda: messagebox.showerror("Error", "No valid road pixels found in the map"))
            return
            
        self.gui_queue.put(lambda: self.canvas.delete("all"))
        if self.image_tk:
            self.gui_queue.put(lambda: self.canvas.create_image(0, 0, anchor=tk.NW, image=self.image_tk))
        
        if self.animation_id:
            self.master.after_cancel(self.animation_id)
            self.animation_id = None
        if self.rotation_id:
            self.master.after_cancel(self.rotation_id)
            self.rotation_id = None
        
        max_attempts = 10
        valid_positions_found = False
        
        for attempt in range(max_attempts):
            self.source = random.choice(self.road_pixels)
            self.destination = random.choice(self.road_pixels)
            while self.destination == self.source:
                self.destination = random.choice(self.road_pixels)
                
            self.courier = random.choice(self.road_pixels)
            while self.courier == self.source or self.courier == self.destination:
                self.courier = random.choice(self.road_pixels)
                
            self.courier_angle = random.choice(list(self.DIRECTIONS.keys()))
            self.target_angle = self.courier_angle
            self.smooth_angle = self.courier_angle
            self.has_package = False
            self.current_step = 0
            self.prev_pos = None
            self.interp_pos = None
            
            path_to_source = self.optimized_a_star(self.courier, self.source)
            if not path_to_source:
                continue
                
            path_to_dest = self.optimized_a_star(self.source, self.destination)
            if path_to_dest:
                valid_positions_found = True
                break
                
        if not valid_positions_found:
            self.gui_queue.put(lambda: messagebox.showerror(
                "Position Error",
                "Couldn't find valid positions with connecting paths after 10 attempts."
            ))
            return
            
        self.gui_queue.put(lambda: self.draw_flag(self.source, self.SOURCE_COLOR, "source"))
        self.gui_queue.put(lambda: self.draw_flag(self.destination, self.DESTINATION_COLOR, "destination"))
        self.gui_queue.put(lambda: self.draw_courier())
        
        self.gui_queue.put(lambda: self.update_status("Positions placed | Ready to deliver"))
    
    def draw_flag(self, position, color, tag):
        """Draw a flag marker at specified position"""
        if self.image is None:
            return
            
        orig_y, orig_x = position
        scale_x = self.image.width / self.original_size[0]
        scale_y = self.image.height / self.original_size[1]
        x = orig_x * scale_x
        y = orig_y * scale_y
        
        self.canvas.create_oval(
            x - self.FLAG_SIZE, y - self.FLAG_SIZE,
            x + self.FLAG_SIZE, y + self.FLAG_SIZE,
            fill=color, outline="black", tags=tag
        )
        
        self.canvas.create_line(
            x, y,
            x, y - self.FLAG_SIZE * 2,
            fill="black", width=2, tags=tag
        )
    
    def draw_courier(self):
        """Draw the courier with smooth interpolation and optimized rendering"""
        if self.image is None or self.courier is None:
            return
            
        # Calculate interpolated position for smooth movement
        if self.prev_pos and self.interp_pos is None:
            self.interp_pos = self.prev_pos
            
        if self.interp_pos:
            # Smooth interpolation
            orig_y = self.interp_pos[0] + (self.courier[0] - self.interp_pos[0]) * self.interp_factor
            orig_x = self.interp_pos[1] + (self.courier[1] - self.interp_pos[1]) * self.interp_factor
            self.interp_pos = (orig_y, orig_x)
        else:
            orig_y, orig_x = self.courier
        
        scale_x = self.image.width / self.original_size[0]
        scale_y = self.image.height / self.original_size[1]
        x = orig_x * scale_x
        y = orig_y * scale_y
        
        self.canvas.delete("courier")
        
        # Smooth angle transition
        angle_diff = (self.target_angle - self.smooth_angle + 180) % 360 - 180
        self.smooth_angle = (self.smooth_angle + angle_diff * 0.2) % 360
        
        # Pre-calculate triangle points for maximum speed
        angle_rad = math.radians(self.smooth_angle)
        size = self.COURIER_SIZE
        points = [
            x + size * math.cos(angle_rad),  # Front point
            y - size * math.sin(angle_rad),
            x + size * 0.7 * math.cos(angle_rad + math.pi * 0.8),  # Rear left
            y - size * 0.7 * math.sin(angle_rad + math.pi * 0.8),
            x + size * 0.7 * math.cos(angle_rad - math.pi * 0.8),  # Rear right
            y - size * 0.7 * math.sin(angle_rad - math.pi * 0.8)
        ]
        
        self.canvas.create_polygon(
            points,
            fill=self.COURIER_COLOR,
            outline="white",
            width=2,
            tags="courier"
        )
        
        if self.has_package:
            self.canvas.create_text(
                x, y - size - 15,
                text="📦", font=("Arial", 14), tags="courier"
            )
    
    def draw_path(self, path):
        """Visualize the path on the canvas with optimized rendering"""
        if not path or len(path) < 2:
            return
            
        self.canvas.delete("path")
        
        scale_x = self.image.width / self.original_size[0]
        scale_y = self.image.height / self.original_size[1]
        
        # Pre-calculate all points for faster line drawing
        points = []
        for y, x in path:
            points.append(x * scale_x)
            points.append(y * scale_y)
        
        self.canvas.create_line(
            *points,
            fill=self.PATH_COLOR,
            width=self.PATH_WIDTH,
            tags="path"
        )
    
    def start_delivery_threaded(self):
        """Threaded version of start_delivery with optimized pathfinding"""
        if self.delivery_in_progress:
            return
            
        if (self.map_array is None or 
            self.source is None or 
            self.destination is None or 
            self.courier is None):
            self.gui_queue.put(lambda: messagebox.showerror("Error", "Please load map and place positions first"))
            return
            
        self.delivery_in_progress = True
        self.current_step = 0
        self.prev_pos = self.courier
        self.interp_pos = self.courier
        self.gui_queue.put(lambda: self.update_status("Starting delivery..."))
        
        if not self.has_package:
            # Going to pick up package
            self.path = self.optimized_a_star(self.courier, self.source)
            if not self.path:
                self.gui_queue.put(lambda: messagebox.showerror("Error", "No path found to source"))
                self.delivery_in_progress = False
                return
                
            self.gui_queue.put(lambda: self.draw_path(self.path))
            self.ultra_fast_animate("source")
        else:
            # Already has package, go to destination
            self.path = self.optimized_a_star(self.courier, self.destination)
            if not self.path:
                self.gui_queue.put(lambda: messagebox.showerror("Error", "No path found to destination"))
                self.delivery_in_progress = False
                return
                
            self.gui_queue.put(lambda: self.draw_path(self.path))
            self.ultra_fast_animate("destination")
    
    def ultra_fast_animate(self, target):
        """Optimized movement animation with smooth transitions"""
        if not self.delivery_in_progress:
            return
            
        # Update position in chunks based on speed
        speed = self.speed_scale.get()
        step_size = min(1 + speed // 5, len(self.path) - self.current_step - 1)
        
        # Store previous position for interpolation
        self.prev_pos = self.courier
        
        # Move forward in the path
        if self.current_step + step_size < len(self.path):
            self.courier = self.path[self.current_step + step_size]
            self.current_step += step_size
        else:
            self.courier = self.path[-1]
            self.current_step = len(self.path) - 1
        
        # Update direction based on next few steps to prevent jitter at intersections
        look_ahead = min(5, len(self.path) - self.current_step - 1)
        if look_ahead > 0:
            next_pos = self.path[self.current_step + look_ahead]
            self.target_angle = self.get_direction_to(next_pos)
        
        # Update display
        self.gui_queue.put(lambda: self.canvas.delete("courier"))
        self.gui_queue.put(lambda: self.draw_courier())
        
        # Calculate delay - exponential scaling for speed
        delay = max(0, int(30 / (speed ** 0.7)))
        
        if self.current_step < len(self.path) - 1:
            self.animation_id = self.master.after(delay, lambda: self.ultra_fast_animate(target))
        else:
            self.handle_delivery_complete(target)
    
    def get_direction_to(self, position):
        """Optimized direction calculation with smoothing"""
        dy = position[0] - self.courier[0]
        dx = position[1] - self.courier[1]
        
        if dx == 0 and dy == 0:
            return self.target_angle
            
        return math.degrees(math.atan2(-dy, dx)) % 360
    
    def get_direction_to_target(self, target_pos):
        """Optimized facing direction calculation"""
        cy, cx = self.courier
        ty, tx = target_pos
        dy = ty - cy
        dx = tx - cx
        
        if dx == 0 and dy == 0:
            return self.target_angle
            
        return math.degrees(math.atan2(-dy, dx)) % 360
    
    def optimized_a_star(self, start, goal):
        """Extremely optimized A* pathfinding algorithm"""
        if start == goal:
            return []
            
        if abs(start[0] - goal[0]) + abs(start[1] - goal[1]) == 1:
            return [goal]
            
        if not (start in self.road_set and goal in self.road_set):
            return []
            
        # Check if we can use a straight line (faster than A*)
        if self.check_straight_line(start, goal):
            return self.bresenham_line(start, goal)
            
        # Otherwise use optimized A*
        rows, cols = self.map_array.shape[:2]
        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self.chebyshev_heuristic(start, goal)}
        
        open_set_hash = {start}
        
        while open_set:
            _, current = heapq.heappop(open_set)
            open_set_hash.remove(current)
            
            if current == goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.reverse()
                return path
                
            # Check neighbors in optimal order (right, down, left, up)
            for dy, dx in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                neighbor = (current[0] + dy, current[1] + dx)
                
                if 0 <= neighbor[0] < rows and 0 <= neighbor[1] < cols:
                    if neighbor in self.road_set:
                        tentative_g = g_score[current] + 1
                        
                        if neighbor not in g_score or tentative_g < g_score[neighbor]:
                            came_from[neighbor] = current
                            g_score[neighbor] = tentative_g
                            f_score[neighbor] = tentative_g + self.chebyshev_heuristic(neighbor, goal)
                            if neighbor not in open_set_hash:
                                heapq.heappush(open_set, (f_score[neighbor], neighbor))
                                open_set_hash.add(neighbor)
        
        return []
    
    def check_straight_line(self, start, goal):
        """Check if a straight line path exists between two points"""
        # Simple check - only works for perfectly straight lines
        if start[0] == goal[0] or start[1] == goal[1]:
            return True
        return False
    
    def bresenham_line(self, start, goal):
        """Bresenham's line algorithm for straight paths"""
        x0, y0 = start[1], start[0]
        x1, y1 = goal[1], goal[0]
        points = []
        
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        x, y = x0, y0
        sx = -1 if x0 > x1 else 1
        sy = -1 if y0 > y1 else 1
        
        if dx > dy:
            err = dx / 2.0
            while x != x1:
                points.append((y, x))
                err -= dy
                if err < 0:
                    y += sy
                    err += dx
                x += sx
        else:
            err = dy / 2.0
            while y != y1:
                points.append((y, x))
                err -= dx
                if err < 0:
                    x += sx
                    err += dy
                y += sy
        
        points.append((y1, x1))
        return points
    
    def chebyshev_heuristic(self, a, b):
        """Optimized Chebyshev distance heuristic"""
        return max(abs(a[0] - b[0]), abs(a[1] - b[1]))
    
    def handle_delivery_complete(self, target):
        """Handle completion of delivery stage"""
        if target == "source":
            self.has_package = True
            self.gui_queue.put(lambda: self.update_status("Package picked up"))
            
            # Face the source when picking up
            self.target_angle = self.get_direction_to_target(self.source)
            
            # Start delivery to destination
            self.path = self.optimized_a_star(self.courier, self.destination)
            if not self.path:
                self.gui_queue.put(lambda: messagebox.showerror("Error", "No path found to destination"))
                self.delivery_in_progress = False
                return
                
            self.current_step = 0
            self.prev_pos = self.courier
            self.interp_pos = self.courier
            self.gui_queue.put(lambda: self.draw_path(self.path))
            self.ultra_fast_animate("destination")
            
        elif target == "destination":
            # Face the destination when delivering
            self.target_angle = self.get_direction_to_target(self.destination)
            
            self.has_package = False
            self.gui_queue.put(lambda: self.update_status("Delivery successful!"))
            self.gui_queue.put(lambda: messagebox.showinfo("Success", "Package delivered successfully!"))
            self.delivery_in_progress = False
    
    def update_status(self, message):
        """Update status label"""
        current_text = self.status_label.cget("text")
        if "FPS:" in current_text:
            fps_part = current_text.split("| FPS:")[1].strip()
            self.status_label.config(text=f"Status: {message} | FPS: {fps_part}")
        else:
            self.status_label.config(text=f"Status: {message}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SmartCourierSimulator(root)
    root.mainloop()
