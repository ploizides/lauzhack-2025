# Feature Port Guide: Topic Tracking & Batched Claim Selection

**Purpose:** Guide for porting features from `unrefactored_mvp_backend` to refactored codebase

**Date Created:** 2025-11-23

---

## 🎯 Features to Port

### 1. **Batched Claim Selection** (instead of per-sentence fact-checking)
### 2. **Topic Tree with Reuse Detection** (detect returning to previous topics)
### 3. **Image Search for Topics** (visual aids for conversation)
### 4. **Topic Path Tracking** (sequential history)
### 5. **Enhanced Search Query Generation** (better fact-check searches)

---

## 📊 Feature 1: Batched Claim Selection

### **What It Does**
Instead of fact-checking every final sentence, accumulates sentences into batches and uses LLM to select the most important claims.

### **Why**
- Reduces API calls (10 sentences → 1 LLM call)
- Better context for claim detection
- Filters out non-factual content (greetings, opinions, questions)

### **Key Components**

#### A. Configuration (`config.py`)
```python
# New settings
claim_selection_batch_size: int = 10  # Accumulate 10 sentences
max_claims_per_batch: int = 2  # Select top 2 claims per batch

# New prompt file to load
CLAIM_SELECTION_PROMPT = Path("CLAIM_SELECTION_PROMPT.txt").read_text()
```

#### B. Prompt File (`CLAIM_SELECTION_PROMPT.txt`)
```
You are analyzing a conversation transcript to identify important factual claims worth fact-checking.

Here is the recent conversation:

{text}

Your task:
1. Identify VERIFIABLE FACTUAL CLAIMS in this conversation
2. Prioritize claims that are:
   - Specific and concrete (numbers, dates, events, names)
   - Potentially controversial or surprising
   - About objective facts that can be verified
3. Extract up to {max_claims} complete claims with enough context

DO NOT select:
- Pure opinions ("I think...", "I feel...")
- Vague statements without specifics
- Greetings or filler words
- Questions

Important: Extract the FULL CLAIM with context, not just fragments.

Respond in JSON format:
{{
    "selected_claims": [
        {{
            "claim": "the complete factual claim with sufficient context",
            "reason": "why this is important to verify"
        }}
    ]
}}

If no important factual claims exist, return: {{"selected_claims": []}}
```

**Note:** Double braces `{{` because Python `.format()` is used

#### C. State Manager (`state_manager.py`)
```python
class StateManager:
    def __init__(self):
        # ... existing fields ...
        self.sentence_batch: List[str] = []  # NEW: Accumulate sentences
```

#### D. Fact Engine (`fact_engine.py`)
```python
class FactEngine:
    async def select_claims(self, statements: List[str]) -> List[str]:
        """
        Select the most important factual claims from a batch.
        
        Args:
            statements: List of recent statements (10 sentences)
            
        Returns:
            List of selected claims (with full context)
        """
        # 1. Concatenate statements into paragraph
        full_text = " ".join(statements)
        
        # 2. Format prompt
        prompt = CLAIM_SELECTION_PROMPT.format(
            text=full_text,
            max_claims=settings.max_claims_per_batch
        )
        
        # 3. Call LLM
        response = self.client.chat.completions.create(
            model=settings.together_model,
            messages=[
                {"role": "system", "content": "You are a claim selection assistant. Always respond in valid JSON format."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=400,
        )
        
        # 4. Parse JSON response
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        
        result = json.loads(content)
        selected = [claim["claim"] for claim in result.get("selected_claims", [])]
        
        # 5. Print selected claims
        if selected:
            print(f"✅ SELECTED CLAIMS:")
            for claim in selected:
                print(f"   • {claim}")
            print()
        
        return selected
```

#### E. Main WebSocket Handler (`main.py`)
```python
async def batch_claim_selection_async(websocket: WebSocket, sentence: str):
    """
    Accumulate sentences and select claims when batch is full.
    
    Called for each final sentence.
    """
    try:
        # Add sentence to batch
        state.sentence_batch.append(sentence)
        
        # Check if batch is full
        if len(state.sentence_batch) >= settings.claim_selection_batch_size:
            # Print batch
            batch_text = " ".join(state.sentence_batch)
            print(f"\n📋 BATCH: {batch_text}\n")
            
            # Select important claims
            selected_claims = await fact_engine.select_claims(state.sentence_batch)
            
            # Queue selected claims for fact-checking
            for claim in selected_claims:
                await state.fact_queue.put(claim)
                
                # Notify client
                await websocket.send_json({
                    "type": "claim_selected",
                    "claim": claim,
                    "queue_size": state.fact_queue.qsize(),
                })
            
            # Clear batch
            state.sentence_batch.clear()
            
    except Exception as e:
        logger.error(f"Error in batch claim selection: {e}")


# In the Deepgram message handler:
if is_final:
    asyncio.create_task(batch_claim_selection_async(websocket, sentence))
```

---

## 📊 Feature 2: Enhanced Search Query Generation

### **What It Does**
Generates optimized search queries from claims using LLM before web search.

### **Why**
- Raw claims are often verbose: "eighty percent not maybe ninety percent of the funding goes to democrats"
- Optimized queries find better results: "political funding distribution democrats republicans percentage"

### **Implementation**

```python
class FactEngine:
    async def _generate_search_query(self, claim: str) -> str:
        """
        Generate an optimized search query from a claim.
        """
        prompt = f"""Convert this claim into an optimized web search query.

Claim: {claim}

Instructions:
1. Extract the CORE FACTUAL ASSERTION (remove filler, opinions, context)
2. Identify KEY ENTITIES (names, organizations, places, numbers, dates)
3. Create a concise search query (3-8 words) that will find relevant evidence

Examples:
- Claim: "eighty percent not maybe ninety percent of the funding goes to the democrats"
  Query: "political funding distribution democrats republicans percentage"
  
- Claim: "ninety percent of the money is going to your opponents"
  Query: "campaign finance political party funding distribution"

Output ONLY the search query, nothing else."""

        response = self.client.chat.completions.create(
            model=settings.together_model,
            messages=[
                {"role": "system", "content": "You are a search query optimization assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=50,
        )
        
        search_query = response.choices[0].message.content.strip().strip('"\'')
        return search_query

    async def search_evidence(self, claim: str, max_results: int = None) -> List[Dict]:
        """
        Search for evidence using DuckDuckGo.
        """
        # Generate optimized query
        search_query = await self._generate_search_query(claim)
        print(f"🔍 Search query: {search_query}")
        
        # Run search
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            lambda: list(
                self.search_client.text(
                    search_query,  # Use optimized query
                    region="wt-wt",
                    safesearch="moderate",
                    max_results=max_results or 5,
                )
            ),
        )
        
        return results
```

---

## 📊 Feature 3: Topic Tree with Reuse Detection

### **What It Does**
- Creates unique topics (no duplicates)
- Detects when conversation returns to previous topics
- Links topics linearly (temporal DAG)
- Tracks sequential path through topics

### **Why**
- Avoids duplicate topics: "Solar Energy" appears twice → reuse same node
- Shows conversation flow: T1 → T2 → T1 → T3
- Maintains clean DAG structure

### **Key Changes**

#### A. State Manager (`state_manager.py`)
```python
class StateManager:
    def __init__(self):
        # ... existing ...
        self.topic_path: List[str] = []  # NEW: Sequential history ["topic_0", "topic_1", "topic_0"]
    
    def add_topic_node(self, topic: str, keywords: List[str], timestamp: datetime) -> str:
        """
        Add NEW topic node (only called for unique topics).
        Always links to current_topic (temporal chain).
        """
        topic_id = f"topic_{self.topic_counter}"
        self.topic_counter += 1
        
        node = TopicNode(topic=topic, keywords=keywords, timestamp=timestamp, sentence_count=1)
        self.topic_tree.add_node(topic_id, data=node)
        
        # Link to current topic (temporal edge)
        if self.current_topic_id is not None:
            self.topic_tree.add_edge(self.current_topic_id, topic_id)
        
        # Update path and current
        self.topic_path.append(topic_id)
        self.current_topic_id = topic_id
        return topic_id
    
    def switch_to_topic(self, topic_id: str) -> None:
        """
        Switch to existing topic (no new edges created).
        """
        if topic_id in self.topic_tree.nodes:
            self.current_topic_id = topic_id
            self.topic_path.append(topic_id)  # Record in path
            
            # Increment sentence count
            node_data = self.topic_tree.nodes[topic_id]["data"]
            node_data.sentence_count += 1
```

#### B. Topic Engine (`topic_engine.py`)
```python
class TopicEngine:
    def find_existing_topic(self, new_topic: str) -> Optional[str]:
        """
        Check if topic already exists (similarity >= threshold).
        
        Returns:
            topic_id if match found, None otherwise
        """
        if len(state.topic_tree.nodes) == 0:
            return None
        
        for topic_id in state.topic_tree.nodes:
            node_data = state.topic_tree.nodes[topic_id]["data"]
            topic_text = node_data.topic
            
            similarity = self.compute_similarity(topic_text, new_topic)
            
            if similarity >= TOPIC_CONFIG["similarity_threshold"]:  # Usually 0.7
                logger.info(f"Found existing topic: '{topic_text}' (similarity: {similarity:.2f})")
                return topic_id
        
        return None
    
    def detect_topic_shift(self, new_topic: str) -> Tuple[bool, Optional[str]]:
        """
        Check if topic is new or existing.
        
        Returns:
            (is_new_topic, existing_topic_id)
        """
        existing_id = self.find_existing_topic(new_topic)
        
        if existing_id:
            return (False, existing_id)  # Reuse existing
        else:
            return (True, None)  # Create new
    
    async def update_topic_tree(self, text: str) -> Optional[str]:
        """
        Update topic tree based on new text.
        """
        # Extract topic and keywords
        result = await self.extract_topic(text)
        if result is None:
            return None
        
        topic, keywords = result
        
        # Check if existing
        is_new_topic, existing_topic_id = self.detect_topic_shift(topic)
        
        if is_new_topic:
            # Create new node
            topic_id = state.add_topic_node(topic, keywords, datetime.now())
            logger.info(f"New topic: {topic} (id={topic_id})")
            
            # Start image search (background)
            asyncio.create_task(self._search_and_record_image(topic_id, topic, keywords))
            
            return topic_id
        else:
            # Switch to existing
            state.switch_to_topic(existing_topic_id)
            logger.info(f"Returning to existing topic: {topic} (id={existing_topic_id})")
            return existing_topic_id
```

#### C. JSON Export Structure
```json
{
  "nodes": [
    {"id": "topic_0", "topic": "Solar Energy", ...},
    {"id": "topic_1", "topic": "AI Future", ...},
    {"id": "topic_2", "topic": "Space", ...}
  ],
  "edges": [
    {"source": "topic_0", "target": "topic_1"},
    {"source": "topic_1", "target": "topic_2"}
  ],
  "topic_path": ["topic_0", "topic_1", "topic_0", "topic_2"],
  "metadata": {...}
}
```

**Key Insight:** 
- `edges` = temporal creation order (DAG, only when new topic created)
- `topic_path` = actual conversation flow (includes returns to previous topics)

---

## 📊 Feature 4: Image Search for Topics

### **What It Does**
Searches DuckDuckGo for relevant images when new topics are created.

### **Why**
Provides visual aids for speakers during conversation.

### **Implementation**

#### A. State Manager
```python
class StateManager:
    def __init__(self):
        # ... existing ...
        self.topic_images: List[Dict[str, Optional[str]]] = []  # NEW
    
    def add_topic_image(self, topic_id: str, topic: str, image_url: Optional[str]) -> None:
        """
        Record image URL for a topic (called after async search completes).
        """
        self.topic_images.append({
            "topic_id": topic_id,
            "topic": topic,
            "image_url": image_url
        })
```

#### B. Topic Engine
```python
class TopicEngine:
    def __init__(self):
        # ... existing ...
        self.search_client = DDGS()  # NEW: For image search
    
    async def search_topic_image(self, topic: str, keywords: List[str]) -> Optional[str]:
        """
        Search for relevant image.
        
        Returns:
            Image URL or None
        """
        try:
            # Create query from topic + keywords
            search_terms = [topic] + keywords[:3]
            query = " ".join(search_terms)
            
            print(f"🖼️  Searching image for: {query}")
            
            # Run in thread pool
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: list(
                    self.search_client.images(
                        query,  # Positional arg (not keywords=)
                        region="wt-wt",
                        safesearch="moderate",
                        max_results=3,
                    )
                ),
            )
            
            if results and len(results) > 0:
                image_url = results[0].get("image")
                if image_url:
                    print(f"✅ Found image: {image_url[:80]}...")
                    return image_url
            
            return None
            
        except Exception as e:
            logger.error(f"Image search failed: {e}")
            return None
    
    async def _search_and_record_image(self, topic_id: str, topic: str, keywords: List[str]) -> None:
        """
        Background task: search image and record result.
        """
        try:
            image_url = await self.search_topic_image(topic, keywords)
            state.add_topic_image(topic_id, topic, image_url)
        except Exception as e:
            logger.error(f"Failed to search/record image: {e}")
            state.add_topic_image(topic_id, topic, None)
```

#### C. JSON Export
```json
{
  "topic_images": [
    {
      "topic_id": "topic_0",
      "topic": "Kardashev Scale",
      "image_url": "https://example.com/image.jpg"
    },
    {
      "topic_id": "topic_1",
      "topic": "Solar Energy",
      "image_url": null
    }
  ]
}
```

#### D. WebSocket Updates
```python
# Send image URL to client
await websocket.send_json({
    "type": "topic_update",
    "topic_id": topic_id,
    "current_topic": topic_node.topic,
    "image_url": image_url,  # NEW
    "total_topics": len(state.topic_tree.nodes),
})
```

---

## 🔧 Configuration Summary

### Required Settings (`config.py`)
```python
class Settings(BaseSettings):
    # Existing...
    deepgram_api_key: str
    together_api_key: str
    together_model: str = "meta-llama/Llama-3.1-70B-Instruct-Turbo"
    
    # NEW: Batched claim selection
    claim_selection_batch_size: int = 10
    max_claims_per_batch: int = 2
    
    # Existing topic settings
    topic_update_threshold: int = 5  # sentences before topic update
    
    # Existing fact-check settings
    fact_check_rate_limit: int = 10  # seconds between fact checks

# Topic similarity threshold (usually in TOPIC_CONFIG dict)
TOPIC_CONFIG = {
    "similarity_threshold": 0.7,  # For topic reuse detection
    # ... other settings ...
}
```

### Required Prompt Files
1. `CLAIM_SELECTION_PROMPT.txt` - For batched claim selection
2. Existing: `CLAIM_DETECTION_PROMPT`, `CLAIM_VERIFICATION_PROMPT`, `TOPIC_EXTRACTION_PROMPT`

---

## 📦 Dependencies

No new dependencies needed! Uses existing:
- `together` - LLM calls
- `ddgs` / `duckduckgo_search` - Web & image search
- `networkx` - Topic tree
- `asyncio` - Async operations

**Note:** DuckDuckGo API change:
```python
# OLD (doesn't work)
self.search_client.images(keywords=query, ...)

# NEW (correct)
self.search_client.images(query, ...)  # Positional argument
```

---

## 🎯 Integration Checklist

When porting to refactored codebase:

### 1. **State Management**
- [ ] Add `sentence_batch: List[str]` to state
- [ ] Add `topic_path: List[str]` to state
- [ ] Add `topic_images: List[Dict]` to state
- [ ] Implement `switch_to_topic()` method
- [ ] Implement `add_topic_image()` method

### 2. **Configuration**
- [ ] Add `claim_selection_batch_size` and `max_claims_per_batch` settings
- [ ] Create `CLAIM_SELECTION_PROMPT.txt` file
- [ ] Load prompt in config

### 3. **Fact Engine**
- [ ] Implement `select_claims()` method
- [ ] Implement `_generate_search_query()` method
- [ ] Update `search_evidence()` to use optimized queries
- [ ] Add debug output for search queries

### 4. **Topic Engine**
- [ ] Add DDGS client for image search
- [ ] Implement `find_existing_topic()` method
- [ ] Update `detect_topic_shift()` to return tuple
- [ ] Implement `search_topic_image()` method
- [ ] Implement `_search_and_record_image()` background task
- [ ] Update `update_topic_tree()` to handle reuse

### 5. **WebSocket Handler**
- [ ] Replace per-sentence fact-check with `batch_claim_selection_async()`
- [ ] Accumulate sentences in batch
- [ ] Process batch when full
- [ ] Send `image_url` in topic updates

### 6. **JSON Export**
- [ ] Add `topic_path` array
- [ ] Add `topic_images` array
- [ ] Auto-save on shutdown

### 7. **Testing**
- [ ] Verify batch accumulation works
- [ ] Verify claim selection runs
- [ ] Verify topic reuse detection works
- [ ] Verify image search completes
- [ ] Verify JSON structure is correct

---

## 🚨 Common Pitfalls

1. **Prompt Format:** Use `{{` and `}}` in prompts because Python `.format()` is used
2. **DuckDuckGo API:** Use positional `query` arg, not `keywords=query`
3. **Async Image Search:** Run as background task with `asyncio.create_task()`, don't await
4. **Topic Edges:** Only create edges when new topic is created, not when returning
5. **Batch Clearing:** Always clear `sentence_batch` after processing
6. **JSON Parsing:** Strip markdown code blocks before parsing LLM responses

---

## 📋 Architecture Differences to Watch For

When integrating into refactored codebase, look for:

1. **State Management Pattern**
   - Centralized state object vs distributed state
   - Singleton pattern vs dependency injection
   
2. **WebSocket Message Flow**
   - How Deepgram messages are handled
   - Where "final" transcript events trigger logic
   
3. **Async Task Management**
   - How background tasks are spawned and tracked
   - Whether there's a task manager/scheduler
   
4. **Configuration Loading**
   - Pydantic BaseSettings vs other config systems
   - Environment variables vs config files
   
5. **Logging Strategy**
   - Terminal output vs file logging
   - Debug output patterns

---

## 💡 Suggestions for AI Agent

To make porting easier:

1. **First, understand the refactored architecture:**
   ```
   "Please show me:
   1. The main WebSocket handler for Deepgram messages
   2. Where state is managed (transcript buffer, topic tree, fact queue)
   3. How fact-checking is currently triggered
   4. The configuration system"
   ```

2. **Map the components:**
   - Identify equivalent of `StateManager` 
   - Find where `FactEngine` lives
   - Locate `TopicEngine` 
   - Find config location

3. **Port in this order:**
   1. Configuration (least invasive)
   2. State fields (just add new fields)
   3. Search query generation (isolated feature)
   4. Batched claim selection (replaces existing logic)
   5. Topic reuse detection (modifies existing logic)
   6. Image search (new background task)

4. **Test incrementally:**
   - After each feature, verify system still works
   - Check JSON export structure
   - Monitor terminal output

5. **Ask for clarification:**
   - "Where does this go in your architecture?"
   - "What's the equivalent of X in your codebase?"
   - "Should I modify existing code or add new methods?"

---

## 📝 Code Snippets Quick Reference

### Print Statements Added
```python
# Batch processing
print(f"\n📋 BATCH: {batch_text}\n")

# Claim selection
print(f"✅ SELECTED CLAIMS:")
for claim in selected:
    print(f"   • {claim}")

# Search query
print(f"🔍 Search query: {search_query}")

# Image search
print(f"🖼️  Searching image for: {query}")
print(f"✅ Found image: {image_url[:80]}...")

# Fact check results
print(f"\n{'='*60}")
print(f"📊 FACT CHECK RESULT")
print(f"{'='*60}")
print(f"Claim: {result.claim}")
print(f"Verdict: {result.verdict} (Confidence: {result.confidence:.0%})")
print(f"Explanation: {result.explanation}")
print(f"{'='*60}\n")
```

---

## 🔗 File Dependencies

```
config.py
├── CLAIM_SELECTION_PROMPT.txt (new file)
├── claim_selection_batch_size (new setting)
└── max_claims_per_batch (new setting)

state_manager.py
├── sentence_batch: List[str] (new field)
├── topic_path: List[str] (new field)
├── topic_images: List[Dict] (new field)
├── switch_to_topic() (new method)
└── add_topic_image() (new method)

fact_engine.py
├── select_claims() (new method)
├── _generate_search_query() (new method)
└── search_evidence() (modified to use query generation)

topic_engine.py
├── search_client: DDGS (new field)
├── find_existing_topic() (new method)
├── search_topic_image() (new method)
├── _search_and_record_image() (new method)
└── update_topic_tree() (modified for reuse detection)

main.py
├── batch_claim_selection_async() (new function, replaces queue_fact_check_async)
├── update_topics_async() (modified to send image_url)
└── lifespan() (modified to save topic tree on shutdown)
```

---

**End of Feature Port Guide**

This guide should provide everything needed to port these features to a different codebase architecture.
