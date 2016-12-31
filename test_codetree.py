import sys

import codetree


# paths = ['test_data/org_sub_get.py']

output = []
def print_log(depth, *a):
  output.append(codetree.format_depth(depth, *a))

paths = ['test_data/' + filename for filename in ('method_resolution.py',)]
my_nodes, short_name_to_proper_names = codetree.create_callgraph_from_files(paths)
codetree.walk_nodes(my_nodes, short_name_to_proper_names)
codetree.print_graph(my_nodes, short_name_to_proper_names, print_log)

assert '''
FooClass.foo_method
  FooClass.bar_method
method_resolution.FooClass
method_resolution.BarClass
BarClass.bar_method
test_data/method_resolution
'''.strip() == '\n'.join(output)
