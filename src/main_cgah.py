import os
import sys
import argparse

from hypergraph import Hypergraph, NullHypergraph
from model import CGAHDynamic
from analysis_pattern import analyze_pattern
from analysis_decomposition import analyze_decomposition
from statistical_test import statistical_test

def main(graph):
    sv_k = {'contact': 326, 'email': 1000, 'substances': 5000, 'tags': 3000, 'threads': 10000, 'coauth': 1000, 'cgah': 500}
    print('# Structural patterns and dynamical patterns')
    print('(See ../results/{}_*.txt and ../plots/{}_*.txt)'.format(graph.datatype, graph.datatype))
    analyze_pattern(graph, sv_k[graph.datatype])
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Official Implementation for 'Growth Patterns and Models of Real-world Hypergraphs'")
    parser.add_argument('dataset', type=str, help='Select dataset for analysis')
    
    parser.add_argument(
        "-b",
        "--b",
        action="store",
        default=6,
        type=int,
        help="Select the number of children of each node in hierarchical community (if the target dataset is 'model')",
    )
    parser.add_argument(
        "-c1",
        "--creation",
        action="store",
        default=8,
        type=float,
        help="Select the parameter for hyperedge creation c_1 (if the target dataset is 'model')",
    )
    parser.add_argument(
        "-c2",
        "--expansion",
        action="store",
        default=10,
        type=float,
        help="Select the parameter for hyperedge expansion c_2 (if the target dataset is 'model')",
    )
    parser.add_argument(
        "-n",
        "--nodes",
        action="store",
        default=10000,
        type=int,
        help="Select the number of nodes n (if the target dataset is 'model')",
    )
    args = parser.parse_args()
    datasets_info = {'contact': 'contact-high-school',
                     'email': 'email-Eu-full',
                     'substances': 'NDC-substances-full',
                     'tags': 'tags-ask-ubuntu',
                     'threads': 'threads-math-sx',
                     'coauth': 'coauth-DBLP-full'}
    
    if not os.path.exists('../results'):
        os.mkdir('../results')
    if not os.path.exists('../plots'):
        os.mkdir('../plots')
    if args.dataset in datasets_info:
        graph = Hypergraph(datasets_info[args.dataset], args.dataset)
    elif args.dataset == 'model':
        print("Generating hypergraph using HyperFF model...")
        graph = CGAHDynamic(args.b, args.creation, args.expansion, args.nodes)
    else:
        print("Invalid arguments.")
        parser.print_help()
        sys.exit(0)
    main(graph)
