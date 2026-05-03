# System Architecture

Visual overview of how the chatbot systems work.

## System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                     CHATBOT INFRASTRUCTURE                       │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────────┐    ┌──────────────────────────────┐
│  Personal Site Chatbot   │    │  Role-Specific Chatbots      │
│  (chatbot.py)            │    │  (role_chatbot_template.py)  │
└──────────────────────────┘    └──────────────────────────────┘
         │                                    │
         │                                    │
         ▼                                    ▼
┌──────────────────────────┐    ┌──────────────────────────────┐
│  Amit's Profile          │    │  Role Content (RAG)          │
│  - summary.txt           │    │  - job_description.txt       │
│  - LinkedIn PDF          │    │  - client_info.txt           │
│  - Web Search (Serper)   │    │  - faqs.txt                  │
└──────────────────────────┘    │  - additional_info.txt       │
         │                       └──────────────────────────────┘
         │                                    │
         └────────────────┬───────────────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │  Gemini API     │
                 │  (via OpenAI)   │
                 └─────────────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │  Gradio UI      │
                 │  (Web Interface)│
                 └─────────────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │  Candidates     │
                 └─────────────────┘
```

---

## Personal Site Chatbot Flow

```
Candidate Question
       │
       ▼
┌──────────────────┐
│ Detect Question  │
│ Type             │
└──────────────────┘
       │
       ├─── About Amit? ──────┐
       │                      │
       └─── About Company? ───┤
                              │
                              ▼
                    ┌──────────────────┐
                    │ Select Context   │
                    │ - LinkedIn chunks│
                    │ - Web search     │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ Build Prompt     │
                    │ + Context        │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ Call Gemini API  │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ Cache Response   │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ Return Answer    │
                    └──────────────────┘
```

---

## Role Chatbot Flow

```
Candidate Question
       │
       ▼
┌──────────────────────────┐
│ Extract Keywords         │
│ from Question            │
└──────────────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Rank Content Chunks      │
│ by Keyword Overlap       │
└──────────────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Select Top N Chunks      │
│ (Most Relevant)          │
└──────────────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Build System Prompt      │
│ + Selected Context       │
└──────────────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Add Chat History         │
│ (Last N Messages)        │
└──────────────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Call Gemini API          │
└──────────────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Cache Response           │
└──────────────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Return Answer            │
└──────────────────────────┘
```

---

## RAG (Retrieval-Augmented Generation) Process

```
┌─────────────────────────────────────────────────────────┐
│                    CONTENT PREPARATION                   │
└─────────────────────────────────────────────────────────┘

Job Description + Client Info + FAQs + Additional Info
                          │
                          ▼
                 ┌─────────────────┐
                 │ Combine All     │
                 │ Content         │
                 └─────────────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │ Split into      │
                 │ Chunks          │
                 │ (1500 chars)    │
                 └─────────────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │ Extract Keywords│
                 │ from Each Chunk │
                 └─────────────────┘

┌─────────────────────────────────────────────────────────┐
│                    QUERY PROCESSING                      │
└─────────────────────────────────────────────────────────┘

                 User Question
                          │
                          ▼
                 ┌─────────────────┐
                 │ Extract Keywords│
                 │ from Question   │
                 └─────────────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │ Calculate       │
                 │ Keyword Overlap │
                 │ with Each Chunk │
                 └─────────────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │ Rank Chunks by  │
                 │ Relevance Score │
                 └─────────────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │ Select Top 4    │
                 │ Chunks          │
                 └─────────────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │ Include in      │
                 │ Prompt          │
                 └─────────────────┘
```

---

## Data Flow

### Personal Site Chatbot

```
Input: "Tell me about your Python experience"
  │
  ├─> Extract keywords: [python, experience]
  │
  ├─> Search LinkedIn chunks for matches
  │
  ├─> Select top 3 relevant chunks
  │
  ├─> Build prompt with context
  │
  └─> Generate response

Output: "I have 8+ years of Python experience, specializing in..."
```

### Role Chatbot

```
Input: "What's the salary range for this role?"
  │
  ├─> Extract keywords: [salary, range, role]
  │
  ├─> Rank all content chunks
  │   - FAQ chunk with salary info: Score 3
  │   - JD chunk with compensation: Score 2
  │   - Client info chunk: Score 0
  │
  ├─> Select top chunks (FAQ + JD)
  │
  ├─> Build prompt with selected context
  │
  └─> Generate response

Output: "The salary range is $120,000 - $160,000 based on experience..."
```

---

## Token Optimization Strategy

```
┌─────────────────────────────────────────────────────────┐
│                   TOKEN MANAGEMENT                       │
└─────────────────────────────────────────────────────────┘

Full Content: 10,000 tokens
       │
       ▼
┌──────────────────┐
│ Chunk into       │
│ Smaller Pieces   │
└──────────────────┘
       │
       ▼
Chunks: 7 × 1,500 tokens each
       │
       ▼
┌──────────────────┐
│ Select Only      │
│ Relevant Chunks  │
└──────────────────┘
       │
       ▼
Selected: 4 × 1,500 = 6,000 tokens
       │
       ▼
┌──────────────────┐
│ Add System       │
│ Prompt (500)     │
└──────────────────┘
       │
       ▼
┌──────────────────┐
│ Add History      │
│ (1,000)          │
└──────────────────┘
       │
       ▼
Total Input: ~7,500 tokens
       │
       ▼
┌──────────────────┐
│ Generate         │
│ Response (600)   │
└──────────────────┘
       │
       ▼
Total: ~8,100 tokens per request

Cost: ~$0.001 per request
```

---

## Caching Strategy

```
┌─────────────────────────────────────────────────────────┐
│                    RESPONSE CACHE                        │
└─────────────────────────────────────────────────────────┘

Question: "What's the salary?"
       │
       ▼
┌──────────────────┐
│ Normalize Query  │
│ (lowercase, trim)│
└──────────────────┘
       │
       ▼
Cache Key: "whats the salary"
       │
       ▼
┌──────────────────┐
│ Check Cache      │
└──────────────────┘
       │
       ├─── Hit ────> Return Cached Response (instant)
       │
       └─── Miss ───> Generate New Response
                      │
                      ▼
                 ┌──────────────────┐
                 │ Store in Cache   │
                 │ (LRU, max 50)    │
                 └──────────────────┘

Benefits:
- Instant responses for repeated questions
- Reduced API costs
- Better user experience
```

---

## Deployment Architecture

### Local Development

```
┌──────────────┐
│ Developer    │
│ Machine      │
└──────────────┘
       │
       ▼
┌──────────────┐
│ Python       │
│ Script       │
└──────────────┘
       │
       ▼
┌──────────────┐
│ Gradio       │
│ localhost    │
└──────────────┘
```

### Temporary Sharing

```
┌──────────────┐
│ Developer    │
│ Machine      │
└──────────────┘
       │
       ▼
┌──────────────┐
│ Gradio       │
│ --share      │
└──────────────┘
       │
       ▼
┌──────────────┐
│ Gradio       │
│ Tunnel       │
└──────────────┘
       │
       ▼
┌──────────────┐
│ Public URL   │
│ (72 hours)   │
└──────────────┘
```

### Production Deployment

```
┌──────────────┐
│ Git Repo     │
└──────────────┘
       │
       ▼
┌──────────────┐
│ Hugging Face │
│ Spaces       │
└──────────────┘
       │
       ▼
┌──────────────┐
│ Permanent    │
│ Public URL   │
└──────────────┘
```

---

## Security Model

```
┌─────────────────────────────────────────────────────────┐
│                    SECURITY LAYERS                       │
└─────────────────────────────────────────────────────────┘

┌──────────────────┐
│ API Keys         │  ← Stored in .env (not committed)
└──────────────────┘
       │
       ▼
┌──────────────────┐
│ Environment      │  ← Loaded at runtime only
│ Variables        │
└──────────────────┘
       │
       ▼
┌──────────────────┐
│ Rate Limiting    │  ← Gemini API limits
└──────────────────┘
       │
       ▼
┌──────────────────┐
│ Input Validation │  ← Sanitize user input
└──────────────────┘
       │
       ▼
┌──────────────────┐
│ No PII Storage   │  ← Stateless design
└──────────────────┘
```

---

## Scalability

### Single Role Chatbot

```
Concurrent Users: 1-10
Response Time: 1-3 seconds
Cost per Day: $0.10 - $1.00
Infrastructure: Single process
```

### Multiple Role Chatbots

```
Concurrent Users: 10-100
Response Time: 1-3 seconds
Cost per Day: $1.00 - $10.00
Infrastructure: Multiple processes
```

### High Volume

```
Concurrent Users: 100+
Response Time: 1-3 seconds
Cost per Day: $10.00+
Infrastructure: Load balancer + multiple instances
```

---

## Performance Characteristics

### Response Time Breakdown

```
Total: ~2 seconds
├─ Context Selection: 0.1s
├─ Prompt Building: 0.1s
├─ API Call: 1.5s
└─ Response Processing: 0.3s
```

### Optimization Techniques

1. **Caching**: Instant responses for repeated questions
2. **Chunking**: Only send relevant content
3. **History Limiting**: Keep context focused
4. **Keyword Matching**: Fast relevance scoring
5. **Response Streaming**: Show partial responses (future)

---

## Technology Stack

```
┌─────────────────────────────────────────────────────────┐
│                    TECHNOLOGY STACK                      │
└─────────────────────────────────────────────────────────┘

Frontend:
├─ Gradio (UI Framework)
└─ HTML/CSS/JavaScript (auto-generated)

Backend:
├─ Python 3.8+
├─ OpenAI SDK (Gemini API client)
└─ Custom RAG logic

APIs:
├─ Google Gemini (LLM)
└─ Serper (Web Search, optional)

Storage:
├─ Local files (.txt, .pdf)
└─ In-memory cache (OrderedDict)

Deployment:
├─ Local (development)
├─ Gradio Share (temporary)
└─ Hugging Face Spaces (production)
```

---

This architecture provides a scalable, cost-effective solution for recruitment chatbots with minimal infrastructure requirements.
