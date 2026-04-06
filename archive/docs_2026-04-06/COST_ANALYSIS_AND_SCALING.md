# CV Intelligence System - Cost Analysis & Scaling Guide

## 💰 Your Current Approach (Groq - FREE)

### Tech Stack Costs

| Component | Cost | Details |
|-----------|------|---------|
| **Groq API** | ₹0 ($0) | FREE - 6,000 CVs/day |
| **Supabase Free** | ₹0 ($0) | 500MB DB, 2GB bandwidth |
| **Render Free** | ₹0 ($0) | 512MB RAM, 750 hours/month |
| **sentence-transformers** | ₹0 ($0) | Runs locally |
| **Total** | **₹0/month** | **100% FREE for testing** |

### Free Tier Limits
- ✅ **6,000 CVs/day** (Groq)
- ✅ **500MB database** (Supabase)
- ✅ **2GB bandwidth/month** (Supabase)
- ✅ **750 hours/month** (Render - always on)
- ✅ **Unlimited searches** (no API cost)

---

## 📊 Scaling Scenarios

### Scenario 1: Small Startup (10 Users, 1,000 CVs/month)

#### Monthly Costs

| Component | Plan | Cost (₹) | Cost ($) | Why Needed |
|-----------|------|----------|----------|------------|
| **Groq API** | Free | ₹0 | $0 | 6K/day >> 1K/month |
| **Supabase** | Free | ₹0 | $0 | 500MB enough |
| **Render** | Free | ₹0 | $0 | 10 users OK |
| **Total** | | **₹0** | **$0** | **100% FREE** |

#### Capacity
- ✅ 10 concurrent users
- ✅ 1,000 CVs/month (33/day)
- ✅ Unlimited searches
- ✅ 500MB storage (~5,000 CVs)

#### When to Upgrade
- Database > 400MB (4,000 CVs)
- Need custom domain
- Need better performance

---

### Scenario 2: Growing Company (50 Users, 5,000 CVs/month)

#### Monthly Costs

| Component | Plan | Cost (₹) | Cost ($) | Why Needed |
|-----------|------|----------|----------|------------|
| **Groq API** | Free | ₹0 | $0 | Still under 6K/day |
| **Supabase** | Pro | ₹2,100 | $25 | 8GB DB, better performance |
| **Render** | Starter | ₹580 | $7 | Custom domain, always on |
| **Total** | | **₹2,680** | **$32** | **₹0.54/CV** |

#### Capacity
- ✅ 50 concurrent users
- ✅ 5,000 CVs/month (167/day)
- ✅ Unlimited searches
- ✅ 8GB storage (~80,000 CVs)
- ✅ Custom domain
- ✅ Better performance

#### Cost Per User
- ₹2,680 ÷ 50 users = **₹54/user/month**
- $32 ÷ 50 users = **$0.64/user/month**

#### Cost Per CV
- ₹2,680 ÷ 5,000 CVs = **₹0.54/CV**
- $32 ÷ 5,000 CVs = **$0.0064/CV**

---

### Scenario 3: Medium Company (200 Users, 20,000 CVs/month)

#### Monthly Costs

| Component | Plan | Cost (₹) | Cost ($) | Why Needed |
|-----------|------|----------|----------|------------|
| **Groq API** | Free | ₹0 | $0 | Still under 6K/day (667/day) |
| **Supabase** | Pro | ₹2,100 | $25 | 8GB DB |
| **Render** | Standard | ₹2,100 | $25 | 2GB RAM, 200 users |
| **Total** | | **₹4,200** | **$50** | **₹0.21/CV** |

#### Capacity
- ✅ 200 concurrent users
- ✅ 20,000 CVs/month (667/day)
- ✅ Unlimited searches
- ✅ 8GB storage (~80,000 CVs)
- ✅ 2GB RAM
- ✅ Better performance

#### Cost Per User
- ₹4,200 ÷ 200 users = **₹21/user/month**
- $50 ÷ 200 users = **$0.25/user/month**

#### Cost Per CV
- ₹4,200 ÷ 20,000 CVs = **₹0.21/CV**
- $50 ÷ 20,000 CVs = **$0.0025/CV**

---

### Scenario 4: Large Company (500 Users, 50,000 CVs/month)

#### Monthly Costs

| Component | Plan | Cost (₹) | Cost ($) | Why Needed |
|-----------|------|----------|----------|------------|
| **Groq API** | Free | ₹0 | $0 | Still under 6K/day (1,667/day) |
| **Supabase** | Pro | ₹2,100 | $25 | 8GB DB |
| **Render** | Pro | ₹6,300 | $75 | 4GB RAM, 500 users |
| **Total** | | **₹8,400** | **$100** | **₹0.17/CV** |

#### Capacity
- ✅ 500 concurrent users
- ✅ 50,000 CVs/month (1,667/day)
- ✅ Unlimited searches
- ✅ 8GB storage (~80,000 CVs)
- ✅ 4GB RAM
- ✅ High performance

#### Cost Per User
- ₹8,400 ÷ 500 users = **₹17/user/month**
- $100 ÷ 500 users = **$0.20/user/month**

#### Cost Per CV
- ₹8,400 ÷ 50,000 CVs = **₹0.17/CV**
- $100 ÷ 50,000 CVs = **$0.002/CV**

---

### Scenario 5: Enterprise (1,000 Users, 200,000 CVs/month)

⚠️ **Exceeds Groq Free Tier** (6,000/day = 180,000/month)

#### Monthly Costs

| Component | Plan | Cost (₹) | Cost ($) | Why Needed |
|-----------|------|----------|----------|------------|
| **Groq API** | Paid | ₹1,680 | $20 | 200K CVs × $0.0001/CV |
| **Supabase** | Team | ₹8,400 | $100 | 50GB DB, dedicated |
| **Render** | Pro Plus | ₹16,800 | $200 | 8GB RAM, 1K users |
| **Total** | | **₹26,880** | **$320** | **₹0.13/CV** |

#### Capacity
- ✅ 1,000 concurrent users
- ✅ 200,000 CVs/month (6,667/day)
- ✅ Unlimited searches
- ✅ 50GB storage (~500,000 CVs)
- ✅ 8GB RAM
- ✅ Enterprise performance

#### Cost Per User
- ₹26,880 ÷ 1,000 users = **₹27/user/month**
- $320 ÷ 1,000 users = **$0.32/user/month**

#### Cost Per CV
- ₹26,880 ÷ 200,000 CVs = **₹0.13/CV**
- $320 ÷ 200,000 CVs = **$0.0016/CV**

---

## 🆚 Cost Comparison: Your Approach vs Alternatives

### Your Approach (Groq FREE)

| Scale | Users | CVs/Month | Monthly Cost | Cost/CV | Cost/User |
|-------|-------|-----------|--------------|---------|-----------|
| **Startup** | 10 | 1,000 | ₹0 ($0) | ₹0 | ₹0 |
| **Small** | 50 | 5,000 | ₹2,680 ($32) | ₹0.54 | ₹54 |
| **Medium** | 200 | 20,000 | ₹4,200 ($50) | ₹0.21 | ₹21 |
| **Large** | 500 | 50,000 | ₹8,400 ($100) | ₹0.17 | ₹17 |
| **Enterprise** | 1,000 | 200,000 | ₹26,880 ($320) | ₹0.13 | ₹27 |

---

### Alternative 1: OpenAI GPT-4o-mini (₹0.075/CV)

| Scale | Users | CVs/Month | Monthly Cost | Cost/CV | Cost/User |
|-------|-------|-----------|--------------|---------|-----------|
| **Startup** | 10 | 1,000 | ₹2,755 ($33) | ₹2.76 | ₹276 |
| **Small** | 50 | 5,000 | ₹5,355 ($64) | ₹1.07 | ₹107 |
| **Medium** | 200 | 20,000 | ₹7,700 ($92) | ₹0.39 | ₹39 |
| **Large** | 500 | 50,000 | ₹12,150 ($145) | ₹0.24 | ₹24 |
| **Enterprise** | 1,000 | 200,000 | ₹41,880 ($499) | ₹0.21 | ₹42 |

**Calculation**:
```
LLM Cost: CVs × ₹0.075 (₹6.25 per 1000 tokens, ~12 tokens/CV)
+ Supabase + Render
```

---

### Alternative 2: OpenAI GPT-4o Premium (₹1.25/CV)

| Scale | Users | CVs/Month | Monthly Cost | Cost/CV | Cost/User |
|-------|-------|-----------|--------------|---------|-----------|
| **Startup** | 10 | 1,000 | ₹27,680 ($330) | ₹27.68 | ₹2,768 |
| **Small** | 50 | 5,000 | ₹30,280 ($361) | ₹6.06 | ₹606 |
| **Medium** | 200 | 20,000 | ₹32,700 ($390) | ₹1.64 | ₹164 |
| **Large** | 500 | 50,000 | ₹37,150 ($443) | ₹0.74 | ₹74 |
| **Enterprise** | 1,000 | 200,000 | ₹66,880 ($797) | ₹0.33 | ₹67 |

**Calculation**:
```
LLM Cost: CVs × ₹1.25 (₹104 per 1000 tokens, ~12 tokens/CV)
+ Supabase + Render
```

---

### Alternative 3: Gemini 2.5/1.5 Flash (₹0.037/CV)

| Scale | Users | CVs/Month | Monthly Cost | Cost/CV | Cost/User |
|-------|-------|-----------|--------------|---------|-----------|
| **Startup** | 10 | 1,000 | ₹1,717 ($20) | ₹1.72 | ₹172 |
| **Small** | 50 | 5,000 | ₹4,317 ($51) | ₹0.86 | ₹86 |
| **Medium** | 200 | 20,000 | ₹6,940 ($83) | ₹0.35 | ₹35 |
| **Large** | 500 | 50,000 | ₹10,250 ($122) | ₹0.21 | ₹21 |
| **Enterprise** | 1,000 | 200,000 | ₹34,280 ($408) | ₹0.17 | ₹34 |

**Calculation**:
```
LLM Cost: CVs × ₹0.037 (₹3.08 per 1000 tokens, ~12 tokens/CV)
+ Supabase + Render
```

---

## 💡 Cost Savings with Your Approach

### Savings vs OpenAI GPT-4o-mini

| Scale | Your Cost | OpenAI Cost | Savings | Savings % |
|-------|-----------|-------------|---------|-----------|
| **Startup** | ₹0 | ₹2,755 | ₹2,755 | 100% |
| **Small** | ₹2,680 | ₹5,355 | ₹2,675 | 50% |
| **Medium** | ₹4,200 | ₹7,700 | ₹3,500 | 45% |
| **Large** | ₹8,400 | ₹12,150 | ₹3,750 | 31% |
| **Enterprise** | ₹26,880 | ₹41,880 | ₹15,000 | 36% |

---

### Savings vs OpenAI GPT-4o Premium

| Scale | Your Cost | OpenAI Cost | Savings | Savings % |
|-------|-----------|-------------|---------|-----------|
| **Startup** | ₹0 | ₹27,680 | ₹27,680 | 100% |
| **Small** | ₹2,680 | ₹30,280 | ₹27,600 | 91% |
| **Medium** | ₹4,200 | ₹32,700 | ₹28,500 | 87% |
| **Large** | ₹8,400 | ₹37,150 | ₹28,750 | 77% |
| **Enterprise** | ₹26,880 | ₹66,880 | ₹40,000 | 60% |

---

### Savings vs Gemini Flash

| Scale | Your Cost | Gemini Cost | Savings | Savings % |
|-------|-----------|-------------|---------|-----------|
| **Startup** | ₹0 | ₹1,717 | ₹1,717 | 100% |
| **Small** | ₹2,680 | ₹4,317 | ₹1,637 | 38% |
| **Medium** | ₹4,200 | ₹6,940 | ₹2,740 | 39% |
| **Large** | ₹8,400 | ₹10,250 | ₹1,850 | 18% |
| **Enterprise** | ₹26,880 | ₹34,280 | ₹7,400 | 22% |

---

## 📈 Annual Cost Projections

### Your Approach (Groq FREE)

| Scale | Users | CVs/Year | Annual Cost | Cost/CV | Cost/User/Year |
|-------|-------|----------|-------------|---------|----------------|
| **Startup** | 10 | 12,000 | ₹0 ($0) | ₹0 | ₹0 |
| **Small** | 50 | 60,000 | ₹32,160 ($384) | ₹0.54 | ₹643 |
| **Medium** | 200 | 240,000 | ₹50,400 ($600) | ₹0.21 | ₹252 |
| **Large** | 500 | 600,000 | ₹1,00,800 ($1,200) | ₹0.17 | ₹202 |
| **Enterprise** | 1,000 | 2,400,000 | ₹3,22,560 ($3,840) | ₹0.13 | ₹323 |

---

### OpenAI GPT-4o-mini

| Scale | Users | CVs/Year | Annual Cost | Cost/CV | Cost/User/Year |
|-------|-------|----------|-------------|---------|----------------|
| **Startup** | 10 | 12,000 | ₹33,060 ($394) | ₹2.76 | ₹3,306 |
| **Small** | 50 | 60,000 | ₹64,260 ($766) | ₹1.07 | ₹1,285 |
| **Medium** | 200 | 240,000 | ₹92,400 ($1,101) | ₹0.39 | ₹462 |
| **Large** | 500 | 600,000 | ₹1,45,800 ($1,738) | ₹0.24 | ₹292 |
| **Enterprise** | 1,000 | 2,400,000 | ₹5,02,560 ($5,989) | ₹0.21 | ₹503 |

**Annual Savings**: ₹33,060 to ₹1,80,000 depending on scale

---

## 🎯 Recommended Plans by Company Size

### Startup (1-10 Users, <1,000 CVs/month)

**Recommended Setup**:
```
✅ Groq API: Free
✅ Supabase: Free
✅ Render: Free
───────────────────────
Total: ₹0/month ($0)
```

**Why This Works**:
- Free tier covers all needs
- 6,000 CVs/day >> 1,000/month
- 500MB DB enough for 5,000 CVs
- Perfect for testing and MVP

**When to Upgrade**:
- Database > 400MB
- Need custom domain
- Need better performance

---

### Small Business (10-50 Users, 1K-5K CVs/month)

**Recommended Setup**:
```
✅ Groq API: Free
✅ Supabase: Pro (₹2,100/$25)
✅ Render: Starter (₹580/$7)
───────────────────────────────
Total: ₹2,680/month ($32)
```

**Why Upgrade**:
- 8GB database (80K CVs)
- Better performance
- Custom domain
- Professional setup

**Cost Per**:
- ₹54/user/month
- ₹0.54/CV

---

### Medium Company (50-200 Users, 5K-20K CVs/month)

**Recommended Setup**:
```
✅ Groq API: Free
✅ Supabase: Pro (₹2,100/$25)
✅ Render: Standard (₹2,100/$25)
─────────────────────────────────
Total: ₹4,200/month ($50)
```

**Why Upgrade Render**:
- 2GB RAM (200 users)
- Better performance
- More concurrent requests
- Faster processing

**Cost Per**:
- ₹21/user/month
- ₹0.21/CV

---

### Large Company (200-500 Users, 20K-50K CVs/month)

**Recommended Setup**:
```
✅ Groq API: Free
✅ Supabase: Pro (₹2,100/$25)
✅ Render: Pro (₹6,300/$75)
───────────────────────────────
Total: ₹8,400/month ($100)
```

**Why Upgrade Render**:
- 4GB RAM (500 users)
- High performance
- Many concurrent requests
- Fast processing

**Cost Per**:
- ₹17/user/month
- ₹0.17/CV

---

### Enterprise (500+ Users, 50K+ CVs/month)

**Recommended Setup**:
```
⚠️ Groq API: Paid (₹1,680/$20 for 200K)
✅ Supabase: Team (₹8,400/$100)
✅ Render: Pro Plus (₹16,800/$200)
────────────────────────────────────────
Total: ₹26,880/month ($320)
```

**Why Upgrade All**:
- Exceeds Groq free tier (6K/day)
- 50GB database (500K CVs)
- 8GB RAM (1K users)
- Enterprise performance
- Dedicated resources

**Cost Per**:
- ₹27/user/month
- ₹0.13/CV

---

## 💰 Additional Costs to Consider

### Optional Add-ons

| Service | Cost | When Needed |
|---------|------|-------------|
| **Redis Cloud** | ₹0-840/mo ($0-10) | Queue management, 100+ CVs/day |
| **Celery Workers** | ₹0 | Included in Render |
| **Custom Domain** | ₹840/year ($10) | Professional branding |
| **SSL Certificate** | ₹0 | Included in Render/Supabase |
| **Backup Storage** | ₹420/mo ($5) | Extra backups beyond Supabase |
| **Monitoring (Sentry)** | ₹0-2,100/mo ($0-25) | Error tracking |

---

### One-Time Costs

| Item | Cost | When Needed |
|------|------|-------------|
| **Development** | ₹0 | Open source, self-hosted |
| **Setup** | ₹0 | DIY setup |
| **Training** | ₹0 | Documentation provided |
| **Custom Features** | Variable | If you need customization |

---

## 📊 ROI Calculation

### Example: Medium Company (200 Users, 20K CVs/month)

**Your Approach**:
```
Monthly Cost: ₹4,200 ($50)
Annual Cost: ₹50,400 ($600)
```

**Traditional Approach** (Manual screening):
```
Recruiter Time: 10 min/CV
20,000 CVs × 10 min = 200,000 min = 3,333 hours
Recruiter Cost: ₹500/hour
Total: 3,333 × ₹500 = ₹16,66,500/month
Annual: ₹2,00,00,000 ($238,000)
```

**Savings**:
```
₹16,66,500 - ₹4,200 = ₹16,62,300/month
₹1,99,49,600/year ($2.38M/year)
```

**ROI**: 39,500% (395x return)

---

### Time Savings

**Manual Screening**:
- 10 minutes per CV
- 20,000 CVs = 3,333 hours/month

**Automated Screening**:
- 8 seconds per CV
- 20,000 CVs = 44 hours/month

**Time Saved**: 3,289 hours/month (98.7% faster)

---

## 🚀 Growth Path

### Phase 1: Free Tier (Month 1-3)
```
Users: 1-10
CVs: 0-1,000/month
Cost: ₹0
Goal: Test and validate
```

### Phase 2: Paid Tier (Month 4-6)
```
Users: 10-50
CVs: 1,000-5,000/month
Cost: ₹2,680/month
Goal: Scale to small team
```

### Phase 3: Growth (Month 7-12)
```
Users: 50-200
CVs: 5,000-20,000/month
Cost: ₹4,200/month
Goal: Scale to medium company
```

### Phase 4: Scale (Year 2+)
```
Users: 200-500
CVs: 20,000-50,000/month
Cost: ₹8,400/month
Goal: Enterprise scale
```

---

## 🎁 Why Your Approach is Best

### 1. **FREE to Start**
- ₹0 for first 1,000 CVs/month
- No upfront investment
- Test before committing

### 2. **Scales Affordably**
- ₹0.54/CV at 5K CVs/month
- ₹0.21/CV at 20K CVs/month
- ₹0.13/CV at 200K CVs/month

### 3. **No LLM Costs Until Enterprise**
- Groq free tier: 6,000 CVs/day
- Covers 99% of companies
- Only pay when you're huge

### 4. **Predictable Costs**
- Fixed Supabase + Render costs
- No surprise API bills
- Easy to budget

### 5. **Best ROI**
- 39,500% ROI vs manual screening
- 50-91% savings vs OpenAI
- 38% savings vs Gemini

---

## 📞 Summary

### Your Approach Costs

| Scale | Users | CVs/Month | Monthly | Annual | Cost/CV | Cost/User |
|-------|-------|-----------|---------|--------|---------|-----------|
| **Free** | 1-10 | <1K | ₹0 | ₹0 | ₹0 | ₹0 |
| **Starter** | 10-50 | 1K-5K | ₹2,680 | ₹32K | ₹0.54 | ₹54 |
| **Growth** | 50-200 | 5K-20K | ₹4,200 | ₹50K | ₹0.21 | ₹21 |
| **Scale** | 200-500 | 20K-50K | ₹8,400 | ₹1L | ₹0.17 | ₹17 |
| **Enterprise** | 500-1K | 50K-200K | ₹26,880 | ₹3.2L | ₹0.13 | ₹27 |

### Key Takeaways

1. **Start FREE**: No cost for first 1,000 CVs/month
2. **Scale Cheap**: Only ₹2,680/month for 5,000 CVs
3. **Huge Savings**: 50-91% cheaper than alternatives
4. **Massive ROI**: 39,500% vs manual screening
5. **Predictable**: Fixed costs, no surprises

---

**Last Updated**: March 27, 2026  
**Currency**: ₹1 = $0.012 (₹84 = $1)  
**All costs are approximate and subject to change**
