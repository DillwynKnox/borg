import io
import sys

from . import is_terminal
from borg.helpers.coverage_diy import register
from borg.helpers.coverage_diy import mark

coverage_hits = {i: False for i in range(1, 26)}

class TextPecker:
    def __init__(self, s):
        self.str = s
        self.i = 0

    def read(self, n):
        self.i += n
        return self.str[self.i - n : self.i]

    def peek(self, n):
        if n >= 0:
            return self.str[self.i : self.i + n]
        else:
            return self.str[self.i + n - 1 : self.i - 1]

    def peekline(self):
        out = ""
        i = self.i
        while i < len(self.str) and self.str[i] != "\n":
            out += self.str[i]
            i += 1
        return out

    def readline(self):
        out = self.peekline()
        self.i += len(out)
        return out


def process_directive(directive, arguments, out, state_hook):
    if directive == "container" and arguments == "experimental":
        state_hook("text", "**", out)
        out.write("++ Experimental ++")
        state_hook("**", "text", out)
    else:
        state_hook("text", "**", out)
        out.write(directive.title())
        out.write(":\n")
        state_hook("**", "text", out)
        if arguments:
            out.write(arguments)
            out.write("\n")


def rst_to_text(text, state_hook=None, references=None):
    CP_BRANCHES = [
        "RST_01_T_eof_break",
        "RST_01_F_eof_break",
        "RST_02_T_state_text",
        "RST_02_F_state_text",
        "RST_03_T_escape_inline",
        "RST_03_F_escape_inline",
        "RST_04_T_prev_not_backslash",
        "RST_04_F_prev_not_backslash",
        "RST_05_T_enter_inline_single",
        "RST_05_F_enter_inline_single",
        "RST_06_T_enter_bold",
        "RST_06_F_enter_bold",
        "RST_07_T_enter_dbltick",
        "RST_07_F_enter_dbltick",
        "RST_08_T_ref_translate",
        "RST_08_F_ref_translate",
        "RST_09_T_ref_endtick",
        "RST_09_F_ref_endtick",
        "RST_10_T_ref_newline_skip",
        "RST_10_F_ref_newline_skip",
        "RST_11_T_ref_defined",
        "RST_11_F_ref_undefined",
        "RST_12_T_codeblock_start",
        "RST_12_F_codeblock_start",
        "RST_13_T_directive_start",
        "RST_13_F_directive_start",
        "RST_14_T_is_directive",
        "RST_14_F_is_directive",
        "RST_15_T_inline_fill",
        "RST_15_F_inline_fill",
        "RST_16_T_inline_replace",
        "RST_16_F_inline_replace",
        "RST_17_process_directive",
        "RST_18_T_close_inline_single",
        "RST_18_F_close_inline_single",
        "RST_19_T_fill_2spaces",
        "RST_19_F_fill_2spaces",
        "RST_20_T_close_dbltick",
        "RST_20_F_close_dbltick",
        "RST_21_T_fill_4spaces",
        "RST_21_F_fill_4spaces",
        "RST_22_T_close_bold",
        "RST_22_F_close_bold",
        "RST_23_T_codeblock_end",
        "RST_23_F_codeblock_end",
    ]
    for bid in CP_BRANCHES:
        register(bid)

    state_hook = state_hook or (lambda old_state, new_state, out: None)
    references = references or {}
    state = "text"
    inline_mode = "replace"
    text = TextPecker(text)
    out = io.StringIO()

    inline_single = ("*", "`")

    while True:
        char = text.read(1)
        if not char:
            mark("RST_01_T_eof_break")
            break
        else:
            mark("RST_01_F_eof_break")

        next = text.peek(1)  # type: str

        if state == "text":
            mark("RST_02_T_state_text")

            if char == "\\" and text.peek(1) in inline_single:
                mark("RST_03_T_escape_inline")
                continue
            else:
                mark("RST_03_F_escape_inline")

            if text.peek(-1) != "\\":
                mark("RST_04_T_prev_not_backslash")

                if char in inline_single and next != char:
                    mark("RST_05_T_enter_inline_single")
                    state_hook(state, char, out)
                    state = char
                    continue
                else:
                    mark("RST_05_F_enter_inline_single")

                if char == next == "*":
                    mark("RST_06_T_enter_bold")
                    state_hook(state, "**", out)
                    state = "**"
                    text.read(1)
                    continue
                else:
                    mark("RST_06_F_enter_bold")

                if char == next == "`":
                    mark("RST_07_T_enter_dbltick")
                    state_hook(state, "``", out)
                    state = "``"
                    text.read(1)
                    continue
                else:
                    mark("RST_07_F_enter_dbltick")

                if text.peek(-1).isspace() and char == ":" and text.peek(5) == "ref:`":
                    mark("RST_08_T_ref_translate")
                    text.read(5)
                    ref = ""
                    while True:
                        char2 = text.peek(1)
                        if char2 == "`":
                            mark("RST_09_T_ref_endtick")
                            text.read(1)
                            break
                        else:
                            mark("RST_09_F_ref_endtick")

                        if char2 == "\n":
                            mark("RST_10_T_ref_newline_skip")
                            text.read(1)
                            continue
                        else:
                            mark("RST_10_F_ref_newline_skip")

                        ref += text.read(1)

                    try:
                        out.write(references[ref])
                        mark("RST_11_T_ref_defined")
                    except KeyError:
                        mark("RST_11_F_ref_undefined")
                        raise ValueError(
                            "Undefined reference in Archiver help: %r — please add reference "
                            "substitution to 'rst_plain_text_references'" % ref
                        )
                    continue
                else:
                    mark("RST_08_F_ref_translate")

                if char == ":" and text.peek(2) == ":\n":
                    mark("RST_12_T_codeblock_start")
                    text.read(2)
                    state_hook(state, "code-block", out)
                    state = "code-block"
                    out.write(":\n")
                    continue
                else:
                    mark("RST_12_F_codeblock_start")
            else:
                mark("RST_04_F_prev_not_backslash")

            if text.peek(-2) in ("\n\n", "") and char == next == ".":
                mark("RST_13_T_directive_start")
                text.read(2)
                directive, is_directive, arguments = text.readline().partition("::")
                text.read(1)

                if not is_directive:
                    mark("RST_14_F_is_directive")
                    if directive == "nanorst: inline-fill":
                        mark("RST_15_T_inline_fill")
                        inline_mode = "fill"
                    else:
                        mark("RST_15_F_inline_fill")

                    if directive == "nanorst: inline-replace":
                        mark("RST_16_T_inline_replace")
                        inline_mode = "replace"
                    else:
                        mark("RST_16_F_inline_replace")

                    continue
                else:
                    mark("RST_14_T_is_directive")
                    mark("RST_17_process_directive")
                    process_directive(directive, arguments.strip(), out, state_hook)
                    continue
            else:
                mark("RST_13_F_directive_start")

        else:
            mark("RST_02_F_state_text")

        if state in inline_single and char == state:
            mark("RST_18_T_close_inline_single")
            state_hook(state, "text", out)
            state = "text"
            if inline_mode == "fill":
                mark("RST_19_T_fill_2spaces")
                out.write(2 * " ")
            else:
                mark("RST_19_F_fill_2spaces")
            continue
        else:
            mark("RST_18_F_close_inline_single")

        if state == "``" and char == next == "`":
            mark("RST_20_T_close_dbltick")
            state_hook(state, "text", out)
            state = "text"
            text.read(1)
            if inline_mode == "fill":
                mark("RST_21_T_fill_4spaces")
                out.write(4 * " ")
            else:
                mark("RST_21_F_fill_4spaces")
            continue
        else:
            mark("RST_20_F_close_dbltick")

        if state == "**" and char == next == "*":
            mark("RST_22_T_close_bold")
            state_hook(state, "text", out)
            state = "text"
            text.read(1)
            continue
        else:
            mark("RST_22_F_close_bold")

        if state == "code-block" and char == next == "\n" and text.peek(5)[1:] != "    ":
            mark("RST_23_T_codeblock_end")
            state_hook(state, "text", out)
            state = "text"
        else:
            mark("RST_23_F_codeblock_end")

        out.write(char)

    assert state == "text", "Invalid final state %r (This usually indicates unmatched */**)" % state
    return out.getvalue()



class RstToTextLazy:
    def __init__(self, str, state_hook=None, references=None):
        self.str = str
        self.state_hook = state_hook
        self.references = references
        self._rst = None

    @property
    def rst(self):
        if self._rst is None:
            self._rst = rst_to_text(self.str, self.state_hook, self.references)
        return self._rst

    def __getattr__(self, item):
        return getattr(self.rst, item)

    def __str__(self):
        return self.rst

    def __add__(self, other):
        return self.rst + other

    def __iter__(self):
        return iter(self.rst)

    def __contains__(self, item):
        return item in self.rst


def ansi_escapes(old_state, new_state, out):
    if old_state == "text" and new_state in ("*", "`", "``"):
        out.write("\033[4m")
    if old_state == "text" and new_state == "**":
        out.write("\033[1m")
    if old_state in ("*", "`", "``", "**") and new_state == "text":
        out.write("\033[0m")


def rst_to_terminal(rst, references=None, destination=sys.stdout):
    """
    Convert *rst* to a lazy string.

    If *destination* is a file-like object connected to a terminal,
    enrich the text with suitable ANSI escapes. Otherwise, return plain text.
    """
    if is_terminal(destination):
        rst_state_hook = ansi_escapes
    else:
        rst_state_hook = None
    return RstToTextLazy(rst, rst_state_hook, references)
