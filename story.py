import os
import sys
import logging
import inspect
from contextlib import suppress
from collections import namedtuple
from itertools import cycle, islice
from functools import lru_cache, partial
from subprocess import run, Popen, STDOUT, PIPE

from blinker import signal
from colorama import init, Fore, Style, Back
from bpython.curtsies import (
    io,
    repl,
    Option,
    bpargs,
    Interp,
    curtsies,
    inspection,
    translations,
    find_iterator,
    combined_events,
    FullCurtsiesRepl,
    extract_exit_value,
    bpythonevents,
    SystemExitFromCodeGreenlet,
)
init()


_CodeSnippet = namedtuple('_CodeSnippet', 'code, suite, example')
_command_line_event = signal('command_line_event')
CLEAR_SCREEN_SYMBOL = '<Ctrl-l>'
NEXT_SYMBOL = '>'
BACK_SYMBOL = '<'
PAGE_UP_SYMBOL = '<PAGEUP>'
PAGE_DOWN_SYMBOL = '<PAGEDOWN>'
ASCII_ART = f"""
  ____  _         __      ___ 
 |  _ \| |        \ \    / (_)           
 | |_) | |_   _  __\ \  / / _ _ __   ___ 
 |  _ <| | | | |/ _ \ \/ / | | '_ \ / _ \\
 | |_) | | |_| |  __/\  /  | | | | |  __/
 |____/|_|\__,_|\___| \/   |_|_| |_|\___|
                 .==.           We're Hiring: https://jobs.lever.co/bluevine
                ()''()-.
     .---.       ;--; /         Author: Lior Mizrahi
   .'_:___". _..'.  __'.        Source In GitHub: liormizr/linux_distance_locker
   |__ --==|'-'''\\'...;
   [  ]  :[|      |---\\        Special Control Commands:
   |__| I=[|     .'    '.       * NEXT: {NEXT_SYMBOL}
   / / ____|     :       '._    * BACK: {BACK_SYMBOL}
  |-/.____.'      | :       :   * PAGE-UP: {PAGE_UP_SYMBOL}
 /___\ /___\      '-'._----'    * PAGE-DOWN: {PAGE_DOWN_SYMBOL}
"""
DO_NOT_CARE_SENSOR_MESSAGES = (
    'Read RSSI failed: Input/output error',
    'Attempting connection...',
    'GONE!',
    'HERE!',
)
PHONE_ADDRESS = os.getenv('PHONE_ADDRESS')


def main(args=None, locals_=None, welcome_message=None):
    """
    banner is displayed directly after the version information.
    welcome_message is passed on to Repl and displayed in the statusbar.
    """
    translations.init()
    config, options, *_ = bpargs.parse(args or [], (
        'curtsies options', None, [
            Option('--log', '-L', action='count',
                   help="log debug messages to bpython.log"),
            Option('--paste', '-p', action='store_true',
                   help="start by pasting lines of a file into session"),
            ]))
    _log_config(options)
    interp, paste = _setup(ASCII_ART, None, options, locals_)
    return _start_curtsies(config, locals_, welcome_message, interp, paste)


def initial_slide(options=None):
    _command_line_event.connect(switch_example)
    if not options:
        return
    for option, value in vars(options).items():
        if not value:
            continue
        if option not in explanation_map.data:
            continue
        code_snippets = explanation_map.data[option]
        explanation_map.current = code_snippets
    return True


def _log_config(options):
    if options.log is None:
        options.log = 0
    logging_levels = [logging.ERROR, logging.INFO, logging.DEBUG]
    level = logging_levels[min(len(logging_levels) - 1, options.log)]
    logging.getLogger('curtsies').setLevel(level)
    logging.getLogger('bpython').setLevel(level)
    if options.log:
        handler = logging.FileHandler(filename='bpython.log')
        logging.getLogger('curtsies').addHandler(handler)
        logging.getLogger('curtsies').propagate = False
        logging.getLogger('bpython').addHandler(handler)
        logging.getLogger('bpython').propagate = False


def _setup(banner, exec_args, options, locals_):
    interp = paste = None
    if exec_args:
        if not options:
            raise ValueError("don't pass in exec_args without options")
        exit_value = ()
        if options.paste:
            paste = curtsies.events.PasteEvent()
            encoding = inspection.get_encoding_file(exec_args[0])
            with io.open(exec_args[0], encoding=encoding) as f:
                sourcecode = f.read()
            paste.events.extend(sourcecode)
        else:
            try:
                interp = Interp(locals=locals_)
                bpargs.exec_code(interp, exec_args)
            except SystemExit as system_error:
                exit_value = system_error.args
            if not options.interactive:
                return extract_exit_value(exit_value)
    else:
        # expected for interactive sessions (vanilla python does it)
        sys.path.insert(0, '')
    # if not options.quiet:
    #     print(bpargs.version_banner())
    if banner is not None:
        print(banner)
    return interp, paste


def _start_curtsies(config, locals_, welcome_message, interp, paste):
    global repl
    repl = FullCurtsiesRepl(config, locals_, welcome_message, interp, paste)
    try:
        with repl.input_generator, repl.window as win, repl:
            repl.height, repl.width = win.t.height, win.t.width
            return _mainloop(repl)
    except (SystemExitFromCodeGreenlet, SystemExit) as error:
        return error.args


def _mainloop(_repl):
    def loop_handler():
        nonlocal event
        for _, result in _command_line_event.send(event):
            if not result:
                continue
            _repl.process_event_and_paint('<Ctrl-j>')
            break
        else:
            _repl.process_event_and_paint(event)  # pylint: disable=undefined-loop-variable

    _repl.initialize_interp()
    _repl.process_event(bpythonevents.RunStartupFileEvent())

    # do a display before waiting for first event
    _repl.process_event_and_paint(None)
    inputs = combined_events(_repl.input_generator)
    for _ in find_iterator:
        event = inputs.send(0)
        if event is not None:
            loop_handler()

    for event in inputs:
        loop_handler()


def explanation_snippets(example=None, *, docs=None):
    if not example:
        return partial(explanation_snippets, docs=docs)
    if docs:
        example.__doc__ = docs

    suite = example.__module__.split('.')[-1]
    code_lines = []
    for line in inspect.getsource(example).splitlines()[2:]:
        line = line[4:]
        if line.startswith('"""'):
            line = line
        elif line.startswith('"'):
            line = line
        code_lines.append(line)
    code_snippet = _CodeSnippet(
        code='\n'.join(code_lines),
        suite=suite,
        example=example)
    if suite not in explanation_map.data:
        explanation_map.data[suite] = CycleSnippets([code_snippet])
    else:
        explanation_map.data[suite].data.append(code_snippet)
    return example


class CycleSnippets:
    def __init__(self, data=None):
        self.data = data
        self.current = None

    def __repr__(self):
        return f'{type(self).__name__}(current={self.current})'

    @property  # type: ignore
    @lru_cache()
    def iterator(self):
        return cycle(self.data)

    @property  # type: ignore
    @lru_cache()
    def jump_to_previous(self):
        jump_to_previous = len(self.data) - 2
        if jump_to_previous < 0:
            return 0
        return jump_to_previous

    def next(self):
        if isinstance(self.data, dict):
            self.current = self.data[next(self.iterator)]
        else:
            self.current = next(self.iterator)
        return self.current

    def previous(self):
        prev = islice(self.iterator, self.jump_to_previous, None)
        if isinstance(self.data, dict):
            self.current = self.data[next(prev)]
        else:
            self.current = next(prev)
        return self.current
explanation_map = CycleSnippets(data={})


def switch_example(event: str):
    def _explaination_next_snippet():
        repl.process_event_and_paint(CLEAR_SCREEN_SYMBOL)

        repl.interp.locals.update(globals())
        code = '\n'.join(
            line
            for line in code_snippet.code.splitlines()
            if not line.startswith('\x1b')
        )

        code_text = f'{code_snippet.example.__name__}:\n{code_snippet.example.__doc__}\n'
        repl.send_to_stdout(code_text)
        if hasattr(code_snippet.example, 'code'):
            for l in '\n'.join(code_snippet.example.code):
                if l == 'B':
                    l = '<BACKSPACE>'
                repl.process_event_and_paint(l)
            repl.process_event_and_paint('<Ctrl-u>')
            repl.process_event_and_paint('\n')

        # exec(code, repl.interp.locals)

    if event == NEXT_SYMBOL:
        code_snippets = explanation_map.current or explanation_map.next()
        code_snippet = code_snippets.next()
        _explaination_next_snippet()
        return '## ' + 'Next Example ' + '#'*30
    if event == BACK_SYMBOL:
        code_snippets = explanation_map.current or explanation_map.next()
        code_snippet = code_snippets.previous()
        _explaination_next_snippet()
        return '## ' + 'Previous Example ' + '#'*30
    if event == PAGE_UP_SYMBOL:
        code_snippets = explanation_map.next()
        code_snippet = code_snippets.current or code_snippets.next()
        _explaination_next_snippet()
        return '## ' + 'Next Suite ' + '#'*30
    if event == PAGE_DOWN_SYMBOL:
        code_snippets = explanation_map.previous()
        code_snippet = code_snippets.current or code_snippets.next()
        _explaination_next_snippet()
        return '## ' + 'Previous Suite ' + '#'*30


@explanation_snippets(docs=f"""
    Our story started a couple of years ago,
    When I worked at a small startup.

    We were successful, and with success comes growth,
    With growth comes {Fore.RED}{Style.BRIGHT}security{Style.RESET_ALL}.

    We needed to become SOC2 compliant.
    """)
def the_story():
    pass


@explanation_snippets(docs=f"""
    New Company Rule:

    If a worker is leaving his station,
    he have to logout his computer.
    {Back.MAGENTA}{Fore.CYAN}{Style.BRIGHT}IMMEDIATELY!!!!!!!!!!!!!!!!!!!!!!!{Style.RESET_ALL}
    """)
def the_issue():
    pass


@explanation_snippets(docs=f"""
    So, What Happens in this case:

    1. Security team start to work more on
       checking the company workers.
       (babysitting)
    2. Company workers (your friends)
       starting to behave differently.
       * pranking on another,
       * hacking each other computer

    What to do? {Style.BRIGHT}ヽ(ಠ_ಠ)ノ{Style.RESET_ALL}
    """)
def the_scenario():
    pass


@explanation_snippets(docs=f"""
    I know! {Style.BRIGHT}{Fore.YELLOW}💡{Style.RESET_ALL}

    Use the Phone (Or any Bluetooth device)
    to lock and unlock the PC automatically!?!?!

    detect distance...
    """)
def the_idea():
    pass


@explanation_snippets(docs=f"""
    {Style.BRIGHT}{Fore.BLUE}G{Fore.RED}o{Fore.YELLOW}o{Fore.BLUE}g{Fore.GREEN}l{Fore.RED}e{Style.RESET_ALL} it!
    Search: {Style.BRIGHT}Bluetooth desktop locker{Style.RESET_ALL}

    * For Windows: Win 10 have a feature: dynamic-lock

    * For Mac: multiple app stor apps for that (Need to pay)
    For Example: https://nearlock.me/

    * For Linux: blueproximity
    In Python, OpenSource, BUT!
    """)
def the_research_1():
    pass


@explanation_snippets(docs=f"""
    {Style.BRIGHT}{Fore.BLUE}G{Fore.RED}o{Fore.YELLOW}o{Fore.BLUE}g{Fore.GREEN}l{Fore.RED}e{Style.RESET_ALL} it again!
    Search: {Style.BRIGHT}Linux Bluetooth distance sensing{Style.RESET_ALL}

    * Found a blog that explains how to write it!
    https://www.raspberrypi.org/forums/viewtopic.php?t=47466

    {Style.BRIGHT}WOWOWOWO!{Style.RESET_ALL} In the comments there's a bash script!!!
    https://www.raspberrypi.org/forums/viewtopic.php?t=47466#p417970
    """)
def the_research_2():
    pass


@explanation_snippets
def developing_1():
    """
    1. copied the bash Bluetooth distance script
    """
developing_1.code = (
    'def distance_script(address):',
    'with suppress(KeyboardInterrupt):',
    "run(['bluetooth_distance_sensor.sh', address])",
    '',
)


@explanation_snippets
def developing_2():
    """
    2. create a Python wrapper that will lock/unlock the desktop
    """
developing_2.code = (
    'def distance_script_wrapper(address):',
    'process = Popen(',
    "    ['bluetooth_distance_sensor.sh', address],",
    'stderr=STDOUT, stdout=PIPE,',
    'bufsize=1, universal_newlines=True)',
    'Bwith process, suppress(KeyboardInterrupt):',
    "for line in iter(process.stdout.readline, ''):",
    'line = line.strip()',
    'if line in DO_NOT_CARE_SENSOR_MESSAGES:',
    'continue',
    "Bprint('sensor filtered line:', line)",
    '',
)


@explanation_snippets
def developing_3():
    """
    3. The logic:

    * Queue: deque(maxlen=5)
    * Every RSSI < -1 == adding RSSI value to the queue
    * Every RSSI >= -1 == poping the oldest RSSI value from the queue

    * If the Queue gets full (5 values)
      - LOCK the Desktop
    * If the status is LOCKED and the queue go down under 4 values
      - UNLOCK the Desktop
    """


@explanation_snippets
def end():
    """
    Demo and questions

    $ distance_locker -a <mac address>
    """


if __name__ == '__main__':
    initial_slide()
    main(welcome_message='Bluetooth distance detection story')
