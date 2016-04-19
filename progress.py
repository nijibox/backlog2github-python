# -*- cofing:utf8 -*-
from __future__ import unicode_literals
import sys


class ProgressText(object):
    GAUGE_POS = '#'

    GAUGE_NEG = ' '

    def __init__(self, out=sys.stdout, max_value=100, gauge_num=100):
        self.out = out
        self.gauge_num = gauge_num
        self.max_value = max_value

    def display(self, value):
        percent = int(100.0 * value / self.max_value)
        self.out.write('{}{}|{}/{}\r'.format(
            self.GAUGE_POS * percent,
            self.GAUGE_NEG * (100 - percent),
            value,
            self.max_value
        ))
        self.out.flush()

    def end(self):
        self.out.write('\n')
