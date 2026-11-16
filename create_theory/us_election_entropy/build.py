#!/usr/bin/env python3
"""us_election_entropy.typ を PDF に組版する (pip install typst)。"""
import typst
typst.compile("us_election_entropy.typ", output="us_election_entropy.pdf")
