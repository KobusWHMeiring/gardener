PRD Phase 2: Voice-to-Action Pipeline
1. Problem Statement
Typing on a phone while gardening is impractical due to dirty hands and glare. The current text-only ingestion is a friction point. Users need to "dump" raw thoughts via voice and trust the system to filter the noise and structure the data.
2. Strategic Goal
Enable "One-Shot" Audio Ingestion. The user records once; the system handles transcription, noise cleaning, and data extraction in a single pass, populating the existing IngestQueue.
3. Proposed Scope
In Scope:
UI: A "Record" button on the Dashboard using standard HTML5 MediaRecorder API.
Backend: Update IngestQueue to store .webm/.ogg audio files.
AI: Update enrich_service to send audio binaries to Gemini.
Prompt Strategy: "Chain-of-Thought" extraction (Transcribe -> Clean -> Structure) in one JSON payload.
Out of Scope (For Now):
WhatsApp/Telegram integration (Deferred).
Real-time streaming transcription (We will use "Record -> Stop -> Upload").
4. UX/UI Concept
The Floating Action Button (FAB): A Microphone icon sits fixed at the bottom right.
The Interaction:
Tap Mic -> Modal opens.
Tap "Record" -> Visual waveform/timer.
Tap "Done" -> Modal closes instantly.
Feedback: A small "Toast" message appears: "Uploading Voice Note..." -> "Processing...".
The Result: The Inbox list refreshes (HTMX). The card shows:
Raw: "Uhh, ok, watered the tomatoes."
Extracted: Action: Water | Target: Tomatoes.
5. Technical Implementation (Schema & Logic)
Step A: Schema Update (core/models.py)
Update IngestQueue to support the hybrid nature of inputs:
code
Python
class IngestQueue(TimeStampedModel):
    # Existing fields...
    audio_file = models.FileField(upload_to='ingest/audio/', null=True, blank=True)
    transcript_clean = models.TextField(blank=True, help_text="AI cleaned version (no fluff)")
    # We keep raw_text for the verbatim transcript
Step B: The "One-Shot" Prompt Strategy
We will wrap your specific logic into a structure that forces Gemini to do the "cleaning" pass first.
System Prompt Structure:
code
Text
You are an expert garden assistant. You will receive an audio file. 
Perform these steps internally:
1. Transcribe the audio verbatim.
2. Clean the text: Remove filler words ("um", "uh"), greetings, and non-garden context.
3. Extract structured data based on the CLEANED text using the rules below.

Return JSON ONLY:
{
  "transcript_raw": "String",
  "transcript_clean": "String",
  "payload": { 
     // ... Insert your exact JSON structure here (event_date, actions, etc) ...
  }
}
Step C: The View Logic
IngestCreateView: Needs to handle request.FILES.
HTMX: The form will use hx-encoding="multipart/form-data".


User Stories

  Title: User Story [01]: Developer - Database Schema Expansion for Audio
  Narrative: As a Developer, I want to update the IngestQueue model to store audio files and cleaned transcripts, so that the system can handle non-textual inputs.
  Acceptance Criteria (AC):
   * Add audio_file field to IngestQueue model in core/models.py (use models.FileField with upload_to='ingest/audio/').
   * Add transcript_clean field (models.TextField, blank=True) to store the AI-refined version of the audio.
   * Ensure migrations are generated and applied.
   * Update admin.py to display the audio file player in the Django Admin for debugging.
  Technical Implementation Notes:
   * Modify core/models.py.
   * The raw_text field will serve as the "Verbatim Transcript" while transcript_clean holds the "Cleaned" version.

  Title: User Story [02]: Developer - Multi-Modal Ingestion Service
  Narrative: As a Developer, I want to update the ingest_media service to handle incoming audio binaries, so that the ingestion pipeline is format-agnostic.
  Acceptance Criteria (AC):
   * Modify core/services/ingestion.py:ingest_media to accept an optional audio_file argument.
   * If an audio_file is provided, create an IngestQueue record with the file and set an initial status (e.g., QUEUED).
   * Trigger the enrich_ingest_item task immediately after saving.
  Technical Implementation Notes:
   * Reference core/services/ingestion.py.
   * Ensure file naming handles collisions (Django's default FileField does this, but keep it in mind).

  Title: User Story [03]: Developer - Gemini Audio-to-Structured-Data Logic
  Narrative: As a Developer, I want to update the enrichment service to send audio files to Gemini, so that we can extract structured garden actions from speech.
  Acceptance Criteria (AC):
   * Update core/services/enrichment.py:enrich_ingest_item to detect if an audio_file exists on the record.
   * If audio exists, use the Gemini API's multimodal capabilities to send the file.
   * Update the System Prompt to include the "Chain-of-Thought" instruction: (1) Transcribe, (2) Clean, (3) Extract JSON.
   * Map the returned transcript_raw to IngestQueue.raw_text and transcript_clean to IngestQueue.transcript_clean.
   * Populate the payload field with the extracted actions as per existing schema.
  Technical Implementation Notes:
   * You will need to use google-generativeai library's file upload method or pass the bytes directly if small enough.
   * Reference core/services/enrichment.py.

  Title: User Story [04]: Developer - Frontend Audio Recorder (HTMX/JS)
  Narrative: As a Gardener, I want a simple microphone button on the dashboard, so that I can record notes without typing.
  Acceptance Criteria (AC):
   * Add a Floating Action Button (FAB) with a microphone icon to core/templates/core/dashboard.html.
   * Implement a Modal (using vanilla CSS/JS) that triggers on click.
   * Use the MediaRecorder API to capture audio.
   * Provide visual feedback during recording (e.g., a simple "Recording..." text or pulse animation).
   * On "Stop", immediately POST the audio blob to /ingest/ using FormData and htmx.ajax or a standard fetch that triggers an HTMX swap.
  Technical Implementation Notes:
   * Target audio/webm or audio/mp4 depending on browser support.
   * Update core/views.py:ingest_view to handle request.FILES.

  Title: User Story [05]: Developer - Inbox UI Refinement for Audio
  Narrative: As a Gardener, I want to see if an item was created via voice in my inbox, so that I can understand why the transcript might be "fuzzy".
  Acceptance Criteria (AC):
   * Update core/templates/core/partials/inbox_card.html to display a "Speaker" icon if the item has an audio_file.
   * If transcript_clean is available, display it prominently; otherwise, show raw_text.
   * Ensure the "Confirm" flow still works perfectly with the AI-extracted data from the audio payload.
  Technical Implementation Notes:
   * Modify core/templates/core/partials/inbox_card.html.
   * Add a simple conditional check: {% if item.audio_file %} ... {% endif %}.

User Story [06]: Frontend - Cross-Browser Audio Support (iOS/Safari)
Narrative
As a Gardener using an iPhone, I want the audio recorder to automatically select a supported file format (like MP4/AAC), so that my recordings are actually captured and not rejected by the browser or server.
Acceptance Criteria (AC)
Dynamic MIME Detection: Implement a JavaScript helper function getSupportedMimeType() in the Dashboard script.
Priority 1: Check audio/mp4 (Standard for iOS/Safari).
Priority 2: Check audio/webm;codecs=opus (High quality for Chrome/Firefox).
Priority 3: Check audio/webm (Standard Fallback).
Priority 4: Empty string (Let the browser use its default).
Recorder Initialization: The MediaRecorder instance must be initialized using this dynamically detected type.
File Extension Logic: When constructing the FormData to send to the server, ensure the filename extension matches the detected type (e.g., recording.mp4 vs recording.webm) so the backend (and Gemini) can identify it correctly.
Error Handling: If MediaRecorder fails to initialize (e.g., on an old browser), display a visible alert: "Microphone not supported on this browser."
Technical Implementation Notes
Files: core/templates/core/dashboard.html (or the specific JS file included there).
Code Snippet Logic:
code
JavaScript
const types = ['audio/mp4', 'audio/webm;codecs=opus', 'audio/webm'];
const selectedType = types.find(type => MediaRecorder.isTypeSupported(type)) || '';

User Story [07]: Tooling - "Live Fire" Verification Command
Narrative
As a Developer, I want to run a manual command that sends a real audio file to the live Gemini API and creates real database records, so that I can verify the integration works end-to-end without relying on "fake" mocks that might hide actual API issues.
Acceptance Criteria (AC)
Command Creation: Create a new Django management command: core/management/commands/verify_voice_pipeline.py.
Input: The command should accept a file path argument (e.g., --file ./test_audio/garden_note.m4a). If no file is provided, it should error out or use a default test file in fixtures/.
Process:
Create a temporary IngestQueue record with the file.
Call the actual enrich_ingest_item service (no mocking).
Wait for the response.
Output: Print a detailed report to the console:
Transcribed Text: (What did Gemini hear?)
Cleaning Status: (Did it remove "Ums/Ahs"?)
Extracted Data: (The JSON payload).
Database ID: The ID of the created record.
Flags: Add a --dry-run flag which sends the data to Gemini but rolls back the database transaction, keeping the DB clean while testing the API.
Technical Implementation Notes
Files: core/management/commands/verify_voice_pipeline.py.
Usage: python manage.py verify_voice_pipeline --file my_voice_note.m4a
Validation: This replaces the need for "Integration Tests" in the CI pipeline. You run this manually after any change to the Prompts or API keys to ensure truth.


## Format: Implementation Summary
- **Stories [01]-[07]: Complete**. 
- The Voice-to-Action pipeline is fully integrated from frontend recording to AI-enriched multi-action processing, with cross-browser support and verification tools.

### File Manifest (Critical)
- `core/models.py`: Expanded `IngestQueue` schema.
- `core/admin.py`: Added audio playback support.
- `core/services/ingestion.py`: format-agnostic ingestion logic.
- `core/services/enrichment.py`: Multimodal Gemini 2.0 Flash integration with dynamic MIME detection.
- `core/views.py`: Handled multipart audio uploads and context injection.
- `core/templates/core/dashboard.html`: Added FAB and recording UX with dynamic MIME support (iOS/Chrome/Firefox).
- `core/templates/core/partials/inbox_card.html`: Updated for voice-first display.
- `core/management/commands/test_voice_pipeline.py`: Verification tool (text-only).
- `core/management/commands/verify_voice_pipeline.py`: "Live Fire" verification tool (real audio).

### Technical Debt & Risks (The "Confessional")
- **Browser Compatibility**: Addressed in Story [06] with dynamic MIME detection. Tested with `audio/mp4` and `audio/webm`.
- **Large Files**: Bytes are read directly into memory for Gemini. This is safe for 10-20 second clips but will fail for long-form dictation.
- **Context Synchronization**: The `ingest_view` manually replicates context from `DashboardView`. If more dropdowns are added to the dashboard, they must be added to the ingest partial view as well.

### Action Suggestions
- Add a "Browser Compatibility" refactor story to detect supported MIME types for MediaRecorder.
- Add a "Gemini File API" story for handling large audio files if users start recording long sessions.

### Learnings
- **One-Shot JSON**: Grouping transcription and extraction into a single AI prompt significantly reduces the "Processing..." wait time for the user.
- **HTMX + AJAX**: Using `htmx.ajax` to send `FormData` is a clean way to handle manual JS interactions (like recording) while staying within the HTMX ecosystem.
