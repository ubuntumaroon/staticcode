# https://rahul.gopinath.org/post/2019/12/08/python-controlflow/
# https://www.fuzzingbook.org/html/ControlFlow.html


import ast
from _ast import AST
import sys
import tokenize
import astunparse
import re

import graphviz
from graphviz import Digraph, Source
from typing import List, Any


def get_color(p, c):
    color = 'black'
    while not p.annotation():
        if p.label == 'if:True':
            return 'blue'
        elif p.label == 'if:False':
            return 'red'
        p = p.parents[0]
    return color


def get_peripheries(p):
    annot = p.annotation()
    if annot  in {'<start>', '<stop>'}:
        return '2'
    if annot.startswith('<define>') or annot.startswith('<exit>'):
        return '2'
    return '1'


def get_shape(p):
    annot = p.annotation()
    if annot in {'<start>', '<stop>'}:
        return 'oval'
    if annot.startswith('<define>') or annot.startswith('<exit>'):
        return 'oval'

    if annot.startswith('if:'):
        return 'diamond'
    else:
        return 'rectangle'


def to_graph(registry, arcs=[], comment='', get_shape=lambda n: 'rectangle', get_peripheries=lambda n: '1', get_color=lambda p,c: 'black'):
    graph = Digraph(comment=comment)
    for nid, cnode in registry.items():
        if not cnode.annotation():
            continue
        sn = cnode.annotation()
        graph.node(cnode.name(), sn, shape=get_shape(cnode), peripheries=get_peripheries(cnode))
        for pn in cnode.parents:
            gp = pn.get_gparent_id()
            color = get_color(pn, cnode)
            graph.edge(gp, str(cnode.rid), color=color)
    return graph


class CFGNode:
    counter = 0
    registry = {}
    stack = []

    def __init__(self, parents: List[Any] = [], ast=None, label=None, annot=None):
        self.parents = parents
        self.calls = []
        self.children = []
        self.ast_node = ast
        self.label = label
        self.annot = annot
        self.rid = CFGNode.counter
        CFGNode.registry[self.rid] = self
        CFGNode.counter += 1

    def i(self):
        return str(self.rid)

    def add_child(self, c):
        if c not in self.children:
            self.children.append(c)

    def add_parent(self, p):
        if p not in self.parents:
            self.parents.append(p)

    def add_parents(self, ps):
        for p in ps:
            self.add_parent(p)

    def add_calls(self, func):
        mid = None
        if hasattr(func, 'id'):  # ast.name
            mid = func.id
        else:
            mid = func.value.id  # ast.Attribute
        self.calls.append(mid)

    def __eq__(self, other):
        return self.rid == other.rid

    def __neq__(self, other):
        return self.rid != other.rid

    def lineno(self):
        return self.ast_node.lineno if hasattr(self.ast_node, 'lineno') else 0

    def name(self):
        return str(self.rid)

    def expr(self):
        return self.source()

    def __str__(self):
        return "id:%d line[%d] parents: %s : %s" % \
               (self.rid, self.lineno(), str([p.rid for p in self.parents]), self.source())

    def __repr__(self):
        return str(self)

    def source(self):
        # return astunparse.unparse(self.ast_node).strip()
        if isinstance(self.ast_node, AST):
            s = astunparse.unparse(self.ast_node)
            if s is None:
                s = "None"
            return s
        else:
            'None'

    def annotation(self):
        if self.annot is not None:
            return self.annot
        return self.source()

    def to_json(self):
        return {'id': self.rid, 'parents': [p.rid for p in self.parents],
                'children': [c.rid for c in self.children],
                'calls': self.calls, 'at': self.lineno(), 'ast': self.source()}

    def get_gparent_id(self):
        p = CFGNode.registry[self.rid]
        while not p.annotation():
            p = p.parents[0]
        return str(p.rid)


class PyCFGExtractor:
    def __init__(self):
        self.founder = CFGNode(parents=[], ast=ast.parse('start').body[0])  # sentinel
        self.founder.ast_node.lineno = 0
        self.functions = {}
        self.functions_node = {}

    def parse(self, src):
        return ast.parse(src)

    def walk(self, node, myparents):
        if node is None:
            return
        fname = "on_%s" % node.__class__.__name__.lower()
        if hasattr(self, fname):
            return getattr(self, fname)(node, myparents)
        raise SyntaxError('walk: Not Implemented in %s' % type(node))

    def on_pass(self, node, myparents):
        p = [CFGNode(parents=myparents, ast=node)]
        return p

    def on_module(self, node, myparents):
        p = myparents
        for n in node.body:
            p = self.walk(n, p)
        return p

    def on_str(self, node, myparents):
        p = [CFGNode(parents=myparents, ast=node, annot='')]
        return p

    def on_num(self, node, myparents):
        p = [CFGNode(parents=myparents, ast=node, annot='')]
        return p
    def on_constant(self, node, myparents):
        p = [CFGNode(parents=myparents, ast=node, annot='')]
        return p

    def on_expr(self, node, myparents):
        p = self.walk(node.value, myparents)
        p = [CFGNode(parents=p, ast=node)]
        return p

    def on_unaryop(self, node, myparents):
        p = [CFGNode(parents=myparents, ast=node, annot='')]
        return self.walk(node.operand, p)

    def on_binop(self, node, myparents):
        left = self.walk(node.left, myparents)
        right = self.walk(node.right, left)
        p = [CFGNode(parents=right, ast=node, annot='')]
        return p

    def on_compare(self, node, myparents):
        left = self.walk(node.left, myparents)
        right = self.walk(node.comparators[0], left)
        p = [CFGNode(parents=right, ast=node, annot='')]
        return p

    def on_augassign(self, node, myparents):
        """
         AugAssign(expr target, operator op, expr value)
        """
        p = [CFGNode(parents=myparents, ast=node)]
        p = self.walk(node.value, p)

        return p

    def on_annassign(self, node, myparents):
        """
        AnnAssign(expr target, expr annotation, expr? value, int simple)
        """
        p = [CFGNode(parents=myparents, ast=node)]
        p = self.walk(node.value, p)

        return p

    def on_assign(self, node, myparents):
        if len(node.targets) > 1: raise NotImplemented('Parallel assignments')
        p = [CFGNode(parents=myparents, ast=node)]
        p = self.walk(node.value, p)
        return p

    def on_name(self, node, myparents):
        p = [CFGNode(parents=myparents, ast=node, annot='')]
        return p

    def on_if(self, node, myparents):
        p = self.walk(node.test, myparents)
        test_node = [CFGNode(parents=p, ast=node, annot="if: %s" % astunparse.unparse(node.test).strip())]
        g1 = test_node
        g_true = [CFGNode(parents=g1, ast=None, label="if:True", annot='')]
        g1 = g_true
        for n in node.body:
            g1 = self.walk(n, g1)
        g2 = test_node
        g_false = [CFGNode(parents=g2, ast=None, label="if:False", annot='')]
        g2 = g_false
        for n in node.orelse:
            g2 = self.walk(n, g2)
        return g1 + g2

    def on_while(self, node, myparents):
        loop_id = CFGNode.counter
        lbl1_node = CFGNode(parents=myparents, ast=node, label='loop_entry', annot='%s:while' % loop_id)
        p = self.walk(node.test, [lbl1_node])

        lbl2_node = CFGNode(parents=p, ast=node.test, label='while:test',
                            annot='if: %s' % astunparse.unparse(node.test).strip())
        g_false = CFGNode(parents=[lbl2_node], ast=None, label="if:False", annot='')
        g_true = CFGNode(parents=[lbl2_node], ast=None, label="if:True", annot='')
        lbl1_node.exit_nodes = [g_false]

        p = [g_true]

        for n in node.body:
            p = self.walk(n, p)

        # the last node is the parent for the lb1 node.
        lbl1_node.add_parents(p)

        return lbl1_node.exit_nodes

    def on_break(self, node, myparents):
        parent = myparents[0]
        while parent.label != 'loop_entry':
            parent = parent.parents[0]

        assert hasattr(parent, 'exit_nodes')
        p = CFGNode(parents=myparents, ast=node)

        # make the break one of the parents of label node.
        parent.exit_nodes.append(p)

        # break doesnt have immediate children
        return []

    def on_continue(self, node, myparents):
        parent = myparents[0]
        while parent.label != 'loop_entry':
            parent = parent.parents[0]

        p = CFGNode(parents=myparents, ast=node)
        parent.add_parent(p)

        return []

    def on_call(self, node, myparents):
        p = myparents
        for a in node.args:
            p = self.walk(a, p)
        myparents[0].add_calls(node.func)
        p = [CFGNode(parents=p, ast=node, label='call', annot='')]
        return p

    def on_for(self, node, myparents):
        # node.target in node.iter: node.body
        loop_id = CFGNode.counter

        for_pre = CFGNode(parents=myparents, ast=None, label='for_pre', annot='')

        init_node = ast.parse('__iv_%d = iter(%s)' % (loop_id, astunparse.unparse(node.iter).strip())).body[0]
        p = self.walk(init_node, [for_pre])

        lbl1_node = CFGNode(parents=p, ast=node, label='loop_entry', annot='%s: for' % loop_id)
        _test_node = ast.parse('__iv_%d.__length__hint__() > 0' % loop_id).body[0].value
        p = self.walk(_test_node, [lbl1_node])

        lbl2_node = CFGNode(parents=p, ast=_test_node, label='for:test',
                            annot='for: %s' % astunparse.unparse(_test_node).strip())
        g_false = CFGNode(parents=[lbl2_node], ast=None, label="if:False", annot='')
        g_true = CFGNode(parents=[lbl2_node], ast=None, label="if:True", annot='')
        lbl1_node.exit_nodes = [g_false]

        p = [g_true]

        # now we evaluate the body, one at a time.
        for n in node.body:
            p = self.walk(n, p)

        # the test node is looped back at the end of processing.
        lbl1_node.add_parents(p)

        return lbl1_node.exit_nodes

    def on_functiondef(self, node, myparents=[]):
        # name, args, body, decorator_list, returns
        fname = node.name
        args = node.args
        returns = node.returns
        p = myparents
        enter_node = CFGNode(parents=p, ast=node, label='enter',
                             annot='<define>: %s' % node.name)
        enter_node.return_nodes = []  # sentinel

        p = [enter_node]
        for n in node.body:
            p = self.walk(n, p)

        enter_node.return_nodes.extend(p)

        self.functions[fname] = [enter_node, enter_node.return_nodes]
        self.functions_node[enter_node.lineno()] = fname

        return myparents

    def get_defining_function(self, node):
        if node.lineno() in self.functions_node:
            return self.functions_node[node.lineno()]
        if not node.parents:
            self.functions_node[node.lineno()] = ''
            return ''
        val = self.get_defining_function(node.parents[0])
        self.functions_node[node.lineno()] = val
        return val


    def on_return(self, node, myparents):
        parent = myparents[0]

        val_node = self.walk(node.value, myparents)
        # on return look back to the function definition.
        while not hasattr(parent, 'return_nodes'):
            parent = parent.parents[0]
        assert hasattr(parent, 'return_nodes')

        p = CFGNode(parents=val_node, ast=node)

        # make the break one of the parents of label node.
        parent.return_nodes.append(p)

        # return doesnt have immediate children
        return []

    def link_functions(self):
        for nid, node in CFGNode.registry.items():
            if node.calls:
                for calls in node.calls:
                    if calls in self.functions:
                        enter, exit = self.functions[calls]
                        enter.add_parent(node)
                        if node.children:
                            # # until we link the functions up, the node
                            # # should only have succeeding node in text as
                            # # children.
                            # assert(len(node.children) == 1)
                            # passn = node.children[0]
                            # # We require a single pass statement after every
                            # # call (which means no complex expressions)
                            # assert(type(passn.ast_node) == ast.Pass)

                        # # unlink the call statement
                            assert node.calllink > -1
                            node.calllink += 1
                            for i in node.children:
                                i.add_parent(exit)
                            # passn.set_parents([exit])
                            # ast.copy_location(exit.ast_node, passn.ast_node)

                            # #for c in passn.children: c.add_parent(exit)
                            # #passn.ast_node = exit.ast_node


    def update_functions(self):
        for nid, node in CFGNode.registry.items():
            _n = self.get_defining_function(node)

    def update_children(self):
        for nid, node in CFGNode.registry.items():
            for p in node.parents:
                p.add_child(node)

    def gen_cfg(self, src):
        """
        >>> i = PyCFG()
        >>> i.walk("100")
        5
        """
        node = self.parse(src)
        nodes = self.walk(node, [self.founder])
        self.last_node = CFGNode(parents=nodes, ast=ast.parse('stop').body[0])
        ast.copy_location(self.last_node.ast_node, self.founder.ast_node)
        self.update_children()
        self.update_functions()
        self.link_functions()

    def compute_dominator(cfg, start=0, key='parents'):
        dominator = {}
        dominator[start] = {start}
        all_nodes = set(cfg.keys())
        rem_nodes = all_nodes - {start}
        for n in rem_nodes:
            dominator[n] = all_nodes

        c = True
        while c:
            c = False
            for n in rem_nodes:
                pred_n = cfg[n][key]
                doms = [dominator[p] for p in pred_n]
                i = set.intersection(*doms) if doms else set()
                v = {n} | i
                if dominator[n] != v:
                    c = True
                dominator[n] = v
        return dominator


    def compute_flow(pythonfile):
        cfg, first, last = get_cfg(pythonfile)
        return cfg, pythonfile.compute_dominator(
            cfg, start=first), pythonfile.compute_dominator(
                cfg, start=last, key='children')


def gen_cfg(fnsrc, remove_start_stop=True):
    # reset_registry()
    cfg = PyCFGExtractor()
    cfg.gen_cfg(fnsrc)
    cache = dict(CFGNode.registry)
    if remove_start_stop:
        return {
            k: cache[k]
            for k in cache if cache[k].source() not in {'start', 'stop'}
        }
    else:
        return cache

def get_cfg(src):
    # reset_registry()
    cfg = PyCFGExtractor()
    cfg.gen_cfg(src)
    cache = dict(CFGNode.registry)
    g = {}
    for k, v in cache.items():
        j = v.to_json()
        at = j['at']
        parents_at = [cache[p].to_json()['at'] for p in j['parents']]
        children_at = [cache[c].to_json()['at'] for c in j['children']]
        if at not in g:
            g[at] = {'parents': set(), 'children': set()}
        # remove dummy nodes
        ps = set([p for p in parents_at if p != at])
        cs = set([c for c in children_at if c != at])
        g[at]['parents'] |= ps
        g[at]['children'] |= cs
        if v.calls:
            g[at]['calls'] = v.calls
        g[at]['function'] = cfg.functions_node[v.lineno()]
    return (g, cfg.founder.ast_node.lineno, cfg.last_node.ast_node.lineno)


def to_graph(cache, arcs=[]):
    graph = Digraph(comment='Control Flow Graph')
    colors = {0: 'blue', 1: 'red'}
    kind = {0: 'T', 1: 'F'}
    cov_lines = set(i for i, j in arcs)
    for nid, cnode in cache.items():
        lineno = cnode.lineno()
        shape, peripheries = 'oval', '1'
        if isinstance(cnode.ast_node, ast.AnnAssign):
            if cnode.ast_node.target.id in {'_if', '_for', '_while'}:
                shape = 'diamond'
            elif cnode.ast_node.target.id in {'enter', 'exit'}:
                shape, peripheries = 'oval', '2'
        else:
            shape = 'rectangle'
        graph.node(cnode.i(), "%d: %s" % (lineno, unhack(cnode.source())), shape=shape, peripheries=peripheries)
        for pn in cnode.parents:
            plineno = pn.lineno()
            if hasattr(pn, 'calllink') and pn.calllink > 0 and not hasattr(
                    cnode, 'calleelink'):
                graph.edge(pn.i(), cnode.i(), style='dotted', weight=100)
                continue

            if arcs:
                if (plineno, lineno) in arcs:
                    graph.edge(pn.i(), cnode.i(), color='green')
                elif plineno == lineno and lineno in cov_lines:
                    graph.edge(pn.i(), cnode.i(), color='green')
                # child is exit and parent is covered
                elif hasattr(cnode, 'fn_exit_node') and plineno in cov_lines:
                    graph.edge(pn.i(), cnode.i(), color='green')
                # parent is exit and one of its parents is covered.
                elif hasattr(pn, 'fn_exit_node') and len(
                        set(n.lineno() for n in pn.parents) | cov_lines) > 0:
                    graph.edge(pn.i(), cnode.i(), color='green')
                # child is a callee (has calleelink) and one of the parents is covered.
                elif plineno in cov_lines and hasattr(cnode, 'calleelink'):
                    graph.edge(pn.i(), cnode.i(), color='green')
                else:
                    graph.edge(pn.i(), cnode.i(), color='red')
            else:
                order = {c.i():i for i,c in enumerate(pn.children)}
                if len(order) < 2:
                    graph.edge(pn.i(), cnode.i())
                else:
                    o = order[cnode.i()]
                    graph.edge(pn.i(), cnode.i(), color=colors[o], label=kind[o])
    return graph

def unhack(v):
    if not isinstance(v, str):
        v = "None"
    for i in ['if', 'while', 'for', 'elif']:
        v = re.sub(r'^_%s:' % i, '%s:' % i, v)
    return v


def read_file(filename):
    with tokenize.open(filename) as fd:
        return fd.read()


def parse_file(filename):
    return ast.parse(read_file(filename))


def check_triangle(a,b,c):
    if a == b:
        if a == c:
            if b == c:
                return "Equilateral"
            else:
                return "Isosceles"
        else:
            return "Isosceles"
    else:
        if b != c:
            if a == c:
                return "Isosceles"
            else:
                return "Scalene"
        else:
              return "Isosceles"

import inspect

if __name__ == '__main__':
    graph = to_graph(gen_cfg(inspect.getsource(check_triangle)))
    print(graph.source)
    graph.render(view=True)
    Source(graph)