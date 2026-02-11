1. Core Identity & Stack
Domain: Legal Tech / Business Process Automation.
Primary Stack: Python 3.12+ / Django 5.x / PostgreSQL.
Frontend: HTML5 + HTMX + Vanilla JS (for specific UX enhancements).
Styling: Vanilla CSS (No build step). Semantic class naming managed by LLM.
Third-Party Whitelist:
django-environ: For .env management.
django-extensions: For shell_plus and debugging tools.
whiteoise: For serving static files efficiently without Nginx complexity.
sentry-sdk: For error monitoring.
pytest-django: For the test runner.
2. Design Philosophies & Architectural Principles
Schema First: STRICT RULE. No UI or View logic begins until models.py is defined. Database integrity is the blocker.
Monolith Modularization:
Use a single core app for the majority of the logic to reduce overhead.
Folder-based separation: As files grow, split services.py into a services/ package (e.g., services/document_logic.py).
Service Layer Pattern:
Thin Views: Views only handle request reception and response rendering.
Rich Services: All business logic (calculations, external API calls, state transitions) lives in core/services/.
Inheritance Strategy: All models must inherit from core.models.TimeStampedModel (abstract base class with created_at, updated_at) to ensure auditability.
Testing ROI: Prioritize Integration Tests (End-to-End flows) over granular Unit Tests. Test the "Golden Path" (e.g., User creates Case -> Case Saved -> Email Sent).
3. The "Agentic" Workflow Rules (Internal Protocol)
A. The "Dry Run" Harness
Before marking a feature "Done," the Agent must create a Management Command (core/management/commands/test_feature_name.py).
This command must manually run the new Service logic with dummy data and print the results to the console.
Why? It proves the code runs in the Django environment without requiring a full browser click-test.

Principles: 
Fail Loudly! Don't fall back into errors, declare the errors and stop the flow so we can find them