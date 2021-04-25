from __future__ import annotations
import ast
import astor
from typing import Optional, List, Any

import graphviz as gv


class Block(object):
    """
    Basic block in a control flow graph.
    Contains a list of statements executed in a program without any control
    jumps. A block of statements is exited through one of its exits. Exits are
    a list of Links that represent control flow jumps.
    """

    __slots__ = ["id", "statements", "func_calls", "predecessors", "exits"]

    def __init__(self, id_: int) -> None:
        # Id of the block.
        self.id = id_
        # Statements in the block.
        self.statements = []
        # Calls to functions inside the block (represents context switches to
        # some functions' CFGs).
        self.func_calls = []
        # Links to predecessors in a control flow graph.
        self.predecessors = []
        # Links to the next blocks in a control flow graph.
        self.exits = []

    def __str__(self) -> str:
        if self.statements:
            return "block:{}@{}".format(self.id, self.at())
        return "empty block:{}".format(self.id)

    def __repr__(self) -> str:
        txt = "{} with {} exits".format(str(self), len(self.exits))
        if self.statements:
            txt += ", body=["
            txt += ", ".join([ast.dump(node) for node in self.statements])
            txt += "]"
        return txt

    def at(self) -> Optional[int]:
        """
        Get the line number of the first statement of the block in the program.
        """
        if self.statements and self.statements[0].lineno >= 0:
            return self.statements[0].lineno
        return None

    def is_empty(self) -> bool:
        """
        Check if the block is empty.
        """
        return len(self.statements) == 0

    def get_source(self) -> str:
        """
        Get a string containing the Python source code corresponding to the
        statements in the block.
        """
        src = ""
        for statement in self.statements:
            if type(statement) in [ast.If, ast.For, ast.While]:
                src += (astor.to_source(statement)).split('\n')[0] + "\n"
            elif type(statement) == ast.FunctionDef or\
                 type(statement) == ast.AsyncFunctionDef:
                src += (astor.to_source(statement)).split('\n')[0] + "...\n"
            else:
                src += astor.to_source(statement)
        return src

    def get_calls(self) -> str:
        """
        Get a string containing the calls to other functions inside the block.
        """
        txt = ""
        for func_name in self.func_calls:
            txt += func_name + '\n'
        return txt


class Link(object):
    """
    Link between blocks in a control flow graph.
    Represents a control flow jump between two blocks. Contains an exitcase in
    the form of an expression, representing the case in which the associated
    control jump is made.
    """

    __slots__ = ["source", "target", "exitcase"]

    def __init__(self, source: Block, target: Block, exitcase=None):
        assert type(source) == Block, "Source of a link must be a block"
        assert type(target) == Block, "Target of a link must be a block"
        # Block from which the control flow jump was made.
        self.source = source
        # Target block of the control flow jump.
        self.target = target
        # 'Case' leading to a control flow jump through this link.
        self.exitcase = exitcase

    def __str__(self) -> str:
        return "link from {} to {}".format(str(self.source), str(self.target))

    def __repr__(self) -> str:
        if self.exitcase is not None:
            return "{}, with exitcase {}".format(str(self),
                                                 ast.dump(self.exitcase))
        return str(self)

    def get_exitcase(self) -> str:
        """
        Get a string containing the Python source code corresponding to the
        exitcase of the Link.
        """
        if self.exitcase:
            return astor.to_source(self.exitcase)
        return ""


class CFG(object):
    """
    Control flow graph (CFG).
    A control flow graph is composed of basic blocks and links between them
    representing control flow jumps. It has a unique entry block and several
    possible 'final' blocks (blocks with no exits representing the end of the
    CFG).
    """

    def __init__(self, name: str, asynchr: bool=False) -> None:
        # Name of the function or module being represented.
        self.name = name
        # Type of function represented by the CFG (sync or async). A Python
        # program is considered as a synchronous function (main).
        self.asynchr = asynchr
        # Entry block of the CFG.
        self.entryblock = None
        # Final blocks of the CFG.
        self.finalblocks = []
        # Sub-CFGs for functions defined inside the current CFG.
        self.functioncfgs = {}

    def __str__(self) -> str:
        return "CFG for {}".format(self.name)

    def _visit_blocks(self, graph, block: Block, visited=List[int], calls=True):
        # Don't visit blocks twice.
        if block.id in visited:
            return

        nodelabel = block.get_source()

        graph.node(str(block.id), label=nodelabel)
        visited.append(block.id)

        # Show the block's function calls in a node.
        if calls and block.func_calls:
            calls_node = str(block.id)+"_calls"
            calls_label = block.get_calls().strip()
            graph.node(calls_node, label=calls_label,
                       _attributes={'shape': 'box'})
            graph.edge(str(block.id), calls_node, label="calls",
                       _attributes={'style': 'dashed'})

        # Recursively visit all the blocks of the CFG.
        for exit in block.exits:
            self._visit_blocks(graph, exit.target, visited, calls=calls)
            edgelabel = exit.get_exitcase().strip()
            graph.edge(str(block.id), str(exit.target.id), label=edgelabel)

    def _build_visual(self, format: str, calls=True) -> Any:
        graph = gv.Digraph(name='cluster'+self.name, format=format,
                           graph_attr={'label': self.name})
        self._visit_blocks(graph, self.entryblock, visited=[], calls=calls)

        # Build the subgraphs for the function definitions in the CFG and add
        # them to the graph.
        for subcfg in self.functioncfgs:
            subgraph = self.functioncfgs[subcfg]._build_visual(format=format,
                                                               calls=calls)
            graph.subgraph(subgraph)

        return graph

    def build_visual(self, output_file: str, format: str = "jpg", calls: bool = True, show: bool = True) -> None:
        """
        Build a visualisation of the CFG with graphviz and output it in a DOT file.
        """
        graph = self._build_visual(format, calls)
        graph.render(output_file, view=show)

    def __iter__(self):
        """
        Generator that yields all the blocks in the current graph, then
        recursively yields from any sub graphs
        """
        visited = set()
        to_visit = [self.entryblock]

        while to_visit:
            block = to_visit.pop(0)
            visited.add(block)
            for exit_ in block.exits:
                if exit_.target in visited or exit_.target in to_visit:
                    continue
                to_visit.append(exit_.target)
            yield block

        for subcfg in self.functioncfgs.values():
            yield from subcfg