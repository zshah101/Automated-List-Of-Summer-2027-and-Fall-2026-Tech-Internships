-- Supabase schema.
--
-- Two independent things live here:
--   1. email_subscribers — the digest list. Committed so the privacy claims in
--      PRIVACY.md are checkable rather than something you take on trust.
--   2. companies / jobs / scrape_runs — the optional Postgres mirror written by
--      src/intern_engine/db.py. These MUST match what `db.sync` actually writes;
--      a schema that merely looks reasonable makes the mirror fail silently.
--
-- Apply this as a versioned migration: run
--   supabase migration new intern_engine_schema
-- copy this file into the generated supabase/migrations/*.sql file, then run
--   supabase db push
-- against the linked project. For a one-off install, paste the complete file
-- into the Supabase SQL editor. Do not deploy the site writer until this
-- migration has succeeded: db.py calls the RPC defined at the end of the file.
--
-- APPLYING THIS IS NOT OPTIONAL, and shipping the site without it fails
-- silently in the one way nobody checks. The double opt-in flow shipped on
-- 2026-08-06; this file was never run against the live project, so the signup
-- form POSTed to /rpc/request_email_subscription — a function that did not
-- exist — and 404'd for 40 days. The dashboard showed no error and the engine
-- never touched that path, so the only symptom was a subscriber count that
-- stopped moving. The email_subscribers half of this file was applied to the
-- live project on 2026-09-15 (224 subscribers preserved, unsub_token converted
-- uuid -> text in place); the mirror half below predates it.

-- pgcrypto supplies gen_random_bytes for the secret tokens below. On
-- Supabase it is installed into the `extensions` schema, NOT public, so every
-- call is schema-qualified: a security definer function pinned to
-- `search_path = public` cannot see an unqualified gen_random_bytes and fails
-- at creation with 42883.
create extension if not exists pgcrypto with schema extensions;

-- ---------------------------------------------------------------------------
-- Email subscribers
-- ---------------------------------------------------------------------------
-- Security model: the anon key can call narrow request/confirm/unsubscribe RPCs
-- but cannot read or mutate the table. New addresses stay pending until the
-- mailbox owner uses a per-request confirmation token.

create table if not exists public.email_subscribers (
    id           uuid primary key default gen_random_uuid(),
    email        text        not null,
    -- The secret in the unsubscribe URL. Random per subscriber, so knowing one
    -- tells you nothing about any other.
    unsub_token  text        not null unique default encode(extensions.gen_random_bytes(24), 'hex'),
    confirmation_token text not null unique default encode(extensions.gen_random_bytes(24), 'hex'),
    -- Existing installations are backfilled as confirmed below. The default
    -- is then removed so every new request must complete double opt-in.
    confirmed_at timestamptz default now(),
    confirmation_sent_at timestamptz,
    created_at   timestamptz not null default now()
);

-- Convert the legacy case-sensitive address key without a gap in uniqueness.
-- The table lock, duplicate reconciliation, and new index are one transaction:
-- an invalid legacy row or failed index build rolls the whole migration back.
begin;
lock table public.email_subscribers in access exclusive mode;

-- The first installation typed unsub_token as uuid default gen_random_uuid().
-- `create table if not exists` above leaves that alone, so unsubscribe_email
-- below (text) would be created as a SECOND overload against a uuid column:
-- PostgREST then cannot resolve /rpc/unsubscribe_email and every unsubscribe
-- link 300s. Convert in place instead. ::text yields the exact hyphenated
-- string those links already carry, so no live unsubscribe URL breaks.
do $$
begin
    if exists (
        select 1 from information_schema.columns
         where table_schema = 'public' and table_name = 'email_subscribers'
           and column_name = 'unsub_token' and data_type = 'uuid'
    ) then
        alter table public.email_subscribers alter column unsub_token drop default;
        alter table public.email_subscribers
            alter column unsub_token type text using unsub_token::text;
    end if;
end $$;
alter table public.email_subscribers alter column unsub_token
    set default encode(extensions.gen_random_bytes(24), 'hex');
drop function if exists public.unsubscribe_email(uuid);

-- Added WITHOUT a default and then filled per row: ADD COLUMN with a volatile
-- default is not a dependable way to give N existing rows N DISTINCT secrets,
-- and one shared confirmation token across the whole list is a vulnerability,
-- not a cosmetic issue.
alter table public.email_subscribers add column if not exists
    confirmation_token text;
update public.email_subscribers
   set confirmation_token = encode(extensions.gen_random_bytes(24), 'hex')
 where confirmation_token is null;
alter table public.email_subscribers
    alter column confirmation_token set not null;
alter table public.email_subscribers alter column confirmation_token
    set default encode(extensions.gen_random_bytes(24), 'hex');
alter table public.email_subscribers add column if not exists
    confirmed_at timestamptz default now();
alter table public.email_subscribers add column if not exists
    confirmation_sent_at timestamptz;
alter table public.email_subscribers alter column confirmed_at drop default;

-- A legacy case-sensitive constraint allowed Alice@example.com and
-- alice@example.com to coexist. Prefer the oldest confirmed row (so its active
-- unsubscribe token survives), merge confirmation history, then remove only
-- the redundant active rows. Unsubscribed addresses are represented by absence
-- from this table, so the migration cannot resurrect them.
create temporary table email_subscriber_survivors on commit drop as
select
    lower(trim(email)) as normalized_email,
    (array_agg(
        id order by (confirmed_at is not null) desc, created_at asc, id asc
    ))[1] as survivor_id,
    min(confirmed_at) as confirmed_at,
    max(confirmation_sent_at) as confirmation_sent_at,
    min(created_at) as created_at
from public.email_subscribers
group by lower(trim(email));

delete from public.email_subscribers as duplicate
using pg_temp.email_subscriber_survivors as survivor
where lower(trim(duplicate.email)) = survivor.normalized_email
  and duplicate.id <> survivor.survivor_id;

update public.email_subscribers as subscriber
set email = survivor.normalized_email,
    confirmed_at = survivor.confirmed_at,
    confirmation_sent_at = survivor.confirmation_sent_at,
    created_at = survivor.created_at
from pg_temp.email_subscriber_survivors as survivor
where subscriber.id = survivor.survivor_id;

alter table public.email_subscribers
    drop constraint if exists email_subscribers_email_key;
drop index if exists public.email_subscribers_email_ci_idx;
create unique index email_subscribers_email_ci_idx
    on public.email_subscribers (lower(email));
-- The `unique` markers in the create table never reach an existing install,
-- and both of these are secrets matched on directly by the RPCs below.
create unique index if not exists email_subscribers_confirmation_token_idx
    on public.email_subscribers (confirmation_token);
create unique index if not exists email_subscribers_unsub_token_idx
    on public.email_subscribers (unsub_token);

alter table public.email_subscribers
    drop constraint if exists email_shape;
alter table public.email_subscribers
    add constraint email_shape check (email ~ '^[^@[:space:]]+@[^@[:space:]]+\.[^@[:space:]]+$');

commit;

alter table public.email_subscribers enable row level security;

-- No direct table policy. The digest sender uses the service key (RLS bypass);
-- public clients can only execute the narrow functions below.
drop policy if exists "anon can subscribe" on public.email_subscribers;
drop policy if exists "public signup" on public.email_subscribers;

revoke all on public.email_subscribers from anon, authenticated;

create or replace function public.request_email_subscription(address text)
returns void
language plpgsql
security definer
set search_path = public, extensions
as $$
declare
    normalized text := lower(trim(address));
begin
    -- Always return the same shape: invalid/existing addresses are not a
    -- public membership oracle.
    if normalized !~ '^[^@[:space:]]+@[^@[:space:]]+\.[^@[:space:]]+$' then
        return;
    end if;
    insert into public.email_subscribers (email, confirmed_at)
    values (normalized, null)
    on conflict ((lower(email))) do update
    set confirmation_token = case
            when email_subscribers.confirmed_at is null
             and coalesce(email_subscribers.confirmation_sent_at, '-infinity')
                 < now() - interval '24 hours'
            then encode(extensions.gen_random_bytes(24), 'hex')
            else email_subscribers.confirmation_token end,
        confirmation_sent_at = case
            when email_subscribers.confirmed_at is null
             and coalesce(email_subscribers.confirmation_sent_at, '-infinity')
                 < now() - interval '24 hours'
            then null else email_subscribers.confirmation_sent_at end;
end;
$$;

create or replace function public.confirm_email_subscription(token text)
returns void
language sql
security definer
set search_path = public, extensions
as $$
    update public.email_subscribers
       set confirmed_at = coalesce(confirmed_at, now()),
           confirmation_token = encode(extensions.gen_random_bytes(24), 'hex')
     where confirmation_token = token;
$$;

create or replace function public.unsubscribe_email(token text)
returns void
language sql
security definer
set search_path = public, extensions
as $$
    delete from public.email_subscribers where unsub_token = token;
$$;

revoke all on function public.unsubscribe_email(text) from public;
grant execute on function public.unsubscribe_email(text) to anon, authenticated;
revoke all on function public.request_email_subscription(text) from public;
grant execute on function public.request_email_subscription(text) to anon, authenticated;
revoke all on function public.confirm_email_subscription(text) from public;
grant execute on function public.confirm_email_subscription(text) to anon, authenticated;

-- ---------------------------------------------------------------------------
-- Run mirror (optional; service key only)
-- ---------------------------------------------------------------------------
-- Written by db.sync when SUPABASE_URL + SUPABASE_SERVICE_KEY are set. Column
-- names and RPC payload fields below are load-bearing: they must match db.py.

create table if not exists public.companies (
    key   text primary key,          -- site-aware registry.board_key(...)
    ats   text not null,
    slug  text not null,
    name  text
);

create table if not exists public.jobs (
    id               text primary key,
    company_key      text references public.companies(key) on delete set null,
    source           text,
    company          text,
    title            text,
    location         text,
    url              text,
    category         text,
    season           text,
    -- Cycles the employer stated, when a posting names more than one.
    seasons          text[],
    -- False = the employer named the cycle; true = we inferred it from the
    -- posting date. The single most important qualifier on this table.
    season_inferred  boolean,
    region           text,
    sponsorship      text,
    salary           text,
    skills           text[],
    posted_at        timestamptz,
    -- exact | date_only | relative_derived — how much the date above is worth.
    posted_at_source text,
    first_seen_at    timestamptz,
    last_seen_at     timestamptz,
    closed_at        timestamptz,
    -- gone-from-feed | out-of-scope
    closed_reason    text,
    canonical_id     text,
    requisition_id   text,
    aliases          text[],
    is_open          boolean
);

-- Migration for projects created before these columns existed. `create table
-- if not exists` above is a no-op on an existing table, so without this an
-- older database silently keeps rejecting every write db.py makes (the sync
-- swallows its own errors, so the mirror just quietly stops updating).
-- Safe to re-run: each add is itself `if not exists`.
alter table public.jobs add column if not exists seasons          text[];
alter table public.jobs add column if not exists season_inferred  boolean;
alter table public.jobs add column if not exists salary           text;
alter table public.jobs add column if not exists skills           text[];
alter table public.jobs add column if not exists posted_at_source text;
alter table public.jobs add column if not exists closed_at        timestamptz;
alter table public.jobs add column if not exists closed_reason    text;
alter table public.jobs add column if not exists company_key      text;
alter table public.jobs add column if not exists region           text;
alter table public.jobs add column if not exists canonical_id     text;
alter table public.jobs add column if not exists requisition_id   text;
alter table public.jobs add column if not exists aliases          text[];

create index if not exists jobs_open_idx on public.jobs (is_open, posted_at desc);
create index if not exists jobs_company_idx on public.jobs (company_key);

create table if not exists public.scrape_runs (
    id                uuid primary key default gen_random_uuid(),
    created_at        timestamptz not null default now(),
    duration_seconds  numeric,
    companies_total   integer,
    fetched_ok        integer,
    fetch_errors      integer,
    fetch_success_rate numeric,
    roles_matched     integer,
    new_this_run      integer,
    open_total        integer,
    roles_by_source   jsonb,
    roles_by_cycle    jsonb,
    roles_by_region   jsonb,
    detection_latency jsonb,
    fetched_at        timestamptz,
    snapshots_complete integer,
    snapshots_partial integer,
    degraded_fetches  integer
);

alter table public.scrape_runs add column if not exists fetched_at timestamptz;
alter table public.scrape_runs add column if not exists snapshots_complete integer;
alter table public.scrape_runs add column if not exists snapshots_partial integer;
alter table public.scrape_runs add column if not exists degraded_fetches integer;
create index if not exists scrape_runs_fetched_at_idx
    on public.scrape_runs (fetched_at desc);

-- Replace the exact mirror and append its run metric in one transaction. An RPC
-- executes inside the caller's transaction, so any parse, constraint, upsert,
-- delete, or metrics failure rolls every live-table change back. The advisory
-- transaction lock also makes two overlapping scheduled runs settle in order
-- instead of deleting each other's rows.
create or replace function public.replace_mirror_snapshot(
    p_companies jsonb,
    p_jobs jsonb,
    p_run jsonb
)
returns void
language plpgsql
security definer
set search_path = pg_catalog, public
as $$
declare
    incoming_fetched_at timestamptz;
    latest_fetched_at timestamptz;
begin
    perform pg_catalog.pg_advisory_xact_lock(
        pg_catalog.hashtextextended('intern-engine:mirror', 0)
    );

    if p_companies is null or jsonb_typeof(p_companies) <> 'array' then
        raise exception 'p_companies must be a JSON array';
    end if;
    if p_jobs is null or jsonb_typeof(p_jobs) <> 'array' then
        raise exception 'p_jobs must be a JSON array';
    end if;
    if p_run is null or jsonb_typeof(p_run) <> 'object' then
        raise exception 'p_run must be a JSON object';
    end if;

    -- A delayed writer must never replace a newer successful mirror. Parse and
    -- require the source fetch time while holding the writer lock, then compare
    -- it with committed history before touching either live mirror table.
    incoming_fetched_at := nullif(btrim(p_run ->> 'fetched_at'), '')::timestamptz;
    if incoming_fetched_at is null then
        raise exception 'p_run.fetched_at must be a timestamp';
    end if;

    select max(fetched_at)
      into latest_fetched_at
      from public.scrape_runs;

    if latest_fetched_at is not null
       and incoming_fetched_at < latest_fetched_at then
        raise exception 'stale mirror snapshot rejected'
            using detail = format(
                'incoming fetched_at %s is older than current %s',
                incoming_fetched_at,
                latest_fetched_at
            );
    end if;

    -- Parse and validate the complete payload before touching production. The
    -- primary keys reject duplicate payload identities rather than silently
    -- picking an arbitrary winner.
    create temporary table intern_engine_mirror_companies (
        key text primary key,
        ats text not null,
        slug text not null,
        name text
    ) on commit drop;

    create temporary table intern_engine_mirror_jobs (
        id text primary key,
        company_key text not null,
        source text,
        company text,
        title text,
        location text,
        url text,
        category text,
        season text,
        seasons text[],
        season_inferred boolean,
        region text,
        sponsorship text,
        salary text,
        skills text[],
        posted_at timestamptz,
        posted_at_source text,
        first_seen_at timestamptz,
        last_seen_at timestamptz,
        closed_at timestamptz,
        closed_reason text,
        canonical_id text,
        requisition_id text,
        aliases text[],
        is_open boolean
    ) on commit drop;

    insert into pg_temp.intern_engine_mirror_companies (key, ats, slug, name)
    select company.key, company.ats, company.slug, company.name
    from jsonb_to_recordset(p_companies) as company(
        key text, ats text, slug text, name text
    );

    insert into pg_temp.intern_engine_mirror_jobs (
        id, company_key, source, company, title, location, url, category,
        season, seasons, season_inferred, region, sponsorship, salary, skills,
        posted_at, posted_at_source, first_seen_at, last_seen_at, closed_at,
        closed_reason, canonical_id, requisition_id, aliases, is_open
    )
    select
        job.id, job.company_key, job.source, job.company, job.title,
        job.location, job.url, job.category, job.season, job.seasons,
        job.season_inferred, job.region, job.sponsorship, job.salary,
        job.skills, job.posted_at, job.posted_at_source, job.first_seen_at,
        job.last_seen_at, job.closed_at, job.closed_reason, job.canonical_id,
        job.requisition_id, job.aliases, job.is_open
    from jsonb_to_recordset(p_jobs) as job(
        id text, company_key text, source text, company text, title text,
        location text, url text, category text, season text, seasons text[],
        season_inferred boolean, region text, sponsorship text, salary text,
        skills text[], posted_at timestamptz, posted_at_source text,
        first_seen_at timestamptz, last_seen_at timestamptz,
        closed_at timestamptz, closed_reason text, canonical_id text,
        requisition_id text, aliases text[], is_open boolean
    );

    if exists (
        select 1
        from pg_temp.intern_engine_mirror_companies
        where btrim(key) = '' or btrim(ats) = '' or btrim(slug) = ''
    ) then
        raise exception 'company mirror rows require non-blank key, ats, and slug';
    end if;

    if exists (
        select 1
        from pg_temp.intern_engine_mirror_jobs as job
        left join pg_temp.intern_engine_mirror_companies as company
          on company.key = job.company_key
        where btrim(job.id) = ''
           or btrim(job.company_key) = ''
           or company.key is null
    ) then
        raise exception 'job mirror rows require an id and a matching company_key';
    end if;

    insert into public.companies as current_company (key, ats, slug, name)
    select key, ats, slug, name
    from pg_temp.intern_engine_mirror_companies
    on conflict (key) do update
    set ats = excluded.ats,
        slug = excluded.slug,
        name = excluded.name;

    insert into public.jobs as current_job (
        id, company_key, source, company, title, location, url, category,
        season, seasons, season_inferred, region, sponsorship, salary, skills,
        posted_at, posted_at_source, first_seen_at, last_seen_at, closed_at,
        closed_reason, canonical_id, requisition_id, aliases, is_open
    )
    select
        id, company_key, source, company, title, location, url, category,
        season, seasons, season_inferred, region, sponsorship, salary, skills,
        posted_at, posted_at_source, first_seen_at, last_seen_at, closed_at,
        closed_reason, canonical_id, requisition_id, aliases, is_open
    from pg_temp.intern_engine_mirror_jobs
    on conflict (id) do update
    set company_key = excluded.company_key,
        source = excluded.source,
        company = excluded.company,
        title = excluded.title,
        location = excluded.location,
        url = excluded.url,
        category = excluded.category,
        season = excluded.season,
        seasons = excluded.seasons,
        season_inferred = excluded.season_inferred,
        region = excluded.region,
        sponsorship = excluded.sponsorship,
        salary = excluded.salary,
        skills = excluded.skills,
        posted_at = excluded.posted_at,
        posted_at_source = excluded.posted_at_source,
        first_seen_at = excluded.first_seen_at,
        last_seen_at = excluded.last_seen_at,
        closed_at = excluded.closed_at,
        closed_reason = excluded.closed_reason,
        canonical_id = excluded.canonical_id,
        requisition_id = excluded.requisition_id,
        aliases = excluded.aliases,
        is_open = excluded.is_open;

    delete from public.jobs as current_job
    where not exists (
        select 1
        from pg_temp.intern_engine_mirror_jobs as replacement
        where replacement.id = current_job.id
    );

    delete from public.companies as current_company
    where not exists (
        select 1
        from pg_temp.intern_engine_mirror_companies as replacement
        where replacement.key = current_company.key
    );

    insert into public.scrape_runs (
        duration_seconds, companies_total, fetched_ok, fetch_errors,
        fetch_success_rate, roles_matched, new_this_run, open_total,
        roles_by_source, roles_by_cycle, roles_by_region, detection_latency,
        fetched_at, snapshots_complete, snapshots_partial, degraded_fetches
    )
    select
        metric.duration_seconds, metric.companies_total, metric.fetched_ok,
        metric.fetch_errors, metric.fetch_success_rate, metric.roles_matched,
        metric.new_this_run, metric.open_total, metric.roles_by_source,
        metric.roles_by_cycle, metric.roles_by_region, metric.detection_latency,
        metric.fetched_at, metric.snapshots_complete, metric.snapshots_partial,
        metric.degraded_fetches
    from jsonb_to_record(p_run) as metric(
        duration_seconds numeric, companies_total integer, fetched_ok integer,
        fetch_errors integer, fetch_success_rate numeric, roles_matched integer,
        new_this_run integer, open_total integer, roles_by_source jsonb,
        roles_by_cycle jsonb, roles_by_region jsonb, detection_latency jsonb,
        fetched_at timestamptz, snapshots_complete integer,
        snapshots_partial integer, degraded_fetches integer
    )
    -- An equal fetched_at is a safe retry of the same source snapshot. Replace
    -- the mirror again, but do not duplicate the historical run metric.
    where not exists (
        select 1
        from public.scrape_runs as completed_run
        where completed_run.fetched_at = metric.fetched_at
    );
end;
$$;

drop function if exists public.finalize_mirror_snapshot(text);
revoke all on function public.replace_mirror_snapshot(jsonb, jsonb, jsonb)
    from public;
grant execute on function public.replace_mirror_snapshot(jsonb, jsonb, jsonb)
    to service_role;

-- Service-key only: RLS on with no policies means the anon key can't read or
-- write any of these.
alter table public.companies   enable row level security;
alter table public.jobs        enable row level security;
alter table public.scrape_runs enable row level security;
