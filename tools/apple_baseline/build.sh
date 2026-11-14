#!/bin/sh
# Build the Apple baseline CLI (macOS with Xcode command-line tools).
cd "$(dirname "$0")" && swiftc -O apple_classify.swift -o apple_classify
