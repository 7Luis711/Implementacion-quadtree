import matplotlib
matplotlib.use('Qt5Agg')

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import math



class QuadNode:
    def __init__(self, x, y, w, h, capacity=1, level=0, max_level=10):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.capacity = capacity
        self.level = level
        self.max_level = max_level
        self.points = []
        self.divided = False
        self.children = []

    def contains(self, point):
        x, y = point
        return self.x <= x < self.x + self.w and self.y <= y < self.y + self.h

    def subdivide(self):
        """Divide este nodo en 4 hijos"""
        if self.divided or self.level >= self.max_level:
            return
            
        hw, hh = self.w / 2, self.h / 2
        self.children = [
            QuadNode(self.x, self.y, hw, hh, self.capacity, self.level + 1, self.max_level),  # NW
            QuadNode(self.x + hw, self.y, hw, hh, self.capacity, self.level + 1, self.max_level),  # NE
            QuadNode(self.x, self.y + hh, hw, hh, self.capacity, self.level + 1, self.max_level),  # SW
            QuadNode(self.x + hw, self.y + hh, hw, hh, self.capacity, self.level + 1, self.max_level)   # SE
        ]
        self.divided = True
        print(f" Nivel {self.level}: Subdividido en 4 regiones")

    def insert(self, point):
        """Inserta un punto en el quadtree"""
        if not self.contains(point):
            return False

        if self.divided:
            for child in self.children:
                if child.insert(point):
                    return True
            return False

        self.points.append(point)
        print(f"Punto {point} agregado al nodo nivel {self.level}. Ahora tiene {len(self.points)} puntos")


        should_subdivide = False
        
        if self.level == 0 and len(self.points) == 1:
            should_subdivide = True
            print(f"Nivel 0: Primer punto - FORZAR SUBDIVISIÓN")
        elif len(self.points) > self.capacity and self.level < self.max_level:

            should_subdivide = True
            print(f" Nivel {self.level}: Excede capacidad ({len(self.points)} > {self.capacity})")

        if should_subdivide:
            self.subdivide()
            
            points_to_redistribute = self.points[:]
            self.points = []  
            
            redistributed_count = 0
            for p in points_to_redistribute:
                point_inserted = False
                for child in self.children:
                    if child.contains(p):

                        child.points.append(p)
                        point_inserted = True
                        redistributed_count += 1
                        print(f" Punto {p} redistribuido a hijo")
                        break
                
                if not point_inserted:
                    self.points.append(p)
                    print(f" Punto {p} no pudo ser redistribuido")
            
            print(f"  Redistribuidos {redistributed_count} puntos a hijos")
        
        return True

    def delete(self, point):
        """Elimina un punto del quadtree"""
        if not self.contains(point):
            return False

        if self.divided:
            for child in self.children:
                if child.delete(point):
                    if all(not c.points and not c.divided for c in self.children):
                        self.children = []
                        self.divided = False
                        print(f"Nivel {self.level}: Colapsado (todos los hijos vacíos)")
                    return True
        else:
            if point in self.points:
                self.points.remove(point)
                print(f"Punto {point} eliminado del nivel {self.level}")
                return True
        return False

    def query_range(self, rect, found_points=None, visited_nodes=None):
        """Busca puntos dentro de un rectángulo (x, y, w, h)"""
        if found_points is None:
            found_points = []
        if visited_nodes is None:
            visited_nodes = []
        
        visited_nodes.append(self)
        

        rx, ry, rw, rh = rect
        if not (self.x < rx + rw and self.x + self.w > rx and 
                self.y < ry + rh and self.y + self.h > ry):
            return found_points, visited_nodes


        for point in self.points:
            px, py = point
            if rx <= px <= rx + rw and ry <= py <= ry + rh:
                found_points.append(point)

        if self.divided:
            for child in self.children:
                found_points, visited_nodes = child.query_range(rect, found_points, visited_nodes)
                
        return found_points, visited_nodes

    def draw(self, ax):
        """Dibuja este nodo y sus subdivisiones"""
        rect = patches.Rectangle((self.x, self.y), self.w, self.h,
                                linewidth=1, edgecolor='blue', facecolor='none', alpha=0.7)
        ax.add_patch(rect)
        
        for point in self.points:
            ax.plot(point[0], point[1], 'ro', markersize=6)
        
        if self.divided:
            for child in self.children:
                child.draw(ax)

class QuadtreeDemo:
    def __init__(self, capacity=1):
        self.capacity = capacity
        self.points = []
        self.root = QuadNode(0, 0, 1, 1, capacity=self.capacity)
        
        self.search_rect = None
        self.found_points = []
        self.visited_nodes = []
        self.dragging = False
        self.drag_start = None

        self.fig, self.ax = plt.subplots(figsize=(10, 8))
        self.canvas = self.fig.canvas
        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(0, 1)
        self.ax.set_aspect('equal')
        self.ax.set_title("Quadtree Corregido | 🖱 Izq: Insertar | Der: Buscar | Rueda: Eliminar")
        self.ax.grid(True, alpha=0.3)

        self.canvas.mpl_connect('button_press_event', self.on_press)
        self.canvas.mpl_connect('button_release_event', self.on_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_motion)
        
        self.draw()

    def draw(self):
        """Redibuja el quadtree completo"""
        self.ax.clear()
        
        for node in self.visited_nodes:
            self.ax.add_patch(patches.Rectangle(
                (node.x, node.y), node.w, node.h,
                linewidth=1, edgecolor='orange', facecolor='yellow', alpha=0.3
            ))
        
        self.root.draw(self.ax)
        
        if self.points:
            xs, ys = zip(*self.points)
            self.ax.scatter(xs, ys, s=50, color='black', zorder=5, label='Puntos')
        
        if self.search_rect:
            rx, ry, rw, rh = self.search_rect
            rect = patches.Rectangle(
                (rx, ry), rw, rh,
                linewidth=2, edgecolor='red', facecolor='none', linestyle='--'
            )
            self.ax.add_patch(rect)
        
        if self.found_points:
            xs, ys = zip(*self.found_points)
            self.ax.scatter(xs, ys, s=80, color='red', marker='*', zorder=6, label='Encontrados')
        
        self.ax.text(0.02, 0.98, f"Puntos totales: {len(self.points)}", 
                    transform=self.ax.transAxes, fontsize=11, color='blue', weight='bold',
                    verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
        
        if self.found_points:
            self.ax.text(0.02, 0.90, f"Puntos encontrados: {len(self.found_points)}", 
                        transform=self.ax.transAxes, fontsize=11, color='red', weight='bold',
                        verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.8))
        
        self.ax.legend(loc='upper right')
        self.ax.grid(True, alpha=0.3)
        self.canvas.draw_idle()

    def on_press(self, event):
        if event.inaxes != self.ax or event.xdata is None or event.ydata is None:
            return

        p = (event.xdata, event.ydata)

        if event.button == 1:
            print(f"\n=== INSERTANDO PUNTO {p} ===")
            success = self.root.insert(p)
            if success:
                self.points.append(p)
                print(f"Punto {p} insertado exitosamente. Total: {len(self.points)} puntos")
            else:
                print(f"Error: No se pudo insertar {p}")
            self.draw()

        elif event.button == 3:
            self.dragging = True
            self.drag_start = p
            self.search_rect = None
            self.found_points = []
            self.visited_nodes = []
            print(f"\n=== INICIANDO BÚSQUEDA desde {p} ===")

        elif event.button == 2:
            if not self.points:
                return
            nearest = min(self.points, key=lambda q: math.dist(p, q))
            print(f"\n=== ELIMINANDO PUNTO {nearest} ===")
            self.root.delete(nearest)
            self.points.remove(nearest)
            print(f"Punto {nearest} eliminado. Total: {len(self.points)} puntos")
            self.draw()

    def on_motion(self, event):
        if not self.dragging or event.inaxes != self.ax or event.xdata is None or event.ydata is None:
            return

        x1, y1 = event.xdata, event.ydata
        x0, y0 = self.drag_start
        
        rx = min(x0, x1)
        ry = min(y0, y1)
        rw = abs(x1 - x0)
        rh = abs(y1 - y0)
        
        self.search_rect = (rx, ry, rw, rh)
        self.draw()

    def on_release(self, event):
        if not self.dragging or event.inaxes != self.ax:
            self.dragging = False
            return

        if event.button == 3 and self.search_rect:
            print(f"\n=== EJECUTANDO BÚSQUEDA en rectángulo {self.search_rect} ===")
            self.found_points, self.visited_nodes = self.root.query_range(self.search_rect)
            print(f"Búsqueda completada: {len(self.found_points)} puntos encontrados, {len(self.visited_nodes)} nodos visitados")
            self.dragging = False
            self.draw()


if __name__ == "__main__":
    print("Iniciando Quadtree corregido...")
    print("COMPORTAMIENTO ESPERADO:")
    print("1. Primer punto: Crear 4 regiones principales")
    print("2. Puntos siguientes: Insertar en regiones existentes") 
    print("3. Subdivisión: Solo cuando una región tiene >1 punto")
    app = QuadtreeDemo(capacity=1)
    plt.show()




