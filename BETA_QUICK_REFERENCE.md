# Beta Launch Quick Reference

**Last Updated:** November 14, 2025  
**Status:** Pre-Beta Validation Phase

---

## 🎯 Core Documents

| Document | Purpose | Location |
|----------|---------|----------|
| **Functional Narratives** | 5 core user journeys that must work | `BETA_FUNCTIONAL_NARRATIVES.md` |
| **Validation Script** | Automated testing of all narratives | `scripts/test_beta_narratives.sh` |
| **Observability Metrics** | Metrics guide + PromQL queries | `OBSERVABILITY_METRICS.md` |
| **Implementation Roadmap** | 12-week plan (Week 12 = Beta) | `docs/Implementation-Roadmap.md` |

---

## 🚀 Quick Start (Beta Testing)

### 1. Start All Services

```bash
# Terminal 1: Start observability stack
docker-compose -f docker-compose.external.yml --profile monitoring up -d

# Terminal 2: Start backend
make dev
# OR
cd /Users/balu/Projects/dyocense
source .venv/bin/activate
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8001

# Terminal 3: Start frontend
cd apps/smb
npm run dev
```

### 2. Verify Services

```bash
# Check backend
curl http://localhost:8001/health

# Check Grafana
open http://localhost:3000
# Login: admin / change_this_secure_password

# Check Prometheus
curl http://localhost:9091/-/healthy

# Check metrics endpoint
curl http://localhost:8001/metrics | grep evidence
```

### 3. Run Automated Tests

```bash
# Validate all 5 narratives
./scripts/test_beta_narratives.sh

# Run evidence tests
pytest tests/test_evidence.py -v

# Run auth tests
pytest tests/test_auth.py -v
```

---

## 📋 The 5 Critical Narratives

### ✅ Narrative 1: Onboarding (0-5 min)

- **Goal:** User signs up → sees first value
- **Critical Path:**
  1. Visit <http://localhost:5173>
  2. Click "Try the pilot"
  3. Fill signup form → Receive verification email
  4. Complete welcome wizard (3 steps)
  5. See health score + first recommendation
- **Success:** < 5 minutes, no errors

### ✅ Narrative 2: Connect Data (5-15 min)

- **Goal:** User connects real business data
- **Critical Paths:**
  - **ERPNext:** Credentials → Test → Sync → Agent insight
  - **CSV Upload:** Drag file → Map columns → Import → Agent insight
- **Success:** Data appears, health score updates

### ✅ Narrative 3: Create Goal (10-20 min)

- **Goal:** User sets business goal, tracks progress
- **Critical Path:**
  1. Goals page → "+ New Goal"
  2. AI suggests goal or user types custom
  3. Review sub-tasks (AI-generated)
  4. Assign owners, set timeline
  5. Track weekly progress
- **Success:** Goal shows progress, version history works

### ✅ Narrative 4: Run Agent (5-10 min)

- **Goal:** User gets AI-powered recommendations
- **Critical Path:**
  1. Agents page → Select "Inventory Optimizer"
  2. Click "Run Analysis"
  3. Watch real-time thinking updates
  4. Review recommendations
  5. Download PDF report
- **Success:** Agent completes < 60 sec, actionable output

### ✅ Narrative 5: Export Evidence (5-10 min)

- **Goal:** User proves decisions with data
- **Critical Path:**
  1. Executor page → Select template
  2. Run correlation, what-if, drivers, Granger
  3. View evidence graph
  4. Export audit trail (JSON/PDF)
- **Success:** All 4 engines run < 5 sec each

---

## 🧪 Beta User Profile

**Ideal Beta Tester:**

- SMB owner (retail, restaurant, e-commerce)
- 5-50 employees
- Currently uses spreadsheets or basic tools
- Has business data (sales, inventory, customers)
- Willing to spend 30 minutes onboarding
- Available for weekly feedback calls

**Red Flags (Not a good fit):**

- Large enterprise (> 500 employees)
- No business data to connect
- Expects fully custom solution
- Not willing to give feedback

---

## 📊 Success Metrics (Week 1)

| Metric | Target | Current |
|--------|--------|---------|
| Users onboarded | 10 | TBD |
| Data sources connected | 5+ | TBD |
| Goals created | 3+ | TBD |
| Agent runs | 10+ | TBD |
| Login frequency | 3+/week | TBD |
| Critical bugs | 0 | TBD |
| NPS score | > 40 | TBD |

---

## 🔥 Known Issues (Pre-Beta)

### 🔴 Critical (Blocking Beta)

- [ ] Prometheus restarting (YAML syntax error line 111)
- [ ] Production passwords still default (security risk)
- [ ] SSL/TLS not configured (required for email verification)

### 🟡 High Priority (Fix Before Beta)

- [ ] Health score uses placeholder logic (not real calculation)
- [ ] Agent recommendations are generic (need industry-specific)
- [ ] PDF export not implemented for goals/evidence
- [ ] Statistical confidence intervals not shown

### 🟢 Nice to Have (Post-Beta)

- [ ] Share link generation for collaboration
- [ ] Interactive evidence graph visualization
- [ ] Email templates (currently plain text)
- [ ] Database backup automation

---

## 🛠️ Troubleshooting

### Backend Won't Start

```bash
# Check PostgreSQL
docker-compose -f docker-compose.external.yml ps postgres

# Check logs
docker logs dyocense-postgres --tail 50

# Reset database (CAUTION: deletes data)
docker-compose -f docker-compose.external.yml down -v
docker-compose -f docker-compose.external.yml up -d postgres
```

### Frontend Build Errors

```bash
cd apps/smb
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Prometheus Not Starting

```bash
# Check alerts file syntax
docker exec dyocense-prometheus cat /etc/prometheus/alerts/system_alerts.yml

# View logs
docker logs dyocense-prometheus --tail 50

# Fix: Edit infra/prometheus/alerts/system_alerts.yml line 111
```

### Grafana Can't Access Prometheus

```bash
# Check Prometheus is running
curl http://localhost:9091/-/healthy

# Check Grafana datasource config
# Login to Grafana → Configuration → Data Sources → Prometheus
# URL should be: http://prometheus:9090
```

---

## 📞 Beta Support Process

### User Reports Issue

1. **Acknowledge** within 1 hour
2. **Triage** (critical, high, medium, low)
3. **Reproduce** locally or in staging
4. **Fix** critical bugs within 4 hours
5. **Deploy** + notify user
6. **Document** in beta feedback log

### Weekly Check-in Template

```
Hi [Name],

How's your first week with Dyocense going?

Quick questions:
1. Did you connect your data successfully?
2. Which features are you using most?
3. Any frustrations or confusing parts?
4. What would make this 10x better?

Thanks!
[Your Name]
```

---

## 🎓 Training Resources for Beta Users

### Onboarding Call Agenda (30 min)

1. **Intro** (5 min) - Project goals, what to expect
2. **Signup** (5 min) - Walk through registration + verification
3. **Connect Data** (10 min) - Help with ERPNext/CSV upload
4. **First Goal** (5 min) - Create goal together
5. **Q&A** (5 min) - Answer questions, set expectations

### Follow-up Resources

- **Video Tutorial:** "Connecting Your Data" (3 min)
- **PDF Guide:** "Getting Started with Dyocense" (2 pages)
- **Slack Channel:** #beta-users (for questions)
- **Office Hours:** Tuesdays 2-3 PM PT (optional)

---

## 📅 Beta Timeline

### Week 1: Onboarding (Days 1-7)

- **Day 1-2:** Invite 10 users, schedule kickoff calls
- **Day 3-5:** Complete onboarding calls, help connect data
- **Day 6-7:** Monitor usage, fix critical bugs

### Week 2: Engagement (Days 8-14)

- **Day 8:** Send first check-in email
- **Day 10:** Review usage analytics
- **Day 12:** Fix high-priority issues
- **Day 14:** Collect initial feedback (survey)

### Week 3-4: Iteration (Days 15-28)

- **Week 3:** Implement top 3 feature requests
- **Week 4:** Final feedback interviews, testimonials
- **End of Month:** Decide: launch publicly or iterate more

---

## ✅ Pre-Beta Launch Checklist

### Infrastructure

- [ ] All Docker services healthy (postgres, grafana, loki, prometheus)
- [ ] Backend running without errors
- [ ] Frontend builds without warnings
- [ ] SSL/TLS certificates configured
- [ ] Database backups scheduled (daily)
- [ ] Monitoring alerts configured (Grafana)

### Functional

- [ ] All 5 narratives tested end-to-end
- [ ] No console errors in browser
- [ ] No 500 errors in backend logs
- [ ] Email verification working
- [ ] Password reset flow working
- [ ] Data connectors stable (ERPNext + CSV)

### Security

- [ ] Production passwords updated (.env)
- [ ] JWT secrets rotated
- [ ] RLS policies enabled (tenant isolation)
- [ ] Connector credentials encrypted
- [ ] CORS restricted (no wildcards)
- [ ] Rate limiting configured

### Documentation

- [ ] Beta user guide published
- [ ] Video tutorials recorded
- [ ] Support Slack channel created
- [ ] Feedback form ready (Typeform/Google Forms)
- [ ] Onboarding call calendar links sent

### Team Readiness

- [ ] Support rotation schedule (who's on call?)
- [ ] Escalation process documented
- [ ] Bug tracking system ready (GitHub Issues)
- [ ] Communication plan (Slack, email)

---

## 🎉 Beta Success Criteria

**Technical Success:**

- [ ] All 5 narratives work without errors
- [ ] Agent analysis completes < 60 seconds
- [ ] Evidence engines run < 5 seconds each
- [ ] Health score updates within 1 minute of data sync
- [ ] Zero critical bugs in production

**Business Success:**

- [ ] 10 beta users onboarded
- [ ] 8/10 users actively engaged (3+ logins/week)
- [ ] NPS score > 40
- [ ] 5+ feature requests captured
- [ ] 2+ success stories (testimonials)
- [ ] Zero churn during beta

**Readiness for Paid Launch:**

- [ ] Pricing finalized ($79/month Run plan)
- [ ] Payment integration tested (Stripe)
- [ ] Invoicing automated
- [ ] Terms of Service + Privacy Policy published
- [ ] Support SLA defined (< 4 hour response)

---

**Document Owner:** Product Team  
**Next Review:** Before beta launch  
**Questions?** Contact: <beta@dyocense.com>
