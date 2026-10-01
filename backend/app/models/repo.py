"""All SQL lives here. Every user-facing query is scoped by user_id."""
from .db import cursor

FILE_UPDATABLE = {"status", "restore_status", "storage_key"}
BACKUP_UPDATABLE = {"status", "provider_hash", "uploaded_at", "verified_at", "error_message", "duration_ms"}


def one(sql, params=()):
    with cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()


def many(sql, params=()):
    with cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def run(sql, params=()):
    with cursor() as cur:
        cur.execute(sql, params)


# ---- users / simulation -------------------------------------------------
def upsert_user(user_id, email):
    run("insert into users(id,email) values(%s,%s) on conflict (id) do update set email=excluded.email",
        (user_id, email))


def get_simulation(user_id):
    return one("select b2_down, supabase_down from simulation where user_id=%s", (user_id,)) or {
        "b2_down": False, "supabase_down": False}


def set_simulation(user_id, email, b2_down, supabase_down):
    upsert_user(user_id, email)
    run("""insert into simulation(user_id,b2_down,supabase_down) values(%s,%s,%s)
           on conflict (user_id) do update set b2_down=excluded.b2_down,
           supabase_down=excluded.supabase_down, updated_at=now()""", (user_id, b2_down, supabase_down))


# ---- files ---------------------------------------------------------------
def find_by_hash(user_id, sha):
    return one("select * from files where user_id=%s and sha256=%s", (user_id, sha))


def insert_file(file_id, user_id, email, filename, size, mime, sha, description, storage_key):
    upsert_user(user_id, email)
    return one("""insert into files(id,user_id,filename,size,mime_type,sha256,description,storage_key,status)
                  values(%s,%s,%s,%s,%s,%s,%s,%s,'UPLOADING') returning *""",
               (file_id, user_id, filename, size, mime, sha, description, storage_key))


def get_file(file_id, user_id=None):
    """user_id=None is only used by the system job (scripts/backup_check.py)."""
    sql, params = "select * from files where id=%s", [file_id]
    if user_id:
        sql, params = sql + " and user_id=%s", params + [user_id]
    f = one(sql, params)
    if f:
        f["backups"] = many("select * from backups where file_id=%s order by provider", (file_id,))
    return f


def list_files(user_id, status=None, limit=200):
    sql, params = "select * from files where user_id=%s", [user_id]
    if status:
        sql, params = sql + " and status=%s", params + [status]
    files = many(sql + " order by created_at desc limit %s", params + [limit])
    return _attach_backups(files)


def _attach_backups(files):
    if files:
        rows = many("select * from backups where file_id = any(%s::uuid[]) order by provider",
                    ([f["id"] for f in files],))
        by = {}
        for r in rows:
            by.setdefault(r["file_id"], []).append(r)
        for f in files:
            f["backups"] = by.get(f["id"], [])
    return files


def update_file(file_id, **fields):
    fields = {k: v for k, v in fields.items() if k in FILE_UPDATABLE}
    if fields:
        sets = ", ".join(f"{k}=%s" for k in fields)
        run(f"update files set {sets} where id=%s", (*fields.values(), file_id))


def delete_file(file_id):
    run("delete from files where id=%s", (file_id,))


def upsert_backup(file_id, provider, **fields):
    fields = {k: v for k, v in fields.items() if k in BACKUP_UPDATABLE}
    cols = ["file_id", "provider", *fields]
    sets = ", ".join(f"{k}=excluded.{k}" for k in fields) or "provider=excluded.provider"
    run(f"insert into backups({','.join(cols)}) values({','.join(['%s'] * len(cols))}) "
        f"on conflict (file_id, provider) do update set {sets}", (file_id, provider, *fields.values()))


def add_event(file_id, event_type, message):
    run("insert into backup_events(file_id,event_type,message) values(%s,%s,%s)", (file_id, event_type, message))


def list_events(file_id, limit=30):
    return many("select event_type,message,created_at from backup_events where file_id=%s "
                "order by created_at desc limit %s", (file_id, limit))


def total_bytes(user_id):
    return one("select coalesce(sum(size),0)::bigint b from files where user_id=%s", (user_id,))["b"]


def uploads_today(user_id):
    return one("select count(*)::int c from files where user_id=%s and created_at >= date_trunc('day', now())",
               (user_id,))["c"]


# ---- system job helpers ----------------------------------------------------
def incomplete_files():
    files = many("""select * from files where status in ('PARTIAL','FAILED')
                    or (status in ('PENDING','UPLOADING') and created_at < now() - interval '15 minutes')
                    order by created_at""")
    return _attach_backups(files)


def files_to_verify(limit):
    files = many("""select f.* from files f where f.status='VERIFIED'
                    order by (select min(verified_at) from backups b where b.file_id=f.id) nulls first
                    limit %s""", (limit,))
    return _attach_backups(files)


# ---- dashboard / history ---------------------------------------------------
def history(user_id, status=None, limit=200):
    return list_files(user_id, status, limit)


def status_counts(user_id):
    rows = many("select status, count(*)::int c from files where user_id=%s group by status", (user_id,))
    return {r["status"]: r["c"] for r in rows}


def dashboard(user_id):
    totals = one("""select count(*)::int files, coalesce(sum(size),0)::bigint bytes,
        count(*) filter (where status='VERIFIED')::int verified,
        count(*) filter (where status='FAILED')::int failed,
        count(*) filter (where status='PARTIAL')::int partial,
        count(*) filter (where status in ('PENDING','UPLOADING'))::int pending,
        count(*) filter (where created_at >= date_trunc('day', now()))::int uploads_today
        from files where user_id=%s""", (user_id,))
    per = {r["provider"]: r["used"] for r in many(
        """select b.provider, coalesce(sum(f.size),0)::bigint used from backups b
           join files f on f.id=b.file_id where f.user_id=%s and b.status='VERIFIED'
           group by b.provider""", (user_id,))}
    perf = one("""select count(*) filter (where b.status='VERIFIED')::int ok, count(*)::int total,
        coalesce(avg(b.duration_ms) filter (where b.status='VERIFIED'),0)::int avg_ms,
        max(b.verified_at) last_ok from backups b join files f on f.id=b.file_id
        where f.user_id=%s and b.status in ('VERIFIED','FAILED')""", (user_id,))
    trend = many("""select to_char(d,'MM-DD') as day, coalesce(t.ok,0)::int ok, coalesce(t.bad,0)::int bad
        from generate_series(current_date-6, current_date, interval '1 day') d
        left join (select b.uploaded_at::date as day, count(*) filter (where b.status='VERIFIED') as ok,
                   count(*) filter (where b.status='FAILED') bad
                   from backups b join files f on f.id=b.file_id
                   where f.user_id=%s and b.uploaded_at >= current_date-6 group by 1) t on t.day=d::date
        order by d""", (user_id,))
    recent = many("select id, filename, status, created_at from files where user_id=%s "
                  "order by created_at desc limit 5", (user_id,))
    return totals, per, perf, trend, recent
