#!/usr/bin/env python3
"""us_election_topology.typ を PDF に組版する (pip install typst)。"""
import typst
typst.compile("us_election_topology.typ", output="us_election_topology.pdf")
