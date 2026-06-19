-- ─────────────────────────────────────────────────────────────────────────────
-- Migration 002 — Strategy Studio: briefs, brief_stages, war_room_messages
-- Run this in the Supabase SQL editor.
-- ─────────────────────────────────────────────────────────────────────────────

-- ── briefs ────────────────────────────────────────────────────────────────────
-- Master record for a client engagement. Lives across all 5 stages.

create table if not exists briefs (
  brief_id          text primary key,
  client_name       text not null,
  client_email      text,
  industry          text not null,
  challenges        jsonb not null default '[]',
  raw_input         text not null,           -- client's original words, always preserved
  budget_inr        integer,
  timeline_weeks    integer,
  inspiration_brand text,
  inspiration_admiration text,
  innovation_technique   text,
  status            text not null default 'intake_received',
  assigned_to       text,
  created_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now()
);

-- Status values:
-- intake_received | debrief_sent | client_confirmed | read_in_progress
-- situation_ready | situation_released | strategy_ready | strategy_released
-- recommendation_ready | recommendation_released


-- ── brief_stages ──────────────────────────────────────────────────────────────
-- One row per stage per brief. Stores internal draft + released client content.

create table if not exists brief_stages (
  id                uuid primary key default gen_random_uuid(),
  brief_id          text not null references briefs(brief_id) on delete cascade,
  stage             text not null,           -- debrief | read | situation | strategy | recommendation
  -- Internal (consultant + AI only — never exposed to client)
  internal_notes    text not null default '',
  ai_angles         jsonb not null default '[]',
  selected_angle    text,
  -- Client-facing (populated when ready to release)
  headline          text not null default '',
  body              text not null default '',
  -- Release gate
  is_released       boolean not null default false,
  released_at       timestamptz,
  created_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now(),
  unique (brief_id, stage)
);


-- ── war_room_messages ─────────────────────────────────────────────────────────
-- Full conversation log between consultant and AI for each brief.
-- Never exposed to the client.

create table if not exists war_room_messages (
  message_id    uuid primary key default gen_random_uuid(),
  brief_id      text not null references briefs(brief_id) on delete cascade,
  role          text not null check (role in ('ai', 'consultant')),
  content       text not null,
  message_type  text not null default 'standard',
  -- message_type values:
  -- opening_briefing | angle_suggestion | corpus_reference | draft_content
  -- consultant_message | standard
  pinned        boolean not null default false,
  created_at    timestamptz not null default now()
);

create index if not exists war_room_messages_brief_id_idx
  on war_room_messages (brief_id, created_at);


-- ── Helper: updated_at trigger ────────────────────────────────────────────────

create or replace function set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists briefs_updated_at on briefs;
create trigger briefs_updated_at
  before update on briefs
  for each row execute function set_updated_at();

drop trigger if exists brief_stages_updated_at on brief_stages;
create trigger brief_stages_updated_at
  before update on brief_stages
  for each row execute function set_updated_at();


-- ── Row-Level Security (recommended) ─────────────────────────────────────────
-- Uncomment and configure after confirming auth setup.

-- alter table briefs          enable row level security;
-- alter table brief_stages    enable row level security;
-- alter table war_room_messages enable row level security;
