import markdown
import re
import xml.etree.ElementTree as etree
from markdown.util import AtomicString

from . import coding
from .syntax import append_text_or_elem

TAG_PREFIX = '@@'
BLANKLINE_PLACEHOLDER = TAG_PREFIX + 'BlankLine'
CODESEGMENT_PLACEHOLDER = TAG_PREFIX + 'CodeSegment'
TAG_RE = re.compile(r'^\s*%s(\w*)(.*)$' % TAG_PREFIX) # matches @@tag params
BLANK_ID_PREFIX = 'b'


#########################
def blank_len(l):
    """ Adds a safety factor to the length of a blank """
    return max(l + 3, int(l * 1.2))


#########################
def text_dimension(text):
    """ Returns the width and height of the given text """
    lines = text.split('\n')
    width = max(map(lambda x:len(x), lines))
    height = len(lines)
    return width, height


#########################
def create_blank_element(width, height, id):
    """ Creates an appropriate HTML text field for the specified width and
        height.  It creates a text input box for the height of 1, and a textarea
        otherwise.
    """
    if height == 1:
        text = etree.Element('input')
        text.set('type', 'text')
        text.set('size', str(blank_len(width)))
        text.set('value', '{{%s}}' % id)
        texttype = 'input'
    else:
        text = etree.Element('textarea')
        text.set('cols', str(blank_len(width)))
        text.set('rows', str(height))
        # prevent this text from being reprocessed by other inline patterns
        text.text = AtomicString('{{%s}}' % id)
        texttype = 'textarea'
        
    return text,texttype


#########################
class BlankLinePreprocessor(markdown.preprocessors.Preprocessor):
    """ Replace any blank line with a 'blank-line' placeholder to prevent
        Markdown from getting rid of two consecutive blank lines.
        These placeholders will be replaced by actual blank lines later.
    """

    #########################
    def run(self, lines):
        new_lines = []
        for line in lines:
            if re.match(r'^\s*$', line):
                new_lines.append(BLANKLINE_PLACEHOLDER + line)
            else:
                new_lines.append(line)
        # print('\n'.join(new_lines))
        return new_lines


class TagPreprocessor(markdown.preprocessors.Preprocessor):
    """ Process all custom tags in the text. """

    #########################
    def __init__(self, md, task):
        self.task = task
        super().__init__(md)
        
    #########################
    def run(self, lines):
        CONFIG_TAG = 'Config'
        BEGINCODE_TAG = 'BeginCode'
        ENDCODE_TAG = 'EndCode'
        BEGINTEST_TAG = 'BeginTest'
        ENDTEST_TAG = 'EndTest'
        BLANKLINE_TAG = 'BlankLine'
        HIDE_TAG = 'Hide'
        EXCLUDE_TAG = 'Exclude'
        BLANK_TAG = 'Blank'
        FIXED_TAG = 'Fixed'
        EMBED_TAG = 'Embed'
        INPUT_TAG = 'Input'
        EXEC_TAG = 'Exec'
        ARGS_TAG = 'Args'
        REQUIRED_TAG = 'Required'
        FORBIDDEN_TAG = 'Forbidden'
        FEEDBACK_TAG = 'Feedback'
        HINT_TAG = 'Hint'
    
        TEXT = 0; CODE = 1; TEST = 2 # available states
        state = TEXT
        task = self.task
        start_line = 0

        parts = {} # parts[TEXT] = [], parts[CODE] = [], parts[TEST] = []
        parts[TEXT] = []
        try:
            for lineno, line in enumerate(lines):
                tag, params = self.parse_line(line)
                if tag is not None:
                    if tag == CONFIG_TAG:
                        exec(f'task.config({params})')
                    elif tag == BEGINCODE_TAG: # start of code segment
                        if state is not TEXT:
                            raise coding.InvalidFormatException(f"Unexpected '{tag}' tag")
                        state = CODE
                        start_line = lineno
                        parts[CODE] = []
                        # create CodeSegment with given params
                        codeseg = eval("coding.CodeSegment({})".format(params)) 
                    elif tag == ENDCODE_TAG: # end of code segment
                        if state is not CODE:
                            raise coding.InvalidFormatException(f"Unexpected '{tag}' tag")
                        state = TEXT
                        parts[TEXT].append(f'{CODESEGMENT_PLACEHOLDER} {len(task.codesegs)}')
                        # add code segment to task
                        codeseg.make_sequence(parts[CODE], start_line)
                        task.add_codesegment(codeseg)
                        # print("CODE SEGMENTS:", [[y for y in x] for x in task.codesegs])
                    elif tag == BEGINTEST_TAG:
                        if state is not TEXT:
                            raise coding.InvalidFormatException(f"Unexpected '{tag}' tag")
                        state = TEST
                        parts[TEST] = []
                        testcase = eval("coding.CodeTestCase({})".format(params))
                    elif tag == ENDTEST_TAG:
                        if state is not TEST:
                            raise coding.InvalidFormatException(f"Unexpected '{tag}' tag")
                        state = TEXT
                        testcase.set_input(parts[TEST])
                        task.add_testcase(testcase)
                        # print("TEST CASES:", [x.input for x in task.testcases])
                    elif tag == BLANKLINE_TAG:
                        parts[state].append(params)
                    # elif tag == 'buildflags':
                        # task.addBuildFlags(params)
                    # elif tag == 'runflags':
                        # task.addRunFlags(params)
                    elif tag == HIDE_TAG:
                        if state != CODE:
                            raise coding.InvalidFormatException(f"Command '{tag}' must be inside a code segment")
                        else:
                            # parts[CODE].append(HiddenLine(params[1:]))
                            pass
                    elif tag == EXCLUDE_TAG:
                        if state != CODE:
                            raise coding.InvalidFormatException(f"Command '{tag}' must be inside a code segment")
                        else:
                            # parts[CODE].append(ExcludedLine(params[1:]))
                            pass
                    elif tag == BLANK_TAG:
                        if state != CODE:
                            raise coding.InvalidFormatException(f"Command '{tag}' must be inside a code segment")
                        else:
                            # parts[CODE].append(ExcludedLine(params[1:]))
                            pass
                    elif tag == FIXED_TAG:
                        if state != CODE:
                            raise coding.InvalidFormatException(f"Command '{tag}' must be inside a code segment")
                        else:
                            # parts[CODE].append(ExcludedLine(params[1:]))
                            pass
                    elif tag == INPUT_TAG:
                        if state != TEST:
                            raise coding.InvalidFormatException(f"Command '{tag}' must be inside a testcase")
                        else:
                            # parts[CODE].append(ExcludedLine(params[1:]))
                            pass
                    elif tag == EXEC_TAG:
                        if state != TEST:
                            raise coding.InvalidFormatException(f"Command '{tag}' must be inside a testcase")
                        else:
                            # parts[CODE].append(ExcludedLine(params[1:]))
                            pass
                    elif tag == ARGS_TAG:
                        if state != TEST:
                            raise coding.InvalidFormatException(f"Command '{tag}' must be inside a testcase")
                        else:
                            # parts[CODE].append(ExcludedLine(params[1:]))
                            pass
                    elif tag == REQUIRED_TAG:
                        if state != TEST:
                            raise coding.InvalidFormatException(f"Command '{tag}' must be inside a testcase")
                        else:
                            # parts[CODE].append(ExcludedLine(params[1:]))
                            pass
                    elif tag == FORBIDDEN_TAG:
                        if state != TEST:
                            raise coding.InvalidFormatException(f"Command '{tag}' must be inside a testcase")
                        else:
                            # parts[CODE].append(ExcludedLine(params[1:]))
                            pass
                    elif tag == FEEDBACK_TAG:
                        if state != TEST:
                            raise coding.InvalidFormatException(f"Command '{tag}' must be inside a testcase")
                        else:
                            # parts[CODE].append(ExcludedLine(params[1:]))
                            pass
                    elif tag == HINT_TAG:
                        if state != TEST:
                            raise coding.InvalidFormatException(f"Command '{tag}' must be inside a testcase")
                        else:
                            # parts[CODE].append(ExcludedLine(params[1:]))
                            pass
                    elif tag == EMBED_TAG:
                        if state in [CODE, TEST]:
                            raise coding.InvalidFormatException(f"Unexpected '{tag}' tag")
                        else:
                            # media = eval("EmbeddedMedia({})".format(params))
                            # parts[TEXT].append('%s %d' % 
                            #     (EMBEDDED_MEDIA_PLACEHOLDER, len(task.embeddedMedia)))
                            # task.embeddedMedia.append(media)
                            pass
                    else:
                        raise coding.InvalidFormatException(f"Unrecognized tag: '{tag}'")
                    continue
                parts[state].append(line)
            lineno = 'EOF'
            if state is CODE:
                raise coding.InvalidFormatException(f"Tag: '{ENDCODE_TAG}' expected")
            elif state is TEST:
                raise coding.InvalidFormatException(f"Tag: '{ENDTEST_TAG}' expected")
        except Exception as e:
            if type(lineno) is int:
                lineno += 1
            if type(e) is SyntaxError:
                e = "Syntax error"
            if type(e) is coding.InvalidFormatException:
                lineno = e.lineno if e.lineno is not None else lineno
            parts[TEXT].append("")
            parts[TEXT].append(f"<span style='color:red;'>*Error: Line {lineno}: {e}*</span>")
            parts[TEXT].append("")

        return parts[TEXT]
    
    #########################
    def parse_line(self, line):
        '''
        Checks whether this line is a custom tag.  It returns a tag and
        an optional parameter string if a tag is found.  Otherwise None is
        returned.
        '''
        match = TAG_RE.match(line)
        if match is None:
            return None, None
        return match.group(1), match.group(2)


#########################
class CodeSegmentInlineProcessor(markdown.inlinepatterns.InlineProcessor):
    
    #########################
    def __init__(self, pattern, task, md=None):
        super().__init__(pattern, md)
        self.task = task
        
    #########################
    def handleMatch(self, m, data):
        # extract CodeSegment ID
        id = int(m.group(1))

        # use the CodeSegment ID to retrieve the code segment data
        codeseg = self.task.codesegs[id]
        if codeseg.hidden:
            return None, None, None

        # the code segment will be wrapped inside the tags:
        # <fieldset><pre><code class="source">...</code></pre></fieldset>
        fs = etree.Element('fieldset')
        pre = etree.Element('pre')
        code = etree.Element('code')
        code.set('class', 'source')
        lineno = 1
        lineno_elem = self.create_lineno_span(lineno)
        for piece in codeseg:
            if codeseg.lineno and lineno_elem is not None:
                code.append(lineno_elem)
                lineno_elem = None

            if isinstance(piece, coding.Blank):
                blank_id = BLANK_ID_PREFIX + str(piece.id)
                width, height = text_dimension(piece.raw_answer())
                text, texttype = create_blank_element(width, height, blank_id)
                text.set('class', 'codeblank')
                text.set('name', blank_id)
                if (texttype == 'textarea'):
                    text.set('wrap', 'off')
            else:  # piece is a string, not a blank
                if isinstance(piece, coding.HiddenLine):
                    text = None
                else:
                    if codeseg.highlight:
                        text = piece
                        # if codeseg.language is None:
                        #     text = self.highlighter.highlight(piece)
                        # else:
                        #     pass
                        #     text = Highlighter(codeseg.language).highlight(piece)
                    else:
                        text = piece

            # resulting 'text' from a highlighter is a list
            if type(text) is list:
                for x in text:
                    append_text_or_elem(code, x)
            elif text is not None:
                append_text_or_elem(code, text)

            # Excluded line is not followed by a new line, so add one
            if isinstance(piece, coding.ExcludedLine):
                append_text_or_elem(code, '\n')

            if piece == '\n' or isinstance(piece, coding.ExcludedLine):
                lineno += 1
                lineno_elem = self.create_lineno_span(lineno)

        pre.append(code)
        fs.append(pre)
        #xx = """
        #<fieldset><pre><code><span>name</span> = <span>x</span></code></pre></fieldset>"""
        #fs = etree.fromstring(xx)
        #etree.dump(fs)
        return fs, m.start(0), m.end(0)
    
    
    #########################
    @staticmethod
    def create_lineno_span(lineno):
        lineno_span = etree.Element('span')
        lineno_span.set('class', 'lineno')
        lineno_span.text = AtomicString(f'{lineno:2d}: ')
        return lineno_span
     
######################### 
class MarkdownExtension(markdown.extensions.Extension):

    #########################
    def __init__(self, task):
        self.task = task
        
    #########################
    def extendMarkdown(self, md):
        md.preprocessors.register(BlankLinePreprocessor(md), 'blankline', 200)
        md.preprocessors.register(TagPreprocessor(md, self.task), 'tagprocessor', 190)
        CODESEGMENT_PLACEHOLDER_RE = re.escape(CODESEGMENT_PLACEHOLDER) + ' ([0-9]*)'
        md.inlinePatterns.register(CodeSegmentInlineProcessor(CODESEGMENT_PLACEHOLDER_RE, self.task), 'codesegment', 190)