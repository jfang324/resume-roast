# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

- Interview mode no longer makes model calls it discards when a question stalls, reducing wasted tokens

## [1.0.2] - 2026-07-20

- New `interview` subcommand: agentic behavioral interview with resume-based fact-checking and competency scoring
- Chat sessions now report metrics per message instead of a single cumulative summary at exit
- Added support for docx files

## [1.0.1] - 2026-07-13

- Updated project metadata

## [1.0.0] - 2026-07-13

- Initial release supporting resume evaluation, bullet refinement, and block generation
