# coding: utf-8
"""
"""

import os

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./data")
request_distance = 0.1

if os.path.exists(OUTPUT_DIR) is False:
    os.makedirs(OUTPUT_DIR)