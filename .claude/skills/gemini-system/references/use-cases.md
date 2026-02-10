# Gemini CLI Use Cases

## Use Case Categories

### 1. Pre-Implementation Research

Before implementing a new feature, use Gemini to research best practices.

```bash
# General research
gemini -p "Research best practices for implementing OAuth2 in Python.
Include:
- Recommended libraries (compare authlib vs python-oauth2 vs others)
- Security considerations
- Common pitfalls to avoid
- Example implementations" 2>> .claude/logs/cli-tools.stderr.log

# Framework-specific research
gemini -p "Research FastAPI authentication patterns in 2025.
Focus on:
- JWT vs session-based auth
- Dependency injection patterns
- Testing strategies" 2>> .claude/logs/cli-tools.stderr.log
```

### 2. Repository-Wide Understanding

Leverage the 1M token context window for comprehensive codebase analysis.

```bash
# Full repository analysis
gemini -p "Analyze this entire codebase and provide:
1. Architecture diagram (describe in text)
2. Module dependency graph
3. Key abstractions and their purposes
4. Suggested areas for improvement" --include-directories src,lib,tests 2>> .claude/logs/cli-tools.stderr.log

# Specific aspect analysis
gemini -p "Trace the data flow for user authentication:
- Entry points (API endpoints)
- Middleware processing
- Database interactions
- Response formatting" --include-directories src 2>> .claude/logs/cli-tools.stderr.log
```

### 3. Multimodal Data Analysis

#### Video Analysis

```bash
# Tutorial video analysis
gemini -p "Analyze this tutorial video:
- Summarize the main concepts taught
- List step-by-step instructions
- Note any important warnings or tips
- Identify timestamps for key sections" --file "tutorial.mp4" 2>> .claude/logs/cli-tools.stderr.log

# Code review video
gemini -p "Extract code patterns and best practices demonstrated in this video" --file "code-review.mp4" 2>> .claude/logs/cli-tools.stderr.log
```

#### Audio Analysis

```bash
# Meeting recording
gemini -p "Transcribe and summarize this technical discussion:
- Key decisions made
- Action items
- Open questions
- Technical terms mentioned" --file "meeting.mp3" 2>> .claude/logs/cli-tools.stderr.log

# Podcast/talk analysis
gemini -p "Extract technical insights from this talk about {topic}" --file "conference-talk.mp3" 2>> .claude/logs/cli-tools.stderr.log
```

#### PDF Analysis

```bash
# API documentation
gemini -p "Extract from this API documentation:
- All available endpoints
- Request/response schemas
- Authentication requirements
- Rate limiting rules" --file "api-spec.pdf" 2>> .claude/logs/cli-tools.stderr.log

# Technical specification
gemini -p "Summarize this technical specification:
- Core requirements
- Constraints
- Interface definitions
- Edge cases to handle" --file "spec.pdf" 2>> .claude/logs/cli-tools.stderr.log

# Research paper
gemini -p "Analyze this paper and explain:
- Problem being solved
- Proposed approach
- Key algorithms
- How to apply this in practice" --file "paper.pdf" 2>> .claude/logs/cli-tools.stderr.log
```

### 4. Documentation & Web Research

```bash
# Latest documentation
gemini -p "Find and summarize the latest React 19 features and migration guide from official docs" 2>> .claude/logs/cli-tools.stderr.log

# Compare libraries
gemini -p "Compare these Python HTTP clients in 2025:
- httpx vs aiohttp vs requests
- Performance benchmarks
- Feature comparison
- Community activity" 2>> .claude/logs/cli-tools.stderr.log

# Troubleshooting
gemini -p "Research common causes and solutions for: {error message}
Search Stack Overflow, GitHub Issues, and official docs" 2>> .claude/logs/cli-tools.stderr.log
```

### 5. Code Migration Analysis

```bash
# Framework migration
gemini -p "Analyze our codebase for Django to FastAPI migration:
- Identify all Django-specific patterns used
- Map to FastAPI equivalents
- Estimate migration complexity per module
- Suggest migration order" --include-directories src 2>> .claude/logs/cli-tools.stderr.log

# Version upgrade
gemini -p "Research breaking changes from Python 3.11 to 3.13.
Cross-reference with our codebase to identify:
- Deprecated features we use
- New features we could adopt
- Required changes" --include-directories . 2>> .claude/logs/cli-tools.stderr.log
```

## When NOT to Use Gemini

| Task | Reason | Use Instead |
|------|--------|-------------|
| Design decisions | Requires deep reasoning | Codex |
| Code implementation | Codex has better code abilities | Codex |
| Debugging | Requires logical analysis | Codex |
| Simple file edits | Overkill | Claude Code directly |
| Running tests | Execution task | Claude Code directly |

## Output Handling

### JSON Output for Structured Data

```bash
gemini -p "List all API endpoints in this codebase with their HTTP methods" \
  --output-format json 2>> .claude/logs/cli-tools.stderr.log
```

### Piping to Files

```bash
gemini -p "Generate comprehensive documentation for src\\auth\" \
  --include-directories src\\auth 2>> .claude/logs/cli-tools.stderr.log > docs\\auth-module.md
```

## Rate Limits

Free tier (personal Google account):
- 60 requests/minute
- 1,000 requests/day

Plan accordingly for large research tasks.
