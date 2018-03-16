from fusesoc.capi1.section import Section, SECTION_MAP


class GeneratorSection(Section):
    '''
    Defines a fusesoc section for a Generator.
    The function specified is run during an extended elaboration to create
    additional source files.
    '''
    TAG = 'generator'

    def __init__(self, items=None):
        super(GeneratorSection, self).__init__()
        self._add_member(
            'file', str, 'File containing the generator function.')
        self._add_member(
            'module', str, 'Module containing the generator function.')
        self._add_member(
            'function', str, 'Name of the generator function')
        self._add_member(
            'type', str, 'Language of the generator function')
        if items:
            self.load_dict(items)


# Add the GeneratorSection to fusesoc's map of of sections.
SECTION_MAP[GeneratorSection.TAG] = GeneratorSection
