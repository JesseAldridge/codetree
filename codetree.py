#!/usr/bin/python
import ast, collections, re, sys, os


def read_lines(filename):
  with open(os.path.expanduser('~/.codetree/python_std/' + filename)) as f:
    text = f.read()
  return set(text.splitlines())

std_funcs, std_methods = read_lines('python_funcs.txt'), read_lines('python_methods.txt')


class MyNode:
  def __init__(self, name):
    self.name = name
    self.callees = []
    self.num_children = 0


def parse_file(filename):

  class TopLevelVisitor(ast.NodeVisitor):
    def __init__(self, prefix):
      self.prefix = prefix
      my_nodes.setdefault(prefix, MyNode(prefix))

    def recurse(self, prefix, node):
      for field, value in ast.iter_fields(node):
        if isinstance(value, list):
          for item in value:
            if isinstance(item, ast.AST):
              TopLevelVisitor(prefix).visit(item)
        elif isinstance(value, ast.AST):
          TopLevelVisitor(prefix).visit(value)

    def append_prefix(self, s):
      if self.prefix:
        return self.prefix + '.' + s
      return s

    def visit_callable(self, callable_node):
      prefix = self.append_prefix(callable_node.name)
      my_nodes.setdefault(prefix, MyNode(prefix))
      short_name_to_proper_names.setdefault(callable_node.name, [])
      short_name_to_proper_names[callable_node.name].append(prefix)
      self.recurse(prefix, callable_node)

    def visit_ClassDef(self, class_node):
      self.visit_callable(class_node)

    def visit_FunctionDef(self, func_node):
      self.visit_callable(func_node)

    def visit_Call(self, call_node):
      if isinstance(call_node.func, ast.Name):
        short_name = call_node.func.id
        ignore_set = std_funcs
      else: # ast.Attribute
        if not hasattr(call_node.func, 'attr'):
          self.generic_visit(call_node)
          return
        short_name = call_node.func.attr
        ignore_set = std_methods

      if short_name not in ignore_set:
        my_nodes[self.prefix].callees.append(short_name)

      self.generic_visit(call_node)

  with open(filename) as f:
    text = f.read()
  text = re.sub('^ *#.+', '', text)

  root_node = ast.parse(text)

  module_prefix = filename.rsplit('.', 1)[0]

  my_nodes = {}
  short_name_to_proper_names = {}

  TopLevelVisitor(module_prefix).visit(root_node)
  return my_nodes, short_name_to_proper_names

class Walker:
  def __init__(self, my_nodes, short_name_to_proper_names):
    self.my_nodes = my_nodes
    self.short_name_to_proper_names = short_name_to_proper_names

  def walk_nodes(self,
                 visit_node=lambda node, depth: None,
                 visit_ambiguous_children=lambda node, depth: None,
                 visit_short_leaf=lambda node, depth: None,
                 sort_key=None):
    name_to_num_children = {}

    def walk_inner(root_proper_name, depth):
      if root_proper_name not in name_to_num_children:
        visit_node(root_proper_name, depth)
        name_to_num_children[root_proper_name] = num_children = 0
        for callee_short_name in self.my_nodes[root_proper_name].callees:
          proper_names = short_name_to_proper_names.get(callee_short_name, [])
          if not proper_names:
            visit_short_leaf(callee_short_name, depth + 1)
            continue
          if len(proper_names) == 1:
            num_children += walk_inner(proper_names[0], depth + 1) + 1
          else:
            # (here we aren't sure which node the short_name refers to)
            visit_ambiguous_children(proper_names, depth)
            num_children += 1
        name_to_num_children[root_proper_name] = num_children
        self.my_nodes[root_proper_name].num_children = num_children
      return name_to_num_children[root_proper_name]

    if sort_key:
      name_node_pairs = sorted(my_nodes.iteritems(), key=sort_key)
    else:
      name_node_pairs = my_nodes.iteritems()

    for prefix, my_node in name_node_pairs:
      walk_inner(prefix, 0)


  def print_graph(self):
    def print_(depth, *a):
      print '{}{}'.format('  ' * depth, ' '.join(str(arg) for arg in a))

    def visit_node(root_proper_name, depth):
      print_(depth, proper_to_short(root_proper_name))

    def visit_ambiguous_children(proper_names, depth):
      print_(depth, ' ', [proper_to_short(proper_name) for proper_name in proper_names])

    self.walk_nodes(visit_node, visit_ambiguous_children, visit_node,
                    sort_key=lambda key_val: -key_val[1].num_children)

def proper_to_short(proper_name):
  short_name = proper_name
  if '.' in proper_name:
    short_name = '.'.join(proper_name.rsplit('/', 1)[-1].rsplit('.', 2)[-2:])
  return short_name

if __name__ == '__main__':
  path = sys.argv[1]
  my_nodes, short_name_to_proper_names = parse_file(path)
  walker = Walker(my_nodes, short_name_to_proper_names)
  walker.walk_nodes()
  print 'code graph'
  print '----------'
  walker.print_graph()
