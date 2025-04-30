import networkx as nx
import itertools
import sys
import matplotlib.pyplot as plt

# ---- Visualization Utility ----
def visualize_graph(G, title, filename, highlight_nodes=None):
    plt.figure(figsize=(10, 8))
    pos = nx.spring_layout(G, seed=42)
    nx.draw_networkx_nodes(G, pos, node_color='lightgray', node_size=300)
    nx.draw_networkx_edges(G, pos)
    if highlight_nodes:
        nx.draw_networkx_nodes(G, pos,
                               nodelist=list(highlight_nodes),
                               node_color='orange', node_size=400)
    nx.draw_networkx_labels(G, pos)
    plt.title(title)
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

# ---- Independent Set (IS) ----
def is_independent_set(G, independent_set):
    for u, v in itertools.combinations(independent_set, 2):
        if G.has_edge(u, v):
            print("Edge exists within independent set:", u, v)
            return False
    return True

def exhaustive_independent_set_search(G, vc_budget):
    """
    Look only for an IS of size exactly |V| - vc_budget.
    """
    n = G.number_of_nodes()
    target = n - vc_budget
    print(f"Searching for Independent set of size {target} since we have to find Vertex Cover of Budget {vc_budget}")
    for combo in itertools.combinations(G.nodes(), target):
        S = set(combo)
        print("\nTrying Independent Set:", S)
        if is_independent_set(G, S):
            print("Found Independent Set:", S)
            return S
    print("No Independent Set found for given budget.")
    return None

# ---- Vertex Cover (VC) ----
def is_vertex_cover(G, vertex_cover):
    uncovered_edges = []
    for u, v in G.edges():
        if u not in vertex_cover and v not in vertex_cover:
            uncovered_edges.append((u, v))
    if uncovered_edges:
        print("Uncovered edges:", uncovered_edges)
        return False
    return True

def exhaustive_vertex_cover_search(G, budget):
    print(f"Searching for any Vertex Cover of size ≤ {budget}…")
    for k in range(budget + 1):
        for combo in itertools.combinations(G.nodes(), k):
            C = set(combo)
            print("\nTrying Vertex Cover:", C)
            if is_vertex_cover(G, C):
                print("Found Vertex Cover :", C)
                return C
    #print("No Vertex Cover for given budget.")
    return None

# ---- Dominating Set (DS) ----
def is_dominating_set(G, D):
    for node in G.nodes():
        if node not in D and not any(G.has_edge(node, d) for d in D):
            print("Undominated node:", node)
            return False
    return True

def find_minimum_dominating_set(G, budget):
    
    # Brute force search for dominating set
    nodes = list(G.nodes())
    for k in range(budget + 1):
        for candidate_set in itertools.combinations(nodes, k):
            # Check if candidate set dominates the entire graph
            print("\nTrying set (dominating):", set(candidate_set))
            if is_dominating_set(G, set(candidate_set)):
                print("Found dominating set:", set(candidate_set))
                return len(set(candidate_set)), set(candidate_set)
            else:
               print("\nDominating Set Not Found.") 
    
    return None, None

def transform_graph_to_vertex(G, budget):
    # add one dummy per edge, bump budget by number of isolated vertices
    isolated = [n for n in G.nodes() if G.degree(n) == 0]
    new_budget = budget + len(isolated)
    H = G.copy()
    for u, v in G.edges():
        dummy = f"dummy_{u}_{v}"
        H.add_node(dummy)
        H.add_edge(u, dummy)
        H.add_edge(v, dummy)
    return H, new_budget, isolated

# ---- Main Flow ----
def main():
    orig_stdout = sys.stdout
    budget = int(input("Enter budget: "))
    original_budget = budget

    # redirect all prints into a log file
    with open("output.txt", "w") as logfile:
        sys.stdout = logfile

        # --- Build the graph from input.csv ---
        edges, isolated = [], set()
        with open("input.csv") as f:
            for line in f:
                nums = list(map(int, line.strip().split(",")))
                if len(nums) == 2:
                    edges.append(tuple(nums))
                else:
                    isolated.add(nums[0])

        G = nx.Graph()
        G.add_edges_from(edges)
        G.add_nodes_from(isolated)

        # account for isolates in budgets
        if isolated:
            budget += len(isolated)

        visualize_graph(G, "Original Graph", "original_graph.png")
        print("Original Graph:")
        print("Edges:", list(G.edges()))
        print("Isolated vertices:", list(isolated))
        print("Original Budget:", original_budget)
        if isolated:
            print("Adjusted Budget:",budget)

        # --- STEP 1: IS → VC → DS (forward) ---
        ind_set = exhaustive_independent_set_search(G, budget)
        if ind_set:
            # derive VC from IS which is complimenting to IS
            vc_from_is = set(G.nodes()) - ind_set
            print("\nDerived VC:", vc_from_is)

            # Adding Dummy nodes
            H, ds_budget, iso2 = transform_graph_to_vertex(G, len(vc_from_is))
            visualize_graph(H, "Transformed Graph", "transformed_graph.png")
            set1 = vc_from_is
            print("Performing Dominating Set with ",ds_budget)
            resulting_size, candidate_set = find_minimum_dominating_set(H, budget)
            
        
            # Visualize Dominating Set if possible
            if resulting_size is not None:
                # Remove isolated vertices from the result
                non_isolated_result = resulting_size - len(set(isolated))
                non_isolated_result_vertex = set(candidate_set) - set(isolated)
                #Transforming the graph
                visualize_graph(H, "Dominating Set", "dominating_set.png", set1)
                if non_isolated_result <= original_budget:
                    print("\nIt is possible to find a Indepedent Set with original budget.")
                    print("Vertex Cover of size", non_isolated_result, "is:", non_isolated_result_vertex)
                    #visualize_graph(G, "Independent Set", "independent_set.png", ind_set)
                    visualize_graph(G, "Vertex Cover", "vertex_cover_from_is.png", vc_from_is)
                else:
                    print("\nIt is not possible to find a Dominating Set with original budget.")

            # --- STEP 2: DS → VC → IS (backward) ---
            print("\nPerforming exhaustive search to confirm if a solution or no solution exists...")
            vc_from_ds = exhaustive_vertex_cover_search(G, original_budget)
            if vc_from_ds:
                ind_from_ds = exhaustive_independent_set_search(G, len(vc_from_ds))
                if ind_from_ds:
                    visualize_graph(G, "IS from DS", "independent_set.png", ind_from_ds)
                    print("A Indepedent Set was found during exhaustive search.")
                    print("Independent Set:", ind_from_ds)
            else:
                print("Confirmed: No Independent Set exists for the graph with budget ",original_budget)
                print("Exhaustive search checked all possible combinations.")


        # restore stdout
        sys.stdout = orig_stdout

if __name__ == "__main__":
    main()
