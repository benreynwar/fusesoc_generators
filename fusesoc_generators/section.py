from fusesoc.section import Section


class GeneratorSection(Section):
    TAG = 'generator'
    def __init__(self, items=None):
        super(GeneratorSection, self).__init__()
        self._add_member('file', str, 'File containing the generator function.')
        self._add_member('module', str, 'Module containing the generator function.')
        self._add_member('function', str, 'Name of the generator function')
        self._add_member('type', str, 'Language of the generator function')
        if items:
            self.load_dict(items)
