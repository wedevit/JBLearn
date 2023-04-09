import re

CODE_MARKER = ('{{', '}}')

#########################
class InvalidFormatException(Exception):
    """ Exception raised when the format of the input file is invalid
        captures the line number where the error occurred
    """
    #########################
    def __init__(self, msg, lineno=None):
        super().__init__(msg)
        self.lineno = lineno
        

#########################     
def extract_params(obj, params):
    valid_params = obj.REQUIRED_PARAMS + obj.OPTIONAL_PARAMS
    req_params = set(obj.REQUIRED_PARAMS)
    for k, v in params.items():
        if k in valid_params:
            setattr(obj, k, v)
            if k in req_params:
                req_params.remove(k)
        else:
            raise Exception(f"Unknown parameter '{k}'")
    if req_params:
        raise Exception("Missing required parameters: %s" % 
            ','.join(f"'{p}'" for p in req_params)
        )

#########################
class HiddenLine(str):
    pass


#########################
class ExcludedLine(str):
    pass


#########################
class Blank:
    """ A fillin-the-blank answer """
    
    #########################
    def __init__(self, answer, indent=0):
        """ indent is used for subsequent lines of a multi-line answer """
        self.answer = [answer]
        self.indent = indent
        self.length = len(answer)

    #########################
    def add_row(self, answer):
        self.answer.append(answer)

    #########################
    def row_count(self):
        return len(self.answer)

    #########################
    def raw_answer(self):
        return '\n'.join(self.answer)

    #########################
    def formatted_answer(self, answer=None):
        if answer != None:
            answer = answer.replace('\r\n','\n').split('\n')
        else:
            answer = self.answer

        return '\n'.join([
            answer[0]] + [(' '*self.indent)+x for x in answer[1:]])

    #########################
    def __str__(self):
        return self.raw_answer()

    #########################
    def __repr__(self):
        return 'Ans(%s)' % self.raw_answer().replace('\n',r'\n')
    
            
#########################
class CodeSegment:
    """ A segment of code to be displayed in the exercise """
    
    REQUIRED_PARAMS = []
    OPTIONAL_PARAMS = [
        'hidden','lineno','highlight','excluded','blank','language',
    ]

    #########################
    def __init__(self, **params):
        self.hidden = False
        self.lineno = False
        self.highlight = True
        self.markers = CODE_MARKER
        self.excluded = False
        self.blank = False
        self.language = None
        extract_params(self, params)

    #########################
    def make_sequence(self, code, start_line):
        """ makes a sequence of shown and hidden (fillin) code portions """
        
        begin, end = self.markers
        marker_re = re.compile(re.escape(begin) + "(.*?)" + re.escape(end))
        seq = []
        prev_blank = None
        for lineno, line in enumerate(code):
            # make sure all resulting pieces are wrapped by the same class as
            # the original line
            lineclass = line.__class__
            line = line.rstrip()
            pieces = [lineclass(x) for x in marker_re.sub('\n', line).split('\n')]
            blanks = marker_re.findall(line)
            indent = 0

            # print(lineno, line, lineclass, pieces, blanks)
            
            # in case the entire code segment is made blank
            # just remove all the markers and add the whole line to the blank
            if self.blank:
                tmpline = [pieces[0]]
                for i, p in enumerate(pieces[1:]):
                    tmpline.append(blanks[i])
                    tmpline.append(p)
                wholeline = ''.join(tmpline)
                if len(seq) == 0:
                    seq.append(Blank(wholeline))
                else:
                    seq[0].add_row(wholeline)

            # See whether this line can be merged with surrounding lines so that
            # multi-row field will be used instead.
            #
            # The conditions are:
            #  - there is exactly one blank
            #  - preceded with all spaces
            #  - and nothing following
            elif len(blanks) == 1 and pieces[0] == ' '*len(pieces[0]) \
                    and pieces[1] == '':

                indent = len(pieces[0])

                # if indent and blank sizes are all matched, merge with previous
                if prev_blank and \
                        prev_blank.indent == indent and \
                        prev_blank.length == len(blanks[0]):
                    prev_blank.add_row(blanks[0])
                else:
                    blank = Blank(blanks[0], indent)
                    seq.append(pieces[0])
                    seq.append(blank)
                    seq.append('\n')
                    prev_blank = blank

            else:
                seq.append(pieces[0])
                if isinstance(pieces[0], HiddenLine) and len(pieces) > 1:
                    raise InvalidFormatException("Hidden line cannot contain a blank",
                            (lineno + start_line + 2) )
                if isinstance(pieces[0], ExcludedLine) and len(pieces) > 1:
                    raise InvalidFormatException("Excluded line cannot contain a blank",
                            (lineno + start_line + 2) )
                for i, p in enumerate(pieces[1:]):
                    seq.append(Blank(blanks[i]))
                    seq.append(p)
                if not isinstance(pieces[0], HiddenLine) and \
                   not isinstance(pieces[0], ExcludedLine):
                    seq.append('\n')
                prev_blank = None

        self.sequence = seq

    #########################
    def __iter__(self):
        for x in self.sequence: yield x
        
#########################
class CodeTestCase:
    """ An input/output test case """

    REQUIRED_PARAMS = []
    OPTIONAL_PARAMS = ['hint','visible','ignorecase','ignorespace','timeout','memlimit','tolerance']

    #########################
    def __init__(self, **params):
        self.hint = ""
        self.visible = False
        extract_params(self, params)

    #########################
    def set_input(self, input):
        self.input = '\n'.join(input)
     
     
#########################
class Code:
    """ Holds an entire code portion of a certain task """

    #########################
    def __init__(self, codesegs=[], flags={}):
        self.sequence = []
        self.blank_index = {}
        self.flags = flags
        blank_count = 0
        for t in codesegs:
            if t.excluded:
                continue
            for s in t.sequence:
                # if this piece of code is a blank, create a map from the
                # sequence index to the blank index for later use
                if isinstance(s, Blank):
                    self.blank_index[len(self.sequence)] = blank_count
                    blank_count += 1
                self.sequence.append(s)
            # TODO: elab's markdown processor sometimes adds a new line at the
            # end of a code segment.  This needs more tests for consistency.
            if self.sequence and self.sequence[-1] != '\n':
                self.sequence.append('\n')

    def dump_solution(self):
        """ returns solution. """

        lines = []
        for s in self.sequence:
            if isinstance(s, Blank):
                lines.append(s.formatted_answer())
            elif isinstance(s, HiddenLine):
                lines.append(s)
                lines.append('\n')
            elif isinstance(s, ExcludedLine):
                pass
            else:
                lines.append(s)

        return ''.join(lines)

    def dump(self, updates={}):
        """
        If a dict is provided as updates argument, blanks inside the
        original code will be replaced by values from the dict.  If
        the blank's key does not exist, '' will be used.
        """
        lines = []
        for i, s in enumerate(self.sequence):
            if isinstance(s, Blank):
                answer = None
                try:
                    answer = updates[self.blank_index[i]]
                except KeyError:
                    answer = ''
                lines.append(s.formatted_answer(answer))
            elif isinstance(s, HiddenLine):
                lines.append(s)
                lines.append('\n')
            elif isinstance(s, ExcludedLine):
                pass
            else:
                lines.append(s)

        return ''.join(lines)
    
            
#########################
class TaskBuilder:
    """ Builds a task """
    
    #########################
    def __init__(self):
        self.codesegs = []
        self.testcases = []
        self.embeddedMedia = []
        self.language = 'python'
        self.markers = ('{{', '}}')
        self.score_markers = ('[', ']')
        self.textBlanks = {}
        self.blank_count = 0
        self.buildflags = []
        self.runflags = []

    #########################
    def config(self, **params):
        for k, v in params.items():
            if k in ['language', 'markers']:
                setattr(self, k, v)
            else:
                raise InvalidFormatException('Unknown parameter: %s' % k)

    #########################
    def add_codesegment(self, codeseg):
        # resolve for each blank's id
        for p in codeseg:
            if isinstance(p, Blank):
                self.blank_count += 1
                p.id = self.blank_count

        self.codesegs.append(codeseg)

    #########################
    def add_testcase(self, testcase):
        self.testcases.append(testcase)

    #########################
    def addTextBlank(self, answer, score):
        self.blank_count += 1
        self.textBlanks[self.blank_count] = (answer,score)
        return self.blank_count

    #########################
    def addBuildFlags(self, flags):
        self.buildflags.append(flags)

    #########################
    def addRunFlags(self, flags):
        self.runflags.append(flags)

    #########################
    def get_code(self):
        return Code(self.codesegs, {
            'build' : ' '.join(self.buildflags),
            'run'   : ' '.join(self.runflags),
            })

    #########################
    def get_testcases(self):
        return self.testcases

    #########################
    def getTextBlanks(self):
        return self.textBlanks
    
