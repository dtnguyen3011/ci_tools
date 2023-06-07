""" See https://docs.python.org/3/library/argparse.html for usage. """


def add_log_level(parser):
    """ Add default logger argument. """
    parser.add_argument('-d', '--debug', dest='log_level',
                        action='store_const', const='DEBUG', default='INFO',
                        help='Print debug information')
    parser.add_argument('-q', '--quiet', dest='log_level',
                        action='store_const', const='ERROR', default='INFO',
                        help='Print only errors')
    return parser


def add_cfg(parser):
    """ Add default config argument. """
    parser.add_argument('--config', default='CONFIG')
    return parser
