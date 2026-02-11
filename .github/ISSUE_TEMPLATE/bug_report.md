name: Bug Report
description: File a bug report to help us improve
title: "[BUG] "
labels: ["bug", "triage"]
body:
  - type: markdown
    attributes:
      value: |
        Thanks for taking the time to fill out this bug report!

  - type: textarea
    id: description
    attributes:
      label: Description
      description: A clear and concise description of what the bug is.
      placeholder: "When I do X, Y happens instead of Z"
    validations:
      required: true

  - type: textarea
    id: reproduction
    attributes:
      label: Reproduction Steps
      description: Steps to reproduce the behavior
      placeholder: |
        1. Go to '...'
        2. Click on '....'
        3. Scroll down to '....'
        4. See error
    validations:
      required: true

  - type: textarea
    id: expected
    attributes:
      label: Expected Behavior
      description: What you expected to happen
      placeholder: "I expected X to happen"
    validations:
      required: true

  - type: textarea
    id: actual
    attributes:
      label: Actual Behavior
      description: What actually happened
      placeholder: "Instead, Y happened"
    validations:
      required: true

  - type: textarea
    id: environment
    attributes:
      label: Environment
      description: Environment details
      placeholder: |
        - OS: [e.g. macOS 13.0, Ubuntu 22.04]
        - Docker version: [e.g. 24.0.6]
        - Python version: [e.g. 3.11.5]
        - Browser: [e.g. Chrome 119, Firefox 120]
    validations:
      required: true

  - type: textarea
    id: logs
    attributes:
      label: Logs/Screenshots
      description: Add any relevant logs, error messages, or screenshots
      render: shell