"""Static Trello card templates, generic across boards.

Single source of truth for the ticket "designs" (description, default checklist,
labels, and cover color). Baked in so ticket creation never reads the board.
"""

TEMPLATES: dict[str, dict] = {
    "User Story Template": {
        "desc": """As <persona>, I want <feature> because <reason>

## Summary

<add a summary/description of the user story>

## Acceptance Criteria

- <add list of criteria to be met to accept the story>

## Attachments

- Business document is added
- UI is added
- Video that describes that user story on the UI""",
        "checklist": "Development Tasks",
        "checkitems": [
            "Implementation completed including docstring",
            "Unit tests pass with high code coverage",
            "Feature tests reviewed",
            "Feature tests pass",
            "Code integrated into master and build succeeds",
            "Versions updated",
            "Configurations updated",
            "Swagger file needed.",
            "Manual testing performed and pass",
            "Implementation covers every affected module, not only the primary one",
        ],
        "labels": [],
        "cover": {"color": "green", "brightness": "light", "size": "normal"},
    },
    "Task Template": {
        "desc": """## Summary

<add a summary/description of the task template>

### **Design Interface:**

- <Figma Link>
- <Screen Shoots>

## Acceptance Criteria

- <add acceptance>""",
        "checklist": "Development Tasks",
        "checkitems": [
            "Implementation completed including docstring",
            "Unit tests pass with high code coverage",
            "Feature tests reviewed",
            "Feature tests pass",
            "Code integrated into master and build succeeds",
            "Versions updated",
            "Configurations updated",
            "Swagger file needed.",
            "Manual testing performed and pass",
        ],
        "labels": [],
        "cover": {"color": "blue", "brightness": "light", "size": "normal"},
    },
    "Documentation (rst file)": {
        "desc": """## Summary

Document the functions and the file modules for `TEST` using docstring.

Example for documenting code with docstring

```python
def send_message(sender, recipient, message_body, priority=1) -> int:
   \"\"\"
   Send a message to a recipient.

   :param str sender: The person sending the message
   :param str recipient: The recipient of the message
   :param str message_body: The body of the message
   :param int priority: The priority of the message, can be a number 1-5

   :return int the message id
   :raises ValueError: if the message_body exceeds 160 characters
   :raises TypeError: if the message_body is not a basestring
   \"\"\"
```

## Acceptance Criteria

- Module is documented.""",
        "checklist": "Development Tasks",
        "checkitems": [
            "Documentation is completed",
            "Code integrated into master and build succeeds",
            "Implementation covers every affected module, not only the primary one",
        ],
        "labels": ["Documentation"],
        "cover": {"color": "sky", "brightness": "light", "size": "normal"},
    },
    "Defect Template": {
        "desc": """## Summary

<add description of the defect>

## Environment

- enter the environment stg or prd

## Steps to Reproduce

- <enter step by step instructions to reproduce the defect>

## Current Behavior

<describe current behavior that is considered a defect>

## Expected Behavior

<describe the expected behavior that is considered valid>

## Discovery and Fix

<document findings and what was changed to fix the problem>""",
        "checklist": "Development Tasks",
        "checkitems": [
            "Fix Implemented including docstring",
            "Unit test that reproduces the problem",
            "Feature tests reviewed",
            "Feature tests pass",
            "Code integrated into master and build succeeds",
            "Versions updated",
            "Configurations updated",
            "Manual testing performed and pass",
            "Fix Implementation covers every affected module, not only the primary one",
        ],
        "labels": [],
        "cover": {"color": "red", "brightness": "light", "size": "normal"},
    },
    "Technical Debt": {
        "desc": """<add description of the technical debt here>

## Impact

<describe the impact of keeping the work the way it is today>

## Acceptance Criteria

<add acceptance criteria>""",
        "checklist": "Development Tasks",
        "checkitems": [
            "Implementation completed including docstring",
            "Unit tests pass with high code coverage",
            "Feature tests reviewed",
            "Feature tests pass",
            "Code integrated into master and build succeeds",
            "Versions updated",
            "Configurations updated",
            "Swagger file needed.",
            "Manual testing performed and pass",
            "Implementation covers every affected module, not only the primary one",
        ],
        "labels": [],
        "cover": {"color": "black", "brightness": "dark", "size": "normal"},
    },
    "Spike Template": {
        "desc": """## Summary

<add summary describing the spike>

## Goal

<define the goal of the spike as well as questions that must be answered>

## Questions

<define the goal of the spike as well as questions that must be answered>""",
        "checklist": "Tasks",
        "checkitems": [
            "Findings are documented",
            "Additional user stories entered",
        ],
        "labels": [],
        "cover": {"color": "yellow", "brightness": "light", "size": "normal"},
    },
    "Distraction": {
        "desc": """## Summary

<add a summary/description of the user story>

## Reason

<add reason for change in behavior>

## Impact

<describe possible impact of the change for the current functionality and who will affect>

## Acceptance Criteria

- <add list of criteria to be met to accept the story>""",
        "checklist": "Development Tasks",
        "checkitems": [
            "Implementation completed including docstring",
            "Unit tests pass with high code coverage",
            "Feature tests reviewed",
            "Feature tests pass",
            "Code integrated into master and build succeeds",
            "Versions updated",
            "Configurations updated",
            "Swagger file needed.",
            "Manual testing performed and pass",
            "Implementation covers every affected module, not only the primary one",
        ],
        "labels": [],
        "cover": {"color": "purple", "brightness": "light", "size": "normal"},
    },
}
