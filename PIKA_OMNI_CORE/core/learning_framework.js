const fs = require('fs');
const { EOL } = require('os');
const { Graph } = require('graphlib');

class KnowledgeGraph {
  constructor() {
    this.graph = new Graph();
  }

  addNode(node) {
    this.graph.setNode(node);
  }

  addEdge(from, to, label) {
    this.graph.setEdge(from, to, label);
  }

  getNeighbors(node) {
    return this.graph.successors(node);
  }

  getEdges(node) {
    return this.graph.outEdges(node);
  }

  expandGraph(node, depth) {
    if (depth === 0) return;
    const neighbors = this.getNeighbors(node);
    for (const neighbor of neighbors) {
      console.log(`Expanding node ${node} to ${neighbor}`);
      this.expandGraph(neighbor, depth - 1);
    }
  }

  adaptiveReasoning(node, goal) {
    const queue = [{ node, path: [node] }];
    while (queue.length > 0) {
      const { node: currentNode, path } = queue.shift();
      if (currentNode === goal) return path;
      for (const neighbor of this.getNeighbors(currentNode)) {
        queue.push({ node: neighbor, path: [...path, neighbor] });
      }
    }
    return null;
  }
}

class AdaptiveReasoner {
  constructor(knowledgeGraph) {
    this.knowledgeGraph = knowledgeGraph;
  }

  reason(node, goal) {
    return this.knowledgeGraph.adaptiveReasoning(node, goal);
  }
}

const knowledgeGraph = new KnowledgeGraph();
knowledgeGraph.addNode('A');
knowledgeGraph.addNode('B');
knowledgeGraph.addNode('C');
knowledgeGraph.addEdge('A', 'B', 'friend');
knowledgeGraph.addEdge('B', 'C', 'friend');
knowledgeGraph.addEdge('A', 'C', 'friend');

const adaptiveReasoner = new AdaptiveReasoner(knowledgeGraph);
console.log(adaptiveReasoner.reason('A', 'C'));

knowledgeGraph.expandGraph('A', 2);