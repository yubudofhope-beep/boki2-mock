-- 簿記2級 模試メーカー：Supabase のテーブル作成
-- Supabase の画面左「SQL Editor」に貼り付けて「Run」を押すだけです。

create table if not exists users (
    name       text primary key,
    created_at timestamptz not null default now(),
    pin_salt   text,
    pin_hash   text
);

-- すでにテーブルを作ってある場合は、この2行で列を追加します（合言葉ログイン用）
alter table users add column if not exists pin_salt text;
alter table users add column if not exists pin_hash text;

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

-- 行レベルセキュリティを有効にします。ポリシーを1つも作らないので、
-- anon キー（公開キー）では読み書きが一切できません。
-- アプリは service_role キーを使い、RLSをバイパスしてアクセスします。
-- ※ service_role キーは絶対に公開しないこと（Streamlit の Secrets と
--   ローカルの .streamlit/secrets.toml にだけ置く）
alter table users   enable row level security;
alter table logins  enable row level security;
alter table results enable row level security;
alter table issued  enable row level security;
