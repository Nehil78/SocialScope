import networkx as nx
from collections import Counter
import plotly.graph_objects as go
from pathlib import Path

class NetworkGraph:
    def __init__(self, messages):
        self.messages = messages
        self.G = nx.Graph()

    def build_graph(self):
        sender_count = Counter()
        for msg in self.messages:
            sender = msg.get('sender', 'Unknown')
            sender_count[sender] += 1

        for sender, count in sender_count.items():
            self.G.add_node(sender, messages=count)

        nodes = list(sender_count.keys())
        for i in range(len(nodes) - 1):
            self.G.add_edge(nodes[i], nodes[i+1], weight=1)

        print(f"[+] Network Graph built with {len(self.G.nodes)} nodes")

    def show_top_contacts(self, top=6):
        print(f"\n[bold cyan]Top {top} Contacts (Sabse Zyada Messages):[/bold cyan]")
        sender_count = Counter(msg.get('sender') for msg in self.messages)
        for sender, count in sender_count.most_common(top):
            print(f"  • {sender} → {count} messages")

    def save_interactive_graph(self):
        Path("./output/graphs").mkdir(parents=True, exist_ok=True)
        
        pos = nx.spring_layout(self.G)
        edge_x = []
        edge_y = []
        for edge in self.G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

        node_x = [pos[node][0] for node in self.G.nodes()]
        node_y = [pos[node][1] for node in self.G.nodes()]

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=edge_x, y=edge_y, mode='lines', line=dict(width=0.5, color='#888')))
        fig.add_trace(go.Scatter(x=node_x, y=node_y, mode='markers+text',
                                 marker=dict(size=25, color='#FF5733'),
                                 text=list(self.G.nodes()),
                                 textposition="top center"))

        fig.update_layout(title="SocialScope - Network Link Analysis",
                          showlegend=False,
                          xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                          yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))

        file_path = Path("./output/graphs/network_graph.html")
        fig.write_html(str(file_path))
        print(f"[bold green]✅ Interactive Graph saved → {file_path}[/bold green]")