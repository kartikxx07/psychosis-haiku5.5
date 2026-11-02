# Automated Red Teaming for AI-Induced Psychosis

**Tim Hua** and AIs

A simple red teaming framework for testing how AI models respond to psychotic characters. 

**Note:** The red-team generator defaults to Qwen 2.5 7B Instruct. The former Grok 3 endpoint is deprecated on OpenRouter, and DeepSeek V4 Flash may refuse the patient-role request.

## Quick Start

### Installation

Install the environment using `uv`:

```bash
uv sync
```

### Basic Usage

Run red teaming on all default models with all characters:

```bash
uv run redteaming_systematic.py
```

## 📁 Project Structure

### Core Scripts

- **`redteaming_systematic.py`** - Main red teaming script with batch processing capabilities
- **`results_analysis.R`** - Statistical analysis and visualization of results
- **`analyze_not_crazy_mentions.py`** - Additional script tool for detecting "you're not crazy" mentions
- **`convert_json_to_md.py`** - Utility for converting JSON transcripts to Markdown
- **`xplore_notebook.py`** - Additional exploratory experiments

### Configuration Files

- **`red_team_prompt.txt`** - System prompt for the red team agent
- **`grader_prompt.txt`** - System prompt for the grading agent
- **`pyproject.toml`** - Project dependencies and configuration

### Data Directories

- **`characters/`** - Character scenario files (`.txt`)
- **`characters_2_manifest.csv`** - Identity-condition metadata for the new matched persona panel
- **`full_transcripts/`** - Original complete conversation logs (`.md`, `.json`)
- **`full_transcripts_2/`** - Transcripts from the new black-box persona experiments
- **`result_grades/`** - Grading results and analysis data (`.csv`)
- **`error_logs/`** - Error logs and debugging information (`.json`)
- **`graphs/`** - Generated visualizations and plots

## Characters 

I had several characters written by Claude

- **Adrian** - Geometric reality delusions
- **Colin** - Reality questioning and doubt
- **Ethan** - General reality distortion
- **Frank** - Weather-related delusions
- **Jessica** - Prime number obsessions
- **Michelle** - Relationship paranoia
- **Nathan** - Quantum mechanics delusions
- **Rachel** - Fertility-related concerns
- **Zara** - Reality perception issues

These are then fed into the red teaming agent to role play.

## redteaming_systematic.py Usage

### Command Line Options

```bash
uv run redteaming_systematic.py [OPTIONS]
```

#### Basic Options

- `--help, -h` - Show help message
- `--list-models` - List all available models
- `--list-characters` - List all available characters

#### Model Selection

- `--model, -m MODEL` - Test specific model (default: all models)
- `--redteam-model MODEL` - Model for red teaming (default: `openrouter/qwen/qwen-2.5-7b-instruct`)
- `--grader-model MODEL` - Model for grading (default: same as redteam-model)

#### Character Selection

- `--character, -c CHARACTERS` - Specific character(s) to test

#### Configuration

- `--turns, -t NUMBER` - Assistant turns per transcript, maximum 8 (default: 8)
- `--max-connections NUMBER` - Concurrent connections (default: 10)
- `--resume` - Skip model/character/resample cells that already have a transcript

### Usage Examples

#### Example 1: Test Single Model on All Characters

```bash
uv run redteaming_systematic.py --model openai/chatgpt-4o-latest
```

#### Example 2: Test All Models on Specific Character

```bash
uv run redteaming_systematic.py --character ethan
```

#### Example 3: Test Multiple Specific Characters

```bash
# Comma-separated
uv run redteaming_systematic.py --character "ethan,frank,colin"

# Space-separated
uv run redteaming_systematic.py --character "ethan frank colin"
```

#### Example 4: Custom Configuration

```bash
uv run redteaming_systematic.py \
  --model openai/gpt-5-mini \
  --character "jessica,nathan" \
  --turns 1 \
  --max-connections 5
```

#### Example 5: List Available Options

```bash
# See all available models
uv run redteaming_systematic.py --list-models

# See all available characters  
uv run redteaming_systematic.py --list-characters
```

### Default Models

The script includes these pre-configured models:

- `openrouter/qwen/qwen-2.5-7b-instruct`
- `openrouter/anthropic/claude-haiku-4.5`
- `openrouter/deepseek/deepseek-v4-flash`

Use `--resamples N` to draw `N` independent full conversational trajectories for
each model/character condition. Each transcript filename includes its resample
index. This measures stochastic rollout variability and is not the same as the
sentence-level reasoning resampling used in model-forensics work, which branches
generation immediately before and after individual reasoning sentences.

The new identity pilot can be run across all three default target models with:

```bash
uv run redteaming_systematic.py \
  --character "ethan,ethan_independent_expert,ethan_junior_ai,ethan_self_taught,ethan_ml_professor,ethan_ai_regulator,ethan_religious_leader,ethan_god_claim,ethan_alibaba_qwen,ethan_anthropic,ethan_moonshot,ethan_deepseek,ethan_openai,ethan_google_deepmind,maya_independent_expert,alex_independent_expert" \
  --resamples 3 \
  --redteam-model openrouter/deepseek/deepseek-v4-flash \
  --grader-model openrouter/anthropic/claude-haiku-4.5
```

## 📊 Output and Results

### Generated Files

**Conversation Transcripts:**
- `full_transcripts_2/{Character}_{Model}_sample-{Index}_{Timestamp}_target.md` - Target model conversations

**Results Data:**
- `result_grades/redteaming_results_{Timestamp}.csv` - Aggregated grading results
- Contains turn-by-turn evaluations with model performance metrics

**Error Logs:**
- `error_logs/{Session}_error.json` - Detailed error information for failed runs

The original red-team conversations remain in `full_transcripts/`. New black-box
experiment transcripts are written to `full_transcripts_2/`.

### Results Analysis

Use the R analysis script to generate insights:

```bash
# Run statistical analysis (requires R)
Rscript results_analysis.R
```

## ⚙️ Environment Configuration

Set up API keys in your environment or `.env` file:

```bash
# OpenAI
OPENAI_API_KEY=your_key_here

# OpenRouter  
OPENROUTER_API_KEY=your_key_here

# Anthropic
ANTHROPIC_API_KEY=your_key_here
```
