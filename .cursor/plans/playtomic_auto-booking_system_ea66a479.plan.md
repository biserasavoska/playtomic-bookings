---
name: Playtomic Auto-Booking System
overview: Build an automated booking system for Playtomic padel courts by adapting the existing open-source playtomic-scheduler project, configured for your group's specific time slots (weekdays 18:00-21:30) with reliable free/cheap cloud deployment.
todos:
  - id: examine-existing
    content: Clone and examine the playtomic-scheduler GitHub repository to understand its architecture and API integration approach
    status: completed
  - id: setup-local
    content: Set up local development environment with Python, install dependencies, and test basic connectivity to Playtomic
    status: completed
    dependencies:
      - examine-existing
  - id: configure-booking
    content: "Create configuration system for your group's specific needs: club ID, time slots (18:00-21:30), weekdays only, court preferences"
    status: completed
    dependencies:
      - setup-local
  - id: implement-timing
    content: Implement precise scheduling logic to trigger bookings at exact release time with retry mechanism for 5-second window
    status: completed
    dependencies:
      - configure-booking
  - id: add-notifications
    content: Add notification system (email/Telegram) to alert group members when bookings succeed or fail
    status: completed
    dependencies:
      - configure-booking
  - id: secure-credentials
    content: Implement secure credential storage using environment variables/secrets, never commit to repository
    status: completed
    dependencies:
      - setup-local
  - id: deploy-github-actions
    content: Set up GitHub Actions workflow with scheduled cron job to run booking automation daily at appropriate time
    status: completed
    dependencies:
      - implement-timing
      - secure-credentials
  - id: test-monitor
    content: Test the complete system, add logging/monitoring, and verify booking success rate
    status: completed
    dependencies:
      - deploy-github-actions
      - add-notifications
isProject: false
---

# Playtomic Automated Booking System

## Research Summary

### Key Findings

- **No official API needed**: Playtomic doesn't offer a public API, but community solutions exist that reverse-engineer the booking endpoints
- **Existing solution available**: `playtomic-scheduler` (GitHub) is an MIT-licensed Flask-based server specifically built for this use case
- **Cost**: Completely free - open source, no API fees
- **Deployment**: Multiple free/cheap options available (GitHub Actions, Render, Railway)

### Why Adapt Existing Project

- Proven approach already working in production
- Saves weeks of development time
- MIT license allows free modification and deployment
- Handles authentication and booking flow already
- Reduces risk vs. reverse-engineering from scratch

## Recommended Architecture

```mermaid
flowchart TD
    A[Scheduler Service] -->|Triggers at booking time| B[Playtomic API Client]
    B -->|Authenticates| C[Playtomic Backend]
    B -->|Checks availability| D[Court Slots 18:00-21:30]
    B -->|Submits booking| E[Reservation Created]
    E -->|Notifies| F[Group Members]
    
    G[Configuration] -->|Court IDs, Times, Credentials| A
    H[Deployment Platform] -->|Runs scheduled job| A
```

## Implementation Plan

### Phase 1: Setup & Exploration

1. **Clone and examine** the `playtomic-scheduler` repository to understand its structure
2. **Identify required configuration**:

   - Playtomic account credentials
   - Club/Venue ID
   - Court preferences
   - Time slots (18:00-21:30 weekdays)
   - Booking release time (when slots open daily)

3. **Test locally** to verify it works with your Playtomic account

### Phase 2: Customization

1. **Configure booking parameters**:

   - Set target time slots (18:00-21:30)
   - Configure weekday-only scheduling
   - Set preferred court(s)
   - Add group member notification system

2. **Optimize timing**:

   - Implement pre-booking checks (30 seconds before release)
   - Add retry logic for the critical 5-second window
   - Handle rate limiting and errors gracefully

3. **Add features**:

   - Success/failure notifications (email/SMS/Telegram)
   - Logging for booking attempts
   - Multiple account support (if group members want to rotate)

### Phase 3: Deployment

**Recommended: GitHub Actions (Free & Reliable)**

- Free for public repos, 2000 minutes/month for private
- Native cron scheduling support
- Runs automatically, no server management
- Alternative: Render free tier or Railway for always-on service

### Phase 4: Security & Configuration

1. **Secure credential storage**:

   - Use environment variables or secrets management
   - Never commit credentials to repository

2. **Create configuration file**:

   - JSON/YAML config for easy updates
   - Separate configs for different booking scenarios

3. **Add monitoring**:

   - Booking success rate tracking
   - Alert on failures

## Technical Stack

- **Language**: Python (existing project uses Flask)
- **Dependencies**: Based on playtomic-scheduler requirements
- **Deployment**: GitHub Actions (free) or Render/Railway (free tier)
- **Storage**: Configuration in repo, credentials in secrets

## Files Structure

```
playtomic-bookings/
├── src/
│   ├── scheduler.py          # Main booking scheduler
│   ├── playtomic_client.py   # API interaction layer
│   └── config.py             # Configuration management
├── config/
│   └── booking_config.yaml   # Your booking preferences
├── .github/
│   └── workflows/
│       └── auto-book.yml     # GitHub Actions schedule
├── requirements.txt
└── README.md
```

## Critical Considerations

1. **Terms of Service**: Verify Playtomic's ToS allows automation (may need to check)
2. **Timing precision**: Must execute within 5-second window - use precise scheduling
3. **Reliability**: System must run consistently - GitHub Actions is reliable for this
4. **Account security**: Store credentials securely, never in code
5. **Error handling**: Network issues, rate limits, booking conflicts

## Next Steps

1. Examine the existing `playtomic-scheduler` codebase
2. Set up local development environment
3. Test with your Playtomic account credentials
4. Customize for your specific club and time slots
5. Deploy to GitHub Actions or chosen platform
6. Monitor and iterate based on success rate