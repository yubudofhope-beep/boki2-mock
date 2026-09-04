-- 簿記2級 模試メーカー：Supabase のテーブル作成
-- Supabase の画面左「SQL Editor」に貼り付けて「Run」を押すだけです。

create table if not exists users (
    name       text primary key,
    created_at timestamptz not null default now()
);

create table if not exists logins (
    id        bigserial primary key,
    user_name text not null,
    at        timestamptz not null default now()
);

create table if not exists results (
    id        bigserial primary key,
    user_name text not null,
    at        timestamptz not null default now(),
    seed      bigint,
    total     real,
    passed    boolean,
    per_part  jsonb,
    per_topic jsonb,
    used      jsonb
);

create table if not exists issued (
    id        bigserial primary key,
    user_name text not null,
    at        timestamptz not null default now(),
    used      jsonb
);

create index if not exists idx_results_user on results (user_name, at);
create index if not exists idx_logins_user  on logins  (user_name, at);
create index if not exists idx_issued_user  on issued  (user_name, id desc);

-- アプリから anon キーで読み書きするため、この4つのテーブルは行レベルセキュリティを外します。
-- （保存されるのは名前と点数だけです。個人情報や本名は入れないでください）
alter table users   disable row level security;
alter table logins  disable row level security;
alter table results disable row level security;
alter table issued  disable row level security;
