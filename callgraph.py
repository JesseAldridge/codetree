import ast, collections, re


with open('python_std/python_funcs.txt') as f:
  text = f.read()
std_funcs = set(text.splitlines())

with open('python_std/python_methods.txt') as f:
  text = f.read()
std_methods = set(text.splitlines())


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

  def walk_nodes(self, visit_node=lambda node, depth: None,
                 visit_ambiguous_children=lambda node, depth: None, sort_key=None):
    self.name_to_num_children = {}

    if sort_key:
      key_vals = sorted(my_nodes.iteritems(), key=sort_key)
    else:
      key_vals = my_nodes.iteritems()

    for prefix, my_node in key_vals:
      self.walk_inner(prefix, 0, visit_node, visit_ambiguous_children)

  def walk_inner(self, root_proper_name, depth, visit_node, visit_ambiguous_children):
    if root_proper_name not in self.name_to_num_children:
      visit_node(root_proper_name, depth)
      self.name_to_num_children[root_proper_name] = num_children = 0
      for callee_short_name in self.my_nodes[root_proper_name].callees:
        proper_names = short_name_to_proper_names.get(callee_short_name, [])
        if not proper_names:
          continue
        if len(proper_names) == 1:
          num_children += self.walk_inner(
            proper_names[0], depth + 1,
            visit_node, visit_ambiguous_children) + 1
        else:
          # (here we aren't sure which node the short_name refers to)
          visit_ambiguous_children(proper_names, depth)
          num_children += 1
      self.name_to_num_children[root_proper_name] = num_children
      self.my_nodes[root_proper_name].num_children = num_children
    return self.name_to_num_children[root_proper_name]

  def print_graph(self):
    def print_(depth, *a):
      print '{}{}'.format('  ' * depth, ' '.join(str(arg) for arg in a))

    def visit_node(root_proper_name, depth):
      short_name = root_proper_name
      if '.' in root_proper_name:
        short_name = root_proper_name.rsplit('.', 1)[1]
      print_(depth, short_name)

    def visit_ambiguous_children(proper_names, depth):
      print_(depth, ' ', proper_names)

    self.walk_nodes(visit_node, visit_ambiguous_children,
                    sort_key=lambda key_val: -key_val[1].num_children)

if __name__ == '__main__':
  my_nodes, short_name_to_proper_names = parse_file('callgraph.py')
  walker = Walker(my_nodes, short_name_to_proper_names)
  walker.walk_nodes()
  walker.print_graph()
