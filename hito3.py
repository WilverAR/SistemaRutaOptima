import csv
import networkx as nx
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QApplication, QPushButton, QLabel
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import sys

class GraphWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GUI HiTO3")
        self.setGeometry(100, 100, 800, 600)

        Nodes = {}
        Edges = {}

        with open('node_list.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                Nodes[row['id']] = {'X': row['X'], 'Y': row['Y']}

        with open('edge_list.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                Edges[row['id']] = {'node1': row['node1'], 'node2': row['node2'], 'distance': row['distance']}

        G = nx.DiGraph()

        # Agregar los nodos al grafo
        for nodo_id, nodo_data in Nodes.items():
            G.add_node(nodo_id, pos=(float(nodo_data['X']), float(nodo_data['Y'])))

        # Agregar las aristas al grafo
        for edge_id, edge_data in Edges.items():
            from_node = edge_data['node1']
            to_node = edge_data['node2']
            distance = float(edge_data['distance'])
            G.add_edge(from_node, to_node, weight=distance)

        self.G = G
        self.start_node = None
        self.end_node = None

        # Crear el lienzo de Matplotlib
        self.figure = Figure(figsize=(7, 7))
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_axis_off()
        self.ax.set_position([0, 0, 1, 1])
        # Agregar el lienzo al diseño de la ventana
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        # Crear botón para establecer el nodo de inicio y el nodo final
        self.set_nodes_button = QPushButton("Establecer nodos inicio/final")
        layout.addWidget(self.set_nodes_button)

        # Conectar la señal de clic del botón a la función set_nodes
        self.set_nodes_button.clicked.connect(self.set_nodes)

        # Agregar QLabel para mostrar el mensaje
        self.message_label = QLabel()
        layout.addWidget(self.message_label)

        # Agregar QLabel para mostrar los IDs de los nodos de inicio y final
        self.ids_label = QLabel()
        layout.addWidget(self.ids_label)

        # Conectar la señal de clic del lienzo a la función handle_click
        self.canvas.mpl_connect("button_press_event", self.handle_click)


        # Dibujar el grafo en el lienzo
        pos = nx.get_node_attributes(G, 'pos')
        nx.draw_networkx(G, pos=pos, node_size=7, width=0.5, with_labels=False, arrows=False, ax=self.ax)
        self.canvas.draw()

    def set_nodes(self):
        self.start_node = None
        self.end_node = None
        self.message_label.setText("Haz clic en el lienzo para establecer el nodo de inicio.")
        self.ids_label.setText("")
        self.clear_canvas()  # Borrar el lienzo anterior
        self.reset_node_colors()  # Restablecer los colores de los nodos a su estado original

    def handle_click(self, event):
        if self.start_node is None:
            self.start_node = self.get_clicked_node(event.xdata, event.ydata)
            if self.start_node is not None:
                self.message_label.setText("Haz clic en el lienzo para establecer el nodo final.")
                self.highlight_node(self.start_node, color='green')  # Cambiar el color del nodo de inicio a verde
        elif self.end_node is None:
            self.end_node = self.get_clicked_node(event.xdata, event.ydata)
            if self.end_node is not None:
                self.message_label.setText("Nodos de inicio y final establecidos.")
                self.highlight_node(self.end_node, color='red')  # Cambiar el color del nodo final a rojo
                self.ids_label.setText(f"Nodo inicio: {self.start_node}\nNodo final: {self.end_node}")

                self.highlight_shortest_path()
        else:
            self.message_label.setText("Ya se han establecido los nodos de inicio y final.")
            self.ids_label.setText(f"Nodo inicio: {self.start_node}\nNodo final: {self.end_node}")

    def cargar_grafo_desde_csv(self, archivo_csv):
        grafo = nx.DiGraph()  # crear un grafo dirigido
        with open(archivo_csv) as csv_file:  # abrir el archivo CSV en modo lectura
            csv_reader = csv.reader(csv_file)  # crear un objeto de lectura CSV
            next(csv_reader)  # saltar la primera fila (cabecera)
            for row in csv_reader:  # iterar sobre cada fila del archivo CSV
                id, origen, destino, peso = row  # separar los datos de la fila en origen, destino y peso
                grafo.add_edge(origen, destino, weight=float(peso),
                               edge_color='black')  # agregar la arista al grafo con su peso y color
        return grafo

    def dijkstra(self, grafo, origen, destino):
        # Implementación del algoritmo de Dijkstra
        distancia = {nodo: float('inf') for nodo in grafo}
        distancia[origen] = 0
        visitados = set()
        cola_prioridad = [(0, origen)]
        anteriores = {}

        while cola_prioridad:
            cola_prioridad.sort()
            (dist_actual, nodo_actual) = cola_prioridad.pop(0)
            if nodo_actual == destino:
                break
            if nodo_actual in visitados:
                continue
            visitados.add(nodo_actual)
            for vecino, peso in grafo[nodo_actual].items():
                dist_nueva = dist_actual + peso['weight']
                if dist_nueva < distancia[vecino]:
                    distancia[vecino] = dist_nueva
                    anteriores[vecino] = nodo_actual
                    cola_prioridad.append((dist_nueva, vecino))

        nodo_actual = destino
        camino = []
        while nodo_actual != origen:
            camino.append(nodo_actual)
            nodo_actual = anteriores[nodo_actual]
        camino.append(origen)
        camino.reverse()
        print("Camino:", " → ".join(camino) + "\n")  # Imprimir el camino en la consola
        print("Distancia recorrida:", distancia[destino], "m.\n")  # Imprimir la distancia recorrida

        return camino

    def highlight_shortest_path(self):
        if self.start_node is not None and self.end_node is not None:
            # Copiar el grafo original
            self.G_copy = self.G.copy()

            # Ejecutar el algoritmo de Dijkstra para encontrar el camino más corto
            camino_mas_corto = self.dijkstra(self.G_copy, self.start_node, self.end_node)

            # Crear un nuevo grafo con solo el camino más corto
            shortest_path_graph = nx.DiGraph()

            # Agregar los nodos del camino más corto al nuevo grafo
            for nodo in camino_mas_corto:
                shortest_path_graph.add_node(nodo, pos=self.G_copy.nodes[nodo]['pos'])

            # Agregar las aristas del camino más corto al nuevo grafo
            for u, v in zip(camino_mas_corto, camino_mas_corto[1:]):
                shortest_path_graph.add_edge(u, v, weight=self.G_copy[u][v]['weight'])

            # Dibujar solo el camino más corto en el lienzo

            pos = nx.get_node_attributes(shortest_path_graph, 'pos')
            nx.draw_networkx(shortest_path_graph, pos=pos, node_size=7, width=2.0, edge_color='red',
                             with_labels=False, arrows=True, ax=self.ax)

            self.canvas.draw()

    def highlight_node(self, node, color):
        # Obtener la posición del nodo
        pos = nx.get_node_attributes(self.G, 'pos')
        node_pos = pos[node]
        # Dibujar el nodo con el color especificado
        self.ax.scatter(node_pos[0], node_pos[1], s=50, c=color, edgecolors='k')
        # Actualizar el lienzo
        self.canvas.draw()

    def clear_canvas(self):
        # Limpiar el lienzo eliminando todos los elementos dibujados
        self.ax.cla()
    def reset_node_colors(self):
        # Restablecer los colores de los nodos a su estado original
        pos = nx.get_node_attributes(self.G, 'pos')
        node_colors = ['k' for _ in self.G.nodes()]
        nx.draw_networkx(self.G, pos=pos, node_size=7, width=0.5, with_labels=False, arrows=False, ax=self.ax)
        self.canvas.draw()

    def get_clicked_node(self, x, y):
        # Obtener el nodo más cercano a las coordenadas x, y
        pos = nx.get_node_attributes(self.G, 'pos')
        distances = [(node, (pos[node][0] - x) ** 2 + (pos[node][1] - y) ** 2) for node in self.G.nodes()]
        if distances:
            closest_node = min(distances, key=lambda x: x[1])[0]
            return closest_node
        return None




if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GraphWindow()
    window.show()
    sys.exit(app.exec_())