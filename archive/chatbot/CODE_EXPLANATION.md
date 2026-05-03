# Code Explanation - Role-Specific Chatbot

## Quick Summary

This chatbot uses **RAG (Retrieval-Augmented Generation)** to answer candidate questions efficiently:
- Loads job info from text files
- Splits content into searchable chunks
- Finds relevant chunks for each question
- Sends only relevant info to AI
- Returns accurate, contextual answers

**Result:** 68% cheaper than sending all content every time!

---

## File Structure

```
chatbot/
├── role_chatbot_template.py    # Main chatbot engine (300 lines)
├── create_role_chatbot.py      # Role creator (150 lines)
├── list_roles.py                # Role lister (100 lines)
└── roles/
    └── example_senior_python_dev/
        ├── job_description.txt      # JD content
        ├── client_info.txt          # Company info
        ├── faqs.txt                 # Q&A pairs
        ├── additional_info.txt      # Extra details
        └── .env                     # API key
```

---

## How It Works (Step by Step)

### Step 1: Initialization

```python
bot = RoleChatbot(role_folder)
```

**What happens:**
1. Loads `.env` file → Gets API key
2. Reads 4 content files (JD, client info, FAQs, additional)
3. Combines all content into one text
4. Splits into chunks (1500 chars each, 200 char overlap)
5. Creates base system prompt

**Example:**
```
Content files → Combined text (10,000 chars)
                     ↓
              Split into chunks
                     ↓
        [Chunk 1] [Chunk 2] [Chunk 3] ... [Chunk 13]
        (1500c)   (1500c)   (1500c)       (1500c)
```

### Step 2: User Asks Question

```python
user_message = "What's the salary range?"
```

### Step 3: Find Relevant Chunks

```python
relevant_chunks = bot._select_relevant_chunks(user_message)
```

**What happens:**
1. Extract keywords from question: `["salary", "range"]`
2. For each chunk, extract keywords
3. Count keyword matches
4. Rank chunks by match score
5. Return top 4 chunks

**Example:**
```
Question: "What's the salary range?"
Keywords: {salary, range, what}

Chunk 1: "The role requires Python..." 
  Keywords: {role, requires, python, ...}
  Match score: 0

Chunk 7: "Compensation: $120k-$150k range..."
  Keywords: {compensation, 120k, 150k, range, ...}
  Match score: 2 ✓

Chunk 9: "Benefits include salary reviews..."
  Keywords: {benefits, salary, reviews, ...}
  Match score: 1 ✓

Result: Send Chunks 7, 9 (most relevant)
```

### Step 4: Build System Prompt

```python
system_prompt = bot._build_system_prompt(user_message)
```

**What happens:**
```python
system_prompt = f"""
You are a recruitment assistant for: Senior Python Developer

Your responsibilities:
- Answer questions about the role
- Be professional and friendly
- Provide accurate information

## Relevant Information:
{chunk_7}
{chunk_9}

Provide helpful information to the candidate.
"""
```

### Step 5: Send to AI

```python
response = client.chat.completions.create(
    model="gemini-2.5-flash-lite",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "What's the salary range?"}
    ]
)
```

**What's sent:**
- System prompt with relevant chunks (~2000 tokens)
- User question (~20 tokens)
- Chat history (~1000 tokens)
- **Total: ~3000 tokens** (vs 9000 without RAG!)

### Step 6: Return Answer

```python
answer = "The salary range for this role is $120,000 - $150,000..."
return answer
```

---

## Key Code Components

### 1. Text Chunking

```python
def _split_chunks(text, chunk_size=1500, overlap=200):
    """Split text into overlapping chunks"""
    chunks = []
    step = chunk_size - overlap  # Move forward by 1300
    
    for start in range(0, len(text), step):
        chunk = text[start:start + chunk_size]
        chunks.append(chunk)
    
    return chunks
```

**Why overlap?**
```
Without overlap:
[Chunk 1: "...Python experi"] [Chunk 2: "ence required..."]
         ❌ Word split!

With overlap:
[Chunk 1: "...Python experience req"] 
              [Chunk 2: "experience required..."]
                    ✓ Complete context!
```

### 2. Keyword Extraction

```python
def _keywords(text):
    """Extract keywords from text"""
    # Find all words (alphanumeric)
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    # Return as set (fast lookup)
    return set(words)
```

**Example:**
```python
text = "What's the salary range?"
keywords = {"what", "s", "the", "salary", "range"}
```

### 3. Relevance Ranking

```python
def _select_relevant_chunks(user_message):
    query_keywords = _keywords(user_message)
    
    ranked = []
    for chunk in content_chunks:
        chunk_keywords = _keywords(chunk)
        # Count matching keywords
        overlap = len(query_keywords & chunk_keywords)
        ranked.append((overlap, chunk))
    
    # Sort by overlap (highest first)
    ranked.sort(key=lambda x: x[0], reverse=True)
    
    # Return top 4
    return [chunk for score, chunk in ranked[:4]]
```

**Visual:**
```
Query: "remote work policy"
Keywords: {remote, work, policy}

Chunk 1: "Python Django Flask" → Score: 0
Chunk 2: "Remote work available" → Score: 2 ✓
Chunk 3: "Work from home policy" → Score: 2 ✓
Chunk 4: "Office location NYC" → Score: 0

Selected: Chunks 2, 3
```

### 4. Response Caching

```python
response_cache = OrderedDict()  # Maintains insertion order

def chat(message, history):
    # Check cache first
    cache_key = clean_text(message).lower()
    if cache_key in response_cache:
        return response_cache[cache_key]  # Instant!
    
    # Call API
    response = call_gemini_api(...)
    
    # Cache for next time
    response_cache[cache_key] = response
    
    # Limit cache size
    if len(response_cache) > 50:
        response_cache.popitem(last=False)  # Remove oldest
    
    return response
```

**Benefits:**
```
First time: "What's the salary?" → API call (1 second)
Second time: "What's the salary?" → Cache hit (instant!)
Third time: "what's the salary?" → Cache hit (instant!)
```

### 5. History Management

```python
def _normalize_history(history):
    """Keep only last 10 messages"""
    normalized = []
    
    for item in history:
        if isinstance(item, tuple):
            user_msg, bot_msg = item
            normalized.append({"role": "user", "content": user_msg})
            normalized.append({"role": "assistant", "content": bot_msg})
    
    # Keep only last 10 messages
    return normalized[-10:]
```

**Why limit history?**
```
Without limit:
Message 1-100 → 10,000 tokens → Slow & expensive

With limit (last 10):
Message 91-100 → 1,000 tokens → Fast & cheap
```

---

## Configuration Options

All in `.env` file:

```bash
# Which AI model to use
CHATBOT_MODEL=gemini-2.5-flash-lite

# How many messages to remember
MAX_HISTORY_MESSAGES=10

# Chunk size (characters)
CHUNK_SIZE=1500

# Overlap between chunks
CHUNK_OVERLAP=200

# How many chunks to send per question
MAX_CONTEXT_CHUNKS=4
```

**Tuning Guide:**

| Setting | Increase If | Decrease If |
|---------|-------------|-------------|
| CHUNK_SIZE | Answers lack context | Too expensive |
| CHUNK_OVERLAP | Info gets cut off | Too slow |
| MAX_CONTEXT_CHUNKS | Answers incomplete | Too expensive |
| MAX_HISTORY_MESSAGES | Need more context | Too slow |

---

## API Integration

### Gemini via OpenAI API

```python
# Initialize client
client = OpenAI(
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=os.getenv("GEMINI_API_KEY")
)

# Make request
response = client.chat.completions.create(
    model="gemini-2.5-flash-lite",
    messages=[
        {"role": "system", "content": "You are a helpful assistant..."},
        {"role": "user", "content": "What's the salary?"}
    ],
    temperature=0.3,    # Lower = more consistent
    max_tokens=600,     # Limit response length
    timeout=45          # 45 second timeout
)

# Extract answer
answer = response.choices[0].message.content
```

**Why Gemini?**
- Fast (flash model)
- Cheap ($0.075 per 1M input tokens)
- Good quality for Q&A
- OpenAI-compatible (easy to switch)

---

## Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ 1. INITIALIZATION (Once per chatbot)                        │
├─────────────────────────────────────────────────────────────┤
│ Load .env → Get API Key                                     │
│ Read job_description.txt                                    │
│ Read client_info.txt                                        │
│ Read faqs.txt                                               │
│ Read additional_info.txt                                    │
│ Combine all content                                         │
│ Split into 13 chunks (1500 chars each)                     │
│ Create base system prompt                                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. USER ASKS QUESTION                                        │
├─────────────────────────────────────────────────────────────┤
│ "What's the salary range?"                                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. CHECK CACHE                                               │
├─────────────────────────────────────────────────────────────┤
│ Question in cache? → Return cached answer (instant!)       │
│ Not in cache? → Continue...                                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. EXTRACT KEYWORDS                                          │
├─────────────────────────────────────────────────────────────┤
│ Question: "What's the salary range?"                        │
│ Keywords: {what, s, the, salary, range}                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. RANK CHUNKS                                               │
├─────────────────────────────────────────────────────────────┤
│ Chunk 1: Score 0 (no matches)                               │
│ Chunk 2: Score 0 (no matches)                               │
│ Chunk 7: Score 2 (salary, range) ✓                         │
│ Chunk 9: Score 1 (salary) ✓                                │
│ ...                                                          │
│ Select top 4: Chunks 7, 9, 3, 11                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. BUILD SYSTEM PROMPT                                       │
├─────────────────────────────────────────────────────────────┤
│ Base prompt (identity, instructions)                        │
│ + Selected chunks (relevant content)                        │
│ = Complete system prompt (~2000 tokens)                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. PREPARE MESSAGES                                          │
├─────────────────────────────────────────────────────────────┤
│ [System] Complete system prompt                             │
│ [User] Previous question 1                                  │
│ [Assistant] Previous answer 1                               │
│ ...                                                          │
│ [User] "What's the salary range?"                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 8. CALL GEMINI API                                           │
├─────────────────────────────────────────────────────────────┤
│ Send messages → Gemini processes → Returns answer          │
│ (~1 second)                                                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 9. CACHE & RETURN                                            │
├─────────────────────────────────────────────────────────────┤
│ Cache answer for future                                      │
│ Return to user                                               │
│ "The salary range is $120k-$150k..."                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Cost Comparison

### Scenario: 100 questions about a role

**Without RAG (naive approach):**
```
Per question:
- Input: 9,000 tokens (all content + history)
- Output: 150 tokens
- Cost: $0.00068 per question

100 questions: $0.068
```

**With RAG (this system):**
```
Per question:
- Input: 3,000 tokens (relevant chunks + history)
- Output: 150 tokens
- Cost: $0.00023 per question

100 questions: $0.023

With caching (50% hit rate):
50 cached (free) + 50 API calls = $0.012
```

**Savings: 82% cheaper!**

---

## Why This Design?

### 1. Template-Based
✓ Create new chatbots in 5 minutes
✓ No code changes needed
✓ Just edit text files

### 2. RAG Architecture
✓ 68% token reduction
✓ Faster responses
✓ More accurate (focused context)

### 3. Smart Caching
✓ Instant responses for common questions
✓ Reduces API costs
✓ Better user experience

### 4. Configurable
✓ Tune performance via .env
✓ No code changes needed
✓ Easy to optimize

### 5. Shareable
✓ One-click public links
✓ No deployment needed
✓ Works on mobile

---

## Summary

**The Magic:**
1. Load content files → Split into chunks
2. User asks question → Find relevant chunks
3. Send only relevant chunks to AI → Get answer
4. Cache answer → Next time is instant

**The Result:**
- Fast responses (1 second)
- Low cost ($0.02 per 100 questions)
- Accurate answers (focused context)
- Easy to create (5 minutes per role)
- Shareable links (one command)

**Perfect for recruitment at scale!**
