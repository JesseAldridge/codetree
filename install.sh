rm -rf ~/.codetree
mkdir ~/.codetree
ln -s "$(realpath python_std)" ~/.codetree/python_std
ln codetree.py /usr/local/bin/codetree
