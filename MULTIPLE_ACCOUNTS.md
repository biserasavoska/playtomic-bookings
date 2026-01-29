# Using multiple Playtomic accounts (e.g. one for Tuesdays, one for Wednesdays)

You can use **several Playtomic logins** in one run. Each account can be limited to specific **weekdays**, so one person books Tuesdays and another Wednesdays (or any split you want).

## How it works

- **One run** (e.g. every day at 8:25 CET): the script tries **each account** in order.
- For each account it only looks at **that account’s** `target_weekdays` (e.g. Tuesday only, Wednesday only).
- Each account can book **at most one** court per run (same as `reservations_per_week`).
- So in a single run you can get e.g. **one Tuesday** (account A) and **one Wednesday** (account B).

## Setup

### 1. Config: add an `accounts` list

In **config/booking_config.yaml**, add an **`accounts`** section. For each account you need:

- **env_email** – name of the env var for that account’s email (e.g. `PLAYTOMIC_EMAIL_TUESDAY`).
- **env_password** – name of the env var for that account’s password (e.g. `PLAYTOMIC_PASSWORD_TUESDAY`).
- **target_weekdays** – weekdays that account is allowed to book.  
  `0` = Monday, `1` = Tuesday, `2` = Wednesday, `3` = Thursday, `4` = Friday, `5` = Saturday, `6` = Sunday.

Example: one account for Tuesdays, one for Wednesdays:

```yaml
accounts:
  - env_email: PLAYTOMIC_EMAIL_TUESDAY
    env_password: PLAYTOMIC_PASSWORD_TUESDAY
    target_weekdays: [1]   # Tuesday only
  - env_email: PLAYTOMIC_EMAIL_WEDNESDAY
    env_password: PLAYTOMIC_PASSWORD_WEDNESDAY
    target_weekdays: [2]   # Wednesday only
```

The rest of the config (tenants, target_hours, duration_hours, etc.) is **shared** by all accounts. Only the **weekdays** and **credentials** change per account.

### 2. Credentials: set env vars for each account

**Locally (`.env`):**

```env
PLAYTOMIC_EMAIL_TUESDAY=person1@example.com
PLAYTOMIC_PASSWORD_TUESDAY=person1_password
PLAYTOMIC_EMAIL_WEDNESDAY=person2@example.com
PLAYTOMIC_PASSWORD_WEDNESDAY=person2_password
```

**On GitHub (Actions):**

In the repo: **Settings → Secrets and variables → Actions**, add:

- `PLAYTOMIC_EMAIL_TUESDAY`
- `PLAYTOMIC_PASSWORD_TUESDAY`
- `PLAYTOMIC_EMAIL_WEDNESDAY`
- `PLAYTOMIC_PASSWORD_WEDNESDAY`

Use the same names as in `env_email` and `env_password` in the config.

### 3. Single account (no `accounts`)

If you **don’t** add an `accounts` section, the script keeps using the **single** account:

- **PLAYTOMIC_EMAIL**
- **PLAYTOMIC_PASSWORD**

and the main **target_weekdays** from the config (e.g. Mon–Fri).

## Summary

- **Multiple logins:** add `accounts` in **config/booking_config.yaml** with `env_email`, `env_password`, and `target_weekdays` per account.
- **Different dates per account:** set each account’s `target_weekdays` (e.g. `[1]` Tuesday, `[2]` Wednesday).
- **Credentials:** set the corresponding env vars (or GitHub Secrets) for each account.
- One run tries all accounts; each can book once on its weekdays.
