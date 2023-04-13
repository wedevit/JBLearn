import sys
import codecs
import markdown

from . import markdown_extensions
from . import coding


def parse_source(text):
    task = coding.TaskBuilder()
    md = markdown.Markdown(
        extensions=[markdown_extensions.MarkdownExtension(task)])
    html = md.convert(text)
    code = task.get_code()
    tests = task.get_testcases()
    # textBlanks = task.getTextBlanks()
    # return html,code,tests,textBlanks
    return html, code, tests


#
# example usage
#
if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: python {} <input> <output> <lang>'.format(sys.argv[0]))
        sys.exit(1)

    input = codecs.open(sys.argv[1], mode='r', encoding='utf8')
    text = input.read()
    input.close()
    # html,code,tests,textBlanks = process_markdown_source(text,sys.argv[3])
    html, code, tests = parse_source(text)
    out = codecs.open(sys.argv[2], 'w', encoding='utf-8')
    print('------------ HTML Template -----------------', file=out)
    print(html, file=out)
    print('------------ Original Code -----------------', file=out)
    print(code.dump_solution(), file=out)
    print('------------ Test Case(s) -----------------', file=out)
    for i, test in enumerate(tests):
        print(f"Test case #{i + 1}", file=out)
        print(test.input, file=out)
    # #print(textBlanks)
    # out.close()
