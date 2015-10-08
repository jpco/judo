#! /usr/bin/python

"""
Judo: todo-list management.  Time- and topic-based to-do software.

Usage:
adding/modifying events:
 - judo (add|schedule) [-s subject] [-t time-spec] do action, or judo action [-s subject] [-t time]
    - topics are one word (ws-separated), dates go until another keyword or end
        thus 'judo add take a bath @tomorrow 3pm :self-care'
             'judo a @tomorrow 3pm do take a bath :self-care', as is
             'judo add @tomorrow 3pm :self-care take a bath', and they are all equiv.

 - judo rm event-id
    - removes the event specified by its event ID (not the same as marking as done!)

 - judo set event-id ([event-spec]|done|undone)
    - changes an event specified by its event ID to either 'done/undone', or to the data
        passed in with syntax equivalent to 'judo add'

listing events:
 - judo (ls|list) [-a|--all] [list-spec] [:topic] [@time-spec]
    - list-spec must come before topic/time-spec if it exists!
    - '-a|--all' lists completed jobs as well as incomplete ones!

server connection & syncing (later functionality):
 - judo connect [server]
    - if server is not given in argument, will be requested
    - username may be requested
    - password may be requested

 - judo sync
    - forces a sync
"""

import os
import argparse
import time
import pickle
import configparser

# default defaults
DEFAULT_SUBJECT = 'other'
DEFAULT_LIST_SUBJECTS = ['electra', 'uts', 'wesley', 'class', 'simech', 'other']
DEFAULT_TIMEOUT = 60*60*24*7
EVTS_FILE = '{}/.judo_evts'.format(os.path.expanduser('~')) 

CONFIG_FILE = '{}/.judocfg'.format(os.path.expanduser('~'))

class Event:
    def __init__(self, title, subject=None):
        self.title = title
        if subject:
            self.subject = subject
        else:
            self.subject = DEFAULT_SUBJECT
        self.id = least_available_id()
        self.done = None

evt_dict = {}

def load_saved():
    global evt_dict
    try:
        with open(EVTS_FILE, 'rb') as fi:
            evt_dict = pickle.load(fi)
    except FileNotFoundError:
        pass


def save_loaded():
    with open(EVTS_FILE, 'wb') as fi:
        pickle.dump(evt_dict, fi)


def prune_dict():
    now = time.time()
    evt_ids = list(evt_dict.keys())
    for evt in evt_ids:
        if evt_dict[evt].done and now - evt_dict[evt].done > DEFAULT_TIMEOUT:
            evt_dict.pop(evt)


def least_available_id():
    least_id = 1
    evt_ids = evt_dict.keys()

    while least_id in evt_ids:
        least_id += 1

    return least_id


def get_subjects():
    subjects = {}

    for evt_id in evt_dict:
        evt = evt_dict[evt_id]
        if subjects.get(evt.subject):
            subjects[evt.subject].append(evt)
        else:
            subjects[evt.subject] = [evt]
    return subjects


def ls_by_subject(list_all, list_subject):
    subjects = get_subjects()
    if list_subject and list_subject not in subjects:
        print ('Subject {} not found in active events.'.format(list_subject))
        return

    # do the printing!!
    if list_subject:
        print ('\033[1m\033[34m{0} =====\033[0m'.format(list_subject.upper()))
        for evt in subjects[list_subject]:
            if evt.done:
                if list_all:
                    print ('\033[31m x {0}: {1}\033[0m'.format(evt.id, evt.title))
            else:
                print (' - {0}: {1}'.format(evt.id, evt.title))
       
    else:
        subj_len = 0
        for subject in subjects.keys():
            if subj_len < len(subject):
                subj_len = len(subject)

        subj_len += 5

        for subj in sorted(subjects.keys()):
            if subj not in DEFAULT_LIST_SUBJECTS and not list_all:
                continue

            subj_printed = False
            for evt in subjects[subj]:
                if evt.done:
                    if list_all:
                        if not subj_printed:
                            print ('\033[1m\033[34m{0} {1}\033[0m'.format(subj.upper(), '=' * (subj_len - len(subj))))
                            subj_printed = True

                        print ('\033[31m x {0}: {1}\033[0m'.format(evt.id, evt.title))
                else:
                    if not subj_printed:
                        print ('\033[1m\033[34m{0} {1}\033[0m'.format(subj.upper(), '=' * (subj_len - len(subj))))
                        subj_printed = True

                    print (' - {0}: {1}'.format(evt.id, evt.title))



"""
cmd functions. These get directly called by argparser
"""
def add_cmd(args):
    if debug:
        print ('ADD! args: {}'.format(args))
    if args.s:
        args.s = args.s[0].lower()
    new_evt = Event(' '.join(args.title), subject=args.s)
    evt_dict[new_evt.id] = new_evt


def rm_cmd(args):
    global evt_dict
    if debug:
        print ('RM! args: {}'.format(args))
    try:
        evt_dict.pop(args.id)
    except:
        print ('No event with id {} found.'.format(args.id))

def set_cmd(args):
    if debug:
        print ('SET! args: {}'.format(args))
    try:
        evt = evt_dict.pop(args.id)
    except:
        print ('No event with id {} found.'.format(args.id))
        return

    if len(args.title) > 0:
        evt.title = ' '.join(args.title)

    if args.s:
        evt.subject = args.s[0].lower()

    if args.t:
        evt.time = args.t

    evt_dict[evt.id] = evt


def ls_cmd(args):
    if debug:
        print ('LS! args: {}'.format(args))
    ls_by_subject(args.a, args.s)


def connect_cmd(args):
    if debug:
        print ('CONNECT! args: {}'.format(args))


def sync_cmd(args):
    if debug:
        print ('SYNC! args: {}'.format(args)) 


def do_cmd(args):
    if debug:
        print ('DO! args: {}'.format(args)) 
    try:
        evt = evt_dict.pop(args.id)
    except:
        print ('No event with id {} found.'.format(args.id))
        return

    if evt.done:
        print ('Event {} already done.'.format(args.id))
    else:
        evt.done = time.time()

    evt_dict[evt.id] = evt


def undo_cmd(args):
    if debug:
        print ('UNDO! args: {}'.format(args)) 
    try:
        evt = evt_dict.pop(args.id)
    except:
        print ('No event with id {} found.'.format(args.id))
        return

    if not evt.done:
        print ('Event {} already not done.'.format(args.id))
    else:
        evt.done = None

    evt_dict[evt.id] = evt


parser = argparse.ArgumentParser(prog='Judo', description='A simple Python todo-list program.')
parser.add_argument('--debug', help='Debug mode', action='store_true')
subparsers = parser.add_subparsers()

add_parser = subparsers.add_parser('add')
add_parser.add_argument('title', nargs='+', help='The action\'s title.')
add_parser.add_argument('-s', metavar='subject', nargs=1, help='The action\'s subject.')
add_parser.add_argument('-t', metavar='time', nargs=1, help='The action\'s time to be done.')
add_parser.set_defaults(func=add_cmd)

rm_parser = subparsers.add_parser('rm')
rm_parser.add_argument('id', type=int)
rm_parser.set_defaults(func=rm_cmd)

set_parser = subparsers.add_parser('set')
set_parser.add_argument('id', type=int)
set_parser.add_argument('title', nargs='*', help='The action\'s new title.')
set_parser.add_argument('-s', metavar='subject', nargs=1, help='The action\'s new subject.')
set_parser.add_argument('-t', metavar='time', nargs=1, help='The action\'s new time to be done.')
set_parser.set_defaults(func=set_cmd)

ls_parser = subparsers.add_parser('ls')
ls_parser.add_argument('-a', action='store_true')
ls_parser.add_argument('-s', metavar='subject')
ls_parser.add_argument('args', nargs='*')
ls_parser.set_defaults(func=ls_cmd)

do_parser = subparsers.add_parser('do')
do_parser.add_argument('id', type=int)
do_parser.set_defaults(func=do_cmd)

undo_parser = subparsers.add_parser('undo')
undo_parser.add_argument('id', type=int)
undo_parser.set_defaults(func=undo_cmd)


config = configparser.ConfigParser()
config.read(CONFIG_FILE)
if not 'config' in config:
    print ('Malformed config.')
    parser.print_help()
    exit (1)
else:
    config = config['config']

if 'Subject' in config:
    DEFAULT_SUBJECT = config['Subject']
if 'DoneTimeout' in config:
    try:
        DEFAULT_TIMEOUT = int(config['DoneTimeout'])
    except Exception:
        print ('Warning: malformed DoneTimeout entry in config.')
if 'EventsFile' in config:
    EVTS_FILE = os.path.abspath(os.path.expanduser(config['EventsFile']))
if 'ListSubjects' in config:
    DEFAULT_LIST_SUBJECTS = [DEFAULT_SUBJECT]
    subjs = config['ListSubjects'].split(',')
    for subj in subjs:
        DEFAULT_LIST_SUBJECTS.append(subj.strip())


# TODO (lol):
# - date/time
# - better arg parsing
# - server
if __name__ == "__main__":
    load_saved()
    prune_dict()

    args = parser.parse_args()

    global debug
    debug = args.debug
    try:
        args.func(args)
    except AttributeError:
        parser.print_help()

    save_loaded()
