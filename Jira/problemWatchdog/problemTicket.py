#!/usr/bin/python3
# -*- coding: utf-8 -*-
# ==============================================================================
#  C O P Y R I G H T
# ------------------------------------------------------------------------------
#  Copyright (c) 2019 by Robert Bosch GmbH. All rights reserved.
#
#  This file is property of Robert Bosch GmbH. Any unauthorized copy, use or
#  distribution is an offensive act against international law and may be
#  prosecuted under federal law. Its content is company confidential.
# ==============================================================================

class ProblemTicket:

    def __init__(self, ticket, type, reason):
        self.ticket = ticket
        self.type = type
        self.reason = reason

    def __add__(self,other):
        x = self.ticket 
        y = self.type + " & " + other.type
        z = self.reason + "<br><br>" + other.reason
        return ProblemTicket( x, y, z)