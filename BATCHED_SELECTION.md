# Batched Claim Selection - Implementation Summary

## What Changed

Replaced **per-sentence fact-checking** with **batched intelligent selection**.

### Before (Old Approach)
```
Every final sentence → Queue for fact-check → Process one by one
```
- ❌ Wastes API calls on greetings, opinions, filler
- ❌ Queue fills with irrelevant sentences  
- ❌ Important claims delayed behind junk

### After (New Approach)
```
Accumulate 10 sentences → LLM selects top 2 claims → Queue only those
```
- ✅ One LLM call processes 10 sentences
- ✅ Prioritizes important/controversial claims
- ✅ Filters out opinions, greetings, filler
- ✅ More efficient use of API quota

## Configuration

In `config.py`:
```python
claim_selection_batch_size: int = 10  # accumulate N sentences
max_claims_per_batch: int = 2         # select top N claims
```

Tune these based on:
- **Smaller batch** (5): More responsive, catches claims faster
- **Larger batch** (15): More context for better selection
- **More claims** (3): Less filtering, catches more
- **Fewer claims** (1): Very selective, only most important

## How It Works

### 1. Accumulation (state_manager.py)
```python
state.sentence_batch = []  # Stores recent final sentences
```

### 2. Selection (fact_engine.py)
When batch reaches size 10:
```python
async def select_claims(statements: List[str]) -> List[str]:
    # Single LLM call analyzes all statements
    # Returns top 2 most important factual claims
```

### 3. Queueing (main.py)
```python
selected_claims = await fact_engine.select_claims(batch)
for claim in selected_claims:
    await state.fact_queue.put(claim)  # Only queue selected ones
```

### 4. Processing (fact_engine.py)
Background worker processes selected claims through 3-step pipeline:
- Step 1: ~~Detect claim~~ (SKIPPED - already selected)
- Step 2: Search evidence
- Step 3: Verify claim

## Selection Criteria

The LLM selects claims that are:
- ✅ Specific and concrete (not vague)
- ✅ Verifiable (numbers, dates, events, facts)
- ✅ Potentially controversial or surprising
- ✅ About objective reality

Automatically filters out:
- ❌ Greetings ("Hello everyone")
- ❌ Opinions ("I think that's cool")
- ❌ Questions ("What do you mean?")
- ❌ Filler ("Um, let me see...")

## Files Modified

1. **config.py**
   - Added batch size and max claims settings
   - Added CLAIM_SELECTION_PROMPT import

2. **CLAIM_SELECTION_PROMPT.txt** (NEW)
   - Prompt for intelligent claim selection

3. **state_manager.py**
   - Added `sentence_batch` list

4. **fact_engine.py**
   - Added `select_claims()` method
   - Import CLAIM_SELECTION_PROMPT

5. **main.py**
   - Replaced `queue_fact_check_async()` call
   - Added `batch_claim_selection_async()` function
   - Old function kept for reference

## Testing

Run a test and observe the difference:
```bash
python main.py
# In another terminal:
python tests/test_simple_stream.py
```

You should see:
- Fewer claims being queued
- Only important/factual statements selected
- `claim_selected` events instead of `fact_queued`

## Next Steps for Tuning

1. **Adjust batch size** if claims arrive too slowly/quickly
2. **Adjust max claims** if too strict/lenient  
3. **Modify selection prompt** to change what counts as "important"
4. **Monitor via logs** which claims get selected vs ignored

## Expected Benefits

- 🚀 **5-10x reduction** in fact-check volume
- 💰 **Lower API costs** (fewer LLM + search calls)
- ⚡ **Faster processing** (queue doesn't back up)
- 🎯 **Better quality** (focus on what matters)
